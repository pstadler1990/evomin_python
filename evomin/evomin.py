#!/usr/bin/env python
# -*- coding: utf-8 -*
from __future__ import annotations
from enum import Enum
from evomin.communication import EvominComInterface
from queue import Queue, Full
from evomin.config import config
from evomin.frame import EvominFrame, EvominFrameMessageType
from evomin.state import *
import logging


class EvominState(Enum):
    """
    EvominState are used to describe the current internal state while sending and / or receiving EvominFrames.

    UNDEFINED: Before initialization or error while initialization
    INIT: EvominInterface is being initialized
    IDLE: Waiting for the beginning of a reception / transmission process (waiting for SOF byte)
    SOF: Start Of Frame byte received, next state: SOF2
    SOF2: Start Of Frame second byte received -> next state: CMD
    CMD: Command byte received -> next state: LEN
    LEN: Payload length received -> next state: CRC
    CRC: CRC byte received -> next state: EOF on successful crc check, CRC_FAIL on crc failure
    REPLY_CREATEFRAME: Used for direct communication i.e. UART to prepare a new frame (only for compatibility reasons)
    REPLY: Slave is sending reply bytes (direct answer) in a master-slave communication
    MSG_SENT_WAIT_FOR_ACK: Used for direct communication to acknowledge a sent frame (only for compatibility reasons)
    ERROR: Any error happened while in a state IDLE..MSG_SENT_WAIT_FOR_ACK
    """
    UNDEFINED = 0
    INIT = 1
    IDLE = 2
    SOF = 3
    SOF2 = 4
    CMD = 5
    LEN = 6
    PAYLD = 7
    CRC = 8
    CRC_FAIL = 9
    EOF = 10
    REPLY_CREATEFRAME = 11
    REPLY = 12
    MSG_SENT_WAIT_FOR_ACK = 13
    ERROR = 14


class StateMachine:
    """
    Internal state machine to handle both, transmission and reception of data and EvominFrames
    """
    def __init__(self, evomin_interface: Evomin):
        self.state_idle = self.StateIdle(self, evomin_interface, EvominFrameMessageType.SOF)
        self.state_sof = self.StateSof(self, evomin_interface, EvominFrameMessageType.SOF)
        self.state_sof2 = self.StateSof2(self, evomin_interface, EvominFrameMessageType.SOF)
        self.state_cmd = self.StateCmd(self, evomin_interface)
        self.state_len = self.StateLen(self, evomin_interface)
        self.state_payld = self.StatePayld(self, evomin_interface)
        self.state_crc = self.StateCRC(self, evomin_interface)
        self.state_crc_fail = self.StateCRCFail(self, evomin_interface)
        self.state_eof = self.StateEof(self, evomin_interface, EvominFrameMessageType.EOF)
        self.state_reply = self.StateReply(self, evomin_interface)
        self.state_reply_createframe = self.StateReplyCreateFrame(self, evomin_interface)
        self.state_error = self.StateError(self, evomin_interface)
        self.interface = evomin_interface
        self.current_state: State = self.state_idle

    def reset(self):
        self.current_state = self.state_idle

    def run(self, byte: int) -> None:
        """
        Run the current state (code execution and state translation)
        :param byte: current received byte (from the low-level receive handler)
        """
        self.current_state = self.current_state.run(byte)

    class StateIdle(State):
        """Waiting for start of frames"""
        def proceed(self, byte: int) -> State:
            return self.state_machine.state_sof

        def fail(self) -> State:
            return self.state_machine.state_error

    class StateSof(State):
        """Waiting for SOF byte 2"""
        def proceed(self, byte: int) -> State:
            return self.state_machine.state_sof2

        def fail(self) -> State:
            return self.state_machine.state_error

    class StateSof2(State):
        """Waiting for SOF byte 3"""
        def proceed(self, byte: int) -> State:
            return self.state_machine.state_cmd

        def fail(self) -> State:
            return self.state_machine.state_error

    class StateCmd(State):
        """Reading in command identifier"""
        def proceed(self, byte: int) -> State:
            # Initialize a new EvominFrame
            self.interface.current_frame = EvominFrame(command=byte)
            return self.state_machine.state_len

        def fail(self) -> State:
            return self.state_machine.state_error

    class StateLen(State):
        """Reading in payload length"""
        def proceed(self, byte: int) -> State:
            self.interface.current_frame.payload_length = byte
            if byte > 0:
                return self.state_machine.state_payld
            else:
                if not self.interface.current_frame.payload_length and self.interface.com_interface.describe().is_master_slave:
                    # On a master-slave communication interface, call the frame_received handler early, to allow
                    # the slave to prepare a reply
                    self.interface.frame_received(self.interface.current_frame)
                return self.state_machine.state_crc

        def fail(self) -> State:
            return self.state_machine.state_error

    class StatePayld(State):
        """Processing and copying payload"""
        def proceed(self, byte: int) -> State:
            # For the reception of a frame body if two 0xAA bytes in a row are received
            # then the next received byte is discarded
            if self.interface.current_frame.last_byte_was_stfbyt:
                self.interface.current_frame.last_byte_was_stfbyt = False
                self.interface.current_frame.last_byte = EvominFrameMessageType.STFBYT
                print('Ignoring additional stuff byte..')
                return self
            if byte == EvominFrameMessageType.SOF \
                    and self.interface.current_frame.last_byte == EvominFrameMessageType.SOF:
                # Stuff byte detected
                self.interface.current_frame.last_byte_was_stfbyt = True

            # Store payload data in the payload buffer
            if self.interface.current_frame.payload_length:
                try:
                    self.interface.current_frame.add_payload(byte)

                    if self.interface.current_frame.payload_buffer.size == self.interface.current_frame.payload_length:
                        # We've copied everything into the payload buffer
                        self.interface.current_frame.finalize()

                        if self.interface.com_interface.describe().is_master_slave:
                            # On a master-slave communication interface, call the frame_received handler early, to allow
                            # the slave to prepare a reply
                            self.interface.frame_received(self.interface.current_frame)

                        return self.state_machine.state_crc
                    else:
                        return self
                except Full:
                    return self.fail()
            else:
                return self.fail()

        def fail(self) -> State:
            return self.state_machine.state_error

    class StateCRC(State):
        """CRC calculation and check"""
        def proceed(self, byte: int) -> State:
            if byte == self.interface.current_frame.crc8:
                self.interface.current_frame.is_valid = True
                if self.interface.com_interface.describe().is_master_slave:
                    # Send ACK byte to acknowledge reception of message (pre-fill TX buffer to be ready at the EOF byte)
                    self.interface.com_interface.send_byte(EvominFrameMessageType.ACK)
                return self.state_machine.state_eof
            else:
                if self.interface.com_interface.describe().is_master_slave:
                    # Send NACK byte to cancel any further sender communication
                    self.interface.com_interface.send_byte(EvominFrameMessageType.NACK)
                return self.fail()

        def fail(self) -> State:
            return self.state_machine.state_crc_fail

    class StateCRCFail(State):
        """Failed crc check"""
        def proceed(self, byte: int) -> State:
            return self.fail()

        def fail(self) -> State:
            # Call the error state directly, as there's no further data reception after this state
            self.interface.log_error('CRC8 failed')
            self.state_machine.state_error.run(0)
            # We can safely return to the idle state here
            return self.state_machine.state_idle

    class StateEof(State):
        """Waiting for end of frame"""
        def proceed(self, byte: int) -> State:
            if self.interface.current_frame.is_valid:
                if self.interface.com_interface.describe().is_master_slave:
                    # Send number of reply bytes
                    self.interface.com_interface.send_byte(self.interface.current_frame.answer_buffer.size)
                    return self.state_machine.state_reply
                else:
                    # Send ACK
                    self.interface.com_interface.send_byte(EvominFrameMessageType.ACK)
                    self.interface.frame_received(self.state_machine.interface.current_frame)
                    return self.state_machine.state_idle
            else:
                return self.fail()

        def fail(self) -> State:
            return self.state_machine.state_error

    class StateReply(State):
        """
        On a master-slave based communication (like SPI, I2C) one can reply directly on a received EvominFrame
        using the provided reply(..) method within the frame_received(..) handler.
        """
        def proceed(self, byte: int) -> State:
            if self.interface.current_frame.answer_buffer.size:
                # Pop byte
                reply_byte: int = self.interface.current_frame.answer_buffer.get()
                self.interface.com_interface.send_byte(reply_byte)
                return self
            return self.state_machine.state_idle

        def fail(self) -> State:
            return self.state_machine.state_error

    class StateReplyCreateFrame(State):
        def proceed(self, byte: int) -> State:
            return self.state_machine.state_idle  # TODO

        def fail(self) -> State:
            return self.state_machine.state_error

    class StateError(State):
        """
        Whenever something terrible happened while receiving a frame, we end up here..
        (except while comparing the checksums, crc errors have their own state)
        """
        def proceed(self, byte: int) -> State:
            # TODO: Check if additional NACK is required here?
            self.interface.log_error('Error while frame reception, discard data')
            return self.state_machine.state_idle

        def fail(self) -> State:
            return self.state_machine.state_error


class Evomin(ABC):
    """
    Evomin is the main entry point to the evomin communication interface
    Note that this class is abstract, as you need to implement some methods, depending on your use case.
    """
    def __init__(self, com_interface: EvominComInterface) -> None:
        """
        Initialize the evomin communication interface
        :param com_interface: An instance of a communication interface implementation (refer to EvominComInterface)
        """
        self.com_interface: EvominComInterface = com_interface
        self.frame_send_queue: Queue = Queue(maxsize=config['interface']['max_queued_frames'])
        self.current_frame = None
        self.state: StateMachine = StateMachine(self)
        self.byte_getter = self.com_interface.receive_byte()

        self._init_logger()

    def _init_logger(self):
        self.enabled = config['logging']['use_logging']
        if self.enabled:
            logging.basicConfig(level=logging.DEBUG, filename=config['logging']['file'], format='%(asctime)s - %(message)s')

    def log_debug(self, message: str) -> None:
        if self.enabled:
            logging.debug(message)

    def log_error(self, message: str) -> None:
        if self.enabled:
            logging.error(message)

    def rx_handler(self) -> None:
        """
        This handler needs to be called periodically (or in a thread / interrupt), i.e. polling, to receive / transmit
        and process bytes and the higher level EvominFrames.
        """
        try:
            incoming_byte: int = next(self.byte_getter)
            if incoming_byte >= 0:
                # Byte received
                print("Received byte: ", incoming_byte)
                self.state.run(incoming_byte)

                if self.current_frame:
                    self.current_frame.last_byte = incoming_byte
        except StopIteration:
            pass

    def reply(self, reply_bytes: bytes) -> None:
        if len(reply_bytes):
            [self.current_frame.answer_buffer.push(b) for b in reply_bytes]

    @abstractmethod
    def frame_received(self, frame: EvominFrame) -> None:
        """
        Blueprint method to be implemented by the user.
        This callback gets called whenever we've received a complete and valid frame.
        Implement this method in your application
        :param frame: The received valid frame including the command, payload and crc
        """
        pass

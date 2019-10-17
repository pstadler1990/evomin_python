#!/usr/bin/env python
# -*- coding: utf-8 -*
from __future__ import annotations
from datetime import datetime
from enum import Enum
from evomin.communication import EvominComInterface
from queue import Queue, Full
from evomin.config import config
from evomin.frame import EvominFrame, EvominFrameMessageType, EvominFrameCommandType, EvominSendFrame
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
        self.state_waiting_for_ack = self.StateWaitingForACK(self, evomin_interface, EvominFrameMessageType.ACK)
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

    class StateWaitingForACK(State):
        """Waiting for ACK in non master-slave mode"""
        def proceed(self, byte: int) -> State:
            return self.state_machine.state_idle

        def fail(self) -> State:
            return self.state_machine.state_error

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

    def poll(self) -> None:
        """

        """
        self._rx_handler()

        # Check for queued frames to be sent
        if not self.frame_send_queue.empty():
            oldest_frame_peek: EvominSendFrame = self.frame_send_queue.queue[0]
            # Check if last try happened a while ago
            if datetime.now().timestamp() - oldest_frame_peek.previous_timestamp.timestamp() >= config['interface']['resend_min_time']:
                oldest_frame: EvominSendFrame = self.frame_send_queue.queue.popleft()
                oldest_frame.previous_timestamp = datetime.now()
                self._send_lowlevel(oldest_frame)

    def _rx_handler(self) -> None:
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

    @abstractmethod
    def reply_received(self, reply_payload: bytes) -> None:
        """
        Blueprint method to be implemented by the user.
        This callback gets called whenever we've received some bytes as a direct reply to a sent frame.
        Implement this method in your application
        :param reply_payload:
        """

    def _queue_frame(self, frame: EvominSendFrame) -> bool:
        # Ensure queue is not full
        try:
            self.frame_send_queue.put(frame)
            return True
        except Full:
            self.log_error('Frame cannot be send, as the queue is full')
            return False

    def _send_lowlevel(self, frame: EvominSendFrame) -> None:
        """

        :param frame:
        """
        print('***** SEND LOWLEVEL *****')
        if frame.retries_left:
            # Send EvominFrame header
            self.com_interface.send_byte(EvominFrameMessageType.SOF)
            self.com_interface.send_byte(EvominFrameMessageType.SOF)
            self.com_interface.send_byte(EvominFrameMessageType.SOF)
            self.com_interface.send_byte(frame.command)
            # Send payload length without the inserted stuff bytes (at this point, payload_length might differ
            # from the real size of the payload buffer, but that's okay!
            self.com_interface.send_byte(frame.payload_length)
            # We actually send the whole payload including the inserted stuff bytes (if any), as the receiver
            # will strip them out
            for b in frame.get_payload():
                self.com_interface.send_byte(b)

            # Send checksum
            self.com_interface.send_byte(frame.crc8)

            # Receive ACK / NACK from receiver in master-slave mode
            receiver_is_ack: bool = (self.com_interface.send_byte(EvominFrameMessageType.EOF) == EvominFrameMessageType.ACK)
            if self.com_interface.describe().is_master_slave:
                if receiver_is_ack:
                    # Receiver replies with number of answer bytes it wants to send back on the second EOF
                    receiver_answer_bytes: int = self.com_interface.send_byte(EvominFrameMessageType.EOF)
                    if receiver_answer_bytes:
                        # Fill reply buffer
                        receiver_bytes_sent: int = 0
                        reply_buffer: bytearray = bytearray()
                        while receiver_bytes_sent < receiver_answer_bytes:
                            reply_buffer.append(self.com_interface.send_byte(EvominFrameMessageType.DUMMY))

                        # Inform user that we've got a reply
                        self.reply_received(reply_buffer)

                    self.com_interface.send_byte(EvominFrameMessageType.ACK)
                    frame.is_sent = True
                else:
                    self.com_interface.send_byte(EvominFrameMessageType.NACK)
                    # Frame hasn't been sent, keep in queue
                    if frame.retries_left - 1 > 0:
                        frame.retries_left -= 1
                        # Enqueue frame again
                        self.frame_send_queue.queue.appendleft(frame)
                        return
                    else:
                        print('Frame dropped, as it could not be sent')
                        # Frame is already removed from the queue at this point
            else:
                # In non-sync mode (master-slave, i.e. UART), set the internal state machine to waiting_for_ack
                # as we expect to receive a ACK / NACK at the end of each transmission
                self.state.current_state = self.state.state_reply_createframe

    def send(self, command: EvominFrameCommandType, payload: bytes) -> bool:
        """

        :param command:
        :param payload:
        :return: Whether the frame could be enqueued or not
        """
        frame: EvominSendFrame = EvominSendFrame(command.value, payload)
        # Queue Frame (sending won't happen directly, but is processed through a sending queue)
        return self._queue_frame(frame)

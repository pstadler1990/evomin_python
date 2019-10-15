#!/usr/bin/env python
# -*- coding: utf-8 -*
from enum import Enum
from evomin.communication import EvominComInterface
from queue import Queue, Full
from evomin.config import config
from evomin.frame import EvominFrame, EvominFrameMessageType
from evomin.state import *


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

    def __init__(self, evomin_interface: 'Evomin'):
        self.state_idle = self.StateIdle(self, EvominFrameMessageType.SOF)
        self.state_sof = self.StateSof(self, EvominFrameMessageType.SOF)
        self.state_sof2 = self.StateSof2(self, EvominFrameMessageType.SOF)
        self.state_cmd = self.StateCmd(self)
        self.state_len = self.StateLen(self)
        self.state_payld = self.StatePayld(self)
        self.state_crc = self.StateCRC(
            self)  # We assign the required crc at the state with self.state_crc.expect(<the crc>)
        self.state_crc_fail = self.StateCRCFail(self)
        self.state_eof = self.StateEof(self, EvominFrameMessageType.EOF)
        self.state_reply = self.StateReply(self)
        self.state_reply_createframe = self.StateReplyCreateFrame(self)
        self.state_error = self.StateError(self)
        self.interface = evomin_interface
        self.current_state: State = self.state_idle

    def reset(self):
        self.current_state = self.state_idle

    def run(self, byte: int) -> None:
        self.current_state = self.current_state.run(byte)

    class StateIdle(State):
        def proceed(self, byte: int) -> 'State':
            print("State idle PROCEED")
            return self.state_machine.state_sof

        def fail(self) -> 'State':
            print("State idle FAIL")
            return self.state_machine.state_error

    class StateSof(State):
        def proceed(self, byte: int) -> 'State':
            print("State sof PROCEED")
            return self.state_machine.state_sof2

        def fail(self) -> 'State':
            print("State sof FAIL")
            return self.state_machine.state_error

    class StateSof2(State):
        def proceed(self, byte: int) -> 'State':
            print("State sof2 PROCEED")
            return self.state_machine.state_cmd

        def fail(self) -> 'State':
            print("State sof2 FAIL")
            return self.state_machine.state_error

    class StateCmd(State):
        def proceed(self, byte: int) -> 'State':
            print("State cmd PROCEED")
            # Initialize a new EvominFrame
            self.state_machine.interface.current_frame = EvominFrame(command=byte)
            return self.state_machine.state_len

        def fail(self) -> 'State':
            print("State idle FAIL")
            return self.state_machine.state_error

    class StateLen(State):
        def proceed(self, byte: int) -> 'State':
            print("State idle PROCEED")
            self.state_machine.interface.current_frame.payload_len = byte
            return self.state_machine.state_payld if byte > 0 else self.state_machine.state_crc

        def fail(self) -> 'State':
            print("State idle FAIL")
            return self.state_machine.state_error

    class StatePayld(State):
        def proceed(self, byte: int) -> 'State':
            print("State idle PROCEED")
            # For the reception of a frame body if two 0xAA bytes in a row are received
            # then the next received byte is discarded
            if self.state_machine.interface.current_frame.last_byte_was_stfbyt:
                self.state_machine.interface.current_frame.last_byte_was_stfbyt = False
                self.state_machine.interface.current_frame.last_byte = EvominFrameMessageType.STFBYT
                return self
            if byte == EvominFrameMessageType.SOF \
                    and self.state_machine.interface.current_frame.last_byte == EvominFrameMessageType.SOF:
                # Stuff byte detected
                self.state_machine.interface.current_frame.last_byte_was_stfbyt = True

            # Store payload data in the payload buffer
            if self.state_machine.interface.current_frame.payload_buffer.size < self.state_machine.interface.current_frame.payload_length:
                try:
                    self.state_machine.interface.current_frame.payload_buffer.push(byte)
                except Full:
                    self.fail()

        def fail(self) -> 'State':
            print("State idle FAIL")
            return self.state_machine.state_error

    class StateCRC(State):
        def proceed(self, byte: int) -> 'State':
            print("State idle PROCEED")

        def fail(self) -> 'State':
            print("State idle FAIL")

    class StateCRCFail(State):
        def proceed(self, byte: int) -> 'State':
            print("State idle PROCEED")

        def fail(self) -> 'State':
            print("State idle FAIL")

    class StateEof(State):
        def proceed(self, byte: int) -> 'State':
            print("State idle PROCEED")

        def fail(self) -> 'State':
            print("State idle FAIL")

    class StateReply(State):
        def proceed(self, byte: int) -> 'State':
            print("State idle PROCEED")

        def fail(self) -> 'State':
            print("State idle FAIL")

    class StateReplyCreateFrame(State):
        def proceed(self, byte: int) -> 'State':
            print("State idle PROCEED")

        def fail(self) -> 'State':
            print("State idle FAIL")

    class StateError(State):
        def proceed(self, byte: int) -> 'State':
            print("State idle PROCEED")

        def fail(self) -> 'State':
            print("State idle FAIL")


class Evomin:

    def __init__(self, com_interface: EvominComInterface) -> None:
        self.com_interface: EvominComInterface = com_interface
        self.frame_send_queue: Queue = Queue(maxsize=config['interface']['max_queued_frames'])
        self.current_frame: EvominFrame = type(None)
        self.state: StateMachine = StateMachine(self)
        self.byte_getter = self.com_interface.receive_byte()

    def rx_handler(self) -> None:
        incoming_byte: int = next(self.byte_getter)
        if incoming_byte >= 0:
            # Byte received
            print("Received byte: ", incoming_byte)
            self.state.run(incoming_byte)

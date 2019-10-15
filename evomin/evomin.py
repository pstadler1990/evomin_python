#!/usr/bin/env python
# -*- coding: utf-8 -*
from enum import Enum
from typing import Type
from evomin.communication import EvominComInterface
from queue import Queue
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
    def __init__(self):
        self.state_idle = StateIdle(EvominFrameMessageType.SOF)
        self.state_sof = StateSof(EvominFrameMessageType.SOF)
        self.state_sof2 = StateSof2(EvominFrameMessageType.SOF)
        self.state_cmd = StateCmd()
        self.state_len = StateLen()
        self.state_payld = StatePayld()
        self.state_crc = StateCRC()     # We assign the required crc at the state with self.state_crc.expect(<the crc>)
        self.state_crc_fail = StateCRCFail()
        self.state_eof = StateEof(EvominFrameMessageType.EOF)
        self.state_reply = StateReply()
        self.state_reply_createframe = StateReplyCreateFrame()
        self.state_error = StateError()
        self.current_state: State = self.state_idle

    def reset(self):
        self.current_state = self.state_idle

    def run(self, byte: int) -> None:
        self.current_state = self.current_state.run(byte)


class Evomin:

    def __init__(self, com_interface: EvominComInterface) -> None:
        self.com_interface: EvominComInterface = com_interface
        self.frame_send_queue: Queue = Queue(maxsize=config['interface']['max_queued_frames'])
        self.frame_received_queue: Queue = Queue(maxsize=config['interface']['max_queued_frames'])
        self.current_frame: EvominFrame = type(None)
        self.state: StateMachine = StateMachine()
        self.byte_getter = self.com_interface.receive_byte()

    def rx_handler(self) -> None:
        incoming_byte: int = next(self.byte_getter)
        if incoming_byte >= 0:
            # Byte received
            print("Received byte: ", incoming_byte)
            self.state.run(incoming_byte)


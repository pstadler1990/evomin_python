#!/usr/bin/env python
# -*- coding: utf-8 -*
from typing import Optional, Generator
from evomin.buffer import EvominBuffer
from datetime import datetime
from evomin.config import config


class EvominFrameMessageType:
    """
    EvominFrameMessageType indicates the function of specific reserved bytes
    within the evomin protocol.
    SOF: Start Of Frame -> Indicates the beginning of a new EvominFrame
    EOF: End Of Frame -> Indicates the end of a EvominFrame
    STFBYT: Stuff byte -> Special byte that is inserted to prevent false detection of frames
    ACK: Acknowledgement -> Indicates positive reception of a full EvominFrame
    NACK: No Acknowledgement -> Indicates positive reception of a full EvominFrame
    DUMMY: Dummy bytes to keep generating clock signals on master-slave communication interfaces (i.e. SPI)
    """
    SOF = 0xAA
    EOF = 0x55
    STFBYT = 0x55
    ACK = 0xFF
    NACK = 0xFE
    DUMMY = 0xF0


class EvominFrameCommandType:
    """
    EvominFrameCommandType defines all protocol internal command types.
    These can be extended, but sometimes it's better to use a predefined command and add a payload, than extending
    the command list for every new operation.
    RESERVED: Not used
    SEND_IDN: Used for defining a self identification frame
    """
    RESERVED = 0x00
    SEND_IDN = 0xCD


class EvominFrame:

    def __init__(self, command: int, payload: Optional[bytes] = None) -> None:
        """
        Initialize a new EvominFrame to be sent respectively queued. Every communication transaction consists of
        a EvominFrame, as it acts as a wrapper for the internal protocol and is processed through the state machine.
        :param command: EvominFrameCommandType
        :param payload: Any number of bytes - for compatibility with the C API pay attention to the defined maximum
                        payload size
        """
        self.is_sent: bool = False
        self.is_valid: bool = False
        self.command: int = command if command in [EvominFrameCommandType] else EvominFrameCommandType.RESERVED
        self.payload_buffer: EvominBuffer = EvominBuffer(payload)
        self.expected_payload_len: int = len(payload) if payload else 0
        self.crc8: int = 0
        self.timestamp: datetime = datetime.now()
        self.retries_left: int = config['frame']['retry_count']
        self.last_byte_was_stfbyt: bool = False
        self.last_byte: int = -1
        # answerBuffer ?
        # replyBuffer ?

    @property
    def payload(self) -> Generator[int, None, None]:
        for b in self.payload_buffer.buffer.queue:
            yield b

    @payload.setter
    def payload(self, payload: bytes):
        map(self.payload_buffer.buffer.put, payload)

    @property
    def payload_length(self) -> int:
        return self.expected_payload_len

    @payload_length.setter
    def payload_length(self, payload_len: int) -> None:
        self.expected_payload_len = payload_len

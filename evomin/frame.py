#!/usr/bin/env python
# -*- coding: utf-8 -*
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

    def __init__(self, command: EvominFrameCommandType, payload: bytes) -> None:
        """
        Initialize a new EvominFrame to be sent respectively queued. Every communication transaction consists of
        a EvominFrame, as it acts as a wrapper for the internal protocol and is processed through the state machine.
        :param command: EvominFrameCommandType
        :param payload: Any number of bytes - for compatibility with the C API pay attention to the defined maximum
                        payload size
        """
        self.is_sent: bool = False
        self.is_valid: bool = False
        self.command: EvominFrameCommandType = command
        self.buffer: EvominBuffer = EvominBuffer(payload)
        self.crc8: int = 0
        self.timestamp: datetime = datetime.now()
        self.retries_left: int = config['frame']['retry_count']
        # answerBuffer ?
        # replyBuffer ?

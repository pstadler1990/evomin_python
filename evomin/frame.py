#!/usr/bin/env python
# -*- coding: utf-8 -*
from enum import Enum


class EvominFrameMessageType(Enum):
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


class EvominFrame:
    pass

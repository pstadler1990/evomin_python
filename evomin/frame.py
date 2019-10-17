#!/usr/bin/env python
# -*- coding: utf-8 -*
from enum import Enum
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


class EvominFrameCommandType(Enum):
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
        Initialize a new EvominFrame from received bytes.
        Every communication transaction consists of a EvominFrame, as it acts as a wrapper for the internal protocol
        that is processed through the state machine.
        :param command: EvominFrameCommandType
        :param payload: Any number of bytes - for compatibility with the C API pay attention to the defined maximum
                        payload size
        """
        self.is_sent: bool = False
        self.is_valid: bool = False
        self.command: int = command if command in [c.value for c in EvominFrameCommandType] else EvominFrameCommandType.RESERVED
        self.payload_buffer: EvominBuffer = EvominBuffer(payload)
        self.answer_buffer: EvominBuffer = EvominBuffer()
        self.expected_payload_len: int = len(payload) if payload else 0
        self.crc8: int = 0
        self.timestamp: datetime = datetime.now()
        self.retries_left: int = config['frame']['retry_count']
        self.last_byte_was_stfbyt: bool = False
        self.last_byte: int = -1

        self._calculate_frame()

    def _calculate_frame(self):
        payload_tmp: list = []

        crc_tmp: list = [
            self.command,
            self.payload_length,
        ]

        found_pl_header: bool = False
        last_byte: int = -1
        for b in self.payload_buffer.buffer.queue:
            if found_pl_header:
                payload_tmp.append(EvominFrameMessageType.STFBYT)
                last_byte = EvominFrameMessageType.STFBYT
                found_pl_header = False
            # For the transmission of a frame body if two 0xAA bytes in a row are transmitted a stuff byte
            # with value 0x55 is inserted into the transmitted byte stream
            if b == EvominFrameMessageType.SOF and last_byte == EvominFrameMessageType.SOF:
                found_pl_header = True

            last_byte = b

            crc_tmp.append(b)
            payload_tmp.append(b)

        self.payload_buffer.reset()
        [self.payload_buffer.push(b) for b in payload_tmp]
        self.payload_length = self.payload_buffer.size
        self.crc8 = self.calculate_crc8(bytes(crc_tmp))

    def get_payload(self) -> Generator[int, None, None]:
        for b in self.payload_buffer.buffer.queue:
            yield b

    def add_payload(self, payload_byte: int) -> None:
        self.payload_buffer.push(payload_byte)

    def finalize(self) -> None:
        self._calculate_frame()

    @property
    def payload_length(self) -> int:
        return self.expected_payload_len

    @payload_length.setter
    def payload_length(self, payload_len: int) -> None:
        self.expected_payload_len = payload_len

    @staticmethod
    def calculate_crc8(stripped_payload: bytes) -> int:
        crc_initial: int = 0x00
        for b in stripped_payload:
            crc_initial ^= b
            for f in range(8):
                if crc_initial & 1:
                    crc_initial = (crc_initial >> 1) ^ 0x8C
                else:
                    crc_initial >>= 1
        return crc_initial


class EvominSendFrame(EvominFrame):
    """
    EvominSendFrame is a EvominFrame to be sent
    """
    def __init__(self, command: int, payload: bytes) -> None:
        super().__init__(command, payload)

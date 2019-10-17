#!/usr/bin/env python
# -*- coding: utf-8 -*
from typing import Generator
from evomin.communication import EvominComInterface, ComDescription


class EvominFakeSPIInterface(EvominComInterface):
    """
    Fake implementation of the EvominComInterface to mock SPI receive and transmission.
    """
    def __init__(self):
        # self.test_data = bytes([0xAA, 0xAA, 0xAA, 0xCD, 0x4, 0xDE, 0xAD, 0xBE, 0xEF, 0x4E, 0x55, 0x55, 0xF0, 0xF0, 0xF0, 0xF0, 0xF0, 0xF0, 0xF0, 0xF0])
        # self.test_data = bytes([0xAA, 0xAA, 0xAA, 0xCD, 0x4, 0xDE, 0xAD, 0xBE, 0xEF, 0x4E, 0x55, 0x55])
        # self.test_data = bytes([0xAA, 0xAA, 0xAA, 0xCD, 0x0, 0x4E, 0x55, 0x55])
        # self.test_data = bytes([0xAA, 0xAA, 0xAA, 0xCD, 0x0, 0x3D, 0x55, 0x55, 0xF0])
        # self.test_data = bytes([0xAA, 0xAA, 0xAA, 0xCD, 0x4, 0xAA, 0xAA, 0x55, 0xBB, 0xBB, 0xD7, 0x55, 0x55, 0xF0])
        self.test_data: bytes = bytes([170, 170, 170, 205, 8, 170, 170, 85, 170, 170, 85, 170, 170, 85, 187, 255, 159, 85, 85])

    def describe(self):
        return ComDescription(is_master_slave=True)

    def send_byte(self, byte: int) -> int:
        print('-> Send byte: ', byte)

        # Possible implementation of SPI receive / transmit at the same time
        # byte_in = spi_rxtx(byte_out)
        # self.receive_byte(byte_in)
        return 0

    def receive_byte(self) -> Generator[int, None, None]:
        for b in self.test_data:
            yield b
        return

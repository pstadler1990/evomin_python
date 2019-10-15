#!/usr/bin/env python
# -*- coding: utf-8 -*
from typing import Generator

from evomin.communication import EvominComInterface, ComDescription


class EvominFakeSPIInterface(EvominComInterface):
    """
    Concrete implementation of the EvominComInterface to be used with SPI.
    """
    def __init__(self):
        self.test_data = bytes([0xAA, 0xAA, 0xAA, 0xCD, 0x4, 0xDE, 0xAD, 0xBE, 0xEF, 0x4E, 0x55, 0x55])

    def describe(self):
        return ComDescription(is_master_slave=True)

    def send_byte(self, byte: int) -> None:
        # TODO
        pass

    def receive_byte(self) -> Generator[int, None, None]:
        for b in self.test_data:
            yield b
        return

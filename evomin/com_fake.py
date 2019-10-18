#!/usr/bin/env python
# -*- coding: utf-8 -*
from typing import Generator, Optional
from evomin.communication import EvominComInterface, ComDescription


class EvominFakeSPIInterface(EvominComInterface):
    """
    Fake implementation of the EvominComInterface to mock SPI receive and transmission.
    This simulates master-slave SPI communication where only the master can send bytes on it's own, while the
    connected slave can only reply to a received byte.
    This differs from a non master-slave communication, like UART, as in such every connected participant is able to
    send bytes independently.
    """
    def __init__(self):
        # Mock test data using a generator                                                                ACK  #AnsBytes    reply
        # The first actual response byte is read on the crc                                                |   |  ___________|__________
        self.test_data: bytes = bytes([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF, 0xF1, 0xFF, 4, 0xDE, 0xAD, 0xBE, 0xEF])
        self.receive_iterator = self.receive_byte()

    def describe(self):
        return ComDescription(is_master_slave=True)

    def send_byte(self, byte: int) -> Optional[int]:
        print('-> Send byte: ', byte)

        # Possible implementation of SPI receive / transmit at the same time
        # byte_in = spi_rxtx(byte_out)
        try:
            byte_in: int = next(self.receive_iterator)
            print('Received response byte in: ', byte_in)
            return byte_in
        except StopIteration:
            return None

    def receive_byte(self) -> Generator[int, None, None]:
        for b in self.test_data:
            yield b
        return

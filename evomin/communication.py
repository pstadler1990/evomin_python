#!/usr/bin/env python
# -*- coding: utf-8 -*
from abc import ABC, abstractmethod
from collections import namedtuple
from typing import Generator

ComDescription: namedtuple = namedtuple('ComDescription', ['is_master_slave'])


class EvominComInterface(ABC):
    """
    EvominComInterface can be used to derive concrete implementations of a low-level communication interface,
    such as UART, USART, SPI or I2C. Ultimately, this could also be used for file based or even ethernet based
    communication. It allows the evomin protocol to be independent from a specific interface.
    """
    @abstractmethod
    def describe(self):
        pass

    @abstractmethod
    def send_byte(self, byte: int) -> int:
        """
        Gets automatically called through the evomin interface in order to send a byte over the low-level communication
        device.
        :param byte: The byte to be sent
        """
        pass

    @abstractmethod
    def receive_byte(self) -> Generator[int, None, None]:
        """
        Needs to be called by the user wherever the low-level reception of bytes happens, i.e. in your application's
        main loop or in an interrupt on lower levels. For performance reasons, it makes sense to put this in a
        separate thread.
        A negative value like -1 indicates no reception, while any value >= 0 indicates a valid received byte.
        :return: -1 -> no byte received, >= 0 valid byte
        """
        pass

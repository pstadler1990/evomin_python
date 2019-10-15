#!/usr/bin/env python
# -*- coding: utf-8 -*
from evomin.communication import EvominComInterface


class EvominSPIInterface(EvominComInterface):
    """
    Concrete implementation of the EvominComInterface to be used with SPI.
    """
    def send_byte(self, byte: int) -> None:
        # TODO
        pass

    def receive_byte(self) -> int:
        # TODO
        pass

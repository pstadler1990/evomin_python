#!/usr/bin/env python
# -*- coding: utf-8 -*
from typing import Optional
from evomin.communication import EvominComInterface, ComDescription


class EvominSPIInterface(EvominComInterface):
    """
    Concrete implementation of the EvominComInterface to be used with SPI.
    """
    def describe(self):
        return ComDescription(is_master_slave=True)

    def send_byte(self, byte: int) -> Optional[int]:
        # TODO
        pass

    def receive_byte(self) -> int:
        # TODO
        pass

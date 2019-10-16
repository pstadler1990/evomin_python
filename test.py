#!/usr/bin/env python
# -*- coding: utf-8 -*
from evomin.com_fake import EvominFakeSPIInterface
from evomin.evomin import Evomin
from evomin.frame import EvominFrame


class EvominImpl(Evomin):
    """
    Concrete application side implementation
    """
    def frame_received(self, frame: EvominFrame) -> None:
        print('Received frame!', frame)


if __name__ == '__main__':
    # Initialize evomin communication interface with SPI transport
    evomin = EvominImpl(com_interface=EvominFakeSPIInterface())

    # Mock polling interface
    while True:
        evomin.rx_handler()

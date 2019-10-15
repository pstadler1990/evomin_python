#!/usr/bin/env python
# -*- coding: utf-8 -*
from evomin.com_fake import EvominFakeSPIInterface
from evomin.evomin import Evomin

if __name__ == '__main__':
    # Initialize evomin communication interface with SPI transport
    evomin = Evomin(EvominFakeSPIInterface())

    # Mock polling interface
    while True:
        evomin.rx_handler()

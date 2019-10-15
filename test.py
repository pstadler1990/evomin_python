#!/usr/bin/env python
# -*- coding: utf-8 -*
from evomin.evomin import Evomin
from evomin.com_spi import EvominSPIInterface

if __name__ == '__main__':
    # Initialize evomin communication interface with SPI transport
    evomin = Evomin(EvominSPIInterface())

#!/usr/bin/env python
# -*- coding: utf-8 -*
from queue import Queue
from evomin.config import config


class EvominBuffer:

    def __init__(self, initial_bytes: bytes = bytes([])):
        self.buffer: Queue = Queue(maxsize=config['frame']['buffer_size'])
        map(self.buffer.put, initial_bytes)

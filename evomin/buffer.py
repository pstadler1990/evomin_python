#!/usr/bin/env python
# -*- coding: utf-8 -*
from queue import Queue
from evomin.config import config
from evomin.exceptions import EvominNotAByteException


class EvominBuffer:

    def __init__(self, initial_bytes: bytes = bytes([])):
        self.buffer: Queue = Queue(maxsize=config['frame']['buffer_size'])
        try:
            [self.buffer.put(b) for b in initial_bytes]
        except TypeError:
            # If no initial bytes were given, skip
            pass

    @property
    def size(self):
        return self.buffer.qsize()

    def push(self, byte: int):
        if byte in range(256):
            self.buffer.put(byte)
        else:
            raise EvominNotAByteException('Payload byte must be a valid byte between 0..255')

    def get(self) -> int:
        return self.buffer.queue.popleft()

    def reset(self):
        self.buffer.queue.clear()

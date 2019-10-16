#!/usr/bin/env python
# -*- coding: utf-8 -*
from queue import Queue
from evomin.config import config


class EvominBuffer:

    def __init__(self, initial_bytes: bytes = bytes([])):
        self.buffer: Queue = Queue(maxsize=config['frame']['buffer_size'])
        try:
            map(self.buffer.put, initial_bytes)
        except TypeError:
            # If no initial bytes were given, skip
            pass

    @property
    def size(self):
        return self.buffer.qsize()

    def push(self, byte: int):
        self.buffer.put(byte)

    def get(self) -> int:
        return self.buffer.queue.popleft()

    def reset(self):
        self.buffer.queue.clear()

# !/usr/bin/env python
# -*- coding: utf-8 -*
from abc import ABC, abstractmethod
from typing import Any, Optional
from evomin.frame import EvominFrameMessageType


class State(ABC):
    """
    Abstract state blueprint
    run: the actual state execution
    proceed: translate to the next state
    fail: fail the current state
    """
    def __init__(self, expected: Optional[Any] = None) -> None:
        self.expected_byte = expected

    def run(self, byte: int) -> 'State':
        if (not self.expected_byte) or (self.expected_byte and byte == self.expected_byte):
            return self.proceed()
        else:
            return self.fail()

    @abstractmethod
    def proceed(self) -> 'State':
        pass

    @abstractmethod
    def fail(self) -> 'State':
        pass

    @property
    def expect(self):
        return self.expected_byte

    @expect.setter
    def expect(self, expected):
        self.expected_byte = expected


class StateIdle(State):
    def proceed(self) -> 'State':
        print("State idle PROCEED")

    def fail(self) -> 'State':
        print("State idle FAIL")


class StateSof(State):
    def proceed(self) -> 'State':
        print("State idle PROCEED")

    def fail(self) -> 'State':
        print("State idle FAIL")


class StateSof2(State):
    def proceed(self) -> 'State':
        print("State idle PROCEED")

    def fail(self) -> 'State':
        print("State idle FAIL")


class StateCmd(State):
    def proceed(self) -> 'State':
        print("State idle PROCEED")

    def fail(self) -> 'State':
        print("State idle FAIL")


class StateLen(State):
    def proceed(self) -> 'State':
        print("State idle PROCEED")

    def fail(self) -> 'State':
        print("State idle FAIL")


class StatePayld(State):
    def proceed(self) -> 'State':
        print("State idle PROCEED")

    def fail(self) -> 'State':
        print("State idle FAIL")


class StateCRC(State):
    def proceed(self) -> 'State':
        print("State idle PROCEED")

    def fail(self) -> 'State':
        print("State idle FAIL")


class StateCRCFail(State):
    def proceed(self) -> 'State':
        print("State idle PROCEED")

    def fail(self) -> 'State':
        print("State idle FAIL")


class StateEof(State):
    def proceed(self) -> 'State':
        print("State idle PROCEED")

    def fail(self) -> 'State':
        print("State idle FAIL")


class StateReply(State):
    def proceed(self) -> 'State':
        print("State idle PROCEED")

    def fail(self) -> 'State':
        print("State idle FAIL")


class StateReplyCreateFrame(State):
    def proceed(self) -> 'State':
        print("State idle PROCEED")

    def fail(self) -> 'State':
        print("State idle FAIL")


class StateError(State):
    def proceed(self) -> 'State':
        print("State idle PROCEED")

    def fail(self) -> 'State':
        print("State idle FAIL")

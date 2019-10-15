# !/usr/bin/env python
# -*- coding: utf-8 -*
from abc import ABC, abstractmethod


class State(ABC):
    """
    Abstract state blueprint
    run: the actual state execution
    proceed: translate to the next state
    fail: fail the current state
    """
    @abstractmethod
    def run(self, byte: int) -> None:
        pass

    @abstractmethod
    def proceed(self) -> 'State':
        pass

    @abstractmethod
    def fail(self) -> 'State':
        pass


class StateIdle(State):
    def run(self, byte: int) -> None:
        pass

    def proceed(self) -> 'State':
        pass

    def fail(self) -> 'State':
        pass


class StateSof(State):
    def run(self, byte: int) -> None:
        pass

    def proceed(self) -> 'State':
        pass

    def fail(self) -> 'State':
        pass


class StateSof2(State):
    def run(self, byte: int) -> None:
        pass

    def proceed(self) -> 'State':
        pass

    def fail(self) -> 'State':
        pass


class StateCmd(State):
    def run(self, byte: int) -> None:
        pass

    def proceed(self) -> 'State':
        pass

    def fail(self) -> 'State':
        pass


class StateLen(State):
    def run(self, byte: int) -> None:
        pass

    def proceed(self) -> 'State':
        pass

    def fail(self) -> 'State':
        pass


class StatePayld(State):
    def run(self, byte: int) -> None:
        pass

    def proceed(self) -> 'State':
        pass

    def fail(self) -> 'State':
        pass


class StateCRC(State):
    def run(self, byte: int) -> None:
        pass

    def proceed(self) -> 'State':
        pass

    def fail(self) -> 'State':
        pass


class StateCRCFail(State):
    def run(self, byte: int) -> None:
        pass

    def proceed(self) -> 'State':
        pass

    def fail(self) -> 'State':
        pass


class StateEof(State):
    def run(self, byte: int) -> None:
        pass

    def proceed(self) -> 'State':
        pass

    def fail(self) -> 'State':
        pass


class StateReply(State):
    def run(self, byte: int) -> None:
        pass

    def proceed(self) -> 'State':
        pass

    def fail(self) -> 'State':
        pass


class StateReplyCreateFrame(State):
    def run(self, byte: int) -> None:
        pass

    def proceed(self) -> 'State':
        pass

    def fail(self) -> 'State':
        pass


class StateError(State):
    def run(self, byte: int) -> None:
        pass

    def proceed(self) -> 'State':
        pass

    def fail(self) -> 'State':
        pass

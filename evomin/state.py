# !/usr/bin/env python
# -*- coding: utf-8 -*
from abc import ABC, abstractmethod


class State(ABC):
    """
    Abstract state blueprint
    proceed: translate to the next state
    fail: fail the current state
    """
    @abstractmethod
    def proceed(self):
        pass

    @abstractmethod
    def fail(self):
        pass


class StateIdle(State):
    def proceed(self):
        pass

    def fail(self):
        pass


class StateSof(State):
    def proceed(self):
        pass

    def fail(self):
        pass


class StateSof2(State):
    def proceed(self):
        pass

    def fail(self):
        pass


class StateCmd(State):
    def proceed(self):
        pass

    def fail(self):
        pass


class StateLen(State):
    def proceed(self):
        pass

    def fail(self):
        pass


class StatePayld(State):
    def proceed(self):
        pass

    def fail(self):
        pass


class StateCRC(State):
    def proceed(self):
        pass

    def fail(self):
        pass


class StateCRCFail(State):
    def proceed(self):
        pass

    def fail(self):
        pass


class StateEof(State):
    def proceed(self):
        pass

    def fail(self):
        pass


class StateReply(State):
    def proceed(self):
        pass

    def fail(self):
        pass


class StateReplyCreateFrame(State):
    def proceed(self):
        pass

    def fail(self):
        pass


class StateError(State):
    def proceed(self):
        pass

    def fail(self):
        pass


# !/usr/bin/env python
# -*- coding: utf-8 -*
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    # Prevent circular dependencies due to type hinting
    from evomin.evomin import StateMachine, Evomin


class State(ABC):
    """
    Abstract state blueprint
    run: the actual state execution
    proceed: translate to the next state
    fail: fail the current state
    """
    def __init__(self, state_machine: StateMachine, interface: Evomin, expected: Optional[Any] = None) -> None:
        self.state_machine = state_machine
        self.interface = interface
        self.expected_byte = expected

    def run(self, byte: int) -> State:
        if (not self.expected_byte) or (self.expected_byte and byte == self.expected_byte):
            return self.proceed(byte)
        else:
            return self.fail()

    @abstractmethod
    def proceed(self, byte: int) -> State:
        pass

    @abstractmethod
    def fail(self) -> State:
        pass

    @property
    def expect(self):
        return self.expected_byte

    @expect.setter
    def expect(self, expected):
        self.expected_byte = expected

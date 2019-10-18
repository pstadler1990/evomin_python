#!/usr/bin/env python
# -*- coding: utf-8 -*
from time import sleep
from evomin.com_fake import EvominFakeSPIInterface
from evomin.evomin import Evomin
from evomin.frame import EvominFrame, EvominFrameCommandType


class EvominImpl(Evomin):
    """
    Concrete application side implementation
    """

    def reply_received(self, reply_payload: bytes) -> None:
        print('** Reply received, {ps} bytes **'.format(ps=len(reply_payload)))
        for b in reply_payload:
            print(b)

    def frame_received(self, frame: EvominFrame) -> None:
        print('** Frame received **')
        self.log_debug('[Evomin] EvominFrame received, Command: {}, Payload length: {}'.format(frame.command, frame.payload_length))

        print('Payload: ')
        for b in frame.get_payload():
            print(b)

        # self.reply(bytes([0xA0, 0xA1, 0xA2, 0xA3, 0xB0, 0xB1, 0xB2, 0xB3]))
        self.reply(bytes([0x01, 0x02]))


if __name__ == '__main__':
    # Initialize evomin communication interface with SPI transport
    evomin = EvominImpl(com_interface=EvominFakeSPIInterface())

    evomin.send(EvominFrameCommandType.SEND_IDN, bytes([0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xBB, 0xFF]))

    # Polling interface
    while True:
        evomin.poll()
        sleep(1)

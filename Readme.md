# evomin (python)


## Mocked SPI interface

### Master sends a test frame, slave replies with 4 answer bytes

Below is a complete frame with comments to show how evomin performs on a single transfer of 8 bytes from the master
and a 4 bytes length reply from the attached slave device.

> Note: This excerpt has been simulated using the `EvominFakeSPIInterface`.

```
-> Send byte:  170                                  Master -> 0xAA SOF
Received response byte in:  0                       Slave <- dummy byte
-> Send byte:  170                                  Master -> 0xAA SOF
Received response byte in:  1                       Slave <- dummy byte
-> Send byte:  170                                  Master -> 0xAA SOF
Received response byte in:  2                       Slave <- dummy byte
-> Send byte:  205                                  Master -> Command type (CMD_IDN)
Received response byte in:  3                       Slave <- dummy byte
-> Send byte:  8                                    Master -> Payload length (8 bytes)
Received response byte in:  4                       Slave <- dummy byte
-> Send byte:  170                                  Master -> Payload byte #1 (0xAA)
Received response byte in:  5                       Slave <- dummy byte
-> Send byte:  170                                  Master -> Payload byte #2 (0xAA)
Received response byte in:  6                       Slave <- dummy byte
-> Send byte:  85                                   Master -> Automatically inserted stuff byte (not part of payload!)
Received response byte in:  7                       Slave <- dummy byte
-> Send byte:  170                                  Master -> Payload byte #3 (0xAA)
Received response byte in:  8                       ...
-> Send byte:  170                                  Master -> Payload byte #4 (0xAA)
Received response byte in:  9
-> Send byte:  85                                   Master -> Automatically inserted stuff byte (not part of payload!)
Received response byte in:  10
-> Send byte:  170                                  Master -> Payload byte #5 (0xAA)
Received response byte in:  11
-> Send byte:  170                                  Master -> Payload byte #6 (0xAA)
Received response byte in:  12
-> Send byte:  85                                   Master -> Automatically inserted stuff byte (not part of payload!)
Received response byte in:  13
-> Send byte:  187                                  Master -> Payload byte #7
Received response byte in:  14
-> Send byte:  255                                  Master -> Payload byte #8
Received response byte in:  15
-> Send byte:  159                                  Master -> CRC8 checksum (159 dec)
Received response byte in:  241                     Slave <- dummy byte
-> Send byte:  85                                   Master -> EOF #1
Received response byte in:  255                     Slave <- ACK (checksum correct)
-> Send byte:  85                                   Master -> EOF #2
Received response byte in:  4                       Slave <- Number of slave's answer bytes (reply)
-> Send byte:  240                                  Master -> Dummy byte to keep SPI communication
Received response byte in:  222                     Slave <- Reply byte #1
-> Send byte:  240                                  ...
Received response byte in:  173                     Slave <- Reply byte #2
-> Send byte:  240
Received response byte in:  190                     Slave <- Reply byte #3
-> Send byte:  240
Received response byte in:  239                     Slave <- Reply byte #4
** Reply received, 4 bytes **
222
173
190
239
-> Send byte:  255                                  Master -> Send ACK to finalize communication
```
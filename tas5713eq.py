#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TAS5713 biquad/equalizer settings.
"""

import sys
import time
import struct

from smbus2 import SMBus
import equalizer
from tas5713 import TAS5713


if __name__ == "__main__":

    fs = 46e3  # use something in between 44.1kHz and 48kHz, the common sample rates of my music
    cmd_lst = TAS5713.bq_cmd_value(equalizer.parameters(fs))

    # connect to the tas5713 and try to write the CH1-BQ and CH2-BQ2 register set
    con_attempts = 5
    audio = None
    while audio is None:
        try:
            # try to open, sometimes the linux kernel driver is still accessing the i2c-1 bus and open() fails
            audio = TAS5713()
        except: ## TODO: catch the right exception only
            if con_attempts == 0:
                sys.exit(1)
            con_attempts -= 1
            time.sleep(5.0)

    try:
        for cmd, data in cmd_lst:
            audio.write_i2c_block_data(audio.addr, cmd, data)

            # verify it is really written, at least print something useful ...
            read = audio.read_i2c_block_data(audio.addr, cmd, len(data))
            print('[{}]:{:02X}: {}'.format('OK' if read == data else 'FAIL', cmd, read))
    finally:
        if audio is not None:
            audio.close()

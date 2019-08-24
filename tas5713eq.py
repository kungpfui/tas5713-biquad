#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TAS5713 biquad/equalizer settings.
"""

import sys
import time

import equalizer
from tas5713 import TAS5713


if __name__ == "__main__":

    fs = 46e3  # use something in between 44.1kHz and 48kHz, the common sample rates of my music
    biquad_param = equalizer.parameters(fs)
    cmd_lst = TAS5713.bq_reg_value(biquad_param)

    # connect to the tas5713 and try to write the CH1-BQ and CH2-BQ2 register set
    con_attempts = 5
    amp = None
    while amp is None:
        try:
            # try to open, sometimes the linux kernel driver is still accessing the i2c-1 bus and open() fails
            amp = TAS5713()
        except: ## TODO: catch the right exception only
            if con_attempts == 0:
                sys.exit(1)
            con_attempts -= 1
            time.sleep(5.0)

    try:
        for reg, data in cmd_lst:
            amp.write_reg(reg, data)

            # verify it is really written, at least print something useful ...
            read = amp.read_reg(reg)
            print('[{}]:{:02X}: {}'.format('OK' if read == data else 'FAIL', reg.addr, reg.hex(data)))
    finally:
        if amp is not None:
            amp.close()

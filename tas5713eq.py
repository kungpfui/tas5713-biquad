#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# $Id: tas5713eq.py 386 2019-08-23 10:40:25Z stefan $

"""
TAS5713 biquad/equalizer settings.
"""

import sys
import time
import struct

from smbus2 import SMBus
import equalizer


class TAS5713(SMBus):
    BQ_nb = 7
    BQ1_reg = 0x29
    BQ2_reg = 0x30

    def __init__(self, bus=1, device_address=0x1b):
        """ c'tor
        @param address   eeproms default is 0x1b
        @param bus_id    I2C bus id, on raspi normally 1
        """
        SMBus.__init__(self, bus, force=True)
        self.addr = device_address

    @staticmethod
    def to_ba(b, a):
        """ Convert biquad coefficient (ba format) to tas5713 conform ba values
            (3.23 fixpoint, negative a's, witout a0)
        @param b
        @param a
        @return 20-byte bytearray
        """
        reg = bytearray()
        coef_fmt = struct.Struct('>i') # big endian, signed, 2's-complement
        for b_co in b:
            reg += coef_fmt.pack(int(round(b_co * 2**23)))
            # mask out the first 6 bits, not really nessesary but when read back the registers these bits are masked out as well.
            reg[-4] &= 0x03

        for a_co in a[1:]:
            reg += coef_fmt.pack(int(round(-a_co * 2**23)))
            reg[-4] &= 0x03
        return reg

    @staticmethod
    def bq_cmd_value(ba_lst):
        """Calculates the whole biquad register values of TAS5713.

        @return list[tuple(reg, [int,...]),]
        """
        biquads = [TAS5713.to_ba(b, a) for b, a in ba_lst]
        assert len(biquads) <= TAS5713.BQ_nb

        # regvals: list of tuple(reg, [val0, val1, ... , val19]),write_i2c_block_data expects
        # list of int instead of bytes() or bytearray()
        regvals = []
        for ch in (TAS5713.BQ1_reg, TAS5713.BQ2_reg):
            for n, bq in enumerate(biquads):
                regvals.append((ch + n, [d for d in bq]))
            else:
                # fill up with the default biquad b0=1, a0=1
                bq = TAS5713.to_ba((1., 0., 0.), (1., 0., 0.))
                for n in range(n + 1, TAS5713.BQ_nb):
                    regvals.append((ch + n, [d for d in bq]))
        return regvals


if __name__ == "__main__":

    fs = 46e3  # use something in between 44.1kHz and 48kHz, the common sample rates of my music
    cmd_lst = TAS5713.bq_cmd_value(equalizer.parameters(fs))

    # connect to the tas5713 and try to write the BQ1 and BQ2 register set
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





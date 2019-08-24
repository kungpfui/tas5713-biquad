#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ti TAS5713 I2C interface and register set definitions
"""

import struct
from struct import Struct
from smbus2 import SMBus

class Reg:
    def __init__(self, addr, size):
        self.addr = addr
        if isinstance(size, str):
            self.struct = Struct(size)
            self.size = self.struct.size
        else:
            self.struct = None
            self.size = size

class TAS5713(SMBus):
    BANK_SWT_EQ_CTRL_reg = Reg(0x50, '>I')
    CH1_BQ_reg = [Reg(r, 20) for r in range(0x29, 0x2F+1)] + [Reg(0x58, 20), Reg(0x59, 20)]
    CH2_BQ_reg = [Reg(r, 20) for r in range(0x30, 0x36+1)] + [Reg(0x5C, 20), Reg(0x5D, 20)]
    CH1b_BQ_reg = [Reg(0x5A, 20), Reg(0x5B, 20)]  # alias Channel 4
    CH2b_BQ_reg = [Reg(0x5E, 20), Reg(0x5F, 20)]  # alias Channel 3

    def __init__(self, bus=1, device_address=0x1b):
        """ c'tor
        :param bus:             I2C bus id, on raspi normally 1
        :param device_address:  device address, 0x1b or 0x1a, selected by A_SEL_FAULT pin
        """
        SMBus.__init__(self, bus, force=True)
        self.addr = device_address

    def read_reg(self, reg):
        """ read a register.
        :param reg: Reg
        :return: register value
        """
        rawdata = self.read_i2c_block_data(self.addr, reg.addr, reg.size)
        if reg.struct is not None:
            data = reg.struct.unpack(bytes(rawdata))
            return data[0] if len(data) == 1 else data
        return rawdata

    def write_reg(self, reg, data):
        """ write a register with some data

        :param reg: type Reg
        :param data:
        """
        assert len(data) == reg.size
        return self.write_i2c_block_data(self.addr, reg.addr, [d for d in data])

    @staticmethod
    def to_ba(b, a):
        """ Convert biquad coefficient (ba format) to tas5713 conform ba values
            (3.23 fixpoint, negative a's, without a0)
        :param b:
        :param a:
        :return: 20-byte bytearray
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
        assert len(biquads) <= len(TAS5713.CH1_BQ_reg)

        # regvals: list of tuple(reg, [val0, val1, ... , val19]),write_i2c_block_data expects
        # list of int instead of bytes() or bytearray()
        regvals = []
        for ch in (TAS5713.CH1_BQ_reg, TAS5713.CH2_BQ_reg):
            for bq, reg in zip(biquads, ch):
                regvals.append((reg.addr, [d for d in bq]))

            # fill up with the default biquad b0=1, a0=1
            bq_def = TAS5713.to_ba((1., 0., 0.), (1., 0., 0.))
            for reg in ch[len(biquads):]:
                regvals.append((reg.addr, [d for d in bq_def]))
        return regvals


if __name__ == "__main__":
    # some simple tests
    amp = TAS5713()
    for addr in range(0, 0xF):
        reg = Reg(addr, 'B')
        print('{:02X}: {:02X}'.format(reg.addr, amp.read_reg(reg)))

    for reg in (TAS5713.BANK_SWT_EQ_CTRL_reg,
                TAS5713.CH1_BQ_reg[0]):
        print('{:02X}: {}'.format(reg.addr, amp.read_reg(reg)))

    amp.close()

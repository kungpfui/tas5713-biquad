#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ti TAS5713 I2C interface and register set definitions
"""

import struct
from struct import Struct
from smbus2 import SMBus


class Reg:
    def __init__(self, addr, size='B'):
        self.addr = addr
        if isinstance(size, str):
            self.struct = Struct(size)
            self.size = self.struct.size
        else:
            self.struct = None
            self.size = size

    def hex(self, data):
        if isinstance(data, int):
            return '{{:0{}X}}'.format(self.size * 2).format(data)
        ## TODO: handle tuples, lists
        return data


class BQReg(Reg):
    size = 20
    def __init__(self, addr):
        Reg.__init__(self, addr, size=BQReg.size)

    def hex(self, b):
        return ' '.join(['{:02X}'.format(i) for i in b])

    @staticmethod
    def ba_to_reg(b, a):
        """ Convert biquad coefficient (ba format) to tas5713 conform ba values
            (3.23 fixpoint, negative a's, without a0)
        :param b:
        :param a:
        :return: 20-byte bytearray
        """
        reg = bytearray()
        coef_fmt = struct.Struct('>i')  # big endian, signed, 2's-complement
        for b_co in b:
            reg += coef_fmt.pack(int(round(b_co * 2 ** 23)))  ## workaround: int() needed by py3.5.3
            # mask out the first 6 bits, not really necessary but when read back the register these bits
            # are masked-out as well and they become comparable.
            reg[-4] &= 0x03

        for a_co in a[1:]:
            reg += coef_fmt.pack(int(round(-a_co * 2 ** 23)))  ## workaround: int() needed by py3.5.3
            reg[-4] &= 0x03

        assert len(reg) == BQReg.size
        return reg

    @staticmethod
    def reg_to_ba(reg_data):
        """
        :param reg_data: data from BQ register
        :return: tuple(b, a) where b,a are list of float
        """
        signext_data = bytearray(reg_data)
        for i in range(0, 20, 4):
            # sign bit set?
            if signext_data[i] & 0x2:
                signext_data[i] |= 0b11111100

        int_data = struct.unpack('>5i', signext_data)
        ba = []
        for sign, v in zip((1., 1., 1., -1., -1), int_data):
            ba.append(sign * v * 2**-23)
        return ba[:3], [1.] + ba[3:]


class TAS5713(SMBus):
    CLOCK_CTRL_reg = Reg(0x00)
    DEVICE_ID_reg = Reg(0x01)
    ERROR_STATUS_reg = Reg(0x02)
    SYSTEM_CTRL1_reg = Reg(0x03)
    SERIAL_DATA_INTERFACE_reg = Reg(0x04)
    SYSTEM_CTRL2_reg = Reg(0x05)
    SOFT_MUTE_reg = Reg(0x06)
    MASTER_VOLUME_reg = Reg(0x07)
    CH1_VOLUME_reg = Reg(0x08)
    CH2_VOLUME_reg = Reg(0x09)
    # HEADPHONE_VOLUME_reg = Reg(0x0A) exists but there is not headphone output
    VOLUME_CFG_reg = Reg(0xE)
    MODULATION_LIMIT_reg = Reg(0x10)
    INTERCHANNEL_DELAY_1_reg = Reg(0x11)
    INTERCHANNEL_DELAY_2_reg = Reg(0x12)
    INTERCHANNEL_DELAY_n1_reg = Reg(0x13)
    INTERCHANNEL_DELAY_n2_reg = Reg(0x14)
    PWM_SHUTDOWN_GROUP_reg = Reg(0x19)
    START_STOP_PERIOD_reg = Reg(0x1A)
    OSCILLATOR_TRIM_reg = Reg(0x1B)
    BKND_ER_reg = Reg(0x1C)
    INPUT_MULTIPLEXER_reg = Reg(0x20, '>I')
    CHANNEL_4_SOURCE_SELECT_reg = Reg(0x21, '>I')
    PWM_OUTPUT_MUX_reg = Reg(0x25, '>I')
    DRC_CTRL_reg = Reg(0x46, '>I')
    BANK_SWT_EQ_CTRL_reg = Reg(0x50, '>I')
    CH1_BQ_reg = [BQReg(r) for r in range(0x29, 0x2F+1)] + [BQReg(0x58), BQReg(0x59)]
    CH2_BQ_reg = [BQReg(r) for r in range(0x30, 0x36+1)] + [BQReg(0x5C), BQReg(0x5D)]
    CH1b_BQ_reg = [BQReg(0x5A), BQReg(0x5B)]  # alias Channel 4
    CH2b_BQ_reg = [BQReg(0x5E), BQReg(0x5F)]  # alias Channel 3

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
        return bytes(rawdata)

    def write_reg(self, reg, data):
        """ write a register with some data

        :param reg: type Reg
        :param data:
        """
        reg.data = data
        # write_i2c_block_data expects list of int. bytes or byte array does not work ... why ever
        return self.write_i2c_block_data(self.addr, reg.addr, [d for d in reg.data])

    @staticmethod
    def bq_reg_value(bqs):
        """Calculates the whole biquad register values of TAS5713.
        :param bqs: list of biquad coefficients
        :type bqs: list[[b=tuple(3), a=tuple(3)],...]
        :return: list[tuple(Reg, bytearray(20)),...]
        """
        assert len(bqs) <= len(TAS5713.CH1_BQ_reg)

        # regvals: list of tuple(reg, bytes(20)),
        # list of int instead of bytes() or bytearray()
        regvals = []
        for ch in (TAS5713.CH1_BQ_reg, TAS5713.CH2_BQ_reg):
            for bq, reg in zip(bqs, ch):
                regvals.append((reg, BQReg.ba_to_reg(*bq)))

            # fill up with the default biquad b0=1, a0=1
            bq_def = BQReg.ba_to_reg((1., 0., 0.), (1., 0., 0.))
            for reg in ch[len(bqs):]:
                regvals.append((reg, bq_def))
        return regvals


if __name__ == "__main__":
    # some simple tests
    amp = TAS5713()
    for addr in range(0, 0xF):
        reg = Reg(addr)
        data = amp.read_reg(reg)
        print('{:02X}: {}'.format(reg.addr, reg.hex(data)))

    for reg in (TAS5713.BANK_SWT_EQ_CTRL_reg,
                TAS5713.CH1_BQ_reg[0]):
        data = amp.read_reg(reg)
        print('{:02X}: {}'.format(reg.addr, reg.hex(data)))
        if isinstance(reg, BQReg):
            # show real biquad coefficients
            print('{:02X}: {}'.format(reg.addr, BQReg.reg_to_ba(data)))

    amp.close()

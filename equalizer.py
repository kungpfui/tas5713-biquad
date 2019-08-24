#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from biquad import highpass, lowpass, bandpass, allpass, notch, peaking, shelf
from scipy import signal

def parameters(fs):
    def hz(f):
        return 2. * f / fs

    choose = 0

    if choose == 0:
        # some bass and treble
        return (
            shelf(Wn=hz(125), dBgain=+5.0, S=1, btype='low'),
            shelf(Wn=hz(8e3), dBgain=+1.5, S=0.7, btype='high'),
        )
    elif choose == 1:
        # bandpass 200...2kHz
        return (
            highpass(hz(200), Q=0.707),
            lowpass(hz(2000), Q=0.707),
        )
    elif choose == 2:
        # peaking a lot
        return (
            peaking(hz(63.5), +6., Q=1, type='constantq'),
            peaking(hz(125), +3., Q=1, type='half'),
            peaking(hz(250), -3., Q=1, type='constantq'),
            peaking(hz(500), -6., Q=1, type='half'),
            peaking(hz(1e3), +7, Q=1, type='constantq'),
            peaking(hz(2e3), -6., Q=1, type='half'),
            peaking(hz(4e3), -3., Q=1, type='constantq'),
            peaking(hz(8e3), +3., Q=1, type='half'),
            peaking(hz(16e3), +6., Q=1, type='constantq'),
        )
    elif choose == 3:
        # try different filter types
        return (
            shelf(hz(125), +5.0, S=1, btype='low'),
            shelf(hz(10e3), +1.0, S=1, btype='high'),
            peaking(hz(3000), -3.0, Q=1., type='half'),
            peaking(hz(5000), +2.0, Q=2.5, type='constantq'),
            notch(hz(440), Q=10),
            lowpass(hz(17.5e3), Q=0.707),
            allpass(hz(2e3), Q=2),
        )
    elif choose == 4:
        # high-order 200...1kHz bandpass filter
        # ripple: passband=1.0dB, stopband=48db attenuation
        iir_second_order_structure = signal.iirfilter(N=9, rp=1., rs=30., Wn=(200, 1000), btype='bandpass', ftype='ellip', output='sos', fs=fs)
        # split up the coefficients
        return [(ba[:3], ba[3:]) for ba in iir_second_order_structure]

    elif choose == 5: # bandstop
        iir_second_order_structure = signal.iirfilter(N=9, rp=1., rs=30., Wn=(200, 1000), btype='bandstop', ftype='ellip', output='sos', fs=fs)
        # split up the coefficients
        return [(ba[:3], ba[3:]) for ba in iir_second_order_structure]

    elif choose == 6:
        # high-order 250Hz lowpass filter with 6dB amplification
        # ripple: passband=0.5dB, stopband=48db attenuation
        iir_second_order_structure = signal.iirfilter(N=12, rp=0.5, rs=48., Wn=250, btype='lowpass', ftype='ellip', output='sos', fs=fs)
        # split up the coefficients
        return [(ba[:3], ba[3:]) for ba in iir_second_order_structure] + [((2.0, 0., 0.), (1.0, 0., 0.))]


def _view():
    import numpy as np
    from scipy.signal import freqz
    import matplotlib.pyplot as plt

    def amp_db(h):
        return 20 * np.log10(np.abs(h))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    ax1.set_title('Equalizer Design')

    hs = None
    fs = 46e3 # between 44100 and 48000
    for b, a in parameters(fs):
        print('ba:', b, a)
        w, h = freqz(b, a, 2048, fs=fs)
        ax1.plot(w, amp_db(h), alpha=0.7)

        angle = np.unwrap(np.angle(h))
        ax2.plot(w, angle)

        if hs is None:
            hs = h
        else:
            hs = hs * h

    # resulting amplitude, angle
    ax1.plot(w, amp_db(hs), alpha=0.3, zorder=0.2, linewidth=7)
    ax1.set_yticks(range(-60, 30, 3))
    ax1.set_ylim(-12, 12)

    # resulting angle
    angle = np.unwrap(np.angle(hs))
    ax2.plot(w, angle, alpha=0.3, zorder=0.2, linewidth=7)

    for ax, ylabel in ((ax1, 'Amplitude [dB]' ), (ax2, 'Phase [radians]')):
        ax.set_xscale('log')
        ax.set_xlim(20, fs/2)
        ax.set_xlabel('Frequency [Hz]')
        ax.set_ylabel(ylabel)

        ax.grid(True, color='0.2', linestyle='-', which='major', axis='both')
        ax.grid(True, color='0.7', linestyle='-', which='minor', axis='both')

    plt.show()


if __name__ == "__main__":
    _view()

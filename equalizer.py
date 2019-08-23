#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# $Id: equalizer.py 386 2019-08-23 10:40:25Z stefan $

from biquad import highpass, lowpass, bandpass, allpass, notch, peaking, shelf


def parameters(fs):
    def hz(f):
        return 2 * f / fs

    choose = 0

    if choose == 0:
        # some bass and treble
        return (
            shelf(hz(125), +5.0, S=1, btype='low'),
            shelf(hz(10e3), +1.0, S=1, btype='high'),
        )
    elif choose == 1:
        # bandpass 200...2kHz
        return (
            highpass(hz(200), Q=0.707),
            lowpass(hz(2000), Q=0.707),
        )
    elif choose == 2:
        # try differten filter types
        return (
            shelf(hz(125), +5.0, S=1, btype='low'),
            shelf(hz(10e3), +1.0, S=1, btype='high'),
            peaking(hz(3000), -3.0, Q=1., type='half'),
            peaking(hz(5000), +2.0, Q=2.5, type='constantq'),
            notch(hz(440), Q=10),
            lowpass(hz(17.5e3), Q=0.707),
            allpass(hz(2e3), Q=2),
        )


def _view():
    import numpy as np
    from scipy.signal import freqz
    import matplotlib.pyplot as plt

    def amp_db(h):
        return 20 * np.log10(np.abs(h))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

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
    ax1.set_yticks(range(-10, 10, 3))
    ax1.set_ylim(-10, 10)

    # resulting angle
    angle = np.unwrap(np.angle(hs))
    ax2.plot(w, angle, alpha=0.3, zorder=0.2, linewidth=7)

    for ax, ylabel in ((ax1, 'Amplitude [dB]' ), (ax2, 'Angle [radians]')):
        ax.set_xscale('log')
        ax.set_xlim(20, fs/2)
        ax.set_xlabel('Frequency [Hz]')
        ax.set_ylabel(ylabel)

        ax.grid(True, color='0.2', linestyle='-', which='major', axis='both')
        ax.grid(True, color='0.7', linestyle='-', which='minor', axis='both')

    plt.show()


if __name__ == "__main__":
    _view()


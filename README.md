# TAS5713 Biquad
A _hack_ script to setup the biquad filters of TI's TAS5713 audio amplifier. With these script
it possible to configure the "equalizer" during runtime by user code. The script calculates
the biquad coefficients by some filter definitions, access the I2C bus and tries to write them
to your TAS5713 IC.


# Installation
Just copy. At the moment there is no setup.py.

# Requirements
- Python3
- numpy>=1.0.0
- smbus2>=0.2.0
- scipy>=1.2.0

For the graphical _verification_ of the equalizer settings:
- matplotlib>=3.0.0


# How to use
_equalizer.py_ contains the filter definition. Therefore you should read the docs of biquad.py
(by Github user Endolith (https://gist.github.com/endolith/5455375) which contains the filter
coefficient calculation implementation and a good documentation of the different filter types.
_equalizer.py_ has implemented a graphical viewer so you can preview your equalizer creation.
Just execute _equalizer.py_.

`> python3 tas5713eq.py`

or use _systemd_ to execute _tas5713eq.py_ once at boot time. See _tas5713eq.service_


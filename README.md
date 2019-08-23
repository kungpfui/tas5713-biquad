# TAS5713 Biquad
A hack script to setup the biquad filters of TI's TAS5713 audio amplifier. With these script it possible to configure the "equalizer" during runtime
by usercode. The script calculates the biquad coefficients by some filter defintions, access the I2C bus and tries to write them to your TAS5713 IC.


# Installation
Just copy. At the moment there is no setup.py.

# Requirements
- Python3.x
- numpy
- smbus2

For the graphical "verification" of the equalizer settings.
- matplotlib
- scipy

# How to use
equalizer.py contains the filter definition. Therefore you should read the docs of biquad.py (by Github user Endolith (https://gist.github.com/endolith/5455375) which contains the filter coefficient calcualtion implementation and a good documentation of the different filter types.
equalizer.py has implemented a graphical viewer so you can preview your equalizer creation. Just execute equalizer.py.

>python3 tas5713eq.py

or use systemd to execute the script at boot. See tas5713eq.service


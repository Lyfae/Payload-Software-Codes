[Dependencies]

This driver depends on:

Adafruit CircuitPython
Adafruit OneWire

[Usage Example]

import board
from adafruit_onewire.bus import OneWireBus
from adafruit_ds18x20 import DS18X20
ow_bus = OneWireBus(board.D2)
ds18 = DS18X20(ow_bus, ow_bus.scan()[0])
ds18.temperature

[Building Locally]

To build this library locally you'll need to install the circuitpython-build-tools package.

python3 -m venv .env
source .env/bin/activate
pip install circuitpython-build-tools
Once installed, make sure you are in the virtual environment:

source .env/bin/activate
Then run the build:

circuitpython-build-bundles --filename_prefix adafruit-circuitpython-ds18x20 --library_location .
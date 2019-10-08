[Installing]

The Driver is dependent on 
- Adafruit Circuit Python
- Bus Device

Ensure that the driver and all dependencies are available on the CircuitPython filesystem.
Recommended: installing the latest Adafruit Library and Driver bundle onto the device

https://github.com/adafruit/Adafruit_CircuitPython_Bundle

===========================================================================================

[Installing from PyPI]

You can install the driver locally from PyPI on a Linux system (Like the raspberry Pi).

To install to the current user:

pip3 install adafruit-circuitpython-bme280

To install system-wide (which we'll most likely need to do):

sudo pip2 install adafruit-circuitpython-bme280

============================================================================================

[Building Locally]

To build locally you'll have to have the circuitpython-build-tool package:
https://github.com/adafruit/circuitpython-build-tools

python3 -m venv .env
source .env/bin/activate
pip3 install circuitpython-build-tools

Once installed, make sure you are in the virtual environmet:

source .env/bin/activate

Then run tircuitpython-build-bundles --filename_prefix adafruit-circuitpython-veml6070 --library_location .he build
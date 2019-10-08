[Dependencies]

This driver depends on the Register and Bus Device Libraries:
Register: https://github.com/adafruit/Adafruit_CircuitPython_Register

==============================================================================================

[Usage Notes]

You must import the library as such

'import adafruit_bno055'

This driver takes an instantiated and active I2C object (from the busio or the bitbangio library) as an argument to its constructor.
The way to create an I2C object depends on the board you are using. For boards with labeled SCL and SDA pins, you can:

'
from busio import I2C
from board import SDA, SCL

i2c = I2C(SCL,SDA)
'

Once you have the I2C object, you can create the sensor object:

sensor = adafruit_bno055.BNO055(i2c)

[Building Locally]

To build this library locally you'll need to install the circuitpython-build-tools package.

python3 -m venv .env
source .env/bin/activate
pip install circuitpython-build-tools

Once installed, make sure you are in the virtual environment:

source .env/bin/activate
Then run the build:

circuitpython-build-bundles --filename_prefix adafruit-circuitpython-bno055 --library_location

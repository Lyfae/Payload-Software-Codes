"""
`adafruit_onewire.device`
====================================================
Provides access to a single device on the 1-Wire bus.
* Author(s): Carter Nelson
"""

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_OneWire.git"

_MATCH_ROM = b'\x55'

class OneWireDevice(object):
    """A class to represent a single device on the 1-Wire bus."""

    def __init__(self, bus, address):
        self._bus = bus
        self._address = address

    def __enter__(self):
        self._select_rom()
        return self

    def __exit__(self, *exc):
        return False

    def readinto(self, buf, *, start=0, end=None):
        """
        Read into ``buf`` from the device. The number of bytes read will be the
        length of ``buf``.
        If ``start`` or ``end`` is provided, then the buffer will be sliced
        as if ``buf[start:end]``. This will not cause an allocation like
        ``buf[start:end]`` will so it saves memory.
        :param bytearray buf: buffer to write into
        :param int start: Index to start writing at
        :param int end: Index to write up to but not include
        """
        self._bus.readinto(buf, start=start, end=end)
        if start == 0 and end is None and len(buf) >= 8:
            if self._bus.crc8(buf):
                raise RuntimeError('CRC error.')

    def write(self, buf, *, start=0, end=None):
        """
        Write the bytes from ``buf`` to the device.
        If ``start`` or ``end`` is provided, then the buffer will be sliced
        as if ``buffer[start:end]``. This will not cause an allocation like
        ``buffer[start:end]`` will so it saves memory.
        :param bytearray buf: buffer containing the bytes to write
        :param int start: Index to start writing from
        :param int end: Index to read up to but not include
        """
        return self._bus.write(buf, start=start, end=end)

    def _select_rom(self):
        self._bus.reset()
        self.write(_MATCH_ROM)
        self.write(self._address.rom)

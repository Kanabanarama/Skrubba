#!/usr/bin/env python

"""
File shiftregister.py
8 relay board connected to 74HC595
by Kana kanabanarama@googlemail.com
"""

import time
import environment

if environment.RUNNINGONPI:
    import RPi.GPIO as GPIO # pylint: disable=import-error,unused-import
else:
    import FakeRPi as GPIO  # pylint: disable=import-error

class Shiftregister():
    """
    Use shift register to control relays
    """
    _CLOCK = 17
    _LATCH = 27
    _DATA = 22
    _OE = 4 # GPIO4 is pulled low by default, so Output Enable will turn off all
            # parallel outs until we set it LOW

    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._DATA, GPIO.OUT)
        GPIO.setup(self._CLOCK, GPIO.OUT)
        GPIO.setup(self._LATCH, GPIO.OUT)
        GPIO.output(self._LATCH, 0)
        GPIO.setup(self._OE, GPIO.OUT)
        GPIO.output(self._OE, 1) # enable output
        self.reset() # set all outputs to HIGH (->OFF for relays)
        #self.enable()

    def __del__(self):
        return #GPIO.cleanup()

    def enable(self):
        """
        Enables GPIO output mode for shift register
        """
        return GPIO.output(self._OE, 0)

    def disable(self):
        """
        Disables GPIO output mode for shift register
        """
        return GPIO.output(self._OE, 1)

    def _pulse_clock(self):
        """
        Used internally to pulse clock pin
        """
        GPIO.output(self._CLOCK, 1)
        GPIO.output(self._CLOCK, 0)

        return True

    def _pulse_latch(self):
        """
        Used internally to pulse the latch pin
        """
        GPIO.output(self._LATCH, 1)
        GPIO.output(self._LATCH, 0)

        return True

    def reset(self):
        """
        Resets the shift register
        """
        for _ in range(0, 8):
            GPIO.output(self._DATA, 1)
            self._pulse_clock()
        self._pulse_latch()

        return True

    def output_decimal(self, decimal_value):
        """
        Outputs HIGH to the pin numbered decimal
        """
        binary_value = 2**(int(decimal_value)-1)
        self.output_binary(binary_value)

        return True

    def output_binary(self, binary_value):
        """
        Outputs high to the pin numbered binary
        """
        self.enable()
        bits = [True for i in range(8)]
        for i in range(8):
            bits[7-i] = False if binary_value & 1 else True
            GPIO.output(self._DATA, bits[7-i])
            self._pulse_clock()
            binary_value = binary_value >> 1
        self._pulse_latch()

        return True

    def output_list(self, value_list):
        """
        Output high to all pins that an array of 8 items has true values
        """
        binary_value = 0
        for i in range(0, 8):
            if value_list[i] == 1:
                value_list = binary_value | 2**i
        self.output_binary(binary_value)

        return True

    def test_loop(self):
        """
        Checks all 8 outputs by setting them to HIGH
        """
        while 1:
            bit_value = 1
            for _ in range(0, 8):
                self.output_binary(bit_value)
                bit_value = bit_value << 1
                time.sleep(2)

        return True

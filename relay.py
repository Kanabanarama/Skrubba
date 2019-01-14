#!/usr/bin/env python

"""
File relay.py
Use defined data pin
by Kana kanabanarama@googlemail.com
"""

import environment

if environment.RUNNINGONPI:
    import RPi.GPIO         # pylint: disable=import-error,unused-import
else:
    import FakeRPi as GPIO  # pylint: disable=import-error

class Relay():
    """
    Controls a single relay
    """
    data = None

    def __init__(self, pin=5):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self.data = pin
        GPIO.setup(self.data, GPIO.OUT)
        #self.switch_off()

    def __del__(self):
        return #GPIO.cleanup()

    def switch_on(self):
        """
        Turn on relay
        """
        return GPIO.output(self.data, 0)

    def switch_off(self):
        """
        Turn off relay
        """
        return GPIO.output(self.data, 1)

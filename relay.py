#!/usr/bin/env python

"""
File relay.py
Use defined data pin
by Kana kanabanarama@googlemail.com
"""

from environment import RUNNINGONPI

if RUNNINGONPI:
    import RPi.GPIO as GPIO
else:
    import FakeRPi as GPIO

class Relay(object):
    """
    Controls a single relay
    """
    data = None

    def __init__(self, pin=5):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self.data = pin
        GPIO.setup(self.data, GPIO.OUT)
        self.off()
        return

    def __del__(self):
        #GPIO.cleanup()
        return

    def on(self):
        GPIO.output(self.data, 0)
        return

    def off(self):
        GPIO.output(self.data, 1)
        return

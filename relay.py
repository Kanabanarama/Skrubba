#!/usr/bin/env python

# File relay.py
# Control single relay
# use defined data pin
# by Kana kanabanarama@googlemail.com

# IMPORTS
import os
from environment import RUNNINGONPI

if RUNNINGONPI:
  import RPi.GPIO as GPIO
else:
  import FakeRPi as GPIO

# CLASS

class Relay(object):
    _DATA = None

    def __init__(self, pin = 5):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self._DATA = pin
        GPIO.setup(self._DATA,GPIO.OUT)
        self.off()
        return

    def __del__(self):
        #GPIO.cleanup()
        return

    def on(self):
        GPIO.output(self._DATA, 0)
        return

    def off(self):
        GPIO.output(self._DATA, 1)
        return

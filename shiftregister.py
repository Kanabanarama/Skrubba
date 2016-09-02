#!/usr/bin/env python

# File shiftregister.py
# Use shift register to control relays
# 8 relay board connected to 74HC595
# by Kana kanabanarama@googlemail.com

# IMPORTS

import RPi.GPIO as GPIO
#import FakeRPi as GPIO

# CLASS

class Shiftregister(object):
    _CLOCK = 17
    _LATCH = 27
    _DATA = 22
    _OE = 4 # GPIO4 is pulled low by default, so Output Enable will turn off all parallel outs until we set it LOW

    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._DATA,GPIO.OUT)
        GPIO.setup(self._CLOCK,GPIO.OUT)
        GPIO.setup(self._LATCH,GPIO.OUT)
        GPIO.output(self._LATCH, 0)
        self.reset() # set all outputs to HIGH (->OFF for relays)
        GPIO.setup(self._OE,GPIO.OUT)
        #GPIO.output(self._OE, 0) # enable output
        self.enable()
        return

    def __del__(self):
        GPIO.cleanup()
        return

    def enable(self):
        print "output enable"
        GPIO.output(self._OE, 0)
        return;

    def disable(self):
        print 'output disable'
        GPIO.output(self._OE, 1)
        return

    def __pulseClock(self):
        GPIO.output(self._CLOCK, 1)
        GPIO.output(self._CLOCK, 0)
        return

    def __pulseLatch(self):
        GPIO.output(self._LATCH, 1)
        GPIO.output(self._LATCH, 0)
        return

    def reset(self):
        for x in range(0, 8):
            GPIO.output(self._DATA, 1)
            self.__pulseClock()
        self.__pulseLatch()
        return

    def outputDecimal(self, decimalValue):
        binaryValue = 2**(int(decimalValue)-1)
        self.outputBinary(binaryValue)
        return

    def outputBinary(self, binaryValue):
        bits = [True for i in range (8)]
        for i in range (8):
            bits[7-i] = False if binaryValue & 1 else True
            GPIO.output(self._DATA, bits[7-i])
            self.__pulseClock()
            binaryValue = binaryValue >> 1
        self.__pulseLatch()
        return

    def outputList(self, valueList):
        binaryValue = 0
        for i in range(0,8):
            if valueList[i] == 1:
                valueList = binaryValue | 2**i
        self.outputBinary(binaryValue)
        return

    def testLoop():
        while 1:
            bitValue = 1
            for i in range(0, 8):
                outputBinary(bitValue)
                bitValue = bitValue << 1
                time.sleep(2)
        return
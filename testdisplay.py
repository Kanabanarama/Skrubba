#!/usr/bin/env python

"""
File testdisplay.py
Test display output
by Kana kanabanarama@googlemail.com
"""

from time import sleep
from display import Display

TFT = Display()
TFT.displayImage('static/gfx/lcd-skrubba-color.png', x=67, y=10, clearScreen=True)
while True:
    sleep(10)

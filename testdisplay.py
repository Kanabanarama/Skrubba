#!/usr/bin/env python

"""
File testdisplay.py
Test display output
by Kana kanabanarama@googlemail.com
"""

from time import sleep
from display import Display

TFT = Display()
TFT.display_image('static/gfx/lcd-skrubba-color.png', pos_x=67, pos_y=10, clear_screen=True)

while True:
    sleep(10)

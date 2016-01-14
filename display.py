#!/usr/bin/env python

# File display.py
# Control display to show status information
# [display type] connected via SPI-Interface
# by Kana kanabanarama@googlemail.com

# IMPORTS

import os
import sys
import time
import pygame

# CLASS

class Display(object):
    _WIDTH = 160
    _HEIGHT = 128

    def __init__(self):
        os.environ['SDL_FBDEV'] = '/dev/fb1'
        os.environ['SDL_VIDEODRIVER'] = 'fbcon'
        pygame.init()
        pygame.mouse.set_visible(0)
        global screen
        screen = pygame.display.set_mode((self._WIDTH, self._HEIGHT))
        return

    def __del__(self):
        # cleanup
        return

    def displayImage(self, url, (x, y), clearScreen):
        if clearScreen:
            screen.fill((0, 0, 0))
        image = pygame.image.load(url)
        screen.blit(image, (x, y))
        pygame.display.flip()
        return

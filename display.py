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
    _WIDTH = 320
    _HEIGHT = 240
    _BGCOLOR = (255, 255, 255)

    def __init__(self):
        os.environ['SDL_FBDEV'] = '/dev/fb1'
        os.environ['SDL_VIDEODRIVER'] = 'fbcon'
        pygame.init()
        pygame.mouse.set_visible(0)
        self._screen = pygame.display.set_mode((self._WIDTH, self._HEIGHT))
        return

    def __del__(self):
        # cleanup
        return

    def clear(self):
        self._screen.fill(self._BGCOLOR)
        return

    def setBackgroundColor(self, (r, g, b)):
        self._BGCOLOR = (r, g, b)
        return

    def displayImage(self, url, (x, y), clearScreen):
        if clearScreen:
            self.clear()
        image = pygame.image.load(url)
        self._screen.blit(image, (x, y))
        pygame.display.flip()
        return

    def displayText(self, text, size, (x, y), color, bgcolor):
        font = pygame.font.Font(None, size)
        text = font.render(text, 1, color)
        rect = text.get_rect()
        pygame.draw.rect(self._screen, bgcolor, [x, y, rect.width, rect.height])
        self._screen.blit(text, (x, y))
        pygame.display.flip()
        return
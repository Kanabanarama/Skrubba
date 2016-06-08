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
        self._font = pygame.font.Font(None, 30)
        self._minifont = pygame.font.Font(None, 15)
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
        #pygame.display.flip()
        return

    _jobDict = []
    _activeJobs = []

    def clearJobDisplay(self):
        del self._jobDict[:]
        return

    def displayJob(self, jobConfig):
        print 'Added job for displaying:'
        print jobConfig
        self._jobDict.append(jobConfig)
        return

    def updateJobDisplay(self):
        for index, job in enumerate(self._jobDict):
            xPos = 4
            yPos = 48 + index * 24
            jobDescription = job['on_time'] + ' - ' + job['name']
            infoText = self._font.render(jobDescription, 1, (255, 255, 255))
            infoRect = infoText.get_rect()
            jobDuration = '(' + str(job['on_duration']) + 's)'
            durationText = self._minifont.render(jobDuration, 1, (0, 0, 0))
            durationRect = durationText.get_rect()
            if(job['id'] in self._activeJobs):
                color = (22, 22, 205)
            else:
                color = (74, 74, 74)
            pygame.draw.rect(self._screen, color, [xPos, yPos, 312, infoRect.height-2]) #(48, 48, 48)

            pygame.draw.rect(self._screen, (255, 0, 0), [312 - durationRect.width + 2, yPos + 4, durationRect.width+2, durationRect.height+2])

            self._screen.blit(infoText, (xPos, yPos))
            self._screen.blit(durationText, (312 - durationRect.width + 4, yPos+6))
            pygame.display.flip()
        return

    def markActiveJob(self, jobId, state):
        if(state == True):
            self._activeJobs.append(jobId)
        else:
            self._activeJobs.remove(jobId)
        return
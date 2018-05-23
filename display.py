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

    _CDRED = (249, 116, 75)
    _CDGREEN = (0, 110, 46)
    _CDBLUE = (79, 145, 196)

    def __init__(self):
        os.environ['SDL_FBDEV'] = '/dev/fb1'
        os.environ['SDL_VIDEODRIVER'] = 'fbcon'
        pygame.init()
        pygame.mouse.set_visible(0)
        self._font = pygame.font.Font(None, 30)
        self._minifont = pygame.font.Font(None, 15)
        self._midifont = pygame.font.Font(None, 24)
        self._screen = pygame.display.set_mode((self._WIDTH, self._HEIGHT), pygame.FULLSCREEN)
        return

    def __del__(self):
        # cleanup
        return

    def clear(self):
        self._screen.fill(self._BGCOLOR)
        return

    def setBackgroundColor(self, r, g, b):
        self._BGCOLOR = (r, g, b)
        return

    _backgroundImage = {}

    def setBackgroundImage(self, url, x, y):
        self._backgroundImage = {'url': url, 'x': x, 'y': y}
        self.displayImage(url, x, y, True)
        return

    def displayImage(self, url, x, y, clearScreen = True):
        if clearScreen:
            self.clear()
        image = pygame.image.load(url)
        self._screen.blit(image, (x, y))
        pygame.display.flip()
        return

    def displayText(self, text, size, x , y, color, bgcolor):
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
        self._jobDict.append(jobConfig)
        return

    _messageDict = {}

    def displayMessage(self, key, message):
        #self._messageDict.update({key, message})
        self._messageDict[key] = message
        return

    def clearMessage(self, key):
        #if last message is removed, rerender backround
        if(len(self._messageDict) == 1):
            print("Removing last message and rerender background")
            print(self._backgroundImage)
            self.displayImage(self._backgroundImage['url'], self._backgroundImage['x'], self._backgroundImage['y'], True)
        self._messageDict.pop(key, None)
        return

    def updateJobDisplay(self):
        for index, job in enumerate(self._jobDict):
            xPos = 4
            yPos = 48 + index * 24
            jobDescription = job['on_time'] + ' - ' + job['name']
            infoText = self._font.render(jobDescription, 1, (255, 255, 255))
            infoRect = infoText.get_rect()
            jobDuration = '(' + str(job['on_duration']) + 's)'
            durationText = self._minifont.render(jobDuration, 1, (255, 255, 255))
            durationRect = durationText.get_rect()
            jobValve = str(job['valve'])
            valveText = self._midifont.render(jobValve, 1, (0, 0, 0))
            valveRect = valveText.get_rect()
            if(job['id'] in self._activeJobs):
                color = self._CDBLUE
            else:
                color = (74, 74, 74)
            pygame.draw.rect(self._screen, color, [xPos, yPos, 312, infoRect.height-2]) #(48, 48, 48)
            pygame.draw.rect(self._screen, self._CDGREEN, [312 - durationRect.width + 2, yPos + 4, durationRect.width+2, durationRect.height+2])
            pygame.draw.rect(self._screen, self._CDBLUE, [0, yPos, valveRect.width+4, valveRect.height+2])
            self._screen.blit(infoText, (xPos+valveRect.width + 2, yPos))
            self._screen.blit(durationText, (312 - durationRect.width + 4, yPos+6))
            self._screen.blit(valveText, (2, yPos+2))
            # after rendering last job, show any existing messages
        messageCount = len(self._messageDict)
        if(messageCount > 0):
            if(int(time.time()) % 2 == 0):
                messageBoxFillColor = self._CDRED
                messageBoxBorderColor = self._CDBLUE
            else:
                messageBoxFillColor = self._CDBLUE
                messageBoxBorderColor = self._CDRED
            pygame.draw.rect(self._screen, messageBoxBorderColor, [46, 0, 272, 42*messageCount+2], 2)
            pygame.draw.rect(self._screen, messageBoxFillColor, [48, 2, 270, 42*messageCount])
            for message in self._messageDict.values():
                messageText = self._font.render(message, 1, (0, 0, 0))
                self._screen.blit(messageText, (62, 42*messageCount-30))
        pygame.display.flip()
        return

    def markActiveJob(self, jobId, state):
        if(state == True):
            self._activeJobs.append(jobId)
        else:
            self._activeJobs.remove(jobId)
        return

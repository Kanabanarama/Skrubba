#!/usr/bin/env python

"""
File display.py
Display must be connected via SPI-Interface
by Kana kanabanarama@googlemail.com
"""

import os
import sys
import signal
import time
import pygame   # pylint: disable=import-error
import environment

class Display():
    """
    Control display to show status information
    """
    _width = 320
    _height = 240

    _bg_color = (255, 255, 255)
    _cdred = (249, 116, 75)
    _cdgreen = (0, 110, 46)
    _cdblue = (79, 145, 196)
    _cdactive = (74, 74, 74)

    _background_image = {}

    _job_dict = []
    _active_jobs = []

    def __init__(self):
        if environment.RUNNINGONPI:
            os.environ['SDL_FBDEV'] = '/dev/fb1'
            os.environ['SDL_VIDEODRIVER'] = 'fbcon'
        pygame.init()

        # fbcon sometimes not freed when app crashes
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        pygame.mouse.set_visible(0)
        self._font = pygame.font.Font(None, 30)
        self._minifont = pygame.font.Font(None, 15)
        self._midifont = pygame.font.Font(None, 24)
        self._screen = pygame.display.set_mode((self._width, self._height), pygame.FULLSCREEN)

    def __del__(self):
        """
        Cleanup
        """
        print('Pygame cleanup')
        pygame.quit()

        return True

    def signal_handler(signal, frame):
      print('Signal: {}'.format(signal))
      time.sleep(1)
      pygame.quit()
      sys.exit(0)

    def clear(self):
        """
        Clears screen by filling it with the default background color
        """
        self._screen.fill(self._bg_color)

        return self

    def set_background_color(self, color_r, color_g, color_b):
        """
        Set default background color
        """
        self._bg_color = (color_r, color_g, color_b)

        return self

    def set_background_image(self, url, pos_x, pos_y):
        """
        Sets default background image
        """
        self._background_image = {'url': url, 'x': pos_x, 'y': pos_y}
        self.display_image(url, pos_x, pos_y, True)
        return self

    def display_image(self, url, pos_x, pos_y, clear_screen=True):
        """
        Displays an image at position x/y
        """
        if clear_screen:
            self.clear()
        image = pygame.image.load(url)
        self._screen.blit(image, (pos_x, pos_y))
        pygame.display.flip()

        return self

    def display_text(self, text, size, pos_x, pos_y, color, bgcolor):
        """
        Displays text at position x/y
        """
        font = pygame.font.Font(None, size)
        text = font.render(text, 1, color)
        rect = text.get_rect()
        pygame.draw.rect(self._screen, bgcolor, [pos_x, pos_y, rect.width, rect.height])
        self._screen.blit(text, (pos_x, pos_y))
        #pygame.display.flip()

        return

    def clear_job_display(self):
        """
        Unsets all lines for job displaying
        """
        del self._job_dict[:]

        return self

    def display_job(self, job_config):
        """
        Adds a line to job displaying
        """
        self._job_dict.append(job_config)

        return self

    _message_dict = {}

    def display_message(self, message):
        """
        Adds a message
        """
        #self._message_dict.update({key, message})
        #self._message_dict[key] = message
        self._message_dict[len(self._message_dict)+1] = message

        return self

    def clear_message(self, key):
        """
        Removes message with a key
        If last message is removed, rerenders backround
        """
        if len(self._message_dict) == 1:
            print("Removing last message and rerender background")
            print(self._background_image)
            self.display_image(self._background_image['url'],
                               self._background_image['x'],
                               self._background_image['y'],
                               True)
        self._message_dict.pop(key, None)

        return self

    def update_job_display(self):
        """
        Manages displaying everything that's in the job and message dictonaries
        TODO: separate job / message management
        """
        for index, job in enumerate(self._job_dict):
            position = {
                'x': 4,
                'y': 48 + index * 24,
            }

            job_valve = str(job['valve'])
            job_label = str(job['on_time']) + ' - ' + str(job['name'])
            job_timer = '(' + str(job['on_duration']) + 's)'

            font = {
                'valve': self._midifont.render(job_valve, 1, (0, 0, 0)),
                'label': self._font.render(job_label, 1, (255, 255, 255)),
                'timer': self._minifont.render(job_timer, 1, (255, 255, 255)),
            }

            if job['id'] in self._active_jobs:
                color = self._cdblue
            else:
                color = self._cdactive

            # bar
            pygame.draw.rect(self._screen,
                             color,
                             [position['x'],
                              position['y'],
                              312,
                              font['label'].get_rect().height-2])

            # display label text
            self._screen.blit(font['label'], (position['x'] + font['valve'].get_rect().width + 2,
                                              position['y']))
            # display box with valve
            pygame.draw.rect(self._screen,
                             self._cdblue,
                             [0,
                              position['y'],
                              font['valve'].get_rect().width+4,
                              font['valve'].get_rect().height+2])

            self._screen.blit(font['valve'], (2, position['y']+2))

            # display box with countdown timer
            pygame.draw.rect(self._screen,
                             self._cdgreen,
                             [312 - font['timer'].get_rect().width + 2,
                              position['y'] + 4,
                              font['timer'].get_rect().width+2,
                              font['timer'].get_rect().height+2])

            self._screen.blit(font['timer'], (312 - font['timer'].get_rect().width + 4,
                                              position['y']+6))

        # after rendering last job, show any existing messages
        message_count = len(self._message_dict)
        if message_count > 0:
            if int(time.time()) % 2 == 0:
                message_box_fill_color = self._cdred
                message_box_border_color = self._cdblue
            else:
                message_box_fill_color = self._cdblue
                message_box_border_color = self._cdred
            pygame.draw.rect(self._screen,
                             message_box_border_color,
                             [46,
                              0,
                              272,
                              42*message_count+2],
                             2)
            pygame.draw.rect(self._screen,
                             message_box_fill_color,
                             [48,
                              2,
                              270,
                              42*message_count])
            for message in self._message_dict.values():
                message_text = self._font.render(message, 1, (0, 0, 0))
                self._screen.blit(message_text, (62, 42*message_count-30))
        pygame.display.flip()

        return self

    def mark_active_job(self, job_id, state):
        """
        Pushes a job ID into _active_jobs that will be rendered differently
        """
        if state:
            self._active_jobs.append(job_id)
        else:
            self._active_jobs.remove(job_id)

        return self

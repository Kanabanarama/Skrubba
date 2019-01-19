#!/usr/bin/env python

"""
File scheduler.py
Job scheduler for managing configured events
by Kana kanabanarama@googlemail.com
"""

import time
import atexit
import logging
from apscheduler.schedulers.background import BackgroundScheduler # pylint: disable=import-error
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR # pylint: disable=import-error

from shiftregister import Shiftregister
from relay import Relay
from display import Display
from db import DB

class Scheduler():
    """
    Scheduler
    """

    SCHEDULER = BackgroundScheduler(standalone=True)
    STORE = DB()
    VALVES = Shiftregister()
    PUMP = Relay()
    TFT = Display()

    def __init__(self):
        logging.basicConfig()
        self.TFT.display_image('static/gfx/lcd-skrubba-color.png',
                          pos_x=67, pos_y=10, clear_screen=True)

    def unload_scheduler(self):
        """
        Scheduler cleanups
        """
        self.SCHEDULER.shutdown()
        self.VALVES.disable()

        return True

    def is_running(self):
        return self.SCHEDULER.running

    def valve_job(self, valve_setting): #(valve, onDuration)
        """
        Open a valve specified with settings
        """
        self.TFT.mark_active_job(valve_setting['id'], True)
        duration_left = int(valve_setting['on_duration']) + 2
        #binaryValveList = map(int, list(format(valve_setting['valve'], '08b')))
        self.PUMP.switch_on()
        time.sleep(1)
        #VALVES = Shiftregister()
        #shiftreg.output_list(binaryValveList)
        self.VALVES.output_decimal(valve_setting['valve'])
        self.VALVES.enable()
        while duration_left > 2:
            time.sleep(1)
            duration_left -= 1
        self.PUMP.switch_off()
        self.VALVES.disable()
        self.VALVES.reset()
        time.sleep(1)

        self.TFT.mark_active_job(valve_setting['id'], False)
        self.STORE.add_log_line(valve_setting, datetime.now())

        return True

    def start_scheduler(self):
        """
        start scheduler if not already running (debug mode has 2 threads, so we
        have to make sure it only starts once)
        """
        self.SCHEDULER.start()
        self.SCHEDULER.add_listener(self.scheduler_job_event_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        atexit.register(self.unload_scheduler)

        return True

    def scheduler_job_event_listener(self, event):
        """
        Event listener for scheduler, do emergency stuff when something goes wrong
        """
        if event.exception:
            print('The scheduler job crashed.')
        #else:
        #    print('The scheduler job finished successfully.')

    def restart_job_manager(self):
        """
        Remove all jobs
        """
        display_time = time.time()

        for job in self.SCHEDULER.get_jobs():
            self.SCHEDULER.remove_job(job.id)
            self.TFT.clear_job_display()

        # Add all jobs that are stored in database
        valve_configs = self.STORE.load_valve_configs()
        for config in valve_configs:
            if config['on_time'] and config['on_duration'] and config['is_active']:
                self.TFT.display_job(config)
                time_components = [int(x) for x in config['on_time'].split(':')]
                if config['interval_type'] == 'daily':
                    self.SCHEDULER.add_job(self.valve_job,
                                      'cron',
                                      day_of_week='mon-sun',
                                      hour=time_components[0],
                                      minute=time_components[1],
                                      second=time_components[2],
                                      args=[config])
                    #print('Scheduled daily job [%i:%i]'
                    #      % (time_components[0], time_components[1]))
                if config['interval_type'] == 'weekly':
                    self.SCHEDULER.add_job(self.valve_job,
                                      'cron',
                                      day_of_week='sun',
                                      hour=time_components[0],
                                      minute=time_components[1],
                                      second=time_components[2],
                                      args=[config])
                    #print('Scheduled weekly job [sun %i:%i]'
                    #      % (time_components[0], time_components[1]))
                if config['interval_type'] == 'monthly':
                    self.SCHEDULER.add_job(self.valve_job,
                                      'cron',
                                      day=1,
                                      hour=time_components[0],
                                      minute=time_components[1],
                                      second=time_components[2],
                                      args=[config])
                    #print('Scheduled monthly job [1st of the month %i:%i]'
                    #      % (time_components[0], time_components[1]))

        # print('JOBS:')
        # print(SCHEDULER.get_jobs())

        while time.time() - display_time < 5:
            time.sleep(1)
        self.TFT.clear()
        self.TFT.set_background_image('static/gfx/lcd-ui-background.png', pos_x=0, pos_y=0)
        self.add_tft_job()

        return True

    def add_tft_job(self):
        """
        Job for updating tft display
        """
        def tft_job():
            #if(os.getenv('SSH_CLIENT')):
            #    os.environ.get('SSH_CLIENT')
            #    os.environ['SSH_CLIENT'] // nothing ?
            #    TFT.display_text(os.getenv('SSH_CLIENT'),
            #                              24,
            #                              (205, 30),
            #                              (249, 116, 75),
            #                              (0, 110, 46))
            # text, size, pos_x, pos_y, color, bg_color
            self.TFT.display_text(time.strftime('%H:%M:%S'), 40, 205, 10, (255, 255, 255), (0, 110, 46))
            self.TFT.update_job_display()

        self.SCHEDULER.add_job(tft_job, 'interval', seconds=1)

        return True

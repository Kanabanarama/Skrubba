#!/usr/bin/env python

"""
File main.py
Start flask webserver and job scheduler
by Kana kanabanarama@googlemail.com
"""

import os
from flask import Flask

from skrubba.scheduler import Scheduler
from skrubba.shiftregister import Shiftregister
from skrubba.relay import Relay
from skrubba.display import Display
from skrubba.db import DB

APP = Flask(__name__, template_folder='templates')

# change working directory to directory of this script so that images
# relative paths can be found
ABSPATH = os.path.abspath(__file__)
DNAME = os.path.dirname(ABSPATH)
os.chdir(DNAME)

APP.secret_key = os.urandom(32)

# Serve all static files from within template folder
#if DEBUG:
from werkzeug import SharedDataMiddleware
APP.wsgi_app = SharedDataMiddleware(APP.wsgi_app, {
    '/': os.path.join(os.path.dirname(__file__), 'templates')})

import views

from config.environment import RUNNINGONPI, DEBUG

if __name__ != "__main__":
    #gunicorn_logger = logging.getLogger(‘gunicorn.error’)
    #app.logger.handlers = gunicorn_logger.handlers
    #app.logger.setLevel(gunicorn_logger.level)
    SCHEDULER = Scheduler()
    if not SCHEDULER.is_running():
        SCHEDULER.start_scheduler()
        SCHEDULER.restart_job_manager()
        #setup_backend_user_tracking()

if __name__ == "__main__":
    if not DEBUG or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        SCHEDULER = Scheduler()
        if not SCHEDULER.is_running():
            SCHEDULER.start_scheduler()
            SCHEDULER.restart_job_manager()
            SCHEDULER.setup_backend_user_tracking()

    PORT = 8000 if RUNNINGONPI else 2525
    print('STARTING APP ON PORT %i WITH DEBUG %i' % (PORT, DEBUG,))
    APP.run(host='0.0.0.0', port=PORT, debug=DEBUG, threaded=True)

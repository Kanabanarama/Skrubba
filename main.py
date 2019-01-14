#!/usr/bin/env python

"""
File main.py
Start flask webserver and job scheduler
by Kana kanabanarama@googlemail.com
"""

import os
import time
import atexit
import logging
from functools import wraps
from datetime import datetime
from flask import Flask, request, send_from_directory, render_template, json # pylint: disable=import-error
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, # pylint: disable=import-error
                          BadSignature, SignatureExpired) # pylint: disable=import-error
from apscheduler.schedulers.background import BackgroundScheduler # pylint: disable=import-error
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR # pylint: disable=import-error
from shiftregister import Shiftregister
from relay import Relay
from db import DB
from environment import RUNNINGONPI, DEBUG

if RUNNINGONPI:
    from display import Display

# change working directory to directory of this script so that images
# relative paths can be found
ABSPATH = os.path.abspath(__file__)
DNAME = os.path.dirname(ABSPATH)
os.chdir(DNAME)

APP = Flask(__name__, template_folder='templates')
APP.secret_key = os.urandom(32)
TOKEN_EXPIRATION = 7200
SCHEDULER = BackgroundScheduler(standalone=True)

# Serve all static files from within template folder
if DEBUG:
    from werkzeug import SharedDataMiddleware
    APP.wsgi_app = SharedDataMiddleware(APP.wsgi_app, {
        '/': os.path.join(os.path.dirname(__file__), 'templates')})

################################################################################
# Scheduler
################################################################################

logging.basicConfig()

DEBUG = True
DISPLAYACCESS = False

def valve_job(valve_setting): #(valve, onDuration)
    """
    Open a valve specified with settings
    """
    print('OPENING VALVE')
    tft.markActiveJob(valve_setting['id'], True)
    duration_left = int(valve_setting['on_duration']) + 2
    #binaryValveList = map(int, list(format(valve_setting['valve'], '08b')))
    #print binaryValveList
    pump = Relay()
    pump.switch_on()
    time.sleep(1)
    #valves = Shiftregister()
    #shiftreg.outputList(binaryValveList)
    valves.output_decimal(valve_setting['valve'])
    #valves.enable()
    while duration_left > 2:
        time.sleep(1)
        duration_left -= 1
        print('TIME LEFT: %i' % (duration_left - 1))
    print('CLOSING VALVE')
    pump.switch_off()
    print('reset shift register 1')
    #valves.disable()
    valves.reset()
    time.sleep(1)

    #valves.reset()
    tft.markActiveJob(valve_setting['id'], False)
    store = DB()
    store.addLogLine(valve_setting, datetime.now())

    return True

def start_scheduler():
    """
    start scheduler if not already running (debug mode has 2 threads, so we
    have to make sure it only starts once)
    """
    SCHEDULER.start()
    SCHEDULER.add_listener(scheduler_job_event_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    atexit.register(unloadScheduler)

    return True

def scheduler_job_event_listener(event):
    """
    Event listener for scheduler, do emergency stuff when something goes wrong
    """
    if event.exception:
        print('The scheduler job crashed.')
    #else:
    #    print('The scheduler job finished successfully.')

def restart_job_manager():
    """
    Remove all jobs
    """
    for job in SCHEDULER.get_jobs():
        SCHEDULER.remove_job(job.id)
    if RUNNINGONPI:
        tft.clearJobDisplay()

    # Add all jobs that are stored in database
    store = DB()
    valve_configs = store.loadValveConfigs()
    for config in valve_configs:
        if config['on_time'] and config['on_duration'] and config['is_active']:
            if RUNNINGONPI:
                tft.displayJob(config)
            time_components = [int(x) for x in config['on_time'].split(':')]
            if config['interval_type'] == 'daily':
                SCHEDULER.add_job(valve_job,
                                  'cron',
                                  day_of_week='mon-sun',
                                  hour=time_components[0],
                                  minute=time_components[1],
                                  second=time_components[2],
                                  args=[config])
                #print('Scheduled daily job [%i:%i]'
                #      % (time_components[0], time_components[1]))
            if config['interval_type'] == 'weekly':
                SCHEDULER.add_job(valve_job,
                                  'cron',
                                  day_of_week='sun',
                                  hour=time_components[0],
                                  minute=time_components[1],
                                  second=time_components[2],
                                  args=[config])
                #print('Scheduled weekly job [sun %i:%i]'
                #      % (time_components[0], time_components[1]))
            if config['interval_type'] == 'monthly':
                SCHEDULER.add_job(valve_job,
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

    if RUNNINGONPI:
        while time.time() - displayTime < 5:
            time.sleep(1)
        tft.clear()
        tft.setBackgroundImage('static/gfx/lcd-ui-background.png', x=0, y=0)
        add_tft_job()

    return True

def add_tft_job():
    def tft_job():
        #if(os.getenv('SSH_CLIENT')):
        #    os.environ.get('SSH_CLIENT')
        #    os.environ['SSH_CLIENT'] // nothing ?
        #    tft.displayText(os.getenv('SSH_CLIENT'),
        #                              24,
        #                              (205, 30),
        #                              (249, 116, 75),
        #                              (0, 110, 46))
        tft.displayText(time.strftime('%H:%M:%S'), 40, 205, 10, (255, 255, 255), (0, 110, 46))
        tft.updateJobDisplay()
        return
    SCHEDULER.add_job(tft_job, 'interval', seconds=1)

    return True

################################################################################
# Authentication
################################################################################

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_login_required():
            return f(*args, **kwargs)
        else:
            headerAuthToken = request.headers.get('authentication')
            if not headerAuthToken or not check_auth_token(headerAuthToken):
                print('return denyAccess()')
                return deny_access_token()
            print('return f()')
            return f(*args, **kwargs)

    return decorated

def is_login_required():
    store = DB()
    loginRequired = False
    for line in store.loadSystemSettings():
        if line['setting_name'] == 'username':
            loginRequired = True
            break

    return loginRequired

def generate_auth_token(self, credentials, expiration=TOKEN_EXPIRATION):
    s = Serializer(APP.config['SECRET_KEY'], expires_in=expiration)
    print("'username': credentials['username']")

    return s.dumps({'username': credentials['username']})

def check_auth_token(authToken):
    s = Serializer(APP.config['SECRET_KEY'])
    try:
        data = s.loads(authToken)
    except SignatureExpired:
        return False # valid token, but expired
    except BadSignature:
        return False # invalid token

    return True

def deny_access_token():
    return json.dumps({'success': 'false', 'message': 'Authentication failed.'})

@APP.route("/action/login", methods=['GET', 'POST'])
def actionLogin():
    if request.method == 'POST':
        params = request.get_json()
        requestUsername = params['username']
        requestPassword = params['password']

        systemCredentials = {}
        store = DB()
        for line in store.loadSystemSettings():
            if line['setting_name'] == 'username':
                systemCredentials['username'] = line['setting_value']
            if line['setting_name'] == 'password':
                systemCredentials['password'] = line['setting_value']

                print(systemCredentials['username'])
                print(systemCredentials['password'])

        if len(systemCredentials) == 2 \
                and requestUsername == systemCredentials['username'] \
                and requestPassword == systemCredentials['password']:
            print('Login successful')
            token = generate_auth_token(request, systemCredentials, 600)
            response = json.dumps({'success': 'true', 'token': token})
        else:
            print('Login failed')
            response = json.dumps({'success': 'false', 'message': 'Invalid login.'})

    return response

def localhost_only(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        requestIp = request.remote_addr
        print('checking request origin: %s' % requestIp)
        if DEBUG:
            allowed = True
        else:
            allowed = (requestIp == '127.0.0.1')
        print('allowed: %i' % allowed)
        if not allowed:
            print('return denyIp()' + requestIp)
            return deny_request_ip()
        #print('return f()')
        return f(*args, **kwargs)
    return decorated

def deny_request_ip():
    return json.dumps({'success': 'false',
                       'message': 'Requests from remote hosts are not allowed.'
                      })

################################################################################
# Flask CRUD routes
################################################################################

@APP.route("/data/plant.json", methods=['GET', 'POST'])
@requires_auth
@localhost_only
def plant():
    store = DB()
    action = request.args.get('action')

    if action == 'read':
        valveConfigs = store.loadValveConfigs()
        # print('READ VALVE CONFIG:')
        # print(valveConfigs)
        response = json.dumps({'plant': valveConfigs})

    elif action == 'create':
        jsonValveConfigs = request.form['plant']
        valveConfig = json.loads(jsonValveConfigs)
        # check if valves can be added (system_settings.valve_amount)
        maxValves = store.getMaxValveCountSetting()
        actualValves = store.getValveCount()
        if not maxValves or actualValves < maxValves:
            # print('CREATED VALVE CONFIG:')
            # print valveConfig
            newRow = store.addValveConfig(valveConfig)
            if len(newRow):
                restart_job_manager()
                responseObj = {'success': 'true', 'plant': newRow}
            else:
                responseObj = {'success': 'false'}
        else:
            responseObj = {'success': 'false',
                           'message': 'No more entrys to add, maximum entries '\
                           'can be configured in settings.'}
        response = json.dumps(responseObj)

    elif action == 'update':
        jsonValveConfigs = request.form['plant']
        valveConfig = json.loads(jsonValveConfigs)
        # print('UPDATED VALVE CONFIG:')
        # print(valveConfig)
        success = store.saveValveConfig(valveConfig)
        if success:
            restart_job_manager()
            responseObj = {'success': 'true'}
        else:
            responseObj = {'success': 'false',
                           'message': 'Valve already used by another entry.'}
        response = json.dumps(responseObj)
        #{'success': 'false', 'message': }#, 500
        #'metaData': { 'messageProperty': 'msg', 'successProperty': 'success' }

    elif action == 'destroy':
        jsonValveConfigs = request.form['plant']
        valveConfig = json.loads(jsonValveConfigs)
        # print('DELETED VALVE CONFIG:')
        # print valveConfig
        success = store.deleteValveConfig(valveConfig['id'])
        restart_job_manager()
        response = json.dumps({'success': str(success).lower()})

    return response

@APP.route("/data/log.json", methods=['GET', 'POST'])
@requires_auth
@localhost_only
def log():
    store = DB()
    action = request.args.get('action')
    if action == 'read':
        logs = store.loadLogs()
        # print('READ LOGS:')
        # print(logs)
        response = json.dumps({'log': logs})

    return response

@APP.route("/data/setting.json", methods=['GET', 'POST'])
#@requires_auth
@localhost_only
def setting():
    store = DB()
    action = request.args.get('action')
    if action == 'read':
        settings = {}
        # print('READ SYSTEM CONF:')
        for line in store.loadSystemSettings():
            if line['setting_name'] == 'password':
                continue
            settings.update({line['setting_name']: line['setting_value']})
        response = json.dumps({'setting': [settings]})
        # print response
    elif action == 'update':
        if request.method == 'POST':
            jsonCredentials = request.form['setting']
            params = json.loads(jsonCredentials)
            response = json.dumps({'success': 'false'})
            if 'username' in params:
                credentialUsername = params['username']
                store.updateSystemSettings('username', credentialUsername)
                response = json.dumps({'success': 'true'})
            if 'password' in params:
                credentialPassword = params['password']
                store.updateSystemSettings('password', credentialPassword)
                response = json.dumps({'success': 'true'})
            if 'valve_amount' in params:
                valveAmount = int(params['valve_amount'])
                actualValves = store.getValveCount()
                if actualValves <= valveAmount:
                    store.updateSystemSettings('valve_amount', valveAmount)
                    response = json.dumps({'success': 'true'})
                else:
                    response = json.dumps({'success': 'false',
                                           'message': 'There are more valves '\
                                           'set up than you want to allow.'\
                                           'Please remove some of them first.'})
    elif action == 'destroy':
        if request.method == 'POST':
            jsonCredentials = request.form['setting']
            params = json.loads(jsonCredentials)
            #print(params)
            #for setting in params:
            for key, value in params.items():
                #print('checking: %s / %s' % (key, value))
                if value == '-DELETE-':
                    store.deleteSystemSetting(key)
            response = json.dumps({'success': 'true'})

    return response

################################################################################
# Flask action routes
################################################################################

@APP.route("/action/manualwatering", methods=['GET', 'POST'])
@requires_auth
@localhost_only
def actionManualwatering():
    if request.method == 'POST':
        params = request.get_json()
        valveNo = params['valve']
        duration = params['duration']
        valves = Shiftregister()
        valves.outputBinary(valveNo)
        print("OPENED VALVE %i" % valveNo)
    response = json.dumps({'success': 'true'})

    return response


@APP.route('/action/serveroff', methods=['POST'])
@requires_auth
@localhost_only
def serveroff():
    print('SERVER SHUTTING DOWN')
    tft.displayMessage('SHUTDOWN SERVER')
    #unloadScheduler()
    unloadFlask()
    return json.dumps({'success': 'true'})

@APP.route('/action/reboot', methods=['POST'])
@requires_auth
@localhost_only
def reboot():
    print('SYSTEM REBOOTING')
    tft.displayMessage('REBOOTING')
    #unloadScheduler()
    unloadFlask()
    os.system("reboot")

    return json.dumps({'success': 'true'})

@APP.route('/action/shutdown', methods=['POST'])
@requires_auth
@localhost_only
def shutdown():
    print('SYSTEM SHUTDOWN')
    tft.displayMessage('SHUTDOWN SYSTEM')
    #unloadScheduler()
    unloadFlask()
    os.system("poweroff")

    return json.dumps({'success': 'true'})

################################################################################
# Unloading
################################################################################

def unloadScheduler():
    print('Shutting down scheduler...')
    SCHEDULER.shutdown()

    return True

def unloadFlask():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    print('Shutting down flask...')
    func()

    return True

'''def postServerOffRequest():
    response = APP.test_client().post('/serveroff')
    return response'''

################################################################################
# Flask main
################################################################################

# Serve favicon from static folder
@APP.route('/favicon.ico')
def favicon():
    faviconPath = os.path.join(APP.root_path, 'static')
    return send_from_directory(faviconPath, 'gfx/favicon.ico', mimetype='image/vnd.microsoft.icon')

# Serve index page
@APP.route("/", methods=['GET', 'POST'])
def index():
    #print("user /")
    return render_template('index.html')

def setupKeepaliveTracking():
    def trackBackendUserActivity():
        for ip, counter in keepaliveCounters.items():
            keepaliveCounters[ip] -= 10
            if RUNNINGONPI and DISPLAYACCESS:
                if keepaliveCounters[ip] > 0:
                    tft.displayMessage(ip, ip + ' is logged in.')
                else:
                    tft.clearMessage(ip)
    SCHEDULER.add_job(trackBackendUserActivity, 'interval', seconds=10)
    return

keepaliveCounters = {}

#@APP.before_request
@APP.route("/keepalive", methods=['GET'])
def refreshKeepalive():
    keepaliveCounters[request.remote_addr] = 11
    return json.dumps({'success': 'true'})

#import argparse
#""
if __name__ == "__main__":
    #parser = argparse.ArgumentParser(description = 'Let program simulate on local machine.')
    #parser.add_argument('local')
    #args = parser.parse_args()
    #print args.accumulate(args.local)
    #exit;
    if not DEBUG or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        if RUNNINGONPI:
            tft = Display()
            tft.displayImage('static/gfx/lcd-skrubba-color.png', x=67, y=10, clearScreen=True)
            displayTime = time.time()
            # All valves off
            valves = Shiftregister()
        if not SCHEDULER.running:
            start_scheduler()
            restart_job_manager()
            setupKeepaliveTracking()
    APP.run(host='0.0.0.0', port=80 if RUNNINGONPI else 2525, debug=DEBUG)

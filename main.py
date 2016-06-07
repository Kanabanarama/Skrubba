#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, struct, time, atexit
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, json
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from shiftregister import Shiftregister
from relay import Relay
from db import DB

# because there is no 64 bit version of pygame and the display is installed
# on the raspberry pi, not on the development system, omit the import
RUNNINGONPI = os.uname()[4][:3] == 'arm'
if RUNNINGONPI:
    from display import Display

app = Flask(__name__, template_folder = 'templates')
app.secret_key = os.urandom(32)
tokenExpiration = 7200
scheduler = BackgroundScheduler(standalone = True)

########################################################################################################################
# Scheduler
########################################################################################################################

import logging
logging.basicConfig()

DEBUG = True

def valveJob(setting): #(valve, onDuration)
    print 'OPENING VALVE'
    durationLeft = int(setting['on_duration']) + 2
    #binaryValveList = map(int, list(format(setting['valve'], '08b')))
    #print binaryValveList
    relay = Relay()
    relay.on()
    time.sleep(1)
    shiftreg = Shiftregister()
    #shiftreg.outputList(binaryValveList)
    shiftreg.outputDecimal(setting['valve'])
    while durationLeft > 2:
        time.sleep(1)
        durationLeft -= 1
        print 'TIME LEFT: %i' % durationLeft
    print 'CLOSING VALVE'
    relay.off()
    time.sleep(1)
    shiftreg.reset()
    db = DB()
    db.addLogLine(setting, datetime.now())
    return

def startScheduler():
    # start scheduler if not already running (debug mode has 2 threads, so we have to make sure it only starts once)
    print 'Starting scheduler...'
    scheduler.start()
    scheduler.add_listener(schedulerJobEventListener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    atexit.register(unloadScheduler)
    return

def schedulerJobEventListener(event):
    if event.exception:
        print('The scheduler job crashed.')
    #else:
    #    print('The scheduler job finished successfully.')

def restartJobManager():
    # Remove all jobs
    if len(scheduler.get_jobs()) > 0:
        for job in scheduler.get_jobs():
            scheduler.remove_job(job.id)
        tft.clearJobDisplay()

    # Add all jobs that are stored in database
    db = DB()
    valveConfigs = db.loadValveConfigs()
    for config in valveConfigs:
        if config['on_time'] and config['on_duration'] and config['is_active']:
            tft.displayJob(config)
            timeComponents = map(int, config['on_time'].split(':'))
            timeNextRun = datetime.now().replace(hour = timeComponents[0], minute = timeComponents[1], second = 0, microsecond = 0)
            if(config['interval_type'] == 'daily'):
                scheduler.add_job(valveJob, 'cron', day_of_week = 'mon-sun', hour = timeComponents[0], minute = timeComponents[1], args = [config])
                print 'Scheduled daily job [%i:%i]' % (timeComponents[0], timeComponents[1])
            if(config['interval_type'] == 'weekly'):
                scheduler.add_job(valveJob, 'cron', day_of_week = 'sun', hour = timeComponents[0], minute = timeComponents[1], args = [config])
                print 'Scheduled weekly job [sun %i:%i]' % (timeComponents[0], timeComponents[1])
            if(config['interval_type'] == 'monthly'):
                scheduler.add_job(valveJob, 'cron', day = 1, hour = timeComponents[0], minute = timeComponents[1], args = [config])
                print 'Scheduled monthly job [1st of the month %i:%i]' % (timeComponents[0], timeComponents[1])

    print 'JOBS:'
    print scheduler.get_jobs()

    if RUNNINGONPI:
        while time.time() - displayTime < 5:
            time.sleep(1)
        tft.clear()
        tft.displayImage('static/gfx/lcd-ui-background.png', (0, 0), True)
        addTftJob()

    return

def addTftJob():
    def tftJob():
        tft.displayText(time.strftime('%H:%M:%S'), 40, (205, 10), (255, 255, 255), (0, 110, 46))
        tft.updateJobDisplay()
        return
    scheduler.add_job(tftJob, 'interval', seconds = 1)
    return

########################################################################################################################
# Authentication
########################################################################################################################

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not isLoginRequired():
            return f(*args, **kwargs)
        else:
            headerAuthToken = request.headers.get('authentication')
            print 'authToken: %s / Token validation result: %i' % (headerAuthToken, checkAuthToken(headerAuthToken))
            if not headerAuthToken or not checkAuthToken(headerAuthToken):
                print 'return denyAccess()'
                return denyAccessToken()
            print 'return f()'
            return f(*args, **kwargs)
    return decorated

def isLoginRequired():
    db = DB()
    loginRequired = False
    for line in db.loadSystemSettings():
        if line['setting_name'] == 'username':
            loginRequired = True
            break
    return loginRequired

def generateAuthToken(self, credentials, expiration = tokenExpiration):
    s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
    print { 'username': credentials['username'] }
    return s.dumps({ 'username': credentials['username'] })

def checkAuthToken(authToken):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(authToken)
    except SignatureExpired:
        return False # valid token, but expired
    except BadSignature:
        return False # invalid token
    return True

def denyAccessToken():
    return json.dumps({ 'success': 'false', 'message': 'Authentication failed.' })

@app.route("/action/login", methods=['GET', 'POST'])
def actionLogin():
    if request.method == 'POST':
        params = request.get_json();
        requestUsername = params['username']
        requestPassword = params['password']

        systemCredentials = {}
        db = DB()
        for line in db.loadSystemSettings():
            if line['setting_name'] == 'username':
                systemCredentials['username'] = line['setting_value']
            if line['setting_name'] == 'password':
                systemCredentials['password'] = line['setting_value']

        if len(systemCredentials) == 2 and requestUsername == systemCredentials['username'] and requestPassword == systemCredentials['password']:
            print 'Login successful'
            token = generateAuthToken(request, systemCredentials, 600)
            response = json.dumps({ 'success': 'true', 'token': token })
        else:
            print 'Login failed'
            response = json.dumps({ 'success': 'false', 'message': 'Invalid login.' })
    return response

def localhost_only(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        requestIp = request.remote_addr
        print 'checking request origin: %s' % requestIp
        if DEBUG:
            allowed = True
        else:
            allowed = (requestIp == '127.0.0.1')
        print 'allowed: %i' % allowed
        if not allowed:
            print 'return denyIp()'
            return denyRequestIp()
        print 'return f()'
        return f(*args, **kwargs)
    return decorated

def denyRequestIp():
    return json.dumps({ 'success': 'false', 'message': 'Requests from remote hosts are not allowed.' })

########################################################################################################################
# Flask CRUD routes
########################################################################################################################

@app.route("/data/plant.json", methods=['GET', 'POST'])
@requires_auth
@localhost_only
def plant():
    db = DB()
    action = request.args.get('action')

    if action == 'read':
        valveConfigs = db.loadValveConfigs()
        print 'READ VALVE CONFIG:'
        print valveConfigs
        response = json.dumps({ 'plant': valveConfigs })

    elif action == 'create':
        jsonValveConfigs = request.form['plant']
        valveConfig = json.loads(jsonValveConfigs)
        # check if valves can be added (system_settings.valve_amount)
        maxValves = db.getMaxValveCountSetting()
        actualValves = db.getValveCount()
        if not maxValves or actualValves < maxValves:
            print 'CREATED VALVE CONFIG:'
            print valveConfig
            newRow = db.addValveConfig(valveConfig)
            if len(newRow):
                restartJobManager()
                responseObj = { 'success': 'true', 'plant': newRow }
            else:
                responseObj = { 'success': 'false' }
        else:
            responseObj = { 'success': 'false', 'message': 'No more entrys to add, maximum entries can be configured in settings.' }
        response = json.dumps(responseObj)

    elif action == 'update':
        jsonValveConfigs = request.form['plant']
        valveConfig = json.loads(jsonValveConfigs)
        print 'UPDATED VALVE CONFIG:'
        print valveConfig
        success = db.saveValveConfig(valveConfig)
        if success == True:
            restartJobManager()
            responseObj = { 'success': 'true' }
        else:
            responseObj = { 'success': 'false', 'message': 'Valve already used by another entry.' }
        response = json.dumps(responseObj)#{'success': 'false', 'message': }#, 500 #'metaData': { 'messageProperty': 'msg', 'successProperty': 'success' }

    elif action == 'destroy':
        jsonValveConfigs = request.form['plant']
        valveConfig = json.loads(jsonValveConfigs)
        print 'DELETED VALVE CONFIG:'
        print valveConfig
        success = db.deleteValveConfig(valveConfig['id'])
        restartJobManager()
        response = json.dumps({ 'success': str(success).lower() })

    return response

@app.route("/data/log.json", methods=['GET', 'POST'])
@requires_auth
@localhost_only
def log():
    db = DB()
    action = request.args.get('action')
    if action == 'read':
        logs = db.loadLogs()
        print 'READ LOGS:'
        print logs
        response = json.dumps({ 'log': logs })
    return response

@app.route("/data/setting.json", methods=['GET', 'POST'])
#@requires_auth
@localhost_only
def setting():
    db = DB()
    action = request.args.get('action')
    if action == 'read':
        settings = {}
        print 'READ SYSTEM CONF:'
        for line in db.loadSystemSettings():
            if line['setting_name'] == 'password':
                continue
            settings.update({ line['setting_name']: line['setting_value'] })
        response = json.dumps({ 'setting': [settings] })
        print response
    elif action == 'update':
        if request.method == 'POST':
            jsonCredentials = request.form['setting']
            params = json.loads(jsonCredentials)
            response = json.dumps({ 'success': 'false' })
            if 'username' in params:
                credentialUsername = params['username']
                db.updateSystemSettings('username', credentialUsername)
                response = json.dumps({ 'success': 'true' })
            if 'password' in params:
                credentialPassword = params['password']
                db.updateSystemSettings('password', credentialPassword)
                response = json.dumps({ 'success': 'true' })
            if 'valve_amount' in params:
                valveAmount = int(params['valve_amount'])
                actualValves = db.getValveCount()
                if actualValves <= valveAmount:
                    db.updateSystemSettings('valve_amount', valveAmount)
                    response = json.dumps({ 'success': 'true' })
                else:
                    response = json.dumps({ 'success': 'false', 'message': 'There are more valves set up than you want to allow. Please remove some of them first.' })
    elif action == 'destroy':
        if request.method == 'POST':
            jsonCredentials = request.form['setting']
            params = json.loads(jsonCredentials)
            print params
            #for setting in params:
            for key, value in params.items():
                print 'checking: %s / %s' % (key, value)
                if value == '-DELETE-':
                    db.deleteSystemSetting(key)
            response = json.dumps({ 'success': 'true' })
    return response

########################################################################################################################
# Flask action routes
########################################################################################################################

@app.route("/action/manualwatering", methods=['GET', 'POST'])
@requires_auth
@localhost_only
def actionManualwatering():
    if request.method == 'POST':
        params = request.get_json();
        valveNo = params['valve']
        duration = params['duration']
        valves = Shiftregister()
        valves.outputBinary(valveNo)
        print "opened valve %i" % valveNo
    response = json.dumps({ 'success': 'true' })
    return response


@app.route('/action/serveroff', methods=['POST'])
@requires_auth
@localhost_only
def serveroff():
    print 'SERVER SHUTTING DOWN'
    #unloadScheduler()
    unloadFlask()
    return json.dumps({ 'success': 'true' })

@app.route('/action/reboot', methods=['POST'])
@requires_auth
@localhost_only
def reboot():
    print 'SYSTEM REBOOTING'
    #unloadScheduler()
    unloadFlask()
    os.system("reboot")
    return json.dumps({ 'success': 'true' })

@app.route('/action/shutdown', methods=['POST'])
@requires_auth
@localhost_only
def shutdown():
    print 'SYSTEM SHUTDOWN'
    #unloadScheduler()
    unloadFlask()
    os.system("poweroff")
    return json.dumps({ 'success': 'true' })

########################################################################################################################
# Unloading
########################################################################################################################

def unloadScheduler():
    print 'Shutting down scheduler...'
    scheduler.shutdown()
    return

def unloadFlask():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    print 'Shutting down flask...'
    func()
    return

'''def postServerOffRequest():
    response = app.test_client().post('/serveroff')
    return response'''

########################################################################################################################
# Flask main
########################################################################################################################

# Serve all static files from within template folder
if DEBUG:
    from werkzeug import SharedDataMiddleware

    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, { '/': os.path.join(os.path.dirname(__file__), 'templates') })

from flask import send_from_directory

# Serve favicon from static folder
@app.route('/favicon.ico')
def favicon():
    faviconPath = os.path.join(app.root_path, 'static')
    return send_from_directory(faviconPath, 'gfx/favicon.ico', mimetype='image/vnd.microsoft.icon')

# Serve index page
@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('index.html')

if __name__ == "__main__":
    if (not DEBUG or os.environ.get('WERKZEUG_RUN_MAIN') == 'true'):
        if RUNNINGONPI:
            tft = Display()
            tft.displayImage('static/gfx/lcd-skrubba-color.png', (67, 10), True)
            displayTime = time.time()
            # All valves off
            shiftreg = Shiftregister()
        if scheduler.running == False:
            startScheduler()
            restartJobManager()
    #('Linux', 'raspberrypi', '3.18.11+', '#781 PREEMPT Tue Apr 21 18:02:18 BST 2015', 'armv6l')
    #('Linux', 'Minzplattenspieler', '3.13.0-24-generic', '#47-Ubuntu SMP Fri May 2 23:30:00 UTC 2014', 'x86_64')
    app.run(host = '0.0.0.0', port = 80 if RUNNINGONPI else 2525, debug = DEBUG)
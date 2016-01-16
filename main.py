#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from flask import Flask, render_template, request, json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from shiftregister import Shiftregister
from db import DB
from datetime import datetime
import time
import atexit

app = Flask(__name__, template_folder = 'templates')
scheduler = BackgroundScheduler(standalone = True)

import logging
logging.basicConfig()

DEBUG = True

def valveJob(setting): #(valve, onDuration)
    print 'OPENING VALVE'
    durationLeft = int(setting['on_duration'])
    #binaryValveList = map(int, list(format(setting['valve'], '08b')))
    #print binaryValveList
    shiftreg = Shiftregister()
    #shiftreg.outputList(binaryValveList)
    shiftreg.outputDecimal(setting['valve'])
    while durationLeft > 0:
        time.sleep(1)
        durationLeft -= 1
        print 'TIME LEFT: %i' % durationLeft
    print 'CLOSING VALVE'
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

    # Add all jobs that are stored in database
    db = DB()
    valveConfigs = db.loadValveConfigs()
    for config in valveConfigs:
        if config['on_time'] and config['on_duration'] and config['is_active']:
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
    return

def addTftJob():
    def tftJob():
        tft.displayText(time.strftime('%H:%M:%S'), 40, (205, 10), (255, 255, 255), (0, 110, 46))
        return
    scheduler.add_job(tftJob, 'interval', seconds = 1)
    return


@app.route("/", methods=['GET', 'POST'])
def index():

    #db = DB()
    #if db.exists() != True :
    #db.createTables()

    message = "Hello Web!"

    inputDefault = '{"type":"config","valveStates":[0,0,0,0,0,0,0,0]}'

    if request.method == 'POST':
        jsonValveConfigs = request.form['valve']
        inputDefault = jsonValveConfigs
        valveConfigs = json.loads(jsonValveConfigs)
        if valveConfigs['type'] == 'config':
            valveStates = valveConfigs['valveStates']
            binaryValue = 0
            for i in range(0,8):
                if valveStates[i] == 1:
                    binaryValue = binaryValue | 2**i
            valves = Shiftregister()
            valves.outputBinary(binaryValue)
        else:
            message = "Type \"%s\" is not defined." % valveConfigs['type']

    templateData = {
        'title': 'Skrubba',
        'message': message,
        'config': inputDefault
    }
    return render_template('main.html', **templateData)

@app.route("/data/plant.json", methods=['GET', 'POST'])
def plant():

    db = DB()

    action = request.args.get('action')

    if action == 'read':
        plants = []
        valveConfigs = db.loadValveConfigs()
        print 'READ VALVE CONFIG:'
        print valveConfigs
        #if(valveConfigs):
        for config in valveConfigs:
            plant = {}
            plant['id'] = config['id']
            plant['valve'] = config['valve']
            plant['name'] = config['name']
            plant['onTime'] = config['on_time']
            plant['onDuration'] = config['on_duration']
            plant['intervalType'] = config['interval_type']
            plant['isActive'] = config['is_active']
            plants.append(plant)
        response = json.dumps({'plant':plants})
        #else:
        #    plants.append({'valve': 1, 'name': 'Glückskastanie (Pachira aquatica)', 'onTime': '18:30', 'onDuration': 15, 'intervalType': 'daily', 'measures':[40,30,20,60,20,50,10], 'isActive': 1 })
        #    plants.append({'valve': 2, 'name': 'Elefantenfuß (Beaucarnea recurvata)', 'onTime': '18:30', 'onDuration': 15, 'intervalType': 'weekly', 'measures':[40,30,30,40,40,30,40], 'isActive': 1})
        #    plants.append({'valve': 3, 'name': 'Wolfsmilch (Euphorbia trigona)', 'onTime': '18:30', 'onDuration': 15, 'intervalType': 'weekly', 'measures': [40,30,40,60,40,50,50], 'isActive': 0 })
        #    response = json.dumps({'plant':[plants[0],plants[1],plants[2]]})
        #    response = json.dumps({'plant':[]})

    elif action == 'create':
        jsonValveConfigs = request.form['plant']
        valveConfig = json.loads(jsonValveConfigs)
        print 'CREATED VALVE CONFIG:'
        print valveConfig
        newRow = db.addValveConfig(valveConfig['name'], valveConfig['onTime'], valveConfig['onDuration'], valveConfig['intervalType'])

        if len(newRow):
            restartJobManager()
            responseObj = { 'success': 'true', 'plant': newRow }
        else:
            responseObj = { 'success': 'false' }
        response = json.dumps(responseObj)

    elif action == 'update':
        jsonValveConfigs = request.form['plant']
        valveConfig = json.loads(jsonValveConfigs)
        print 'UPDATED VALVE CONFIG:'
        print valveConfig
        success = db.saveValveConfig(valveConfig['id'], valveConfig['valve'], valveConfig['name'], valveConfig['onTime'], valveConfig['onDuration'], valveConfig['intervalType'], valveConfig['isActive'])
        if success == True:
            restartJobManager()
            responseObj = { 'success': 'true' }
        else:
            responseObj = { 'success': 'false', 'message': 'Valve already used by another entry.' }
        response = json.dumps(responseObj)#{'success': 'false', 'message': }#, 500 #'metaData': { 'messageProperty': 'msg', 'successProperty': 'success' }

    elif action == 'destroy':
        jsonValveConfigs = request.form['plant']
        valveConfig = json.loads(jsonValveConfig)
        print 'DELETED VALVE CONFIG:'
        print valveConfig
        success = db.deleteValveConfig(valveConfig['id'])
        restartJobManager()
        response = json.dumps({ 'success': str(success).lower() })

    return response

@app.route("/data/log.json", methods=['GET', 'POST'])
def log():
    db = DB()
    action = request.args.get('action')
    if action == 'read':
        logs = []
        print 'READ LOGS:'
        for line in db.loadLogs():
            log = {}
            #log['id'] = line['id']
            log['valve'] = line['valve']
            log['name'] = line['name']
            log['intervalType'] = line['interval_type']
            log['lastOnDate'] = line['last_on_date']
            logs.append(log)
        response = json.dumps({ 'log': logs })
    return response

@app.route("/actions/manualwatering", methods=['GET', 'POST'])
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

@app.route("/data/setting.json", methods=['GET', 'POST'])
def setting():
    db = DB()
    action = request.args.get('action')
    if action == 'read':
        settings = []
        print 'READ SYSTEM CONF:'
        for line in db.loadSystemSettings():
            # TODO: use same identifiers in backend and frontend...
            if line['setting_name'] == 'valve_amount':
                setting = { 'valveAmount': line['setting_value'] }
            settings.append(setting)
        response = json.dumps({ 'setting': settings })
        print response
    return response

@app.route("/actions/configure", methods=['GET', 'POST'])
def actionConfigure():
    if request.method == 'POST':
        params = request.get_json();
        valveAmount = params['valve_amount']
        print "Set config option [valve amount] to: %i" % valveAmount
        db = DB()
        db.updateSystemSettings('valve_amount', valveAmount)
    response = json.dumps({ 'success': 'true' })
    return response

def checkLocalAccess():
    print 'checking access:'
    requestIp = request.remote_addr
    allowed = (requestIp == '127.0.0.1')
    print requestIp
    print allowed
    return allowed

def postServerOffRequest():
    response = app.test_client().post('/serveroff')
    return response

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

@app.route('/serveroff', methods=['POST'])
def serveroff():
    print 'SERVER SHUTTING DOWN'
    if checkLocalAccess() == True:
        #unloadScheduler()
        unloadFlask()
        response = json.dumps({ 'success': 'true' })
    else:
        response = json.dumps({ 'success': 'false', 'message': 'access denied' })
    return response

@app.route('/reboot', methods=['POST'])
def reboot():
    if checkLocalAccess() == True:
        #unloadScheduler()
        unloadFlask()
        os.system("reboot")
    else:
        response = json.dumps({ 'success': 'false', 'message': 'access denied' })
    return

@app.route('/shutdown', methods=['POST'])
def shutdown():
    if checkLocalAccess() == True:
        #unloadScheduler()
        unloadFlask()
        os.system("poweroff")
    else:
        response = json.dumps({ 'success': 'false', 'message': 'access denied' })
    return

# because there is no 64 bit version of pygame and the display is installed
# on the raspberry pi, not on the development system, omit the import
import struct
cpuArchitecture = struct.calcsize('P') * 8
if cpuArchitecture < 64:
    from display import Display

if __name__ == "__main__":
    if (not DEBUG or os.environ.get('WERKZEUG_RUN_MAIN') == 'true'):
        if cpuArchitecture < 64:
            tft = Display()
            tft.displayImage('static/gfx/lcd-skrubba-color.png', (67, 10), True)
            displayTime = time.time()
        if scheduler.running == False:
            startScheduler()
            restartJobManager()
        if cpuArchitecture < 64:
            while time.time() - displayTime < 5:
                time.sleep(1)
            tft.clear()
            tft.displayImage('static/gfx/lcd-ui-background.png', (0, 0), True)
            addTftJob()
    app.run(host = '0.0.0.0', port = 2525, debug = DEBUG)
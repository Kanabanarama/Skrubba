#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from shiftregister import Shiftregister
from db import DB
from datetime import datetime
import time

app = Flask(__name__, template_folder = 'templates')
scheduler = BackgroundScheduler(standalone = True)

import logging
logging.basicConfig()

def valveJob(setting): #(valve, onDuration)
    print 'OPENING VALVE'
    durationLeft = int(setting['on_duration'])
    binaryValveList = map(int, list(format(3, '08b')))
    print binaryValveList
    shiftreg = Shiftregister()
    shiftreg.outputList(binaryValveList)
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
    print 'Scheduler is running..'
    scheduler.start()
    scheduler.add_listener(schedulerJobEventListener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    return

def schedulerJobEventListener(event):
    if event.exception:
        print('The scheduler job crashed.')
    else:
        print('The scheduler job finished successfully.')


def restartJobManager():
    db = DB()
    valveSettings = db.loadValveSettings()

    #if scheduler.running == True:
    #    scheduler.shutdown()

    # Remove all jobs
    if len(scheduler.get_jobs()) > 0:
        for job in scheduler.get_jobs():
            scheduler.remove_job(job.id)

    # Start scheduler if jobs are set and not already running
    #if scheduler.running == False:
    #    print 'Scheduler is running..'
    #    scheduler.start()
    #    scheduler.add_listener(schedulerJobEventListener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    for setting in valveSettings:
        if setting['on_time'] and setting['on_duration'] and setting['is_active']:
            timeComponents = map(int, setting['on_time'].split(':'))
            timeNextRun = datetime.now().replace(hour = timeComponents[0], minute = timeComponents[1], second = 0, microsecond = 0)
            #valveToOpen = int(setting['valve'])
            #openingDuration = int(setting['on_duration'])
            if(setting['interval_type'] == 'daily'):
                scheduler.add_job(valveJob, 'cron', day_of_week = 'mon-sun', hour = timeComponents[0], minute = timeComponents[1], args = [setting])
                print 'Scheduled daily job [%i:%i]' % (timeComponents[0], timeComponents[1])
            if(setting['interval_type'] == 'weekly'):
                scheduler.add_job(valveJob, 'cron', day_of_week = 'so', hour = timeComponents[0], minute = timeComponents[1], args = [setting])
                print 'Scheduled weekly job [sun %i:%i]' % (timeComponents[0], timeComponents[1])
            if(setting['interval_type'] == 'monthly'):
                scheduler.add_job(valveJob, 'cron', day = 1, hour = timeComponents[0], minute = timeComponents[1], args = [setting])
                print 'Scheduled monthly job [1st of the month %i:%i]' % (timeComponents[0], timeComponents[1])

    print 'JOBS:'
    print scheduler.get_jobs()
    return

@app.route("/", methods=['GET', 'POST'])
def index():

    #db = DB()
    #if db.exists() != True :
    #db.createTables()

    message = "Hello Web!"

    inputDefault = '{"type":"setting","valveStates":[0,0,0,0,0,0,0,0]}'

    if request.method == 'POST':
        jsonValveSettings = request.form['valve']
        inputDefault = jsonValveSettings
        valveSettings = json.loads(jsonValveSettings)
        if valveSettings['type'] == 'setting':
            valveStates = valveSettings['valveStates']
            binaryValue = 0
            for i in range(0,8):
                if valveStates[i] == 1:
                    binaryValue = binaryValue | 2**i
            valves = Shiftregister()
            valves.outputBinary(binaryValue)
        else:
            message = "Type \"%s\" is not defined." % valveSettings['type']

    templateData = {
        'title': 'Skrubba',
        'message': message,
        'settings': inputDefault
    }
    return render_template('main.html', **templateData)

@app.route("/data/plant.json", methods=['GET', 'POST'])
def plant():

    db = DB()

    action = request.args.get('action')

    if action == 'read':
        plants = []
        valveSettings = db.loadValveSettings()
        print 'READ SETTINGS:'
        print valveSettings
        #if(valveSettings):
        for setting in valveSettings:
            plant = {}
            plant['id'] = setting['id']
            plant['valve'] = setting['valve']
            plant['name'] = setting['name']
            plant['onTime'] = setting['on_time']
            plant['onDuration'] = setting['on_duration']
            plant['intervalType'] = setting['interval_type']
            plant['isActive'] = setting['is_active']
            plants.append(plant)
        response = json.dumps({'plant':plants})
        #else:
        #    plants.append({'valve': 1, 'name': 'Glückskastanie (Pachira aquatica)', 'onTime': '18:30', 'onDuration': 15, 'intervalType': 'daily', 'measures':[40,30,20,60,20,50,10], 'isActive': 1 })
        #    plants.append({'valve': 2, 'name': 'Elefantenfuß (Beaucarnea recurvata)', 'onTime': '18:30', 'onDuration': 15, 'intervalType': 'weekly', 'measures':[40,30,30,40,40,30,40], 'isActive': 1})
        #    plants.append({'valve': 3, 'name': 'Wolfsmilch (Euphorbia trigona)', 'onTime': '18:30', 'onDuration': 15, 'intervalType': 'weekly', 'measures': [40,30,40,60,40,50,50], 'isActive': 0 })
        #    response = json.dumps({'plant':[plants[0],plants[1],plants[2]]})
        #    response = json.dumps({'plant':[]})

    elif action == 'create':
        jsonValveSettings = request.form['plant']
        valveSetting = json.loads(jsonValveSettings)
        print 'CREATED SETTINGS:'
        print valveSetting
        newRow = db.addValveSetting(valveSetting['name'], valveSetting['onTime'], valveSetting['onDuration'], valveSetting['intervalType'])

        if len(newRow):
            restartJobManager()
            responseObj = { 'success': 'true', 'plant': newRow }
        else:
            responseObj = { 'success': 'false' }
        response = json.dumps(responseObj)

    elif action == 'update':
        jsonValveSettings = request.form['plant']
        valveSetting = json.loads(jsonValveSettings)
        print 'UPDATED SETTINGS:'
        #print valveSetting
        success = db.saveValveSetting(valveSetting['id'], valveSetting['valve'], valveSetting['name'], valveSetting['onTime'], valveSetting['onDuration'], valveSetting['intervalType'], valveSetting['isActive'])
        if success == True:
            restartJobManager()
            responseObj = { 'success': 'true' }
        else:
            responseObj = { 'success': 'false', 'message': 'Valve already used by another entry.' }
        response = json.dumps(responseObj)#{'success': 'false', 'message': }#, 500 #'metaData': { 'messageProperty': 'msg', 'successProperty': 'success' }

    elif action == 'destroy':
        jsonValveSettings = request.form['plant']
        valveSetting = json.loads(jsonValveSettings)
        print 'DELETED SETTINGS:'
        print valveSetting
        success = db.deleteValveSetting(valveSetting['id'])
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
    response = 'watered plants.';
    return response

if __name__ == "__main__":
    startScheduler()
    restartJobManager()
    app.run(host = '0.0.0.0', port = 2525, debug = False) #True
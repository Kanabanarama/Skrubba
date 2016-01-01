#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, json
#from celery import Celery
from shiftregister import Shiftregister
from db import DB

app = Flask(__name__, template_folder = 'templates')

#app.config.update(
#    CELERY_BROKER_URL = 'redis://localhost:6379/0',
#    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
#)

#celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
#celery.conf.update(app.config)

#@celery.task()
#def valveWorker():
#    console.log('test');
#    return True

#result = valveWorker.delay()
#result.wait();

#from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR#, EVENT_JOB_MISSED
#import time, datetime
import time
from datetime import datetime

'''
scheduler = BackgroundScheduler(standalone = True)

print 'JOBS:'
print scheduler.get_jobs()

@scheduler.scheduled_job('interval', seconds = 10)
def valveWorker():
    print 'Scheduler Job started %s' % datetime.datetime.now().time()
    db = DB()
    valveSettings = db.loadValveSettings()
    #now = datetime.datetime.now()
    for setting in valveSettings:
        #print setting['on_time']
        if setting['on_time'] and setting['on_duration']:
            if(setting['interval_type'] == 'daily'):
                #timeNow = datetime.datetime.now().strftime('%H:%M')
                #timeComponents = setting['on_time'].split(':')
                #timeComponents = [int(n) for n in setting['on_time'].split(':')]
                timeComponents = map(int, setting['on_time'].split(':'))
                timeNextRun = datetime.datetime.now().replace(hour = timeComponents[0], minute = timeComponents[1], second = 0, microsecond = 0)
                timeNextRunFinished = timeNextRun + datetime.timedelta(seconds = setting['on_duration'])
                timeNow = datetime.datetime.now()

                # TODO: reload config after change

                if timeNow > timeNextRun and timeNow < timeNextRunFinished:
                    duration = int(setting['on_duration'])
                    while duration > 0:
                        time.sleep(1)
                        duration -= 1
                        print 'TIME LEFT: %i' % duration

                    print 'FINISHED'

                #print timeNow > nextRun



                #if timeNow < setting['on_time']:
                #    testTime = timeNow + setting['on_time']
                #    print '__'
            elif(setting['interval_type'] == 'weekly'):
                print 'TODO: implement weekly interval'
            elif(setting['interval_type'] == 'monthly'):
                print 'TODO: implement monthly interval'
            #nextRun = datetime.datetime.strptime(setting['on_time'], '%H:%M')
                #print 'RUN'
            #nextRun = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return

scheduler.start()

def schedulerJobEventListener(event):
    if event.exception:
        print('The scheduler job crashed.')
    else:
        print('The scheduler job finished successfully.')

scheduler.add_listener(schedulerJobEventListener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

#scheduler.shutdown(wait = True)
'''

from apscheduler.schedulers.background import BackgroundScheduler
#from apscheduler.schedulers import Scheduler

#import logging
#logging.basicConfig()



'''
def testJob():
    print 'job'
    return

job = scheduler.add_job(testJob, run_date = datetime(2015, 12, 27, 15, 58))
'''

def valveJob(valve, onDuration):
    print 'OPENING VALVE'
    durationLeft = onDuration
    while durationLeft > 0:
        time.sleep(1)
        durationLeft -= 1
        print 'TIME LEFT: %i' % durationLeft
    print 'CLOSING VALVE'
    return

def restartJobManager():
    db = DB()
    valveSettings = db.loadValveSettings()
    scheduler = BackgroundScheduler(standalone = True)
    for setting in valveSettings:
        if setting['on_time'] and setting['on_duration']:
            if(setting['interval_type'] == 'daily'):
                timeComponents = map(int, setting['on_time'].split(':'))
                #print timeComponents
                timeNextRun = datetime.now().replace(hour = timeComponents[0], minute = timeComponents[1], second = 0, microsecond = 0)
                valveToOpen = int(setting['valve'])
                openingDuration = int(setting['on_duration'])
                #scheduler.add_job(valveJob, run_date = timeNextRun, args = [valveToOpen, openingDuration])
                #scheduler.add_cron_job(valveJob, day_of_week = '0-7', hour = timeComponents[0], minute = timeComponents[1])
                # TODO: implement active
                scheduler.add_job(valveJob, 'cron', day_of_week = 'mon-fri', hour = timeComponents[0], minute = timeComponents[1], args = [valveToOpen, openingDuration])
            if(setting['interval_type'] == 'weekly'):
                print 'implement weekly interval'
    scheduler.start()
    print 'JOBS:'
    #print scheduler.print_jobs()
    print scheduler.get_jobs()
    #for job in scheduler.get_jobs():
    #    print job
    #    print job.trigger
    #    print job.trigger.hour
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
def data():

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
        print valveSetting
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
    app.run(
        host='0.0.0.0', port=2525, debug=False#True
    )
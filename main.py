#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, json
from shiftregister import Shiftregister
from db import DB
app = Flask(__name__, template_folder='templates')

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
        if(valveSettings):
            for setting in valveSettings:
                plant = {}
                plant['valve'] = setting['valve']
                plant['name'] = setting['name']
                plant['onTime'] = setting['on_time']
                plant['onDuration'] = setting['on_duration']
                plant['intervalType'] = setting['interval_type']
                plants.append(plant)
            response = json.dumps({'plant':plants})
        else:
            plants.append({'valve': 1, 'name': 'Glückskastanie (Pachira aquatica)', 'onTime': '18:30', 'onDuration': 15, 'intervalType': 'daily', 'measures':[40,30,20,60,20,50,10], 'isActive': 1 })
            plants.append({'valve': 2, 'name': 'Elefantenfuß (Beaucarnea recurvata)', 'onTime': '18:30', 'onDuration': 15, 'intervalType': 'weekly', 'measures':[40,30,30,40,40,30,40], 'isActive': 1})
            plants.append({'valve': 3, 'name': 'Wolfsmilch (Euphorbia trigona)', 'onTime': '18:30', 'onDuration': 15, 'intervalType': 'weekly', 'measures': [40,30,40,60,40,50,50], 'isActive': 0 })
            response = json.dumps({'plant':[plants[0],plants[1],plants[2]]})
    elif action == 'create':
        #jsonValveSettings = request.get_json();
        jsonValveSettings = request.form['plant']
        valveSettings = json.loads(jsonValveSettings)
        print 'SETTINGS:'
        print valveSettings
        valveSetting = valveSettings
        #query = 'INSERT INTO valve_settings (valve, name, on_time, on_duration, interval_type) VALUES ({valve}, "{name}", "{on_time}", {on_duration}, "{interval_type}")'
        #dbquery = query.format(valve=1, name="test", on_time="18:30", on_duration=15, interval_type="daily")
        #db.query(dbquery)
        db.addValveSetting(valveSetting['valve'], valveSetting['name'], valveSetting['onTime'], valveSetting['onDuration'])
        response = json.dumps({'success':1})

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
        host='0.0.0.0', port=2525, debug=True
    )
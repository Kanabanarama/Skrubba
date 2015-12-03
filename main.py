#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, json
from shiftregister import Shiftregister
app = Flask(__name__, template_folder='templates')

@app.route("/", methods=['GET', 'POST'])
def index():
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
    plant = []
    plant.append({'valve': 1, 'name': 'Glückskastanie (Pachira aquatica)', 'onTime': '18:30', 'onDuration': 15, 'intervalType': 'daily', 'measures':[40,30,20,60,20,50,10], 'isActive': 1 })
    plant.append({'valve': 2, 'name': 'Elefantenfuß (Beaucarnea recurvata)', 'onTime': '18:30', 'onDuration': 15, 'intervalType': 'weekly', 'measures':[40,30,30,40,40,30,40], 'isActive': 1})
    plant.append({'valve': 3, 'name': 'Wolfsmilch (Euphorbia trigona)', 'onTime': '18:30', 'onDuration': 15, 'intervalType': 'weekly', 'measures': [40,30,40,60,40,50,50], 'isActive': 0 })
    response = json.dumps({'plant':[plant[0],plant[1],plant[2]]})
    return response

@app.route("/actions/manualwatering", methods=['GET', 'POST'])
def actionManualwatering():
    if request.method == 'POST':
        params = request.get_json();
        valveNo = params['id']
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
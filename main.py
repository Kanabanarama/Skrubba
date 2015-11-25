#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, json
app = Flask(__name__, template_folder='templates')

@app.route("/", methods=['GET', 'POST'])
def index():
    message = "Hello Web!"

    if request.method == 'POST':
        jsonValveSettings = request.form['valve']
        valveSettings = json.loads(jsonValveSettings)
        if valveSettings['type'] == 'setting':
            valveStates = valveSettings['valveStates']
            message = "Valve states: | %i | %i | %i | %i | %i | %i | %i | %i |" % (valveStates[0], valveStates[1], valveStates[2], valveStates[3], valveStates[4], valveStates[5], valveStates[6], valveStates[7])
        else:
            message = "Type \"%s\" is not defined." % valveSettings['type']

    templateData = {
        'title': 'Skrubba',
        'message': message
    }
    return render_template('main.html', **templateData)

if __name__ == "__main__":
    app.run(
        host='0.0.0.0', port=2525, debug=True
    )
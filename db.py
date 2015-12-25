#!/usr/bin/env python

# File db.py
# Class for saving and loading configuration
# Database is sqlite3
# by Kana kanabanarama@googlemail.com

import sqlite3, itertools, os

class DB(object):
    _connection = None
    _cursor = None
    def __init__(self):
        self._connection = sqlite3.connect('skrubba.db')
        self._connection.row_factory = sqlite3.Row
        self._cursor = self._connection.cursor()
        self._cursor.execute('SELECT name FROM sqlite_master WHERE name="valve_settings";')
        result = self._cursor.fetchone()
        if not result:
            self.__createTables()
        return

    def __del__(self):
        self._connection.close()
        return

    def __exists(self):
        if os.path.isfile('skrubba.db'):
            return True
        return False

    def __createTables(self):
        print "Creating table..."
        success = self._cursor.execute('CREATE TABLE valve_settings(valve INTEGER PRIMARY KEY, name TEXT, on_time DATETIME, on_duration INTEGER, interval_type TEXT, is_active BOOLEAN);')
        return success

    def query(self, query, params = None):
        self._cursor.execute(query)
        self._connection.commit()
        return self._cursor

    def addValveSetting(self, name, onTime, onDuration, intervalType):
        success = self._cursor.execute('INSERT INTO valve_settings(name, on_time, on_duration, interval_type) VALUES((?), (?), (?), (?));', (name, onTime, onDuration, 'daily'))
        self._connection.commit()
        row = [{'valve': self._cursor.lastrowid}]
        return row

    def saveValveSetting(self, valve, name, onTime, onDuration, intervalType, isActive):
        success = self._cursor.execute('UPDATE valve_settings set name = (?), on_time = (?), on_duration = (?), interval_type = (?), is_active = (?) WHERE valve = (?);', (name, onTime, onDuration, intervalType, isActive, valve))
        self._connection.commit()
        return success

    def deleteValveSetting(self, valveID):
        success = self._cursor.execute('DELETE FROM valve_settings WHERE valve = (?);', (valveID,))
        self._connection.commit()
        return success

    def loadValveSettings(self):
        rows = []
        self._cursor.execute('SELECT * FROM valve_settings')
        for row in self._cursor:
            print row
            rowDict = dict(itertools.izip(row.keys(), row))
            rows.append(rowDict)
        return rows
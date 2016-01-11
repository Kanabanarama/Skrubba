#!/usr/bin/env python

# File db.py
# Class for saving and loading configuration
# Database is sqlite3
# by Kana kanabanarama@googlemail.com

import sqlite3, itertools, re, os

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
        print "Closing db connection."
        self._connection.close()
        return

    def __exists(self):
        if os.path.isfile('skrubba.db'):
            return True
        return False

    def __createTables(self):
        print "Creating table..."
        createdTables = 0
        self._cursor.execute('CREATE TABLE valve_settings(id INTEGER PRIMARY KEY, valve INTEGER UNIQUE, name TEXT, on_time DATETIME, on_duration INTEGER, interval_type TEXT, is_active BOOLEAN);')
        createdTables += self._cursor.rowcount
        self._cursor.execute('CREATE TABLE valve_logs(settings_id INTEGER, valve INTEGER, on_time DATETIME, on_duration INTEGER, interval_type TEXT, last_on_date TEXT);')
        createdTables += self._cursor.rowcount
        #success = bool(self._cursor.rowcount)
        success = (createdTables == 2)
        return success

    #def query(self, query, params = None):
    #    self._cursor.execute(query)
    #    self._connection.commit()
    #    return self._cursor

    def addValveSetting(self, name, onTime, onDuration, intervalType):
        # find first available valve
        self._cursor.execute('SELECT (s1.valve+1) as unused FROM valve_settings s1 LEFT JOIN valve_settings s2 ON s1.valve = s2.valve -1 WHERE s2.valve IS NULL')
        nextUnusedValve = self._cursor.fetchone()
        if nextUnusedValve is not None:
            #print int(re.search(r'\d+', nextUnusedValve).group())
            nextUnusedValve = nextUnusedValve[0]
        else:
            nextUnusedValve = 1
        success = self._cursor.execute('INSERT INTO valve_settings(valve, name, on_time, on_duration, interval_type) VALUES((?), (?), (?), (?), (?));', (nextUnusedValve, name, onTime, onDuration, 'daily')) #(SELECT IFNULL(MAX(valve), 0) + 1 FROM valve_settings)
        self._connection.commit()
        row = [{ 'id': self._cursor.lastrowid, 'valve': nextUnusedValve }]
        return row

    def saveValveSetting(self, id, valve, name, onTime, onDuration, intervalType, isActive):
        try:
            success = self._cursor.execute('UPDATE valve_settings set valve = (?), name = (?), on_time = (?), on_duration = (?), interval_type = (?), is_active = (?) WHERE id = (?);', (valve, name, onTime, onDuration, intervalType, isActive, id))
            self._connection.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False
        return success

    def deleteValveSetting(self, id):
        self._cursor.execute('DELETE FROM valve_settings WHERE id = (?);', (id,))
        self._connection.commit()
        success = bool(self._cursor.rowcount)
        return success

    def loadValveSettings(self):
        rows = []
        self._cursor.execute('SELECT * FROM valve_settings')
        for row in self._cursor:
            rowDict = dict(itertools.izip(row.keys(), row))
            rows.append(rowDict)
        return rows

    def addLogLine(self, valveInfo, onDate):
        print 'ADDING LOG LINE:'
        print valveInfo
        print onDate
        success = self._cursor.execute('INSERT INTO valve_logs(settings_id, valve, on_time, on_duration, interval_type, last_on_date) VALUES((?), (?), (?), (?), (?), (?));', (valveInfo['id'], valveInfo['valve'], valveInfo['on_time'], valveInfo['on_duration'], valveInfo['interval_type'], onDate))
        self._connection.commit()
        print 'LINES ADDED: %i' % self._cursor.rowcount
        row = [{ 'id': self._cursor.lastrowid }]
        return row

    def loadLogs(self):
        rows = []
        self._cursor.execute('SELECT * FROM valve_logs LEFT JOIN valve_settings ON valve_logs.valve = valve_settings.valve')
        for row in self._cursor:
            print row
            rowDict = dict(itertools.izip(row.keys(), row))
            rows.append(rowDict)
        return rows
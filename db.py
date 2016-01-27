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
        self._cursor.execute('SELECT name FROM sqlite_master WHERE name="system_settings";')
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
        self._cursor.execute('CREATE TABLE system_settings(setting_name TEXT UNIQUE, setting_value TEXT);')
        createdTables += self._cursor.rowcount
        self._cursor.execute('CREATE TABLE valve_configs(id INTEGER PRIMARY KEY, valve INTEGER UNIQUE, name TEXT, on_time DATETIME, on_duration INTEGER, interval_type TEXT, is_active BOOLEAN);')
        createdTables += self._cursor.rowcount
        self._cursor.execute('CREATE TABLE valve_logs(valve_config_id INTEGER, valve INTEGER, on_time DATETIME, on_duration INTEGER, interval_type TEXT, last_on_date TEXT);')
        createdTables += self._cursor.rowcount
        #success = bool(self._cursor.rowcount)
        success = (createdTables == 3)
        return success

    def updateSystemSettings(self, settingName, settingValue):
        print 'UPDATE SYSTEM SETTINGS: %s = %s' % (settingName, settingValue)
        sql = 'INSERT OR REPLACE INTO system_settings (setting_name, setting_value) VALUES ((?), (?));'
        success = self._cursor.execute(sql, (settingName, settingValue))
        self._connection.commit()
        return success

    def loadSystemSettings(self):
        rows = []
        self._cursor.execute('SELECT * FROM system_settings;')
        for row in self._cursor:
            print row
            rowDict = dict(itertools.izip(row.keys(), row))
            rows.append(rowDict)
        return rows

    def getValveCount(self):
        sql = 'SELECT IFNULL(COUNT(*), 0) AS count FROM valve_configs;'
        self._cursor.execute(sql)
        result = self._cursor.fetchone()
        valveCount = int(result[0])
        print 'getValveCount: %i' % valveCount
        return valveCount

    def getMaxValveCountSetting(self):
        sql = 'SELECT IFNULL(setting_value, 99) FROM system_settings WHERE setting_name = "valve_amount";'
        self._cursor.execute(sql)
        result = self._cursor.fetchone()
        valveMaxCount = int(result[0])
        print 'getMaxValveCountSetting: %i' % valveMaxCount
        return valveMaxCount

    def addValveConfig(self, config):
        sql = 'SELECT (s1.valve+1) as unused FROM valve_configs s1 LEFT JOIN valve_configs s2 ON s1.valve = s2.valve -1 WHERE s2.valve IS NULL;'
        self._cursor.execute(sql)
        nextUnusedValve = self._cursor.fetchone()
        if nextUnusedValve is not None:
            #print int(re.search(r'\d+', nextUnusedValve).group())
            nextUnusedValve = nextUnusedValve[0]
        else:
            nextUnusedValve = 1
        sql = 'INSERT INTO valve_configs(valve, name, on_time, on_duration, interval_type) VALUES((?), (?), (?), (?), (?));'
        success = self._cursor.execute(sql, (nextUnusedValve, config['name'], config['on_time'], config['on_duration'], config['interval_type']))
        self._connection.commit()
        row = [{ 'id': self._cursor.lastrowid, 'valve': nextUnusedValve }]
        return row

    def saveValveConfig(self, config): #id, valve, name, onTime, onDuration, intervalType, isActive
        try:
            sql = 'UPDATE valve_configs set valve = (?), name = (?), on_time = (?), on_duration = (?), interval_type = (?), is_active = (?) WHERE id = (?);'
            success = self._cursor.execute(sql, (config['valve'], config['name'], config['on_time'], config['on_duration'], config['interval_type'], config['is_active'], config['id']))
            self._connection.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False
        return success

    def deleteValveConfig(self, id):
        self._cursor.execute('DELETE FROM valve_configs WHERE id = (?);', (id,))
        self._connection.commit()
        success = bool(self._cursor.rowcount)
        return success

    def loadValveConfigs(self):
        rows = []
        self._cursor.execute('SELECT * FROM valve_configs')
        for row in self._cursor:
            rowDict = dict(itertools.izip(row.keys(), row))
            rows.append(rowDict)
        return rows

    def addLogLine(self, data, logDate):
        print 'ADDING LOG LINE:'
        print valveInfo
        print onDate
        sql = 'INSERT INTO valve_logs(valve_config_id, valve, on_time, on_duration, interval_type, last_on_date) VALUES((?), (?), (?), (?), (?), (?));'
        success = self._cursor.execute(sql, (data['id'], data['valve'], data['on_time'], data['on_duration'], data['interval_type'], logDate))
        self._connection.commit()
        print 'LINES ADDED: %i' % self._cursor.rowcount
        row = [{ 'id': self._cursor.lastrowid }]
        return row

    def loadLogs(self):
        rows = []
        self._cursor.execute('SELECT * FROM valve_logs LEFT JOIN valve_configs ON (valve_logs.valve_config_id = valve_configs.valve_config_id);')
        for row in self._cursor:
            print row
            rowDict = dict(itertools.izip(row.keys(), row))
            rows.append(rowDict)
        return rows
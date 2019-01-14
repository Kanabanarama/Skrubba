#!/usr/bin/env python

"""
File db.py
Database is sqlite3
by Kana kanabanarama@googlemail.com
"""

import os
import sqlite3

class DB():
    """
    Class for saving and loading configuration
    """
    _store_path = 'store/skrubba.db'
    _connection = None
    _cursor = None

    def __init__(self):
        self._connection = sqlite3.connect(self._store_path)
        self._connection.row_factory = sqlite3.Row
        self._cursor = self._connection.cursor()
        self._cursor.execute('SELECT name FROM sqlite_master WHERE name="system_settings";')
        result = self._cursor.fetchone()
        if not result:
            self.__create_tables()

    def __del__(self):
        return self._connection.close()

    def __exists(self):
        """
        Check if there is an existing database
        """
        if os.path.isfile(self._store_path):
            return True
        return False

    def __create_tables(self):
        """
        Create database tables
        """
        created_tables = 0
        self._cursor.execute('CREATE TABLE system_settings(setting_name TEXT'
                             'UNIQUE, setting_value TEXT);')
        created_tables += self._cursor.rowcount
        self._cursor.execute('CREATE TABLE valve_configs(id INTEGER PRIMARY KEY'
                             ', valve INTEGER UNIQUE, name TEXT, on_time'
                             'DATETIME, on_duration INTEGER, interval_type TEXT'
                             ', is_active BOOLEAN);')
        created_tables += self._cursor.rowcount
        self._cursor.execute('CREATE TABLE valve_logs(valve_config_id INTEGER, '
                             'valve INTEGER, on_time DATETIME, on_duration '
                             'INTEGER, interval_type TEXT, last_on_date TEXT);')
        created_tables += self._cursor.rowcount
        #success = bool(self._cursor.rowcount)
        success = (created_tables == 3)

        return success

    def update_system_settings(self, setting_name, setting_value):
        """
        Update entries in system settings table
        """
        # print 'UPDATE SYSTEM SETTINGS: %s = %s' % (setting_name, setting_value)
        sql = ('INSERT OR REPLACE INTO system_settings (setting_name, ' \
               'setting_value) VALUES ((?), (?));')
        success = self._cursor.execute(sql, (setting_name, setting_value))
        self._connection.commit()
        return success

    def delete_system_setting(self, setting_name):
        """
        Delete entries in system settings table
        """
        # print 'DELETE SYSTEM SETTING: %s' % setting_name
        sql = 'DELETE FROM system_settings WHERE setting_name = (?);'
        success = self._cursor.execute(sql, (setting_name,))
        self._connection.commit()
        return success

    def get_system_settings(self):
        """
        Load all entries from system settings table
        """
        rows = []
        self._cursor.execute('SELECT * FROM system_settings;')
        for row in self._cursor:
            # print row
            row_dict = dict(zip(row.keys(), row))
            rows.append(row_dict)
        return rows

    def get_max_valve_count_setting(self):
        """
        Get setting for maximum configurable number of valves
        """
        sql = 'SELECT setting_value FROM system_settings WHERE setting_name = "valve_amount";'
        self._cursor.execute(sql)
        result = self._cursor.fetchone()
        valve_max_count = int(result[0]) if result else 8
        # print 'get_max_valve_count_setting: %i' % valve_max_count
        return valve_max_count

    def get_valve_count(self):
        """
        Get current count of entries in valve table
        """
        sql = 'SELECT IFNULL(COUNT(*), 0) AS count FROM valve_configs;'
        self._cursor.execute(sql)
        result = self._cursor.fetchone()
        valve_count = int(result[0])
        # print 'get_valve_count: %i' % valve_count
        return valve_count

    def add_valve_config(self, config):
        """
        Insert a new valve entry into valve table
        """
        sql = 'SELECT (s1.valve+1) as unused FROM valve_configs s1 LEFT JOIN ' \
        'valve_configs s2 ON s1.valve = s2.valve -1 WHERE s2.valve IS NULL;'
        self._cursor.execute(sql)
        next_unused_valve = self._cursor.fetchone()
        if next_unused_valve is not None:
            # print 'Next unused valve: ' + str(int(re.search(r'\d+', next_unused_valve).group()))
            next_unused_valve = next_unused_valve[0]
        else:
            next_unused_valve = 1
        sql = ('INSERT INTO valve_configs(valve, name, on_time, on_duration, ' \
               'interval_type) VALUES((?), (?), (?), (?), (?));')
        self._cursor.execute(sql, (
            next_unused_valve,
            config['name'],
            config['on_time'],
            config['on_duration'],
            config['interval_type']))
        self._connection.commit()
        row = [{'id': self._cursor.lastrowid, 'valve': next_unused_valve}]
        return row

    def update_valve_config(self, config):
        """
        Update existing valve entry
        """
        # config: id, valve, name, on_time, on_duration, interval_type, is_active
        try:
            sql = ('UPDATE valve_configs set valve = (?), name = (?), on_time = ' \
                   '(?), on_duration = (?), interval_type = (?), is_active = (?) ' \
                   'WHERE id = (?);')
            success = self._cursor.execute(sql, (
                config['valve'],
                config['name'],
                config['on_time'],
                config['on_duration'],
                config['interval_type'],
                config['is_active'],
                config['id']))
            self._connection.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False
        return success

    def delete_valve_config(self, valve_id):
        """
        Delete a valve entry
        """
        self._cursor.execute('DELETE FROM valve_configs WHERE id = (?);', (valve_id,))
        self._connection.commit()
        success = bool(self._cursor.rowcount)
        return success

    def load_valve_configs(self):
        """
        Get all valve entries
        """
        rows = []
        self._cursor.execute('SELECT * FROM valve_configs ORDER BY valve')
        for row in self._cursor:
            row_dict = dict(zip(row.keys(), row))
            rows.append(row_dict)
        return rows

    def add_log_line(self, data, log_date):
        """
        Insert new log entry
        """
        sql = ('INSERT INTO valve_logs(valve_config_id, valve, on_time, ' \
               'on_duration, interval_type, last_on_date) VALUES((?), (?), (?), (?), ' \
               '(?), (?));')
        self._cursor.execute(sql, (
            data['id'],
            data['valve'],
            data['on_time'],
            data['on_duration'],
            data['interval_type'],
            log_date))
        self._connection.commit()
        # print 'LINES ADDED: %i' % self._cursor.rowcount
        row = [{'id': self._cursor.lastrowid}]
        return row

    def load_logs(self):
        """
        Get all log entries
        """
        rows = []
        self._cursor.execute('SELECT valve_logs.* FROM valve_logs LEFT JOIN '
                             'valve_configs ON (valve_logs.valve_config_id = '
                             'valve_configs.id);')
        for row in self._cursor:
            # print row
            row_dict = dict(zip(row.keys(), row))
            rows.append(row_dict)
        return rows

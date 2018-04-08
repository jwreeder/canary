#! /bin/env python

import pymongo, json

class Database():
    def fetch(self, id):
        pass
    def upsert(self, data):
        pass
    def delete(self, id):
        pass

class Mongo(Database):

    def __init__(self, host='localhost', port=27017):
        self.client = pymongo.MongoClient(host, port)
        self.db = self.client.sensors
        self.collection = self.db.sensors

    def fetch(self, uuid, sensor, start, end):
        data = self.collection.find({'device_uuid': uuid, 'sensor_type': sensor, 'sensor_reading_time': {'$gte': start, '$lte': end}})
        a = []
        for d in data:
            buf = {}
            buf['device_uuid'] = d['device_uuid']
            buf['sensor_type'] = d['sensor_type']
            buf['sensor_value'] = d['sensor_value']
            buf['sensor_reading_time'] = d['sensor_reading_time']
            a.append(buf)

        return json.dumps(a)

    def insert(self, record):
        oid = self.collection.insert_one(record)
        return '{{"ObjectId": "{0}"}}'.format(oid.inserted_id)

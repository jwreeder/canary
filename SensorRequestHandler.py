#! /bin/env python


from http.server import BaseHTTPRequestHandler
from Database import Mongo
import time, re, json, sys

PORT = 5000

class SensorRequestHandler(BaseHTTPRequestHandler):

    def set_headers(self):
        self.send_response(self.response_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

    def do_GET(self):
        self.err = False
        req_data = self.validate_get(self.path)
        if(self.err):
            self.return_error(req_data)
        else:
            self.response_code = 200
            self.db_client = Mongo()
            data = self.db_client.fetch(req_data[0], req_data[1], req_data[2], req_data[3])
            self.set_headers()
            self.wfile.write(data.encode())

    # Returning a 201. My first plan was to implement a queue and return immediately 202 Accepted would have
    #    been appropriate. This would be the better approach for a production system so that the
    #    persistent storage is not overwhelmed during peak load periods and data is buffered
    #    Could have implemented logic to disallow the insertion of identical records and return 409
    def do_POST(self):
        self.err = False
        self.response_code = 201
        content_length = int(self.headers['Content-Length'])
        data = self.rfile.read(content_length)
        j = self.validate_post(self.path, data.decode())
        if self.err:
            self.return_error(j)
        else:
            self.db_client = Mongo()
            data = self.db_client.insert(j)
            self.set_headers()
            self.wfile.write(data.encode())

    # Unsupported methods, overridden so a 500 isn't sent back to the client
    def do_HEAD(self):
        self.response_code = 405
        self.set_headers()

    # was going to implement but didn't see a reason why sensor data would need to be updated
    def do_PATCH(self):
        self.response_code = 405
        self.set_headers()

    def do_PUT(self):
        self.response_code = 405
        self.set_headers()

    def do_DELETE(self):
        self.response_code = 405
        self.set_headers()

    def return_error(self, err_data):
        self.response_code = 400
        self.set_headers()
        msg = '{{"ERROR": "{0}"}}'.format(err_data)
        self.wfile.write(msg.encode())

    COLLECTION_NAME = 'sensors'
    VALID_SENSOR_TYPES = {'temperature', 'humidity'}

    # device uuid is the common uuid format with the '-' removed
    path_re = re.compile(r'/\w+/(?P<device_uuid>\w+)/(?P<sensor_type>\w+)/(?P<start_time>\d+)/(?P<end_time>\d+)')#.format(COLLECTION_NAME))
    uuid_re = re.compile(r'^[0-9a-fA-F]{32}$')

    def parse_get_path(self, path):
        ''' The path for a GET request should be:
        /sensors/<device_uuid>/<sensor_type>/<start_time>/<end_time>
        All elements are required, if some are missing blow up'''
        elements = SensorRequestHandler.path_re.search(path)
        if elements:
            return (self.validate_device_uuid(elements.group('device_uuid')),
                    self.validate_sensor_type(elements.group('sensor_type')),
                    self.validate_time(elements.group('start_time'), 'start'),
                    self.validate_time(elements.group('end_time'), 'end'))
        else:
            return None

    def valid_collection(self, path, required_length):
        parts = path.lstrip('/').split('/')
        if parts[0] != SensorRequestHandler.COLLECTION_NAME or len(parts) != required_length:
            self.err = True
            return False
        return True

    def check_invalid(self, req_data):
        errors = []
        if req_data:
            for i in range(4):
                if str(req_data[i]).startswith('Invalid'):
                    errors.append(req_data[i])
                    self.err = True
                    return req_data[i]
        return errors #will be empty list and eval to false if not invalid

    def validate_get(self, path):
        ''' validates that all fields are present in the REST URI
        returns a tuple of the data that will be used to query the db'''
        if self.valid_collection(path, 5):
            req_data = self.parse_get_path(path)
            errors = self.check_invalid(req_data)
            if errors:
                return ','.join(errors)
            return req_data

        return self.error_string('request')

    def validate_post(self, path, data):
        ''' Validates collection name in path and no
        extraneous data, ensures that the data can be
        parsed into json. Returns a json object or error string'''

        if self.valid_collection(path, 1):
            try:
                j = json.loads(data)
                req_data = (self.validate_device_uuid(j['device_uuid']),
                            self.validate_sensor_type(j['sensor_type']),
                            self.validate_sensor_value(j['sensor_value']),
                            self.validate_time(j['sensor_reading_time'], 'sensor reading'))
                errors = self.check_invalid(req_data)
                if errors:
                    if isinstance(errors, str):
                        return errors
                    else:
                        return ','.join(errors)
                return j
            except NameError: # probably a missing key in the data, all 4 fields are required
                self.err = True
                return self.error_string('request: {0}'.format(sys.exc_info()[1]))
            except json.JSONDecodeError: # probably a deserialization error due to bad data
                self.err = True
                return self.error_string('request: {0}'.format('Error decoding json data'))
            except:
                self.err = True
                return self.error_string('request: {0}'.format(sys.exc_info()[0]))

    def validate_device_uuid(self, uuid):
        if SensorRequestHandler.uuid_re.match(uuid):
            return uuid
        return self.error_string('device uuid')

    def validate_sensor_type(self, st):
        if st in SensorRequestHandler.VALID_SENSOR_TYPES:
            return st
        return self.error_string('sensor type')

    def validate_time(self, time_str, iden):
        time_int = int(time_str)
        if time_int <= 0:
            return self.error_string('{0} time value'.format(iden))
        return time_int

    def validate_sensor_value(self, value):
        try:
            float_value = float(value)
            if float_value < 0.0 or float_value > 100.0:
                return self.error_string('sensor value')
            return float_value
        except:
            self.err = True

    def error_string(self, appendage):
        return 'Invalid {0}'.format(appendage)

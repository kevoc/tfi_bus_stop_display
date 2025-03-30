
"""
`mqtt_controller`
====================================================

MQTT controller allows you to specify an adhoc command-response
protocol over MQTT, where a published command triggers an
action or returns some information.

* Author: Kevin O'Connell

"""

from . import MQTTClient, MQTTException


import umqtt


with open("homeautomation.key.der", 'rb') as f:
    key = f.read()
with open("homeautomation.crt.der", 'rb') as f:
    cert = f.read()
ssl_params = dict()
ssl_params["cert"] = cert
ssl_params["key"] = key
client = MQTTClient(client_id, mqtt_server, port=8883, user='power', password='1p0w3R6', keepalive=30, ssl=True, ssl_params=ssl_params)
client.connect()
print('Connected to %s MQTT broker' % (mqtt_server))

class MQTTController:
    """A controller to run various commands. """

    def __init__(self, ):
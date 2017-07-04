#!/usr/bin/env python3

# Temperature and Humidity meter with MQTT support
# By Michael Ludvig, Enterprise IT Ltd, New Zealand

import time
import serial
import re
import os
import json

from threading import Timer
from datetime import datetime
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

client_id = "te-m-pi"
endpoint = "a2yydx75cijpoy.iot.ap-southeast-2.amazonaws.com"
root_ca = "certs/root-ca.pem"
cert = "certs/certificate.pem.crt"
key = "certs/private.pem.key"

w1 = None
nx = None
iot = None

class w1therm(object):
    W1_DIR="/sys/devices/w1_bus_master1"

    def __init__(self, w1_dir = None):
        if w1_dir:
            self.W1_DIR = w1_dir
        self.thermometers = self.list_thermometers()
        self.readings = self.update_readings()

    def list_thermometers(self):
        with open(os.path.join(self.W1_DIR, "w1_master_slaves"), "r") as f:
            slaves = [ x.strip() for x in f.readlines() if x.startswith("28-") ]
        return slaves

    def update_readings(self):
        readings = {}
        for th in self.thermometers:
            with open(os.path.join(self.W1_DIR, th, "w1_slave"), "r") as f:
                lines = [ x.strip() for x in f.readlines() ]
            if not lines[0].endswith("YES"):
                temp = None
            else:
                m = re.search("t=(\d+)", lines[1])
                temp = round(float(m.group(1))/1000, 1)
            readings[th] = temp
        self.readings = readings
        return readings

class nextion(object):
    def __init__(self, port, baudrate = 9600):
        self.s = serial.Serial(
            port = port,
            baudrate = baudrate,
            xonxoff = False, rtscts = False, dsrdtr = False,
            timeout = 0.1, writeTimeout = 1, interCharTimeout = None)
        self.send("bkcmd=3")

    def send(self, cmd):
        #print("nx> %s" % cmd)
        if type(cmd) != bytearray:
            cmd = bytearray(cmd, "ascii")
        self.s.write(cmd)
        self.s.write(b"\xff\xff\xff")
        return self.recv()

    def recv(self):
        xff = 0
        buf = []
        while True:
            r = self.s.read()
            if r == '':
                break
            buf.append(r)
            if r == b'\xff':
                xff += 1
            if xff == 3:
                break
        return buf

class awsiot(object):
    def __init__(self, endpoint, client_id, root_ca, cert, key):
        # Init AWSIoTMQTTClient
        self.mqtt = AWSIoTMQTTClient(client_id)
        self.mqtt.configureEndpoint(endpoint, 8883)
        self.mqtt.configureCredentials(root_ca, key, cert)

        # AWSIoTMQTTClient connection configuration
        self.mqtt.configureAutoReconnectBackoffTime(1, 32, 20)
        self.mqtt.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        self.mqtt.configureDrainingFrequency(2)  # Draining: 2 Hz
        self.mqtt.configureConnectDisconnectTimeout(10)  # 10 sec
        self.mqtt.configureMQTTOperationTimeout(5)  # 5 sec

        # Connect to AWS IoT
        self.mqtt.connect()

    def publish(self, topic, message):
	    self.mqtt.publish(topic, message, 1)

def get_rpi_serial_number():
    serial = "UNKNOWN_00000000"
    with open("/proc/cpuinfo", "r") as cpuinfo:
        for line in cpuinfo.readlines():
            m=re.match("Serial\s*:\s*(\w+)", line)
            if m:
                serial = m.group(1)
                break
    return serial

def update_readings():
    Timer(10, update_readings).start()
    w1.update_readings()
    for probe in w1.thermometers:
        topic = "te-m-pi/%s/%s" % (client_id, probe)
        payload = {
            "ClientId": client_id,
            "ProbeId": probe,
            "ProbeType": "Temperature",
            "Temperature": ("%0.1f" % w1.readings[probe])
        }
        message = json.dumps(payload)
        iot.publish(topic, message)

if __name__ == "__main__":
    client_id = get_rpi_serial_number()

    w1 = w1therm()
    nx = nextion(port="/dev/ttyAMA0")
    iot = awsiot(endpoint, client_id, root_ca, cert, key)

    update_readings()

    nx.send("t0.font=7")
    nx.send("t1.font=3")
    nx.send("t2.font=2")

    while True:
        val="%0.1f C" % (w1.readings[w1.thermometers[0]])
        nx.send("t0.txt=\"%s\"" % val)

        val="Probe:"
        nx.send("t1.txt=\"%s\"" % val)

        val=w1.thermometers[0]
        nx.send("t2.txt=\"%s\"" % val)

        val = datetime.strftime(datetime.now(), "%Y/%m/%d %H:%M")
        nx.send("t3.txt=\"%s\"" % val)
        time.sleep(10)

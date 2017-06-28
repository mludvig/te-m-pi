#!/usr/bin/env python3

import time
import serial
import re
import os

from threading import Timer
from datetime import datetime

w1 = None
nx = None

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
        print("update_readings @ %s" % time.time())
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
        print("readings: %r" % self.readings)
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

def update_readings():
    Timer(10, update_readings).start()
    w1.update_readings()

if __name__ == "__main__":
    w1 = w1therm()
    nx = nextion(port="/dev/ttyAMA0")

    update_readings()

    nx.send("t0.font=7")
    while True:
        val="%0.1f C" % (w1.readings[w1.thermometers[0]])
        nx.send("t0.txt=\"%s\"" % val)

        val = datetime.strftime(datetime.now(), "%Y/%m/%d %H:%M")
        nx.send("t3.txt=\"%s\"" % val)
        time.sleep(10)

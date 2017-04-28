#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import requests
from yaml import safe_load
import logging
import logging.handlers
import argparse
import sys

# Deafults
LOG_FILENAME = "/tmp/alarm.log"
LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping  backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=30)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
    def __init__(self, logger, level):
        """Needs a logger and a logger level."""
        self.logger = logger
        self.level = level

    def write(self, message):
        # Only log if there is a message (not just a new line)
        if message.rstrip() != "":
            self.logger.log(self.level, message.rstrip())
    
    def flush(self):
        pass

# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)

with open("/home/pi/alarm/config.yml", "r") as f:
    config = safe_load(f)

pin_list = [s["pin"] for s in config["Sensors"]]
pin_id_lookup = {s["pin"]:s["id"] for s in config["Sensors"]}
pin_name_lookup = {s["pin"]:s["Name"] for s in config["Sensors"]}

GPIO.setmode(GPIO.BCM)
GPIO.setup(list(pin_id_lookup.keys()), GPIO.IN, pull_up_down = GPIO.PUD_UP)

def log_change(pin):
    val = GPIO.input(pin)
    logger.info("{} read {}".format(pin_name_lookup[pin], val))
    data = {
        "sensor_id": pin_id_lookup[pin],
        "state": val
    }

    response = requests.post(json=data, **config["API"])
    logger.info(response.json())

for pin in pin_id_lookup.keys():
    GPIO.add_event_detect(pin, GPIO.BOTH, log_change)

while True:
    time.sleep(1e6)

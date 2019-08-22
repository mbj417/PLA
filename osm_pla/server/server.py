#!/usr/bin/python3
# -*- coding: utf-8 -*-

##
# Copyright 2019 ArctosLabs Scandinavia AB
# *************************************************************

# This file is part of OSM Placement module
# All Rights Reserved to ArctosLabs Scandinavia AB

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# For those usages not covered by the Apache License, Version 2.0 please
# contact: patrik.rynback@arctoslabs.com or martin.bjorklund@arctoslabs.com
##

import asyncio
import logging

from osm_common import msglocal, msgkafka

#import yaml
#import logging.handlers
#import getopt
#import sys
#from time import time, sleep
#from osm_common import dbmemory, dbmongo, fslocal, msglocal, msgkafka
#from osm_common import version as common_version
#from osm_common.msgbase import MsgException

from osm_pla.config.config import Config

__author__ = "Martin Bjorklund, Patrik Rynback"
log = logging.getLogger(__name__)
pla_version = '0.0.1'
pla_version_date = '2019-08-22'

class Server:

    # PING
    ping_interval_pace = 120  # how many time ping is send once is confirmed all is running
    ping_interval_boot = 5    # how many time ping is sent when booting


    def __init__(self, config: Config, loop=None):
        self.msgBus = None
        self.config = config
        self.loop = loop or asyncio.get_event_loop()

        # PING
        self.pings_not_received = 1
        self.worker_id = "123456"
#        self.worker_id = self.get_process_id()

        try:
            if config.get('message', 'driver') == "local":
                self.msgBus = msglocal.MsgLocal()
            elif config.get('message', 'driver') == "kafka":
                self.msgBus = msgkafka.MsgKafka()
            else:
                raise Exception("Invalid message bus driver {}".format(
                    config.get('message', 'driver')))
            self.msgBus.connect(config.get('message'))
        except Exception as e:
            log.error("kafka setup error. Exception: {}".format(e))

    def handle_kafka_command(self, topic, command, params):
        log.info("Kafka message arrived: {} {} {}".format(topic, command, params))
        # PING
        if topic == "pla":
            if command == "ping" and params["to"] == "pla" and params["from"] == "pla":
                if params.get("worker_id") == self.worker_id:
                    self.pings_not_received = 0

    async def kafka_read(self):
        log.info("Task kafka_read start")
        while True:
            try:
                topics = ("pla", "ns")
                await self.msgBus.aioread(topics, self.loop, self.handle_kafka_command)
            except Exception as e:
                log.error("kafka read error. Exception: {}".format(e))
                await asyncio.sleep(5, loop=self.loop)

        log.info("Task kafka_read exit")

    # PING
    async def kafka_ping(self):
        log.info("Task kafka_ping Enter")
        consecutive_errors = 0
        first_start = True
        kafka_has_received = False
        self.pings_not_received = 1
        while True:
            try:
                await self.msgBus.aiowrite(
                    "pla", "ping",
                    {"from": "pla", "to": "pla", "worker_id": self.worker_id, "version": pla_version},
                    self.loop)
                # time between pings are low when it is not received and at starting
                wait_time = self.ping_interval_boot if not kafka_has_received else self.ping_interval_pace
                if not self.pings_not_received:
                    kafka_has_received = True
                self.pings_not_received += 1
                await asyncio.sleep(wait_time, loop=self.loop)
                if self.pings_not_received > 10:
                    raise Exception("It is not receiving pings from Kafka bus")
                consecutive_errors = 0
                first_start = False
#            except Exception:
#                raise
            except Exception as e:
                # if not first_start is the first time after starting. So leave more time and wait
                # to allow kafka starts
                if consecutive_errors == 8 if not first_start else 30:
                    self.logger.error("Task kafka_read task exit error too many errors. Exception: {}".format(e))
                    raise
                consecutive_errors += 1
                self.logger.error("Task kafka_read retrying after Exception {}".format(e))
                wait_time = 2 if not first_start else 5
                await asyncio.sleep(wait_time, loop=self.loop)
                
    def run(self):
#       self.loop.run_until_complete(self.kafka_read())

        #PING
        self.loop.run_until_complete(asyncio.gather(self.kafka_read(), self.kafka_ping()))
         
        self.loop.close()
        self.loop = None
        if self.msgBus:
            self.msgBus.disconnect()

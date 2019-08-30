#!/usr/bin/python3
# -*- coding: utf-8 -*-

##
# Copyright 2019 ArctosLabs Scandinavia AB
#
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
##

import asyncio
import yaml
import json
import logging
import logging.handlers
import getopt
import sys
from time import time, sleep

from osm_common import dbmemory, dbmongo, fslocal, msglocal, msgkafka
from osm_common import version as common_version
from osm_common.msgbase import MsgException

from osm_pla.config.config import Config

__author__ = "Martin Bjorklund"

class Server:

    def __init__(self, config: Config, loop=None):
        self.log = logging.getLogger("pla.server")
        self.db = None
        self.msgBus = None
        self.config = config
        self.loop = loop or asyncio.get_event_loop()

        try:
            if config.get('database', 'driver') == "mongo":
                self.db = dbmongo.DbMongo()
                self.db.db_connect(config.get('database'))
            elif config.get('database', 'driver') == "memory":
                self.db = dbmemory.DbMemory()
                self.db.db_connect(config.get('database'))
            else:
                raise Exception("Invalid configuration param '{}' at '[database]':'driver'".format(
                    config.get('database', 'driver')))
            
            if config.get('message', 'driver') == "local":
                self.msgBus = msglocal.MsgLocal()
            elif config.get('message', 'driver') == "kafka":
                self.msgBus = msgkafka.MsgKafka()
            else:
                raise Exception("Invalid message bus driver {}".format(
                    config.get('message', 'driver')))
            self.msgBus.loop = loop
            self.msgBus.connect(config.get('message'))
            
            self.log.info("VIM Accounts in DB:")
            self.vim_accounts = self.db.get_list("vim_accounts", {})
            self.log.info(json.dumps(self.vim_accounts))
        except Exception as e:
            self.log.exception("kafka setup error. Exception: {}".format(e))

    async def get_placement_suggestions(self, params):
        suggestions = []
        vnf1 = {"member-vnf-index": "1", "vimAccountId": "8460b670-31cf-4fae-9f3e-d0dd6c57b61e"}
        vnf2 = {"member-vnf-index": "2", "vimAccountId": "9b8b5268-acb7-4893-b494-a77656b418f2"}
        suggestions.append({'placement' : [vnf1, vnf2]})
        await self.msgBus.aiowrite("pla", "suggestions", { 'suggestions': suggestions })

    def handle_kafka_command(self, topic, command, params):
        self.log.info("Kafka msg arrived: {} {} {}".format(topic, command, params))
        if topic == "pla" and command == "get_suggestions":
            self.loop.create_task(self.get_placement_suggestions(params))

    async def kafka_read(self):
        self.log.info("Task kafka_read start")
        while True:
            try:
                topics = ("pla", "ns", "nsds")
                await self.msgBus.aioread(topics, self.loop, self.handle_kafka_command)
            except Exception as e:
                self.log.error("kafka read error. Exception: {}".format(e))
                await asyncio.sleep(5, loop=self.loop)

        self.log.info("Task kafka_read exit")

    def run(self):
        self.loop.run_until_complete(self.kafka_read())
        self.loop.close()
        self.loop = None
        if self.msgBus:
            self.msgBus.disconnect()

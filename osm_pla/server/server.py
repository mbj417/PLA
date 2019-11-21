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
#import yaml
import json
import logging
#import logging.handlers
#import getopt
#import sys
#from time import time, sleep

from osm_common import dbmemory, dbmongo, msglocal, msgkafka
from osm_pla.placement.mznplacement import MznPlacementConductor
from osm_pla.placement.mznplacement import NsPlacementDataFactory

#from osm_common import version as common_version
#from osm_common.msgbase import MsgException

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
            
#            self.log.info("VIM Accounts in DB:")
#            self.vim_accounts = self.db.get_list("vim_accounts", {})
#            self.log.info(json.dumps(self.vim_accounts))
        except Exception as e:
            self.log.exception("kafka setup error. Exception: {}".format(e))

    def _get_project_filter(self, session):
        p_filter = {}

        if session is not None:
            project_filter_n = []
            project_filter = list(session["project_id"])

            if session["public"] is not None:
                if session["public"]:
                    project_filter.append("ANY")
                else:
                    project_filter_n.append("ANY")

            if session.get("PROJECT.ne"):
                project_filter_n.append(session["PROJECT.ne"])

            if project_filter:
                p_filter["_admin.projects_read.cont"] = project_filter
            if project_filter_n:
                p_filter["_admin.projects_read.ncont"] = project_filter_n

        return p_filter

    def _get_nslcmop(self, nsdlcmopId, session):
        filter = self._get_project_filter(session)
        filter["_id"] = nsdlcmopId
        nslcmop = self.db.get_one("nslcmops", filter)
        return nslcmop

    def _get_nsd(self, nsdId, session):
        filter = self._get_project_filter(session)
        filter["_id"] = nsdId
        nsd = self.db.get_one("nsds", filter)
        return nsd

    def _get_vnfd(self, vnfdId, session):
        filter = self._get_project_filter(session)
        filter["id"] = vnfdId
        vnfds = self.db.get_list("vnfds", filter)
        return vnfds[0]

    async def get_placement(self, session, nslcmopId):
        nslcmop = self._get_nslcmop(nslcmopId, session)
        nsd = self._get_nsd(nslcmop['operationParams']['nsdId'], session)
        vims = nslcmop['operationParams']['validVimAccounts']
        vnfds = {}
        for vnfdRef in nsd['constituent-vnfd']:
            vnfdId = vnfdRef['vnfd-id-ref']
            vnfd = self._get_vnfd(vnfdId, session)
            vnfds[vnfdId] = vnfd

        #pops = self.config.get('pop')
        #for vim in vims:
        #    for pop in pops:
        #        if vim['vim_url'] == pop['vim_url']:
        #            pop.update(vim)
        #            self.db.create("pops", pop)

        self.log.info("vims = {}".format(json.dumps(vims)))
        self.log.info("nsd = {}".format(json.dumps(nsd)))

        vim_index = 1
        vim_table = {}
        for vim in vims:
            vim_table[str(vim_index)] = vim
            vim_index += 1
            
        nspd = NsPlacementDataFactory(nsd, vnfds).create_ns_placement_data()
        self.log.info("nspd = {}".format(json.dumps(nspd._mzn_model_data)))
        placement = MznPlacementConductor(vim_table, self.log).do_placement_computation(nspd)
        self.log.info("MZN Placement = {}".format(json.dumps(placement._placement)))
        vnfs = []
        for vnfIndex, vimAccountId in placement._placement.items():
            vnf = { 'member-vnf-index' :  vnfIndex, 'vimAccountId' : vimAccountId }
            vnfs.append(vnf)
            
        # create vld info
        vlds = []
        for nsVld in nsd.get('vld', []):
            vld = { 'name' : nsVld.get('name', "noname") }
            vimNetworkNames = {}
            for cp in nsVld.get('vnfd-connection-point-ref', []):
                vnfIndex = cp.get('member-vnf-index-ref')
                for vnf in vnfs:
                    if vnf['member-vnf-index'] == vnfIndex:
                        vimAccountId = vnf['vimAccountId']
                        vimNetworkNames[vimAccountId] = 'private'
                        break;
            vld['vim-network-name'] = vimNetworkNames
            vlds.append(vld)

        result = {'vnf' : vnfs, 'vld': vlds,'wimAccountId': False, 'nslcmopId' : nslcmopId }
        await self.msgBus.aiowrite("pla", "placement", result)

    def handle_kafka_command(self, topic, command, params):
        self.log.info("Kafka msg arrived: {} {} {}".format(topic, command, params))
        if topic == "pla" and command == "get_placement":
            session = params.get('session', None)
            nslcmopId = params.get('nslcmopId')
            self.loop.create_task(self.get_placement(session, nslcmopId))

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

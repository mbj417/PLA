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
# import yaml
import json
import logging
# import logging.handlers
# import getopt
# import sys
# from time import time, sleep
from pathlib import Path

import pkg_resources
import yaml
from osm_common import dbmemory, dbmongo, msglocal, msgkafka
from osm_pla.placement.mznplacement import MznPlacementConductor
from osm_pla.placement.mznplacement import NsPlacementDataFactory

# from osm_common import version as common_version
# from osm_common.msgbase import MsgException

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
                    # FIXME when is this reachable
                    project_filter_n.append("ANY")

            if session.get("PROJECT.ne"):
                project_filter_n.append(session["PROJECT.ne"])

            if project_filter:
                p_filter["_admin.projects_read.cont"] = project_filter
            if project_filter_n:
                p_filter["_admin.projects_read.ncont"] = project_filter_n

        return p_filter

    def _get_nsd(self, nsdId, session):
        filter = self._get_project_filter(session)
        filter["_id"] = nsdId
        nsd = self.db.get_one("nsds", filter)
        return nsd

    def _get_enabled_vims(self, session):
        filter = self._get_project_filter(session)
        filter["_admin.operationalState"] = "ENABLED"
        vims = self.db.get_list("vim_accounts", filter)
        return vims

    def _get_vnf_price_list(self):
        """
        read vnf price list configuration file and reformat its content
        FIXME file location outside package to prefer.
        FIXME should we make this static?
        :return: dictionary formatted as {'<vnfd>': {'<vim-url>':'<price>'}}
        """
        price_list_file = pkg_resources.resource_filename(__name__, 'vnf_price_list.yaml')
        with open(price_list_file) as pl_fd:
            price_list_data = yaml.safe_load_all(pl_fd)
            return {i['vnfd']: {i1['vim_url']: i1['price'] for i1 in i['prices']} for i in next(price_list_data)}

    def _get_pop_pil_info(self):
        """
        Read and return pop_pil information from file
        :return: pop_pil configuration file content as Python object
        """
        path = pkg_resources.resource_filename(__name__, 'pop_pil.yaml')
        with open(path) as pp_fd:
            data = yaml.safe_load_all((pp_fd))
            return next(data)

    async def get_placement(self, session, params, request_id, pinning):
        """
        - Collects and prepares placement information.
        - Request placement computation.
        - Formats and distribute placement result

        Note: exceptions result in empty response message

        :param request_id:
        :param session:
        :param params:
        :param pinning:
        :return:
        """
        try:
            nsd = self._get_nsd(params.get('nsdId'), session)
            vims_information = {_['vim_url']: _['_id'] for _ in self._get_enabled_vims(session)}
            price_list = self._get_vnf_price_list()
            pop_pil_info = self._get_pop_pil_info()

            nspd = NsPlacementDataFactory(vims_information,
                                          price_list,
                                          nsd,
                                          pop_pil_info,
                                          pinning).create_ns_placement_data()

            vnf_placement = MznPlacementConductor(self.log).do_placement_computation(nspd)

            # convenience mapping of index to vim account that simplifies construction of vld section of the response
            vnf_index_to_vim_account = {_['member-vnf-index']: _['vimAccountId'] for _ in vnf_placement}

            # FIXME is 'noname' and empty list acceptable or should we simply take the exception?
            vlds = []
            for ns_vld in nsd.get('vld', []):
                vld = {'name': ns_vld.get('name', "noname")}
                vim_network_name = ns_vld.get('vim-network-namee')
                # FIXME vim-network-name may not be available. Use default or report fail?
                if vim_network_name is None:
                    pass
                vld['vim-network-name'] = {vnf_index_to_vim_account[cp_ref_info.get('member-vnf-index-ref')]
                                           : vim_network_name for cp_ref_info in ns_vld.get('vnfd-connection-point-ref')}
                vlds.append(vld)
        except Exception as e:
            # Note: there is no cure for failure so we have a catch-all clause here
            self.log.exception("PLA fault. Exception: {}".format(e))
            vnf_placement = []
            vlds = []
        finally:
            await self.msgBus.aiowrite("pla", "placement", {'vnf': vnf_placement, 'vld': vlds, 'wimAccountId': False,
                                                            'request_id': request_id})

    def handle_kafka_command(self, topic, command, params):
        self.log.info("Kafka msg arrived: {} {} {}".format(topic, command, params))
        if topic == "pla" and command == "get_placement":
            session = params.get('session', None)  # FIXME why setting the default to the default fallback?
            nsParams = params.get('nsParams')
            request_id = params.get('request_id')
            pinning = params.get('pinning')
            self.loop.create_task(self.get_placement(session, nsParams, request_id, pinning))

    async def kafka_read(self):
        self.log.info("Task kafka_read start")
        while True:
            try:
                topics = ("pla", "ns", "nsds")
                await self.msgBus.aioread(topics, self.loop, self.handle_kafka_command)
            except Exception as e:
                self.log.error("kafka read error. Exception: {}".format(e))
                await asyncio.sleep(5, loop=self.loop)

        self.log.info("Task kafka_read exit") # FIXME unreachable?

    def run(self):
        self.loop.run_until_complete(self.kafka_read())
        self.loop.close()
        self.loop = None
        if self.msgBus:
            self.msgBus.disconnect()

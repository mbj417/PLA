# Copyright 2019 ArctosLabs Scandinavia AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import asyncio
import random
import sys
from unittest import TestCase, mock
from unittest.mock import Mock

from osm_pla.placement.mznplacement import NsPlacementDataFactory, MznPlacementConductor

sys.modules['osm_common'] = Mock()
from osm_pla.server.server import Server
from osm_pla.config.config import Config

pla_get_suggestions_w_session = {'nsParams': {'nsdId': '15fc1941-f095-4cd8-af2d-1000bd6d9eaa',
                                              'additionalParamsForNs': {'placementEngine': 'PLA'},
                                              'vimAccountId': '8460b670-31cf-4fae-9f3e-d0dd6c57b61e',
                                              'nsName': 'Test_constrained4', 'ssh_keys': [],
                                              'nsDescription': 'LowLatency'},
                                 'session': {'project_id': ['0a5d0c5b-7e08-48a1-a686-642a038bbd70'],
                                             'username': 'admin', 'method': 'write', 'admin': True,
                                             'public': None, 'force': False}}

pla_get_suggestions_wo_session = {'nsParams': {'nsName': 'Test_constrained5', 'ssh_keys': [],
                                               'nsdId': '15fc1941-f095-4cd8-af2d-1000bd6d9eaa',
                                               'nsDescription': 'LowLatency',
                                               'vimAccountId': '8460b670-31cf-4fae-9f3e-d0dd6c57b61e'}}

pla_get_placement_w_pinning = {'nsParams': {'nsName': 'Test_constrained5', 'ssh_keys': [],
                                            'nsdId': '15fc1941-f095-4cd8-af2d-1000bd6d9eaa',
                                            'nsDescription': 'LowLatency',
                                            'vimAccountId': '8460b670-31cf-4fae-9f3e-d0dd6c57b61e'},
                               'pinning': [{'member-vnf-index': '1',
                                           'vim_account': '73cd1a1b-333e-4e29-8db2-00d23bd9b644'}]}

list_of_vims = [{"_id": "73cd1a1b-333e-4e29-8db2-00d23bd9b644", "vim_user": "admin", "name": "OpenStack1",
                 "vim_url": "http://10.234.12.47:5000/v3", "vim_type": "openstack", "vim_tenant_name": "osm_demo",
                 "vim_password": "O/mHomfXPmCrTvUbYXVoyg==", "schema_version": "1.1",
                 "_admin": {"modified": 1565597984.3155663, "deployed":
                     {"RO": "f0c1b516-bcd9-11e9-bb73-02420aff0030",
                      "RO-account": "f0d45496-bcd9-11e9-bb73-02420aff0030"},
                            "projects_write": ["admin"], "operationalState": "ENABLED", "detailed-status": "Done",
                            "created": 1565597984.3155663, "projects_read": ["admin"]},
                 "config": {}},
                {"_id": "684165ea-2cf9-4fbd-ac22-8464ca07d1d8", "vim_user": "admin",
                 "name": "OpenStack2", "vim_url": "http://10.234.12.44:5000/v3",
                 "vim_tenant_name": "osm_demo", "vim_password": "Rw7gln9liP4ClMyHd5OFsw==",
                 "description": "Openstack on NUC", "vim_type": "openstack",
                 "admin": {"modified": 1566474766.7288046,
                           "deployed": {"RO": "5bc59656-c4d3-11e9-b1e5-02420aff0006",
                                        "RO-account": "5bd772e0-c4d3-11e9-b1e5-02420aff0006"},
                           "projects_write": ["admin"], "operationalState": "ENABLED",
                           "detailed-status": "Done", "created": 1566474766.7288046,
                           "projects_read": ["admin"]},
                 "config": {}, "schema_version": "1.1"},
                {"_id": "8460b670-31cf-4fae-9f3e-d0dd6c57b61e", "vim_user": "admin", "name": "OpenStack1",
                 "vim_url": "http://10.234.12.47:5000/v3", "vim_type": "openstack",
                 "vim_tenant_name": "osm_demo", "vim_password": "NsgJJDlCdKreX30FQFNz7A==",
                 "description": "Openstack on Dell",
                 "_admin": {"modified": 1566992449.5942867,
                            "deployed": {"RO": "aed94f86-c988-11e9-bb38-02420aff0088",
                                         "RO-account": "aee72fac-c988-11e9-bb38-02420aff0088"},
                            "projects_write": ["0a5d0c5b-7e08-48a1-a686-642a038bbd70"],
                            "operationalState": "ENABLED", "detailed-status": "Done", "created": 1566992449.5942867,
                            "projects_read": ["0a5d0c5b-7e08-48a1-a686-642a038bbd70"]}, "config": {},
                 "schema_version": "1.1"},
                {"_id": "9b8b5268-acb7-4893-b494-a77656b418f2",
                 "vim_user": "admin", "name": "OpenStack2",
                 "vim_url": "http://10.234.12.44:5000/v3",
                 "vim_type": "openstack", "vim_tenant_name": "osm_demo",
                 "vim_password": "AnAV3xtoiwwdnAfv0KahSw==",
                 "description": "Openstack on NUC",
                 "_admin": {"modified": 1566992484.9190753,
                            "deployed": {"RO": "c3d61158-c988-11e9-bb38-02420aff0088",
                                         "RO-account": "c3ec973e-c988-11e9-bb38-02420aff0088"},
                            "projects_write": ["0a5d0c5b-7e08-48a1-a686-642a038bbd70"],
                            "operationalState": "ENABLED", "detailed-status": "Done",
                            "created": 1566992484.9190753,
                            "projects_read": ["0a5d0c5b-7e08-48a1-a686-642a038bbd70"]},
                 "config": {}, "schema_version": "1.1"},
                {"_id": "3645f215-f32d-4355-b5ab-df0a2e2233c3", "vim_user": "admin", "name": "OpenStack3",
                 "vim_url": "http://10.234.12.46:5000/v3", "vim_tenant_name": "osm_demo",
                 "vim_password": "XkG2w8e8/DiuohCFNp0+lQ==", "description": "Openstack on NUC",
                 "vim_type": "openstack",
                 "_admin": {"modified": 1567421247.7016313,
                            "deployed": {"RO": "0e80f6a2-cd6f-11e9-bb50-02420aff00b6",
                                         "RO-account": "0e974524-cd6f-11e9-bb50-02420aff00b6"},
                            "projects_write": ["0a5d0c5b-7e08-48a1-a686-642a038bbd70"],
                            "operationalState": "ENABLED", "detailed-status": "Done",
                            "created": 1567421247.7016313,
                            "projects_read": ["0a5d0c5b-7e08-48a1-a686-642a038bbd70"]},
                 "schema_version": "1.1", "config": {}},
                {"_id": "53f8f2bb-88b5-4bf9-babf-556698b5261f",
                 "vim_user": "admin", "name": "OpenStack4",
                 "vim_url": "http://10.234.12.43:5000/v3",
                 "vim_tenant_name": "osm_demo",
                 "vim_password": "GLrgVn8fMVneXMZq1r4yVA==",
                 "description": "Openstack on NUC",
                 "vim_type": "openstack",
                 "_admin": {"modified": 1567421296.1576457,
                            "deployed": {
                                "RO": "2b43c756-cd6f-11e9-bb50-02420aff00b6",
                                "RO-account": "2b535aea-cd6f-11e9-bb50-02420aff00b6"},
                            "projects_write": [
                                "0a5d0c5b-7e08-48a1-a686-642a038bbd70"],
                            "operationalState": "ENABLED",
                            "detailed-status": "Done",
                            "created": 1567421296.1576457,
                            "projects_read": [
                                "0a5d0c5b-7e08-48a1-a686-642a038bbd70"]},
                 "schema_version": "1.1", "config": {}}]

nsd_from_db = {"_id": "15fc1941-f095-4cd8-af2d-1000bd6d9eaa", "short-name": "three_vnf_constrained_nsd_low",
               "name": "three_vnf_constrained_nsd_low", "version": "1.0", "description": "Placement constraints NSD",
               "_admin": {"modified": 1567672251.7531693,
                          "storage": {"pkg-dir": "ns_constrained_nsd", "fs": "local",
                                      "descriptor": "ns_constrained_nsd/ns_constrained_nsd.yaml",
                                      "zipfile": "package.tar.gz",
                                      "folder": "15fc1941-f095-4cd8-af2d-1000bd6d9eaa", "path": "/app/storage/"},
                          "onboardingState": "ONBOARDED", "usageState": "NOT_IN_USE",
                          "projects_write": ["0a5d0c5b-7e08-48a1-a686-642a038bbd70"], "operationalState": "ENABLED",
                          "userDefinedData": {}, "created": 1567672251.7531693,
                          "projects_read": ["0a5d0c5b-7e08-48a1-a686-642a038bbd70"]},
               "constituent-vnfd": [{"vnfd-id-ref": "cirros_vnfd_v2", "member-vnf-index": "1"},
                                    {"vnfd-id-ref": "cirros_vnfd_v2", "member-vnf-index": "2"},
                                    {"vnfd-id-ref": "cirros_vnfd_v2", "member-vnf-index": "3"}],
               "id": "three_vnf_constrained_nsd_low", "vendor": "ArctosLabs",
               "vld": [{"type": "ELAN", "short-name": "ns_constrained_nsd_low_vld1",
                        "link-constraint": [{"constraint-type": "LATENCY", "value": "100"},
                                            {"constraint-type": "JITTER", "value": "30"}],
                        "vim-network-name": "external", "mgmt-network": True,
                        "id": "three_vnf_constrained_nsd_low_vld1",
                        "vnfd-connection-point-ref": [{"vnfd-id-ref": "cirros_vnfd_v2", "member-vnf-index-ref": "1",
                                                       "vnfd-connection-point-ref": "vnf-cp0"},
                                                      {"vnfd-id-ref": "cirros_vnfd_v2",
                                                       "member-vnf-index-ref": "2",
                                                       "vnfd-connection-point-ref": "vnf-cp0"}],
                        "name": "ns_constrained_nsd_vld1"},
                       {"type": "ELAN", "short-name": "ns_constrained_nsd_low_vld2",
                        "link-constraint": [{"constraint-type": "LATENCY", "value": "50"},
                                            {"constraint-type": "JITTER", "value": "30"}],
                        "vim-network-name": "lanretxe", "mgmt-network": True,
                        "id": "three_vnf_constrained_nsd_low_vld2",
                        "vnfd-connection-point-ref": [{"vnfd-id-ref": "cirros_vnfd_v2", "member-vnf-index-ref": "2",
                                                       "vnfd-connection-point-ref": "vnf-cp0"},
                                                      {"vnfd-id-ref": "cirros_vnfd_v2", "member-vnf-index-ref": "3",
                                                       "vnfd-connection-point-ref": "vnf-cp0"}],
                        "name": "ns_constrained_nsd_vld2"}]}


######################################################
# These are helper functions to handle unittest of asyncio.
# Inspired by: https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code
def _run(co_routine):
    return asyncio.get_event_loop().run_until_complete(co_routine)


def _async_mock(*args, **kwargs):
    m = mock.MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


######################################################

class TestServer(TestCase):
    @mock.patch.object(Config, '_read_config_file')
    @mock.patch.object(Config, 'get', side_effect=['doesnotmatter', 'memory', 'memory', 'local', 'doesnotmatter'])
    def serverSetup(self, mock_get, mock__read_config_file):
        """
        Helper that returns a Server object
        :return:
        """
        cfg = Config(None)
        return Server(cfg)

    def test__get_project_filter(self):  # OK
        server = self.serverSetup()

        session = pla_get_suggestions_w_session['session']
        project_id = session['project_id'][0]
        p_filter = server._get_project_filter(session)
        self.assertEqual({'_admin.projects_read.cont'}, set(p_filter.keys()), 'missing expected key')
        self.assertEqual(project_id, p_filter['_admin.projects_read.cont'][0], 'invalid project id')

        p_filter = server._get_project_filter(None)
        self.assertEqual({}, p_filter, 'filter should be empty dict')

    def test__get_nsd(self):  # OK
        """
        ToDo
        - add another test with session information in the _get_nsd() call
        :return:
        """
        server = self.serverSetup()
        server.db = Mock()
        _ = server._get_nsd(pla_get_suggestions_w_session['nsParams']['nsdId'], None)
        server.db.get_one.assert_called_with("nsds", {'_id': pla_get_suggestions_w_session['nsParams']['nsdId']})

    def test__get_enabled_vims(self):  # OK
        server = self.serverSetup()
        server.db = Mock()
        _ = server._get_enabled_vims(None)
        server.db.get_list.assert_called_with('vim_accounts', {'_admin.operationalState': 'ENABLED'})

    def test_get_vnf_price_list(self):  # OK
        server = self.serverSetup()
        pl = server._get_vnf_price_list()
        # assert we get a dict, assert that the values on top level themselves are dicts
        self.assertIs(type(pl), dict, "price list not a dictionary")
        for k, v in pl.items():
            self.assertIs(type(v), dict, "price list values not a dict")

    def test__get_pop_pil_info(self):  # OK
        server = self.serverSetup()
        ppi = server._get_pop_pil_info()
        self.assertIs(type(ppi), dict, "pop_pil is not a dict")
        self.assertIn('pil', ppi.keys(), "pop_pil has no pil key")
        self.assertIs(type(ppi['pil']), list, "pil does not contain a list")
        # check for expected keys
        expected_keys = {'pil_description', 'pil_price', 'pil_latency', 'pil_endpoints'}
        self.assertEqual(expected_keys, ppi['pil'][0].keys(), 'expected keys not found')

    def test_handle_kafka_command(self):  # OK
        server = self.serverSetup()
        server.loop.create_task = Mock()
        server.handle_kafka_command('pli', 'get_placement', {})
        server.loop.create_task.assert_not_called()
        server.loop.create_task.reset_mock()
        server.handle_kafka_command('pla', 'get_placement', {})
        self.assertTrue(server.loop.create_task.called, 'create_task not called')
        args, kwargs = server.loop.create_task.call_args
        self.assertIn('Server.get_placement', str(args[0]), 'get_placement not called')

    # Note: does not mock reading of price list and pop_pil_info
    @mock.patch.object(NsPlacementDataFactory, '__init__', lambda x0, x1, x2, x3, x4,x5: None)
    @mock.patch.object(MznPlacementConductor, 'do_placement_computation')
    @mock.patch.object(NsPlacementDataFactory, 'create_ns_placement_data')
    @mock.patch.object(Server, '_get_nsd')
    @mock.patch.object(Server, '_get_enabled_vims')
    def test_get_placement(self, mock_get_enabled_vims,
                           mock_get_nsd,
                           mock_create_ns_placement_data,
                           mock_do_placement_computation):
        """
        test that NsPlacementDataFactory is called with proper args not supported...
        :param mock_get_enabled_vims:
        :param mock_get_nsd:
        :param mock_create_ns_placement_data:
        :param mock_do_placement_computation:
        :return:
        """
        server = self.serverSetup()

        server.msgBus.aiowrite = _async_mock()
        mock_get_nsd.return_value = nsd_from_db
        mock_get_enabled_vims.return_value = list_of_vims
        mock_do_placement_computation.return_value = \
            [{'vimAccountId': 'bbbbbbbb-38f5-438d-b8ee-3f93b3531f87', 'member-vnf-index': '1'},
             {'vimAccountId': 'aaaaaaaa-38f5-438d-b8ee-3f93b3531f87', 'member-vnf-index': '2'},
             {'vimAccountId': 'aaaaaaaa-38f5-438d-b8ee-3f93b3531f87', 'member-vnf-index': '3'}]
        session = pla_get_suggestions_w_session.get('session')
        nsParams = pla_get_suggestions_w_session.get('nsParams')
        request_id = random.randint(1000, 2000)

        _run(server.get_placement(session, nsParams, request_id, None))

        # mock_get_nsd.assert_called_once() assert_called_once() for python > 3.5
        self.assertTrue(mock_get_nsd.called, 'get_nsd not called as expected')
        # mock_get_enabled_vims.assert_called_once() assert_called_once() for python > 3.5
        self.assertTrue(mock_get_enabled_vims.called, 'get_enabled_vims not called as expected')
        # mock_create_ns_placement_data.assert_called_once() assert_called_once() for python > 3.5
        self.assertTrue(mock_create_ns_placement_data.called, 'create_ns_placement_data not called as expected')
        # mock_do_placement_computation.assert_called_once()  assert_called_once() for python > 3.5
        self.assertTrue(mock_do_placement_computation.called, 'do_placement_computation not called as expected')
        self.assertTrue(server.msgBus.aiowrite.mock.called)

        args, kwargs = server.msgBus.aiowrite.mock.call_args
        self.assertTrue(len(args) == 3, 'invalid format')
        self.assertEqual('pla', args[0], 'topic invalid')
        self.assertEqual('placement', args[1], 'message invalid')

        # extract placement result and check content
        placement = args[2]
        expected_keys = {'vnf', 'vld', 'wimAccountId', 'request_id'}
        self.assertEqual(expected_keys, set(placement.keys()), "placement response missing keys")
        self.assertIs(type(placement['vnf']), list, 'vnf not a list')
        expected_vnf_keys = {'vimAccountId', 'member-vnf-index'}
        self.assertEqual(expected_vnf_keys, set(placement['vnf'][0]), "placement['vnf'] missing keys")
        self.assertIs(type(placement['vld']), list, 'vld not a list')
        # FIXME the model behind the vnf is tested elsewhere but the vld is in fact created here so content tests needed
        expected_vld_keys = {'name', 'vim-network-name'}
        self.assertEqual(expected_vld_keys, set(placement['vld'][0]), "placement['vld'] missing keys")
        self.assertTrue(placement['wimAccountId'] is False, "wimAccountId invalid")
        self.assertEqual(request_id, placement['request_id'], 'invalid request_id')
    @mock.patch.object(NsPlacementDataFactory, '__init__', lambda x0, x1, x2, x3, x4,x5: None)
    @mock.patch.object(MznPlacementConductor, 'do_placement_computation')
    @mock.patch.object(NsPlacementDataFactory, 'create_ns_placement_data')
    @mock.patch.object(Server, '_get_nsd')
    @mock.patch.object(Server, '_get_enabled_vims')
    def test_get_placement_w_pinning(self, mock_get_enabled_vims,
                           mock_get_nsd,
                           mock_create_ns_placement_data,
                           mock_do_placement_computation):
        """
        test that NsPlacementDataFactory is called with proper args not supported...
        :param mock_get_enabled_vims:
        :param mock_get_nsd:
        :param mock_create_ns_placement_data:
        :param mock_do_placement_computation:
        :return:
        """
        server = self.serverSetup()

        server.msgBus.aiowrite = _async_mock()
        mock_get_nsd.return_value = nsd_from_db
        mock_get_enabled_vims.return_value = list_of_vims
        mock_do_placement_computation.return_value = \
            [{'vimAccountId': 'bbbbbbbb-38f5-438d-b8ee-3f93b3531f87', 'member-vnf-index': '1'},
             {'vimAccountId': 'aaaaaaaa-38f5-438d-b8ee-3f93b3531f87', 'member-vnf-index': '2'},
             {'vimAccountId': 'aaaaaaaa-38f5-438d-b8ee-3f93b3531f87', 'member-vnf-index': '3'}]
        session = pla_get_placement_w_pinning.get('session')
        nsParams = pla_get_placement_w_pinning.get('nsParams')
        pinning = pla_get_placement_w_pinning.get('pinning')
        request_id = random.randint(1000, 2000)

        _run(server.get_placement(session, nsParams, request_id, pinning))

        # mock_get_nsd.assert_called_once() assert_called_once() for python > 3.5
        self.assertTrue(mock_get_nsd.called, 'get_nsd not called as expected')
        # mock_get_enabled_vims.assert_called_once() assert_called_once() for python > 3.5
        self.assertTrue(mock_get_enabled_vims.called, 'get_enabled_vims not called as expected')
        # mock_create_ns_placement_data.assert_called_once() assert_called_once() for python > 3.5
        self.assertTrue(mock_create_ns_placement_data.called, 'create_ns_placement_data not called as expected')
        # mock_do_placement_computation.assert_called_once()  assert_called_once() for python > 3.5
        self.assertTrue(mock_do_placement_computation.called, 'do_placement_computation not called as expected')
        self.assertTrue(server.msgBus.aiowrite.mock.called)

        args, kwargs = server.msgBus.aiowrite.mock.call_args
        self.assertTrue(len(args) == 3, 'invalid format')
        self.assertEqual('pla', args[0], 'topic invalid')
        self.assertEqual('placement', args[1], 'message invalid')

        # extract placement result and check content
        placement = args[2]
        expected_keys = {'vnf', 'vld', 'wimAccountId', 'request_id'}
        self.assertEqual(expected_keys, set(placement.keys()), "placement response missing keys")
        self.assertIs(type(placement['vnf']), list, 'vnf not a list')
        expected_vnf_keys = {'vimAccountId', 'member-vnf-index'}
        self.assertEqual(expected_vnf_keys, set(placement['vnf'][0]), "placement['vnf'] missing keys")
        self.assertIs(type(placement['vld']), list, 'vld not a list')
        # FIXME the model behind the vnf is tested elsewhere but the vld is in fact created here so content tests needed
        expected_vld_keys = {'name', 'vim-network-name'}
        self.assertEqual(expected_vld_keys, set(placement['vld'][0]), "placement['vld'] missing keys")
        self.assertTrue(placement['wimAccountId'] is False, "wimAccountId invalid")
        self.assertEqual(request_id, placement['request_id'], 'invalid request_id')


    # Note: does not mock reading of price list and pop_pil_info
    @mock.patch.object(NsPlacementDataFactory, '__init__', lambda x0, x1, x2, x3, x4, x5: None)
    @mock.patch.object(MznPlacementConductor, 'do_placement_computation')
    @mock.patch.object(NsPlacementDataFactory, 'create_ns_placement_data')
    @mock.patch.object(Server, '_get_nsd')
    @mock.patch.object(Server, '_get_enabled_vims')
    def test_get_placement_w_exception(self, mock_get_enabled_vims,
                                       mock_get_nsd,
                                       mock_create_ns_placement_data,
                                       mock_do_placement_computation):
        """
        check that raised exceptions are handled and response provided accordingly
        """
        server = self.serverSetup()

        server.msgBus.aiowrite = _async_mock()
        mock_get_nsd.return_value = nsd_from_db
        mock_get_nsd.side_effect = RuntimeError('kaboom!')
        mock_get_enabled_vims.return_value = list_of_vims
        mock_do_placement_computation.return_value = \
            [{'vimAccountId': 'bbbbbbbb-38f5-438d-b8ee-3f93b3531f87', 'member-vnf-index': '1'},
             {'vimAccountId': 'aaaaaaaa-38f5-438d-b8ee-3f93b3531f87', 'member-vnf-index': '2'},
             {'vimAccountId': 'aaaaaaaa-38f5-438d-b8ee-3f93b3531f87', 'member-vnf-index': '3'}]
        session = pla_get_suggestions_w_session.get('session')
        nsParams = pla_get_suggestions_w_session.get('nsParams')
        request_id = random.randint(1000, 2000)

        _run(server.get_placement(session, nsParams, request_id, None))
        self.assertTrue(server.msgBus.aiowrite.mock.called)
        args, kwargs = server.msgBus.aiowrite.mock.call_args
        placement = args[2]
        expected_keys = {'vnf', 'vld', 'wimAccountId', 'request_id'}
        self.assertEqual(expected_keys, set(placement.keys()), "placement response missing keys")
        self.assertIs(type(placement['vnf']), list, 'vnf not a list')
        self.assertEqual(placement['vnf'], [], 'vnf list not empty')
        self.assertIs(type(placement['vld']), list, 'vld not a list')
        self.assertEqual(placement['vld'], [], 'vld list not empty')
        self.assertTrue(placement['wimAccountId'] is False, "wimAccountId invalid")
        self.assertEqual(request_id, placement['request_id'], 'invalid request_id')

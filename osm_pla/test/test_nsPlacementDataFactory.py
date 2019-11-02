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
from collections import Counter
from pathlib import Path
from unittest import TestCase, mock
from unittest.mock import call

import yaml

from osm_pla.placement.mznplacement import NsPlacementDataFactory


class TestNsPlacementDataFactory(TestCase):
    vim_accounts = [{"vim_password": "FxtnynxBCnouzAT4Hkerhg==", "config": {},
                     "_admin": {"modified": 1564579854.0480285, "created": 1564579854.0480285,
                                "operationalState": "ENABLED",
                                "projects_read": ["69915588-e5e2-46d3-96b0-a29bedef6f73"],
                                "deployed": {"RO-account": "6beb4e2e-b397-11e9-a7a3-02420aff0008",
                                             "RO": "6bcfc3fc-b397-11e9-a7a3-02420aff0008"},
                                "projects_write": ["69915588-e5e2-46d3-96b0-a29bedef6f73"], "detailed-status": "Done"},
                     "name": "OpenStack1", "vim_type": "openstack", "_id": "92b056a7-38f5-438d-b8ee-3f93b3531f87",
                     "schema_version": "1.1", "vim_user": "admin", "vim_url": "http://10.234.12.47:5000/v3",
                     "vim_tenant_name": "admin"},
                    {"config": {}, "vim_tenant_name": "osm_demo", "schema_version": "1.1", "name": "OpenStack2",
                     "vim_password": "gK5v4Gh2Pl41o6Skwp6RCw==", "vim_type": "openstack",
                     "_admin": {"modified": 1567148372.2490237, "created": 1567148372.2490237,
                                "operationalState": "ENABLED",
                                "projects_read": ["69915588-e5e2-46d3-96b0-a29bedef6f73"],
                                "deployed": {"RO-account": "b7fb0034-caf3-11e9-9388-02420aff000a",
                                             "RO": "b7f129ce-caf3-11e9-9388-02420aff000a"},
                                "projects_write": ["69915588-e5e2-46d3-96b0-a29bedef6f73"], "detailed-status": "Done"},
                     "vim_user": "admin", "vim_url": "http://10.234.12.44:5000/v3",
                     "_id": "6618d412-d7fc-4eb0-a6f8-d2c258e0e900"},
                    {"config": {}, "schema_version": "1.1", "name": "OpenStack3",
                     "vim_password": "1R2FoMQnaL6rNSosoRP2hw==", "vim_type": "openstack", "vim_tenant_name": "osm_demo",
                     "_admin": {"modified": 1567599746.689582, "created": 1567599746.689582,
                                "operationalState": "ENABLED",
                                "projects_read": ["69915588-e5e2-46d3-96b0-a29bedef6f73"],
                                "deployed": {"RO-account": "a8161f54-cf0e-11e9-9388-02420aff000a",
                                             "RO": "a80b6280-cf0e-11e9-9388-02420aff000a"},
                                "projects_write": ["69915588-e5e2-46d3-96b0-a29bedef6f73"], "detailed-status": "Done"},
                     "vim_user": "admin", "vim_url": "http://10.234.12.46:5000/v3",
                     "_id": "331ffdec-44a8-4707-94a1-af7a292d9735"},
                    {"config": {}, "schema_version": "1.1", "name": "OpenStack4",
                     "vim_password": "6LScyPeMq3QFh3GRb/xwZw==", "vim_type": "openstack", "vim_tenant_name": "osm_demo",
                     "_admin": {"modified": 1567599911.5108898, "created": 1567599911.5108898,
                                "operationalState": "ENABLED",
                                "projects_read": ["69915588-e5e2-46d3-96b0-a29bedef6f73"],
                                "deployed": {"RO-account": "0a651200-cf0f-11e9-9388-02420aff000a",
                                             "RO": "0a4defc6-cf0f-11e9-9388-02420aff000a"},
                                "projects_write": ["69915588-e5e2-46d3-96b0-a29bedef6f73"], "detailed-status": "Done"},
                     "vim_user": "admin", "vim_url": "http://10.234.12.43:5000/v3",
                     "_id": "eda92f47-29b9-4007-9709-c1833dbfbe31"}]

    # vim_url, _id as dict, i.e. take the selected _values_ from vim_url and _id
    def _produce_ut_vim_accounts_info(self):
        """
        FIXME temporary, we will need more control over vim_urls and _id for test purpose - make a generator
        :return: vim_url and _id as dict, i.e. extract these from vim_accounts data
        """
        return {_['vim_url']: _['_id'] for _ in TestNsPlacementDataFactory.vim_accounts}

    def _populate_pop_pil_info(self):
        """
        FIXME we need more control over content in pop_pil information - more files or generator and data
        Note str(Path()) is a 3.5 thing
        """
        with open(str(Path('pop_pil_unittest1.yaml'))) as pp_fd:
            test_data = yaml.safe_load_all(pp_fd)
            return next(test_data)

    def _get_ut_nsd_from_file(self, nsd_file_name):
        with open(str(Path(nsd_file_name))) as nsd_fd:
            test_data = yaml.safe_load_all(nsd_fd)
            return next(test_data)

    def _produce_ut_vnf_price_list(self):
        price_list_file = "../server/vnf_price_list.yaml"
        with open(str(Path(price_list_file))) as pl_fd:
            price_list_data = yaml.safe_load_all(pl_fd)
            return {i['vnfd']: {i1['vim_url']: i1['price'] for i1 in i['prices']} for i in next(price_list_data)}

    def _produce_ut_vnf_price_list_OBSOLETE(self):
        import pandas as pd
        file = 'vnf_price_list.xlsx'
        df = pd.read_excel(file, sheet_name='vnf_price_list', index_col=0, skiprows=1)
        return {vnfd_id_ref: {vim: df.loc[vnfd_id_ref][vim] for vim in df.columns}
                for vnfd_id_ref in df.index.values}

    def test__produce_trp_link_characteristics_link_latency(self):
        """
        -test with full set of vims as in pil
        -test with fewer vims compared to pil
        -test with more(other) vims compared to pil
        -test with invalid/corrupt pil configuration file (e.g. missing endpoint), empty file, not yaml conformant
        - test with non-supported characteristic

        :return:
        """
        content_expected = [0, 0, 0, 0, 120, 120, 130, 130, 140, 140, 230, 230, 240, 240, 340, 340]

        nspdf = NsPlacementDataFactory(self._produce_ut_vim_accounts_info(),
                                       self._produce_ut_vnf_price_list(),
                                       nsd=None,
                                       pop_pil_info=self._populate_pop_pil_info())
        pil_latencies = nspdf._produce_trp_link_characteristics_data('pil_latency')
        content_produced = [i for row in pil_latencies for i in row]
        self.assertEqual(Counter(content_expected), Counter(content_produced), 'trp_link_latency incorrect')

    def test__produce_trp_link_characteristics_link_jitter(self):
        """
        -test with full set of vims as in pil
        -test with fewer vims compared to pil
        -test with more(other) vims compared to pil
        -test with invalid/corrupt pil configuration file (e.g. missing endpoint), empty file, not yaml conformant
        - test with non-supported characteristic

        :return:
        """
        content_expected = [0, 0, 0, 0, 1200, 1200, 1300, 1300, 1400, 1400, 2300, 2300, 2400, 2400, 3400, 3400]

        nspdf = NsPlacementDataFactory(self._produce_ut_vim_accounts_info(),
                                       self._produce_ut_vnf_price_list(),
                                       nsd=None,
                                       pop_pil_info=self._populate_pop_pil_info())
        pil_jitter = nspdf._produce_trp_link_characteristics_data('pil_jitter')
        content_produced = [i for row in pil_jitter for i in row]
        self.assertEqual(Counter(content_expected), Counter(content_produced), 'trp_link_jitter incorrect')

    def test__produce_trp_link_characteristics_link_price(self):
        """
        ToDo
        -test with full set of vims as in pil
        -test with fewer vims compared to pil
        -test with more(other) vims compared to pil
        -test with invalid/corrupt pil configuration file (e.g. missing endpoint), empty file, not yaml conformant
        :return:
        """
        content_expected = [0, 0, 0, 0, 12, 12, 13, 13, 14, 14, 23, 23, 24, 24, 34, 34]
        nspdf = NsPlacementDataFactory(self._produce_ut_vim_accounts_info(),
                                       self._produce_ut_vnf_price_list(),
                                       nsd=None,
                                       pop_pil_info=self._populate_pop_pil_info())
        pil_prices = nspdf._produce_trp_link_characteristics_data('pil_price')
        content_produced = [i for row in pil_prices for i in row]
        self.assertEqual(Counter(content_expected), Counter(content_produced), 'invalid trp link prices')

    def test__produce_vld_desc(self):
        """

        :return:
        """
        vld_desc_expected = [{'cp_refs': ['1', '2'], 'latency': 150, 'jitter': 30},
                             {'cp_refs': ['2', '3'], 'latency': 90, 'jitter': 30}]

        nsd = self._get_ut_nsd_from_file('nsd_unittest1.yaml')
        nsd = nsd['nsd:nsd-catalog']['nsd'][0]
        nspdf = NsPlacementDataFactory(self._produce_ut_vim_accounts_info(),
                                       self._produce_ut_vnf_price_list(),
                                       nsd=nsd,
                                       pop_pil_info=None)

        self.assertEqual(nspdf._produce_vld_desc(),
                         vld_desc_expected, "vld_desc incorrect")

    def test__produce_ns_desc(self):
        """
        ToDo
        - price list sheet with more vims than associated with session
        - price list sheet with fewer vims than associated with session
        - nsd with different vndfd-id-refs
        - fault case scenarios with non-existing vims, non-existing vnfds
        """
        nsd = self._get_ut_nsd_from_file('nsd_unittest1.yaml')
        nsd = nsd['nsd:nsd-catalog']['nsd'][0]
        nspdf = NsPlacementDataFactory(self._produce_ut_vim_accounts_info(),
                                       self._produce_ut_vnf_price_list(),
                                       nsd=nsd,
                                       pop_pil_info=None)

        ns_desc = nspdf._produce_ns_desc()
        # check that all expected member-vnf-index are present
        vnfs = [e['member-vnf-index'] for e in ns_desc]
        self.assertEqual(Counter(['1', '3', '2']), Counter(vnfs), 'member-vnf-index invalid')
        # check that vnf_price_per_vim has  proper values
        for e in ns_desc:
            self.assertEqual(Counter([7, 8, 9, 10]), Counter(e['vnf_price_per_vim']), 'vnf_price_per_vim invalid')

    @mock.patch.object(NsPlacementDataFactory, '_produce_trp_link_characteristics_data')
    @mock.patch.object(NsPlacementDataFactory, '_produce_vld_desc')
    @mock.patch.object(NsPlacementDataFactory, '_produce_ns_desc')
    def test_create_ns_placement_data(self, mock_prd_ns_desc, mock_prd_vld_desc, mock_prd_trp_link_char):
        """
        :return:
        """
        vim_accounts_expected = [v.replace('-', '_') for v in ['92b056a7-38f5-438d-b8ee-3f93b3531f87',
                                                               '6618d412-d7fc-4eb0-a6f8-d2c258e0e900',
                                                               '331ffdec-44a8-4707-94a1-af7a292d9735',
                                                               'eda92f47-29b9-4007-9709-c1833dbfbe31']]

        nsd = self._get_ut_nsd_from_file('nsd_unittest1.yaml')
        nsd = nsd['nsd:nsd-catalog']['nsd'][0]
        nspdf = NsPlacementDataFactory(self._produce_ut_vim_accounts_info(),
                                       self._produce_ut_vnf_price_list(),
                                       nsd=nsd,
                                       pop_pil_info=self._populate_pop_pil_info())
        nspd = nspdf.create_ns_placement_data()
        self.assertEqual(Counter(nspd['vim_accounts']),
                         Counter(vim_accounts_expected), "vim_accounts incorrect")
        # mock1.assert_called_once() Note for python > 3.5
        self.assertTrue(mock_prd_ns_desc.called, '_produce_ns_desc not called')
        # mock2.assert_called_once() Note for python > 3.5
        self.assertTrue((mock_prd_vld_desc.called, ' _produce_vld_desc not called'))
        mock_prd_trp_link_char.assert_has_calls([call('pil_latency'), call('pil_jitter'), call('pil_price')])

        regexps = [r"\{.*\}", r".*'file':.*mznplacement.py", r".*'time':.*datetime.datetime\(.*\)"]
        generator_data = str(nspd['generator_data'])
        for regex in regexps:
            self.assertRegex(generator_data, regex, "generator data invalid")

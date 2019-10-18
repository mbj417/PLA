from pathlib import Path
from unittest import TestCase, mock
import unittest

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
    def _populate_vim_accounts_info(self):
        return {_['vim_url']: _['_id'] for _ in TestNsPlacementDataFactory.vim_accounts}

    def _populate_pop_pil_dict(self):
        """
        ToDo
        - read file, just as NsPlacementDataFactory but from other location
        """
        with open(Path('pop_pil_unittest1.yaml')) as pp_fd:
            test_data = yaml.safe_load_all(pp_fd)
            return next(test_data)

    def _get_ut_nsd_from_file(self, nsd_file_name):
        with open(Path(nsd_file_name)) as nsd_fd:
            test_data = yaml.safe_load_all(nsd_fd)
            return next(test_data)

    @unittest.skip('Not now')
    @mock.patch.object(NsPlacementDataFactory, '_harvest_pil_data')
    @mock.patch.object(NsPlacementDataFactory, '_harvest_pop_data')
    def test__add_pop_pil_info(self, mock1, mock2):
        """
        file exists and is valid
        file does not exist
        file is corrupt (empty, not proper yaml content in this context)

        ToDo
        - mock so that we do not call _harvest_pop_data/_harvest_pel_data those are other tests
        - control which file to use so that we can have valid, invalid and non-existing
        """
        print(self.nspdf._nsd_path)
        print(self.nspdf._pp_dict)
        self.nspdf._add_pop_pil_info()
        # print(self.nspdf._pp_dict)
        # print(self.nspdf._nspd._mzn_model_data)
        self.assertTrue(self.nspdf is not None, "Should be an instance")
        mock1.assert_called_once()
        mock2.assert_called_once()

    def test__add_pop_pil_info_nonexist(self):
        """
        failure to find the configuration file causes IOError
        """

        with mock.patch.object(NsPlacementDataFactory, 'pop_pil_path', 'nonexisting.yaml'):
            nspdf = NsPlacementDataFactory()
            self.assertRaises(IOError, nspdf._add_pop_pil_info)

    @unittest.skip('Incomplete')
    def test__add_pop_pil_info_invalid(self):
        """
        reading an empty file raise some to be defined exception
        Can I first create a test where a valid file is read from another location (i.e. the test catalog)
        """
        pass

    @unittest.skip('Not now')
    def test__harvest_pop_data(self):
        """
        Todo
        - populate dict with test data (default pop_pil.yaml will do to start with)
        FIXME Let's wait with this until we now if we really need PoP anymore
        """
        nspdf = NsPlacementDataFactory(self._populate_vim_accounts_info())

        nspdf._pp_dict = self._populate_pop_pil_dict()
        nspdf._harvest_pop_data()
        print(nspdf._nspd._mzn_model_data)

    def test__harvest_pil_data(self):
        """
        Todo
        -populate dict with test data (default pop_pil.yaml will do to start with)
        -test with full set of vims as in pil
        -test with fewer vims compared to pil
        -test with more(other) vims compared to pil
        -test with invalid/corrupt pil configuration file (e.g. missing endpoint), empty file, not yaml conformant
        - where does the system validate the format of e.g vim_url's and _id's?
        """
        nspdf = NsPlacementDataFactory(self._populate_vim_accounts_info())
        nspdf._pp_dict = self._populate_pop_pil_dict()
        nspdf._harvest_pil_data()
        self.assertEqual(nspdf._nspd._mzn_model_data['trp_link_latency'],
                         [[0, 50, 120, 150], [50, 0, 100, 150], [120, 100, 0, 50], [150, 150, 50, 0]],
                         "trp_link_latency incorrect")
        self.assertEqual(nspdf._nspd._mzn_model_data['trp_link_price_list'],
                         [[0, 5, 6, 6], [5, 0, 5, 6], [6, 5, 0, 5], [6, 6, 5, 0]], "trp_link_price incorrect")

    @unittest.skip('Not now')
    def test__add_nsd_info(self):
        self.fail()

    @unittest.skip('Not now')
    def test__add_nsd_info_local_file(self):
        self.fail()

    def test__harvest_nsd_data(self):
        """
        Todo
        - get some test nsd into the factory (the nsd from the patras revision will do to start with
        - test with yada yada yada
        :return:
        """
        vld_desc_expected = [{'cp_refs': ['1', '2'], 'latency': 150, 'jitter': 30},
                             {'cp_refs': ['2', '3'], 'latency': 90, 'jitter': 30}]

        nsd = self._get_ut_nsd_from_file('nsd_unittest1.yaml')
        nsd = nsd['nsd:nsd-catalog']['nsd'][0]
        nspdf = NsPlacementDataFactory(self._populate_vim_accounts_info(), nsd=nsd)
        nspdf._harvest_nsd_data()
        self.assertEqual(nspdf._nspd._mzn_model_data['vld_desc'],
                         vld_desc_expected, "vld_desc incorrect")

    def test__produce_ns_desc(self):
        """
        ToDo
        - price list sheet with more vims than associated with session
        - price list sheet with fewer vims than associated with session
        - nsd with different vndfd-id-refs
        - fault case scenarios with non-existing vims, non-existing vnfds
        """
        ns_desc_expected =[{'member-vnf-index': '1', 'vnf_price_per_vim': [10, 9, 8, 7]},
                           {'member-vnf-index': '2', 'vnf_price_per_vim': [10, 9, 8, 7]},
                           {'member-vnf-index': '3', 'vnf_price_per_vim': [10, 9, 8, 7]}]

        nsd = self._get_ut_nsd_from_file('nsd_unittest1.yaml')
        nsd = nsd['nsd:nsd-catalog']['nsd'][0]
        nspdf = NsPlacementDataFactory(self._populate_vim_accounts_info(),
                                       self._get_ut_vnf_price_list(), nsd=nsd)
        nspdf._produce_ns_desc()
        self.assertEqual(nspdf._nspd._mzn_model_data['ns_desc'],
                         ns_desc_expected, "ns_desc incorrect")

    @unittest.skip('Not now')
    def test__add_vnfd_info(self):
        self.fail()

    @unittest.skip('Not now')
    def test__add_vnfd_info_local_file(self):
        self.fail()

    @unittest.skip('Not now')
    def test__harvest_vnfd_data(self):
        self.fail()

    @unittest.skip('Not now')
    def test__add_inventory_data(self):
        self.fail()

    @unittest.skip('Not now')
    def test_create_ns_placement_data(self):
        self.fail()

    def _get_ut_vnf_price_list(self):
        import pandas as pd
        file = 'vnf_price_list.xlsx'
        df = pd.read_excel(file, sheet_name='vnf_price_list', index_col=0, skiprows=1)
        return {vnfd_id_ref: {vim: df.loc[vnfd_id_ref][vim] for vim in df.columns}
                for vnfd_id_ref in df.index.values}

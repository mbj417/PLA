from pathlib import Path
from unittest import TestCase, mock
import unittest

import yaml

from osm_pla.placement.mznplacement import NsPlacementDataFactory


class TestNsPlacementDataFactory(TestCase):

    def _populate_pop_pil_dict(self):
        """
        ToDo
        - read file, just as NsPlacementDataFactory but from other location
        """
        with open(Path('pop_pil_unittest1.yaml')) as pp_fd:
            test_data = yaml.safe_load_all(pp_fd)
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
            # nspdf._add_pop_pil_info2()
            self.assertRaises(IOError, nspdf._add_pop_pil_info)

    @unittest.skip('Incomplete')
    def test__add_pop_pil_info_invalid(self):
        """
        reading an empty file raise some to be defined exception
        Can I first create a test where a valid file is read from another location (i.e. the test catalog)
        """
        pass

    def test__harvest_pop_data(self):
        """
        Todo
        - populate dict with test data (default pop_pil.yaml will do to start with)
        """
        nspdf = NsPlacementDataFactory()
        nspdf._pp_dict = self._populate_pop_pil_dict()
        nspdf._harvest_pop_data()
        print(nspdf._nspd._mzn_model_data)


    @unittest.skip('Not now')
    def test__harvest_pil_data(self):
        self.fail()

    @unittest.skip('Not now')
    def test__add_nsd_info(self):
        self.fail()

    @unittest.skip('Not now')
    def test__add_nsd_info_local_file(self):
        self.fail()

    @unittest.skip('Not now')
    def test__harvest_nsd_data(self):
        self.fail()

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

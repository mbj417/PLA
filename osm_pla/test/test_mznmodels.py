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
import datetime
from unittest import TestCase


vim_accounts = ['00000000-38f5-438d-b8ee-3f93b3531f87',
                '11111111-38f5-438d-b8ee-3f93b3531f87',
                '22222222-38f5-438d-b8ee-3f93b3531f87',
                '33333333-38f5-438d-b8ee-3f93b3531f87',
                '44444444-38f5-438d-b8ee-3f93b3531f87',
                '55555555-38f5-438d-b8ee-3f93b3531f87',
                '66666666-38f5-438d-b8ee-3f93b3531f87',
                '77777777-38f5-438d-b8ee-3f93b3531f87',
                '88888888-38f5-438d-b8ee-3f93b3531f87',
                '99999999-38f5-438d-b8ee-3f93b3531f87']

trp_link_latency = [[0, 30, 70, 80, 0, 0, 0, 0, 0, 0], [30, 0, 75, 60, 0, 0, 0, 0, 0, 0],
                    [70, 75, 0, 40, 100, 0, 0, 0, 0, 0], [80, 60, 40, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 100, 0, 0, 5, 5, 0, 0, 0], [0, 0, 0, 0, 5, 0, 5, 0, 0, 0], [0, 0, 0, 0, 5, 5, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 30, 20], [0, 0, 0, 0, 0, 0, 0, 30, 0, 20],
                    [0, 0, 0, 0, 0, 0, 0, 20, 20, 0]]

trp_link_jitter = [[0, 5, 5, 10, 0, 0, 0, 0, 0, 0], [5, 0, 5, 10, 0, 0, 0, 0, 0, 0], [5, 5, 0, 10, 5, 0, 0, 0, 0, 0],
                   [10, 10, 10, 0, 0, 0, 0, 0, 0, 0], [0, 0, 5, 0, 0, 4, 4, 0, 0, 0], [0, 0, 0, 0, 4, 0, 10, 0, 0, 0],
                   [0, 0, 0, 0, 4, 10, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 1, 1], [0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
                   [0, 0, 0, 0, 0, 0, 0, 1, 1, 0]]

trp_link_price_list = [[0, 5, 5, 10, 0, 0, 0, 0, 0, 0], [5, 0, 5, 10, 0, 0, 0, 0, 0, 0],
                       [5, 5, 0, 10, 10, 0, 0, 0, 0, 0], [10, 10, 10, 0, 0, 0, 0, 0, 0, 0],
                       [0, 0, 10, 0, 0, 20, 20, 0, 0, 0], [0, 0, 0, 0, 20, 0, 20, 0, 0, 0],
                       [0, 0, 0, 0, 20, 20, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 15, 15],
                       [0, 0, 0, 0, 0, 0, 0, 15, 0, 15], [0, 0, 0, 0, 0, 0, 0, 15, 15, 0]]

inventory_placement_data = {'vim_accounts': vim_accounts,
                            'trp_link_latency': trp_link_latency,
                            'trp_link_jitter': trp_link_jitter}


test_ns_placement_data = {
    'vim_accounts': [vim_account.replace('-', '_') for vim_account in ['aaaaaaaa-38f5-438d-b8ee-3f93b3531f87',
                                                                       'bbbbbbbb-38f5-438d-b8ee-3f93b3531f87',
                                                                       'cccccccc-ed84-4e49-b5df-a9d117bd731f',
                                                                       'dddddddd-ed84-4e49-b5df-a9d117bd731f',
                                                                       'eeeeeeee-38f5-438d-b8ee-3f93b3531f87']],
    'trp_link_latency': [[0, 50, 100, 150, 200], [0, 0, 100, 150, 200], [0, 0, 0, 150, 200], [0, 0, 0, 0, 200],
                         [0, 0, 0, 0, 0]],
    'trp_link_jitter': [[0, 5, 10, 15, 20], [0, 0, 10, 15, 20], [0, 0, 0, 15, 20], [0, 0, 0, 0, 20],
                        [0, 0, 0, 0, 0]],
    'trp_link_price_list': [[0, 5, 6, 6, 7], [0, 0, 6, 6, 7], [0, 0, 0, 6, 7], [0, 0, 0, 0, 7], [0, 0, 0, 0, 0]],
    'ns_desc': [
        {'vnf_id': '1', 'vnf_price_per_vim': [50, 51, 52, 53, 54]},
        {'vnf_id': '2', 'vnf_price_per_vim': [20, 21, 22, 23, 24]},
        {'vnf_id': '3', 'vnf_price_per_vim': [70, 71, 72, 73, 74]},
        {'vnf_id': '4', 'vnf_price_per_vim': [40, 41, 42, 43, 44]}],
    'vld_desc': [{'cp_refs': ['1', '2'], 'latency': 150, 'jitter': 30},
                 {'cp_refs': ['2', '3'], 'latency': 140, 'jitter': 30},
                 {'cp_refs': ['3', '4'], 'latency': 130, 'jitter': 30}],
    'generator_data': {'file': __file__, 'time': datetime.datetime.now()}
}


class TestMznModels(TestCase):
    pass

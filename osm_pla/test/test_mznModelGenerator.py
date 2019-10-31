import datetime
import logging
from unittest import TestCase

from jinja2 import Template

from osm_pla.placement.mznplacement import MznModelGenerator

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

expected_model_fragment = """
%This is the NETWORK RESOURCE MODEL
enum  Vims = {
aaaaaaaa_38f5_438d_b8ee_3f93b3531f87,
bbbbbbbb_38f5_438d_b8ee_3f93b3531f87,
cccccccc_ed84_4e49_b5df_a9d117bd731f,
dddddddd_ed84_4e49_b5df_a9d117bd731f,
eeeeeeee_38f5_438d_b8ee_3f93b3531f87}; % The vim-accounts
array[Vims, Vims] of int: trp_link_latency = [|0,50,100,150,200,
|0,0,100,150,200,
|0,0,0,150,200,
|0,0,0,0,200,
|0,0,0,0,0,
|]; % Transport link latency between data centers
array[Vims, Vims] of int: trp_link_jitter = [|0,50,100,150,200,
|0,0,100,150,200,
|0,0,0,150,200,
|0,0,0,0,200,
|0,0,0,0,0,
|]; % Transport link jitter between data centers
array[Vims, Vims] of int: trp_link_price_list = [|0,5,6,6,7,
|0,0,6,6,7,
|0,0,0,6,7,
|0,0,0,0,7,
|0,0,0,0,0,
|]; % Transport link price list
array[Vims] of int: vim_price_list_1 = [50,51,52,53,54];
array[Vims] of int: vim_price_list_2 = [20,21,22,23,24];
array[Vims] of int: vim_price_list_3 = [70,71,72,73,74];
array[Vims] of int: vim_price_list_4 = [40,41,42,43,44];


% This is the NETWORK BASIC LOAD MODEL (CONSUMED)
% NOTE. This is not applicable in OSM Release 7

% This is the SERVICE CONSUMPTION MODEL
% These are the variables, i.e. which DC to select for each VNF
var Vims: VNF1;
var Vims: VNF2;
var Vims: VNF3;
var Vims: VNF4;


% These are the set of rules for selecting DCs to VNFs
constraint trp_link_latency[VNF1, VNF2] <= 150;
constraint trp_link_latency[VNF2, VNF3] <= 140;
constraint trp_link_latency[VNF3, VNF4] <= 130;
constraint trp_link_jitter[VNF1, VNF2] <= 30;
constraint trp_link_jitter[VNF2, VNF3] <= 30;
constraint trp_link_jitter[VNF3, VNF4] <= 30;

% Calculate the cost for VNFs and cost for transport link and total cost
var int: used_transport_cost =trp_link_price_list[VNF1, VNF2]+
trp_link_price_list[VNF2, VNF3]+
trp_link_price_list[VNF3, VNF4];

var int: used_vim_cost =vim_price_list_1[VNF1]+
vim_price_list_2[VNF2]+
vim_price_list_3[VNF3]+
vim_price_list_4[VNF4];

var int: total_cost = used_transport_cost + used_vim_cost;

solve minimize total_cost;
"""


class TestMznModelGenerator(TestCase):
    def test_create_model(self):
        mg = MznModelGenerator(logging.getLogger(__name__))
        mzn_model = mg.create_model(test_ns_placement_data)

        # so asserting exact content is difficult due to the datetime.now(), therefore we ignore the first lines
        self.assertTrue(expected_model_fragment.replace('\n', '') in
                        mzn_model.render_thyself_as_str().replace('\n', ''), "faulty model generated")

    def test__load_jinja_template(self):
        """

        add other test to check exception if template not loaded (e.g. invalid template name,
        perhaps also valid name but invalid content (in case jinja2 detects such things))
        """
        mg = MznModelGenerator(logging.getLogger(__name__))
        template = mg._load_jinja_template()  # Note we use the default template
        self.assertTrue(isinstance(template, Template), "failed to load jinja2 template")
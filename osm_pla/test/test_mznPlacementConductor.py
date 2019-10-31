import logging
from unittest import TestCase, mock

import osm_pla
from osm_pla.placement.mznplacement import MznPlacementConductor, MznModelGenerator, MznModel

test_mzn_model = """
% This minizinc model is generated using C:/Users/LG/PycharmProjects/dynamic_jijna2_mzn/osm_pla/placement/mznplacement.py
% at 2019-10-24 11:12:02.058905.

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
array[Vims] of int: vim_price_list_1 = [500,51,52,53,54];
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
test_mzn_unsatisfyable_model = """ 
var 1..2: item1;
var 1..2: item2;
constraint item1 + item2 == 5;

solve satisfy;
"""


# FIXME We can really get rid of the placementresult class. No need for that.


class TestMznPlacementConductor(TestCase):
    def test__run_placement_model(self):
        expected_result = [{'vimAccountId': 'bbbbbbbb-38f5-438d-b8ee-3f93b3531f87', 'member-vnf-index': '1'},
                           {'vimAccountId': 'aaaaaaaa-38f5-438d-b8ee-3f93b3531f87', 'member-vnf-index': '2'},
                           {'vimAccountId': 'aaaaaaaa-38f5-438d-b8ee-3f93b3531f87', 'member-vnf-index': '3'},
                           {'vimAccountId': 'aaaaaaaa-38f5-438d-b8ee-3f93b3531f87', 'member-vnf-index': '4'}]

        mpc = MznPlacementConductor(logging.getLogger(__name__))
        placement = mpc._run_placement_model(mzn_model=test_mzn_model)
        self.assertEqual(placement, expected_result, "Faulty syntax or content")

    def test_run_placement_model_unsatisfiable(self):
        mpc = MznPlacementConductor(logging.getLogger(__name__))
        self.assertEqual(mpc._run_placement_model(mzn_model=test_mzn_unsatisfyable_model),
                         [{}], "Faulty syntax or content for unsatisfiable model")

    @mock.patch.object(MznModelGenerator, 'create_model', side_effect=[MznModel('%model')])
    @mock.patch.object(MznPlacementConductor, '_run_placement_model')
    def test_do_placement_computation(self, mock_run, mock_create):
        mpc = MznPlacementConductor(logging.getLogger(__name__))
        dummy_nspd = {'key': 'value'}
        placement = mpc.do_placement_computation(dummy_nspd)
        mock_create.assert_called_with(dummy_nspd)
        mock_run.assert_called_with(mzn_model='%model')

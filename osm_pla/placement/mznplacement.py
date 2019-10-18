'''
Created on 30 aug. 2019

@author: LG
'''
from jinja2 import Environment
from jinja2.loaders import FileSystemLoader
import yaml
from pathlib import Path
import pymzn
import re
import platform
from _collections import OrderedDict
import pkg_resources
import os
import json

dummy_model = '''
        int: range;
        var 1..range: x;
        var 1..range: y;
        
        constraint x+y > 2;
        
        solve satisfy;'''

dummy_model_data = {'range': '3'}


class MznPlacementConductor(object):
    '''
    Knows how to process placment req using minizinc
    '''
    # FIXME is this a reasonable way to handle cross-platform mzn paths?
    if platform.system() == 'Windows':
        default_mzn_path = 'C:\Program Files\MiniZinc IDE (bundled)\minizinc.exe'
    else:
        default_mzn_path = '/minizinc/bin/minizinc'

    def __init__(self, vim_accounts, log, mzn_path=default_mzn_path):
        pymzn.config['minizinc'] = mzn_path
        self._vim_accounts = vim_accounts
        self.log = log
        self.log.info("VIM Accounts: {}".format(json.dumps(vim_accounts)))

    def _run_placement_model(self, model=dummy_model, mzn_model_data=dummy_model_data):
        '''run the minzinc model.
        Note: essentially pointless to call with just one keyword argument.
        FIXME remove default values once code more stable'''

        self.log.info('launch minizinc with data as follows:')
        for k, v in mzn_model_data.items():
            self.log.info("  {} = {}".format(k, v))
        self.log.info("======================")
        solns = pymzn.minizinc(model, data=mzn_model_data)

        # map the solution to vim_accounts and member-vnf-index
        # assume dc1 equals vim_account 1 and VNF1 equals member-vnf-index 1 and so forth
        result = {}
        for k, v in solns[0].items():
            vim = self._vim_accounts[str(v)]
            vnf = k[-1:]
            result[vnf] = vim
        return PlacementResult(result)

    def do_placement_computation(self, nspd):
        '''compute placement suggestion from service reqs and infra metrics'''
        mzn_model = MznModelGenerator(self.log).create_model(nspd)
        return self._run_placement_model(model=mzn_model.render_thyself_as_str(), mzn_model_data=nspd._mzn_model_data)


class MznModelGenerator(object):
    '''
    Has the capability to generate minizinc models from information contained in
    NsPlacementData objects. Uses jinja2 as templating language for the model
    
    FIXME - need to decide file system location for template (and possibly model in target system)
    '''
    default_j2_template = 'osm_pla_static_template.j2'
    template_search_path = ['/pla/osm_pla/placement']  # FIXME need another location eventually

    def __init__(self, log):
        '''
        Constructor
        '''
        self.log = log

    def create_model(self, nspd):
        '''
        Creates a minizinc model according to the content of nspd
        
        nspd - NSPlacementData
        
        return MZNModel
        '''
        mzn_model_template = self._load_jinja_template()
        mzn_model = MznModel(mzn_model_template.render())
        return mzn_model

    def _load_jinja_template(self, template_name=default_j2_template):
        '''loads the jinja template used for model generation'''
        env = Environment(loader=FileSystemLoader(MznModelGenerator.template_search_path))
        return env.get_template(template_name)


class MznModel(object):
    ''' container for minizinc model'''

    def __init__(self, model):
        '''
        model - a str comprising a minizinc model
        '''
        self._model = model

    def render_thyself_as_str(self):
        ''' return a str respresentation of the minizinc model'''
        return self._model


class NsPlacementDataFactory(object):
    ''' collect service requirements, network resource and cost information
    and place in NsPlacementData'''

    pop_pil_path = 'pop_pil.yaml'
    nsd_path = 'nsd.yaml'  # FIXME should go away
    vnfd_path = 'vnfd.yaml'  # FIXME should go away
    inventory_path = 'inventory.yaml'  # FIXME should go away
    vnf_price_per_vim = [{'vnfd': '<vnfd-id-ref>',
                          'price_list': {'<vim_account1>': '<price in some to be decided unit>',
                                         '<vim_account2>': '<price in some to be decided unit>'}}]
    simpler_vnf_price_per_vim = {'<vnfd-id-ref': {'<vim_account1>': '<price in some to be decided unit>',
                                                  '<vim_account2>': '<price in some to be decided unit>'}}

    # FIXME a lot of things to consider. What to do if there is no price information? Assume free of charge or remove vim from viable alternatives?
    # FIXME shall we actually produce(or outline) some functionality that consider instances, vcpu, memory, storage? Maybe import from .xlsx

    def __init__(self, vim_accounts_info, vnf_prices, nsd=None, member_vnfds=None):
        """
        vim_accounts: is a dictionary with vim url as key and id as value, we add a unique index to it for use
        in the mzn array constructs
        vnf_price: is a dictionary with 'vnfd'id'ref' as key and a dictionary with vim_urls and cost as value
        """
        import itertools
        _next_idx = itertools.count()
        self._vim_accounts_info = {k: {'id': v, 'idx': next(_next_idx)} for k, v in vim_accounts_info.items()}
        self._vnf_prices = vnf_prices
        self._pp_dict = {}
        self._nsd = nsd
        self._member_vnfds = member_vnfds
        self._pop_pil_path = pkg_resources.resource_filename(__name__, NsPlacementDataFactory.pop_pil_path)
        self._nsd_path = pkg_resources.resource_filename(__name__, NsPlacementDataFactory.nsd_path)
        self._vnfd_path = pkg_resources.resource_filename(__name__, NsPlacementDataFactory.vnfd_path)
        self._inventory_path = pkg_resources.resource_filename(__name__, NsPlacementDataFactory.inventory_path)

        self._nspd = NsPlacementData()

    def _add_pop_pil_info(self):
        '''collect information on PoPs and PiL and update the
         dictionary '''

        with open(self._pop_pil_path) as pp_fd:
            pop_pil_data = yaml.safe_load_all(pp_fd)
            self._pp_dict.update(next(pop_pil_data))

            self._harvest_pop_data()
            self._harvest_pil_data()

    def _harvest_pop_data(self):
        '''extracts selected data from pop config'''
        dc_ids = []
        num_vms = []
        vm_cost = []
        dc_dict = {}
        next_dc_no = 0

        # FIXME there is no storage information in pop, only number of vms. For now we hard code this
        storage = [100, 100, 100, 100]

        # FIXME the minizinc model has single vm cost, as we are from the 'lagom' country we chose medium for this.
        vims = [e for e in self._pp_dict['pop']]
        for e in vims:
            e['dc_no'] = next_dc_no
            dc_ids.append(next_dc_no)
            next_dc_no += 1
            for k, v in e.items():
                if k == 'vim_url':
                    dc_dict[v] = e
                elif k == 'num_vm':
                    num_vms.append(v)
                elif k == 'vm_price':
                    for flavors in v:
                        for k1, v1 in flavors.items():
                            if k1 == 'medium':
                                vm_cost.append(v1)

        self.dc_dict = dc_dict

        self._nspd._mzn_model_data['number_of_dc'] = len(dc_ids)
        self._nspd._mzn_model_data['datacenter_id'] = dc_ids
        self._nspd._mzn_model_data['vm'] = num_vms
        self._nspd._mzn_model_data['vm_cost'] = vm_cost

    def _harvest_pil_data(self):
        """extracts trl_link_latency, trp_link_jitter and trp_link_price_list from pil configuration"""

        num_vims = len(self._vim_accounts_info)
        trp_link_latency = [[0 for _ in range(num_vims)] for _ in range(num_vims)]
        trp_link_price_list = [[0 for _ in range(num_vims)] for _ in range(num_vims)]

        for pil in [_ for _ in self._pp_dict['pil']]:
            url1 = pil['pil_endpoints'][0]
            url2 = pil['pil_endpoints'][1]
            # only consider links between applicable vims
            if url1 in self._vim_accounts_info and url2 in self._vim_accounts_info:
                idx1 = self._vim_accounts_info[url1]['idx']
                idx2 = self._vim_accounts_info[url2]['idx']
                trp_link_latency[idx1][idx2] = pil['pil_latency']
                trp_link_latency[idx2][idx1] = pil['pil_latency']
                trp_link_price_list[idx1][idx2] = pil['pil_price']
                trp_link_price_list[idx2][idx1] = pil['pil_price']
                # trp_link_jitter[idx1][idx2] = pil['pil_jitter']
                # trp_link_jitter[idx2][idx1] = pil['pil_jitter']

        self._nspd._mzn_model_data['trp_link_latency'] = trp_link_latency
        # self._nspd._mzn_model_data['trp_link_jitter'] = trp_link_jitter
        self._nspd._mzn_model_data['trp_link_price_list'] = trp_link_price_list

    def _add_nsd_info(self):
        '''collect information on nsd and update the
         dictionary'''
        if not self._nsd:
            self._add_nsd_info_local_file()
        self._harvest_nsd_data()

    def _add_nsd_info_local_file(self):
        '''collect from local config file
        FIXME this is obsolete and should go away
        '''
        try:
            with open(self._nsd_path) as nsd_fd:
                nsd_data = yaml.safe_load_all(nsd_fd)
                self._nsd = next(nsd_data)
                self._nsd = self._nsd['nsd:nsd-catalog']['nsd'][0]

        except Exception as e:
            raise Exception(e)

    def _harvest_nsd_data(self):
        """
        extract vld_desc[] information from the nsd
        """
        vld_desc = []
        for vld in self._nsd['vld']:
            cp_refs = [str(ep_ref['member-vnf-index-ref']) for ep_ref in [_ for _ in vld['vnfd-connection-point-ref']]]
            latency = [constraint['value'] for constraint in
                       vld['link-constraint'] if constraint['constraint-type'] == 'LATENCY'][0]
            jitter = [constraint['value'] for constraint in
                      vld['link-constraint'] if constraint['constraint-type'] == 'JITTER'][0]

            vld_desc.append({'cp_refs': cp_refs, 'latency': latency, 'jitter': jitter})

        self._nspd._mzn_model_data['vld_desc'] = vld_desc

    def _produce_ns_desc(self):
        """
        collect information for the nd_desc part of the placement data

        for the vim_accounts that are applicable, collect the vnf_price
        FIXME exceptions to be raised at fault scenarios
        """
        ns_desc = []
        for vnfd in self._nsd['constituent-vnfd']:
            prices_for_vnfd = self._vnf_prices[vnfd['vnfd-id-ref']]
            # the list of prices must be ordered according to the indexing of the vim_accounts
            price_list = [_ for _ in range(len(self._vim_accounts_info))]
            for k in prices_for_vnfd.keys():
                price_list[self._vim_accounts_info[k]['idx']] = prices_for_vnfd[k]

            ns_desc.append({'member-vnf-index': str(vnfd['member-vnf-index']),
                            'vnf_price_per_vim': price_list})
        self._nspd._mzn_model_data['ns_desc'] = ns_desc

    def _add_vnfd_info(self):
        '''collect information from vnfd and update the dictionary'''
        if not self._member_vnfds:
            self._add_vnfd_info_local_file()
        self._harvest_vnfd_data()

    def _add_vnfd_info_local_file(self):
        '''collect from local config file'''
        try:
            with open(self._vnfd_path) as vnfd_fd:
                vnfd_data = yaml.safe_load_all(vnfd_fd)
                vnfd = next(vnfd_data)
                vnfd = vnfd['vnfd:vnfd-catalog']['vnfd'][0]
                vnfdId = vnfd['id']
                self._member_vnfds[vnfdId] = vnfd

        except Exception as e:
            raise Exception(e)

    def _harvest_vnfd_data(self):
        '''Note: currently assume one single vnf for entire 3-vnf style nsd
        and therefore does not traverse data'''
        for vnf in self._nsd['constituent-vnfd']:
            vnfdId = vnf['vnfd-id-ref']
            vnfIndex = vnf['member-vnf-index']
            vnfd = self._member_vnfds[vnfdId]
            vm_flavor = vnfd['vdu'][0]['vm-flavor']
            vcpu_count = vm_flavor['vcpu-count']
            storage_gb = vm_flavor['storage-gb']
            if vnfIndex == '1':
                self._nspd._mzn_model_data['service_vnf1_vm'] = vcpu_count
                self._nspd._mzn_model_data['service_vnf1_storage'] = storage_gb
            elif vnfIndex == '2':
                self._nspd._mzn_model_data['service_vnf2_vm'] = vcpu_count
                self._nspd._mzn_model_data['service_vnf2_storage'] = storage_gb
            elif vnfIndex == '3':
                self._nspd._mzn_model_data['service_vnf3_vm'] = vcpu_count
                self._nspd._mzn_model_data['service_vnf3_storage'] = storage_gb

    def _add_inventory_data(self):
        '''this is where we setup the used resources
        FIXME obsolete
        '''
        try:
            invntry_dict = {}
            with open(self._inventory_path) as invntry_fd:
                invntry_data = yaml.safe_load_all(invntry_fd)
                invntry_dict.update(next(invntry_data))
                self._nspd._mzn_model_data['consumed_vm'] = invntry_dict['consumed_vm']
                self._nspd._mzn_model_data['consumed_storage'] = invntry_dict['consumed_storage']
        except Exception as e:
            raise Exception(e)

    def create_ns_placement_data(self):
        '''populate NsPlacmentData object'''
        self._nspd._mzn_model_data['vim_accounts'] = [vim.replace('-', '_') for vim in self._vim_accounts_info.values()]
        self._add_pop_pil_info()
        self._add_nsd_info()
        self._add_vnfd_info()
        self._add_inventory_data()

        return self._nspd


class NsPlacementData(object):
    '''Container for service requirements and infrastructure data.
    
    FIXME at the moment a dictionary matching the data to be sent to the static model.
    Content directly added from factory. Wrapped in a class for expected future additions
    of behavior. '''

    def __init__(self):
        self._mzn_model_data = {}


class PlacementResult(object):
    '''container for placement result'''

    def __init__(self, placement):
        '''Note: single placement. In case multiple solutions are found
        the selection of placement is done elsewhere'''
        self._placement = placement

    def render_thyself_as_kafka_payload(self):
        vnf_field_content = ', '.join(
            "{{'vimAccountId': '{}'', 'member-vnf-index': '{}'}}".format(vim, vnf) for vnf, vim in
            self._placement.items())
        return 'vnf: [' + vnf_field_content + ']'

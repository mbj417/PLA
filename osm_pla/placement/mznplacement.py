'''
Created on 30 aug. 2019

@author: LG
'''
import datetime
import platform

import pymzn
from jinja2 import Environment
from jinja2.loaders import FileSystemLoader


class MznPlacementConductor(object):
    """
    Knows how to process placement req using minizinc
    """
    # FIXME is this a reasonable way to handle cross-platform mzn paths?
    if platform.system() == 'Windows':
        default_mzn_path = 'C:\Program Files\MiniZinc IDE (bundled)\minizinc.exe'
    else:
        default_mzn_path = '/minizinc/bin/minizinc'

    def __init__(self, log, mzn_path=default_mzn_path):
        pymzn.config['minizinc'] = mzn_path
        self.log = log  # FIXME what to log (besides forwarding it to MznModelGenerator) here?

    def _run_placement_model(self, mzn_model, mzn_model_data={}):
        """
        Runs the minizinc placement model and post process the result
        Note: in this revision we use the 'item' output mode from pymzn.minizinc since it ease
        post processing of the solutions when we use enumerations in mzn_model
        Note: minizinc does not support '-' in identifiers and therefore we convert back from use of '_' when we
        process the result

        :param mzn_model: a minizinc model as str (note: may also be path to .mzn file)
        :param mzm_model_data: minizinc model data dictionary (typically not used with our models)
        :return: list of dicts formatted as {'vimAccountId': '<account id>', 'member-vnf-index': <'index'>}
        or formatted as [{}] if unsatisfiable model FIXME should probably be an exception!
        """
        solns = pymzn.minizinc(mzn_model, data=mzn_model_data, output_mode='item')

        # FIXME what if unsatisfiable?
        if 'UNSATISFIABLE' in str(solns):
            return [{}]

        # FIXME is there a need to consider other alternatives besides the first
        solns_as_str = str(solns[0])

        # make it easier to extract the desired information by cleaning from newline, whitespace etc.
        solns_as_str = solns_as_str.replace('\n', '').replace(' ', '').rstrip(';')

        vnf_vim_mapping = (e.split('=') for e in solns_as_str.split(';'))
        res = [{'vimAccountId': e[1].replace('_', '-'), 'member-vnf-index': str(e[0][-1:])} for e in vnf_vim_mapping]
        return res

    def do_placement_computation(self, nspd):
        """
        Orchestrates the placement computation

        :param nspd: placement data
        :return: see _run_placement_model
        """
        mzn_model = MznModelGenerator(self.log).create_model(nspd)

        return self._run_placement_model(mzn_model=mzn_model.render_thyself_as_str())


class MznModelGenerator(object):
    '''
    Has the capability to generate minizinc models from information contained in
    NsPlacementData objects. Uses jinja2 as templating language for the model
    
    FIXME - need to decide file system location for template (and possibly model in target system)
    '''
    default_j2_templateold = 'osm_pla_static_template.j2'
    default_j2_template = "osm_pla_dynamic_template.j2"
    template_search_path = ['osm_pla/placement', '../placement']  # FIXME need another location eventually

    def __init__(self, log):
        '''
        Constructor
        '''
        self.log = log  # FIXME we do not log anything so far

    def create_model(self, ns_placement_data):
        '''
        Creates a minizinc model according to the content of nspd
        
        nspd - NSPlacementData
        
        return MZNModel
        '''
        mzn_model_template = self._load_jinja_template()
        mzn_model = MznModel(mzn_model_template.render(ns_placement_data))
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
        ''' return a str representation of the minizinc model'''
        return self._model


class NsPlacementDataFactory(object):
    """
    process information an network service and applicable network infrastructure resources in order to produce
    information tailored for the minizinc model code generator
    """

    def __init__(self, vim_accounts_info, vnf_prices, nsd, pop_pil_info):
        """
        :param vim_accounts_info: a dictionary with vim url as key and id as value, we add a unique index to it for use
        in the mzn array constructs
        :param vnf_prices: a dictionary with 'vnfd-id-ref' as key and a dictionary with vim_urls: cost as value
        :param nsd: FIXME
        :param pop_pil_info: FIXME
        """
        import itertools
        next_idx = itertools.count()
        self._vim_accounts_info = {k: {'id': v, 'idx': next(next_idx)} for k, v in vim_accounts_info.items()}
        self._vnf_prices = vnf_prices
        self._nsd = nsd
        self._pop_pil_info = pop_pil_info

        # self._nspd = NsPlacementData() FIXME

    def _produce_trp_link_characteristics_data(self, characteristics):
        """
        :param characteristics: one of  {pil_latency, pil_price, pil_jitter}
        :return: 2d array of requested trp_link characteristics data

        FIXME decide on exception (should probably be an assert)
        """
        if characteristics not in {'pil_latency', 'pil_price'}:
            raise Exception('characteristic \'{}\' not supported'.format(characteristics))
        num_vims = len(self._vim_accounts_info)
        trp_link_characteristics = [[0 for _ in range(num_vims)] for _ in range(num_vims)]
        for pil in [_ for _ in self._pop_pil_info['pil']]:
            url1 = pil['pil_endpoints'][0]
            url2 = pil['pil_endpoints'][1]
            # only consider links between applicable vims
            if url1 in self._vim_accounts_info and url2 in self._vim_accounts_info:
                idx1 = self._vim_accounts_info[url1]['idx']
                idx2 = self._vim_accounts_info[url2]['idx']
                trp_link_characteristics[idx1][idx2] = pil[characteristics]
                trp_link_characteristics[idx2][idx1] = pil[characteristics]

        return trp_link_characteristics

    def _produce_vld_desc(self):
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

        return vld_desc

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
        return ns_desc

    def create_ns_placement_data(self):
        """populate NsPlacmentData object
        FIXME we are lacking jitter data in the yaml file
        """
        ns_placement_data = {'vim_accounts': [vim_data['id'].replace('-', '_') for
                                              vim_data in self._vim_accounts_info.values()],
                             'trp_link_latency': self._produce_trp_link_characteristics_data('pil_latency'),
                             'trp_link_price_list': self._produce_trp_link_characteristics_data('pil_price'),
                             'ns_desc': self._produce_ns_desc(), 'vld_desc': self._produce_vld_desc(),
                             'generator_data': {'file': __file__, 'time': datetime.datetime.now()}}

        return ns_placement_data


# class NsPlacementData2(object):
#     """
#     record like thingamajig
#     """
#
#
# class NsPlacementDataObsolete(object):
#     '''Container for service requirements and infrastructure data.
#
#     FIXME at the moment a dictionary matching the data to be sent to the static model.
#     Content directly added from factory. Wrapped in a class for expected future additions
#     of behavior. '''
#
#     def __init__(self):
#         self._mzn_model_data = {}
#
#
# class PlacementResultObsolete(object):
#     '''container for placement result
#
#     '''
#
#     def __init__(self, placement):
#         '''Note: single placement. In case multiple solutions are found
#         the selection of placement is done elsewhere'''
#         self._placement = placement
#
#     def render_thyself_as_kafka_payload(self):
#         vnf_field_content = ', '.join(
#             "{{'vimAccountId': '{}'', 'member-vnf-index': '{}'}}".format(vim, vnf) for vnf, vim in
#             self._placement.items())
#         return 'vnf: [' + vnf_field_content + ']'

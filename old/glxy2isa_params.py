#!/usr/bin/env python
"""Map galaxy input JSON to something cli.py and ISA API can consume"""

import json
import sys
import os

parameters_file = sys.argv[1]
out_dir = sys.argv[2]
with open(parameters_file) as fp:
    tool_params = json.load(fp)
    print(json.dumps(tool_params, indent=4))
if tool_params is None:
    raise IOError('Could not load tool parameters file')
sample_and_assay_plans = {
    "sample_types": [],
    "group_size": 1,
    "sample_plan": [],
    "sample_qc_plan": [],
    "assay_types": [],
    "assay_plan": []
}
for sample_plan_params in tool_params[
        'sampling_and_assay_plans']['sample_record_series']:
    sample_plan = {
        'sample_type': sample_plan_params['sample_type']['sample_type'],
        'sampling_size': sample_plan_params['sample_size']
    }
    sample_and_assay_plans['sample_types'].append(
        sample_plan['sample_type'])
    sample_and_assay_plans['sample_plan'].append(sample_plan)

    if 'assay_record_series' in sample_plan_params.keys():
        for assay_plan_params in sample_plan_params['assay_record_series']:
            tt = assay_plan_params['assay_type']['assay_type']
            if tt == 'mass spectrometry':
                raise NotImplementedError(
                    'MS assays not yet supported, try NMR first')
                # try:
                #     chromatography_instruments = [x['inj_mod_cond']['chromato']
                #                                   for x in assay_plan_params[
                #                                       'assay_type'][
                #                                       'inj_mod_series']]
                # except KeyError:
                #     chromatography_instruments = []
                # assay_type = {
                #     'topology_modifiers': {
                #         'technical_replicates': 1,
                #         'acquisition_modes': [x['fraction'] for x in
                #                               assay_plan_params['assay_type'][
                #                                   'samp_frac_series']],
                #         'instruments': [x['inj_mod_cond']['instrument'] for x in
                #                         assay_plan_params['assay_type'][
                #                             'inj_mod_series']],
                #         'injection_modes': [x['inj_mod_cond']['inj_mod'] for x
                #                             in assay_plan_params['assay_type'][
                #                                 'inj_mod_series']],
                #         'chromatography_instruments': chromatography_instruments
                #     },
                #     'technology_type': tt,
                #     'measurement_type': 'metabolite profiling'
                # }
            elif tt == 'nmr spectroscopy':
                assay_type = {
                    'topology_modifiers': {
                        'technical_replicates': assay_plan_params['assay_type'][
                            'acq_mod_cond']['technical_replicates'],
                        'acquisition_modes': [
                            assay_plan_params['assay_type']['acq_mod_cond']['acq_mod']],
                        'instruments': [
                            assay_plan_params['assay_type']['acq_mod_cond']['nmr_instrument']],
                        'injection_modes': [],
                        'pulse_sequences': [
                            assay_plan_params['assay_type']['acq_mod_cond']['pulse_seq']]
                    },
                    'technology_type': 'nmr spectroscopy',
                    'measurement_type': 'metabolite profiling'
                }
            else:
                raise NotImplementedError('Only NMR and MS assays supported')
            assay_plan = {
                "sample_type": sample_plan['sample_type'],
                "assay_type": assay_type
            }
            sample_and_assay_plans['assay_types'].append(assay_type)
            sample_and_assay_plans['assay_plan'].append(assay_plan)
    for qc_plan_params in tool_params['qc_plan']['qc_record_series']:
        if 'dilution' in qc_plan_params['qc_type_conditional']['qc_type']:
            raise NotImplementedError('Dilution series not yet implemented')
        else:
            qc_plan = {
                'sample_type': qc_plan_params['qc_type_conditional']['qc_type'],
                'injection_interval': qc_plan_params['qc_type_conditional'][
                    'injection_freq']
            }
        sample_and_assay_plans['sample_qc_plan'].append(qc_plan)
sample_and_assay_plans['group_size'] = tool_params['treatment_plan'][
    'study_group_size']
with open(os.path.join(out_dir, 'sample_assay_plans.json'), 'w') as out_fp:
    json.dump(sample_and_assay_plans, out_fp, indent=4)
with open(os.path.join(out_dir, 'study_info.json'), 'w') as out_fp:
    json.dump(tool_params['study_overview'], out_fp, indent=4)
with open(os.path.join(out_dir, 'treatment_plan.json'), 'w') as out_fp:
    json.dump(tool_params['treatment_plan'], out_fp, indent=4)
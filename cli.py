#!/usr/bin/env python3
"""Commandline interface for running ISA API create mode"""
import click
import datetime
import io
import json
import os
import uuid

from isatools import isatab
from isatools.create.models import (
    TreatmentSequence,
    INTERVENTIONS,
    BASE_FACTORS,
    TreatmentFactory,
    IsaModelObjectFactory,
    SampleAssayPlanDecoder
)
from isatools.model import Investigation, Person


def map_galaxy_to_isa_create_json(tool_params):
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
            'sample_type': sample_plan_params['sample_type']['sample_type']
            if not sample_plan_params['sample_type']['sample_type'] == 'user_defined'
            else sample_plan_params['sample_type']['sample_type_ud'],
            'sampling_size': sample_plan_params['sample_size']
        }
        sample_and_assay_plans['sample_types'].append(
            sample_plan['sample_type'])
        sample_and_assay_plans['sample_plan'].append(sample_plan)

        if 'assay_record_series' in sample_plan_params.keys():
            for assay_plan_params in sample_plan_params['assay_record_series']:
                tt = assay_plan_params['assay_type']['assay_type']
                if tt == 'nmr spectroscopy':
                    assay_type = {
                        'topology_modifiers': {
                            'technical_replicates':
                                assay_plan_params['assay_type'][
                                    'acq_mod_cond']['technical_replicates'],
                            'acquisition_modes': [
                                assay_plan_params['assay_type']['acq_mod_cond'][
                                    'acq_mod']],
                            'instruments': [
                                assay_plan_params['assay_type']['acq_mod_cond'][
                                    'nmr_instrument']],
                            'injection_modes': [],
                            'pulse_sequences': [
                                assay_plan_params['assay_type']['acq_mod_cond'][
                                    'pulse_seq']]
                        },
                        'technology_type': 'nmr spectroscopy',
                        'measurement_type': 'metabolite profiling'
                    }
                    assay_plan = {
                        "sample_type": sample_plan['sample_type'],
                        "assay_type": assay_type
                    }
                    sample_and_assay_plans['assay_types'].append(assay_type)
                    sample_and_assay_plans['assay_plan'].append(assay_plan)
                elif tt == 'mass spectrometry':
                    if len(assay_plan_params['assay_type']['samp_frac_series']) > 0:
                        raise NotImplementedError('Sample fractions not supported')
                    if len(assay_plan_params['assay_type']['inj_mod_series']) > 0:
                        for inj_mod in assay_plan_params['assay_type']['inj_mod_series']:
                            for acq_mod in inj_mod['inj_mod_cond']['acq_mod_series']:
                                try:
                                    chromato = inj_mod['chromato']
                                except KeyError:
                                    chromato = None
                                try:
                                    chromato_col = inj_mod['chromato_col']
                                except KeyError:
                                    chromato_col = None
                                if chromato_col:
                                    print('Chromatograpy column not yet supported; ignoring in serialization')
                                assay_type = {
                                    'topology_modifiers': {
                                        'technical_replicates': acq_mod['technical_replicates'],
                                        'acquisition_modes': [acq_mod['acq_mod']],
                                        'instruments': [inj_mod['inj_mod_cond']['instrument']],
                                        'injection_modes': [inj_mod['inj_mod_cond']['inj_mod']],
                                        'chromatography_instruments': [chromato] if chromato else []
                                    },
                                    'technology_type': tt,
                                    'measurement_type': 'metabolite profiling'
                                }
                                assay_plan = {
                                    "sample_type": sample_plan['sample_type'],
                                    "assay_type": assay_type
                                }
                                sample_and_assay_plans['assay_types'].append(assay_type)
                                sample_and_assay_plans['assay_plan'].append(assay_plan)
                else:
                    raise NotImplementedError('Only NMR and MS assays supported')
        for qc_plan_params in tool_params['qc_plan']['qc_record_series']:
            if 'dilution' in qc_plan_params['qc_type_conditional']['qc_type']:
                raise NotImplementedError('Dilution series not yet implemented')
            else:
                qc_plan = {
                    'sample_type': qc_plan_params['qc_type_conditional'][
                        'qc_type'],
                    'injection_interval': qc_plan_params['qc_type_conditional'][
                        'injection_freq']
                }
            sample_and_assay_plans['sample_qc_plan'].append(qc_plan)
    sample_and_assay_plans['group_size'] = tool_params['treatment_plan'][
        'study_group_size']

    return sample_and_assay_plans, tool_params['study_overview'], \
            tool_params['treatment_plan']


@click.command()
@click.option('--galaxy_parameters_file',
              help='Path to JSON file containing input Galaxy JSON',
              type=click.File('r'))
@click.option('--sample_assay_plans_file',
              help='Path to JSON file containing input Sample Assay Plan JSON',
              type=click.File('r'))
@click.option('--study_info_file',
              help='Path to JSON file containing input study overview',
              type=click.File('r'))
@click.option('--treatment_plans_file',
              help='Path to JSON file containing treatment plan info',
              type=click.File('r'))
@click.option('--target_dir', help='Output path to write', nargs=1,
              type=click.Path(exists=True), default='./')
def create_from_plan_parameters(
        galaxy_parameters_file, sample_assay_plans_file, study_info_file,
        treatment_plans_file, target_dir):
    decoder = SampleAssayPlanDecoder()
    if galaxy_parameters_file:
        galaxy_parameters = json.load(galaxy_parameters_file)
        sample_and_assay_plans, study_info, treatment_plan_params = \
            map_galaxy_to_isa_create_json(galaxy_parameters)
        plan = decoder.load(io.StringIO(json.dumps(sample_and_assay_plans)))
    elif sample_assay_plans_file and study_info_file and treatment_plans_file:
        plan = decoder.load(sample_assay_plans_file)
        study_info = json.load(study_info_file)
        treatment_plan_params = json.load(treatment_plans_file)
    else:
        raise IOError('Wrong parameters provided')

    study_type = treatment_plan_params['study_type_cond']['study_type']
    if study_type != 'intervention':
        raise NotImplementedError('Only supports Intervention studies')

    single_or_multiple = treatment_plan_params['study_type_cond']['one_or_more']['single_or_multiple']
    if single_or_multiple == 'multiple':
        raise NotImplementedError(
            'Multiple treatments not yet implemented. Please select Single')

    intervention_type = treatment_plan_params['study_type_cond']['one_or_more'][
        'intervention_type']['select_intervention_type']
    if intervention_type != 'chemical intervention':
        raise NotImplementedError(
            'Only Chemical Interventions supported at this time')

    treatment_factory = TreatmentFactory(
        intervention_type=INTERVENTIONS['CHEMICAL'], factors=BASE_FACTORS)
    agent_levels = treatment_plan_params['study_type_cond']['one_or_more'][
        'intervention_type']['agent'].split(',')
    for agent_level in agent_levels:
        treatment_factory.add_factor_value(BASE_FACTORS[0], agent_level.strip())
    dose_levels = treatment_plan_params['study_type_cond']['one_or_more'][
        'intervention_type']['intensity'].split(',')
    for dose_level in dose_levels:
        treatment_factory.add_factor_value(BASE_FACTORS[1], dose_level.strip())
    duration_of_exposure_levels = treatment_plan_params[
        'study_type_cond']['one_or_more']['intervention_type'][
        'duration'].split(',')
    for duration_of_exposure_level in duration_of_exposure_levels:
        treatment_factory.add_factor_value(BASE_FACTORS[2],
                                           duration_of_exposure_level.strip())
    treatment_sequence = TreatmentSequence(
        ranked_treatments=treatment_factory.compute_full_factorial_design())
    isa_object_factory = IsaModelObjectFactory(plan, treatment_sequence)
    s = isa_object_factory.create_assays_from_plan()
    contact = Person()
    contact.affiliation = study_info['study_pi_affiliation']
    contact.last_name = study_info['study_pi_last_name']
    contact.email = study_info['study_pi_email']
    contact.first_name = study_info['study_pi_first_name']
    s.contacts = [contact]
    s.description = study_info['study_description']
    s.filename = 's_study.txt'
    s.title = 'ISA created {}'.format(datetime.datetime.now().isoformat())
    s.identifier = 'ISA-{}'.format(uuid.uuid4().hex[:8])

    i = Investigation()
    i.contacts = [contact]
    i.description = s.description
    i.title = s.title
    i.identifier = s.identifier

    i.studies = [s]
    isatab.dump(isa_obj=i, output_path=target_dir,
                i_file_name='i_investigation.txt')

    for assay in s.assays:
        for data_file in assay.data_files:
            data_file_path = os.path.join(target_dir, data_file.filename)
            with open(data_file_path, 'a'):
                os.utime(data_file_path, None)


if __name__ == '__main__':
    create_from_plan_parameters()

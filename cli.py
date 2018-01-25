#!/usr/bin/env python3
"""Commandline interface for running ISA API create mode"""
import click
import json
import logging
import sys

from isatools import isatab
from isatools.create.models import (
    TreatmentSequence,
    INTERVENTIONS,
    BASE_FACTORS,
    TreatmentFactory,
    IsaModelObjectFactory,
    AssayType,
    AssayTopologyModifiers,
    SampleAssayPlan
)
from isatools.model import Investigation, Person


class SampleAssayPlanDecoder(object):

    def __init__(self):
        self.dna_micro_key_signature = ('technical_replicates', 'array_designs')
        self.dna_seq_key_signature = (
            'technical_replicates', 'distinct_libraries', 'instruments')
        self.ms_key_signature = (
            'technical_replicates', 'injection_modes', 'acquisition_modes',
            'instruments', 'chromatography_instruments')
        self.nmr_key_signature = (
            'technical_replicates', 'injection_modes', 'acquisition_modes',
            'pulse_sequences', 'instruments')

    def load_top_mods(self, top_mods_json):
        # do a bit of duck-typing
        top_mods = None
        key_signature = top_mods_json.keys()
        if set(self.dna_micro_key_signature).issubset(key_signature):
            top_mods = AssayTopologyModifiers()
            top_mods.array_designs = set(
                map(lambda x: x, top_mods_json['array_designs']))
            top_mods.technical_replicates = top_mods_json[
                'technical_replicates']
        elif set(self.dna_seq_key_signature).issubset(key_signature):
            top_mods = AssayTopologyModifiers()

            top_mods.distinct_libraries = top_mods_json['distinct_libraries']
            top_mods.technical_replicates = top_mods_json[
                'technical_replicates']
            top_mods.instruments = set(
                map(lambda x: x, top_mods_json['instruments']))
        elif set(self.ms_key_signature).issubset(key_signature):
            top_mods = AssayTopologyModifiers()
            top_mods.injection_modes = set(
                map(lambda x: x, top_mods_json['injection_modes']))
            top_mods.acquisition_modes = set(
                map(lambda x: x, top_mods_json['acquisition_modes']))
            top_mods.technical_replicates = top_mods_json[
                'technical_replicates']
            top_mods.instruments = set(
                map(lambda x: x, top_mods_json['instruments']))
            top_mods.chromatography_instruments = set(
                map(lambda x: x, top_mods_json['chromatography_instruments']))
        elif set(self.nmr_key_signature).issubset(key_signature):
            top_mods = AssayTopologyModifiers()
            top_mods.injection_modes = set(
                map(lambda x: x, top_mods_json['injection_modes']))
            top_mods.acquisition_modes = set(
                map(lambda x: x, top_mods_json['acquisition_modes']))
            top_mods.pulse_sequences = set(
                map(lambda x: x, top_mods_json['pulse_sequences']))
            top_mods.technical_replicates = top_mods_json[
                'technical_replicates']
            top_mods.instruments = set(
                map(lambda x: x, top_mods_json['instruments']))
        return top_mods

    def load_assay_type(self, assay_type_json):
        assay_type = AssayType(
            measurement_type=assay_type_json['measurement_type'],
            technology_type=assay_type_json['technology_type'],
            topology_modifiers=self.load_top_mods(
                assay_type_json['topology_modifiers']
            )
        )
        return assay_type

    def load(self, fp):
        sample_assay_plan_json = json.load(fp)

        sample_assay_plan = SampleAssayPlan(
            group_size=sample_assay_plan_json['group_size'],
        )

        for sample_type in sample_assay_plan_json['sample_types']:
            sample_assay_plan.add_sample_type(sample_type=sample_type)
        for sample_plan_record in sample_assay_plan_json['sample_plan']:
            sample_assay_plan.add_sample_plan_record(
                sample_type=sample_plan_record['sample_type'],
                sampling_size=sample_plan_record['sampling_size']
            )

        for assay_type in sample_assay_plan_json['assay_types']:
            sample_assay_plan.add_assay_type(
                assay_type=self.load_assay_type(assay_type))
        for assay_plan_record in sample_assay_plan_json['assay_plan']:
            sample_assay_plan.add_assay_plan_record(
                sample_type=assay_plan_record['sample_type'],
                assay_type=self.load_assay_type(assay_plan_record['assay_type'])
            )

        for sample_qc_plan_record in sample_assay_plan_json['sample_qc_plan']:
            sample_assay_plan.add_sample_qc_plan_record(
                material_type=sample_qc_plan_record['sample_type'],
                injection_interval=sample_qc_plan_record['injection_interval']
            )

        return sample_assay_plan


@click.command()
@click.option('--sample_assay_plans_file',
              help='Path to JSON file containing input Sample Assay Plan JSON',
              nargs=1, type=str, default='sample_assay_plans.json')
@click.option('--study_info_file',
              help='Path to JSON file containing input study overview',
              nargs=1, type=str, default='study_info_file.json')
@click.option('--treatment_plans_file',
              help='Path to JSON file containing treatment plan info',
              nargs=1, type=str, default='treatment_plan.json')
@click.option('--target_dir', help='Output path to write', nargs=1, type=str,
              default='/')
def create_from_plan_parameters(sample_assay_plans_file, study_info_file,
                                treatment_plans_file, target_dir):
    decoder = SampleAssayPlanDecoder()
    with open(sample_assay_plans_file) as fp:
        plan = decoder.load(fp)
    with open(study_info_file) as fp:
        study_info = json.load(fp)
    with open(treatment_plans_file) as fp:
        treatment_plan_params = json.load(fp)
    treatment_group_size = treatment_plan_params['study_group_size']

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

    i = Investigation()
    i.contacts = [contact]
    i.description = s.description

    i.studies = [s]
    isatab.dump(isa_obj=i, output_path=target_dir,
                i_file_name='i_investigation.txt')


if __name__ == '__main__':
    try:
        create_from_plan_parameters()
    except Exception as e:
        logger = logging.getLogger()
        logger.fatal(e)
        sys.exit(e.code if hasattr(e, 'code') else 99)

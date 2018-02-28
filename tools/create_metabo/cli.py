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
    AssayType,
    MSTopologyModifiers,
    MSInjectionMode,
    MSAcquisitionMode,
    SampleAssayPlan,
    Study,
    SampleQCBatch,
    Characteristic,
    OntologyAnnotation
)
from isatools.model import Investigation, Person


def map_galaxy_to_isa_create(tool_params):
    print(json.dumps(tool_params, indent=4))
    sample_assay_plan = SampleAssayPlan()
    for sample_plan_params in tool_params['sampling_and_assay_plans'][
            'sample_record_series']:
        sample_type = sample_plan_params['sample_type']['sample_type'] if \
            not sample_plan_params['sample_type']['sample_type'] == \
            'user_defined' else sample_plan_params[
            'sample_type']['sample_type_ud']
        sample_assay_plan.add_sample_type(sample_type)
        sample_size = sample_plan_params['sample_size']
        sample_assay_plan.group_size = sample_size
        sample_assay_plan.add_sample_plan_record(sample_type, sample_size)
        if 'assay_record_series' in sample_plan_params.keys():
            for assay_plan_params in sample_plan_params['assay_record_series']:
                tt = assay_plan_params['assay_type']['assay_type']
                if tt == 'nmr spectroscopy':
                    nmr_assay_type = AssayType(
                        measurement_type='metabolite profiling',
                        technology_type='nmr spectroscopy')
                    from isatools.create.models import NMRTopologyModifiers
                    nmr_top_mods = NMRTopologyModifiers()
                    nmr_top_mods.technical_replicates = assay_plan_params[
                        'assay_type']['acq_mod_cond']['technical_replicates']
                    nmr_top_mods.acquisition_modes.add(
                        assay_plan_params['assay_type']['acq_mod_cond'][
                            'acq_mod'])
                    nmr_top_mods.instruments.add('{} {}'.format(
                        assay_plan_params['assay_type']['acq_mod_cond'][
                                    'nmr_instrument'],assay_plan_params['assay_type']['acq_mod_cond'][
                                    'magnet']))
                    nmr_top_mods.pulse_sequences.add(
                        assay_plan_params['assay_type']['acq_mod_cond'][
                            'pulse_seq']
                    )
                    nmr_top_mods.magnet_power = assay_plan_params['assay_type']['acq_mod_cond'][
                            'magnet']
                    nmr_assay_type.topology_modifiers = nmr_top_mods
                    sample_assay_plan.add_assay_type(nmr_assay_type)
                    sample_assay_plan.add_assay_plan_record(sample_type,
                                                            nmr_assay_type)
                elif tt == 'mass spectrometry':
                    ms_assay_type = AssayType(
                        measurement_type='metabolite profiling',
                        technology_type='mass spectrometry')
                    ms_assay_type.topology_modifiers = MSTopologyModifiers(
                        sample_fractions=set(
                            map(lambda x: x['fraction'], assay_plan_params[
                                'assay_type']['samp_frac_series'])))
                    injection_modes = ms_assay_type.topology_modifiers.injection_modes
                    if len(assay_plan_params['assay_type']['inj_mod_series']) > 0:
                        for inj_mod in assay_plan_params['assay_type']['inj_mod_series']:
                            injection_mode = MSInjectionMode(
                                injection_mode=inj_mod['inj_mod_cond']['inj_mod'],
                                ms_instrument=inj_mod['inj_mod_cond']['instrument']
                            )
                            if inj_mod['inj_mod_cond']['inj_mod'] in ('LC', 'GC'):
                                injection_mode.chromatography_instrument = \
                                    inj_mod['inj_mod_cond']['chromato']
                                if inj_mod['inj_mod_cond']['inj_mod'] == 'LC':
                                    injection_mode.chromatography_column = \
                                        inj_mod['inj_mod_cond']['chromato_col']
                            injection_modes.add(injection_mode)
                            for acq_mod in inj_mod['inj_mod_cond']['acq_mod_series']:
                                injection_mode.acquisition_modes.add(
                                    MSAcquisitionMode(
                                        acquisition_method=acq_mod['acq_mod'],
                                        technical_repeats=acq_mod['technical_replicates']
                                    )
                                )
                    sample_assay_plan.add_assay_type(ms_assay_type)
                    sample_assay_plan.add_assay_plan_record(sample_type, ms_assay_type)
                else:
                    raise NotImplementedError('Only MS assays supported')
        for qc_plan_params in tool_params['qc_plan']['qc_record_series']:
            if 'interval series' == qc_plan_params['qc_type_conditional']['qc_type']:
                sample_assay_plan.add_sample_qc_plan_record(
                    material_type=qc_plan_params['qc_type_conditional']['qc_material_type'],
                    injection_interval=qc_plan_params['qc_type_conditional']['injection_freq'])
            elif 'dilution series' in qc_plan_params['qc_type_conditional']['qc_type']:
                raise NotImplementedError(
                    'Dilution series QCs not yet supported!')
                # batch = SampleQCBatch()
                # batch.material = qc_plan_params[
                #     'qc_type_conditional']['qc_material_type']
                # for value in range(qc_plan_params['qc_type_conditional']['start_val'],
                #                    qc_plan_params['qc_type_conditional']['stop_val'],
                #                    qc_plan_params['qc_type_conditional']['step']):
                #     characteristic = Characteristic(
                #         category=OntologyAnnotation(term='charac_name'), value=value)
                #     batch.characteristic_values.append(characteristic)
                # if 'pre-run' in qc_plan_params['qc_type_conditional']['qc_type']:
                #     sample_assay_plan.pre_run_batch = batch
                # elif 'post-run' in qc_plan_params['qc_type_conditional']['qc_type']:
                #     sample_assay_plan.post_run_batch = batch
    sample_assay_plan.group_size = tool_params['treatment_plan']['study_group_size']
    return sample_assay_plan, tool_params['study_overview'], tool_params['treatment_plan']


@click.command()
@click.option('--galaxy_parameters_file',
              help='Path to JSON file containing input Galaxy JSON',
              type=click.File())
@click.option('--target_dir', help='Output path to write', nargs=1,
              type=click.Path(exists=True), default='./')
def create_from_plan_parameters(galaxy_parameters_file, target_dir):
    if galaxy_parameters_file:
        galaxy_parameters = json.load(galaxy_parameters_file)
        print(json.dumps(galaxy_parameters, indent=4))
        plan, study_info, treatment_plan_params = \
            map_galaxy_to_isa_create(galaxy_parameters)
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
    if len(plan.sample_plan) == 0:
        print('No sample plan defined')
    if len(plan.assay_plan) == 0:
        print('No assay plan defined')
    isa_object_factory = IsaModelObjectFactory(plan, treatment_sequence)
    if len(plan.sample_plan) == 0:
        s = Study()
    else:
        s = isa_object_factory.create_assays_from_plan()
    contact = Person()
    contact.affiliation = study_info['study_pi_affiliation']
    contact.last_name = study_info['study_pi_last_name']
    contact.email = study_info['study_pi_email']
    contact.first_name = study_info['study_pi_first_name']
    s.contacts = [contact]
    s.description = study_info['study_description']
    s.filename = 's_study.txt'
    s.title = study_info['study_title']
    s.identifier = 'ISA-{}'.format(uuid.uuid4().hex[:8])

    i = Investigation()
    i.contacts = [contact]
    i.description = ""
    i.title = "Investigation"
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

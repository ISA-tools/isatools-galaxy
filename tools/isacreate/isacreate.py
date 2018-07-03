#!/usr/bin/env python3
"""Commandline interface for running ISA API create mode (metabo flavoured)"""
import click
import os
import uuid
import re

from isatools import isatab
from isatools.create.models import *
from isatools.model import Investigation, Person


@click.command()
@click.option('--galaxy_parameters_file',
              help='Path to JSON file containing input Galaxy JSON',
              type=click.File())
@click.option('--target_dir', help='Output path to write', nargs=1,
              type=click.Path(exists=True), default='./')
def create_from_galaxy_parameters(galaxy_parameters_file, target_dir):

    def _create_treatment_sequence(galaxy_parameters):
        treatment_plan = galaxy_parameters['treatment_plan']
        study_type = treatment_plan['study_type']['study_type_selector']

        if 'intervention' not in study_type:
            raise NotImplementedError('Only supports Intervention studies')
        try:
            single_or_multiple = treatment_plan['study_type']['balanced'][
                'multiple_interventions']
        except KeyError:
            single_or_multiple = \
                treatment_plan['study_type']['multiple_interventions'][
                    'multiple_interventions_selector']
        if single_or_multiple == 'multiple':
            raise NotImplementedError(
                'Multiple treatments not yet implemented. Please select Single')

        if study_type == 'full_factorial_intervention':
            intervention_type = \
            treatment_plan['study_type']['multiple_interventions'][
                'intervention_type']['intervention_type_selector']
            if intervention_type == 'chemical intervention':
                interventions = INTERVENTIONS['CHEMICAL']
            elif intervention_type == 'dietary intervention':
                interventions = INTERVENTIONS['DIET']
            elif intervention_type == 'behavioural intervention':
                interventions = INTERVENTIONS['BEHAVIOURAL']
            elif intervention_type == 'biological intervention':
                interventions = INTERVENTIONS['BIOLOGICAL']
            elif intervention_type == 'surgical intervention':
                interventions = INTERVENTIONS['SURGICAL']
            elif intervention_type == 'radiological intervention':  # not in tool yet
                interventions = INTERVENTIONS['RADIOLOGICAL']
            else:  # default to chemical
                interventions = INTERVENTIONS['CHEMICAL']
            treatment_factory = TreatmentFactory(
                intervention_type=interventions, factors=BASE_FACTORS)

            # Treatment Sequence
            agent_levels = \
            treatment_plan['study_type']['multiple_interventions'][
                'intervention_type']['agent'].split(',')
            for agent_level in agent_levels:
                treatment_factory.add_factor_value(BASE_FACTORS[0],
                                                   agent_level.strip())
            dose_levels = \
            treatment_plan['study_type']['multiple_interventions'][
                'intervention_type']['intensity'].split(',')
            for dose_level in dose_levels:
                treatment_factory.add_factor_value(BASE_FACTORS[1],
                                                   dose_level.strip())
            duration_of_exposure_levels = treatment_plan[
                'study_type']['multiple_interventions']['intervention_type'][
                'duration'].split(',')
            for duration_of_exposure_level in duration_of_exposure_levels:
                treatment_factory.add_factor_value(BASE_FACTORS[2],
                                                   duration_of_exposure_level.strip())
            treatment_sequence = TreatmentSequence(
                ranked_treatments=treatment_factory.compute_full_factorial_design())
            return treatment_sequence

        elif study_type == 'fractional_factorial_intervention':
            intervention_type = \
                treatment_plan['study_type_cond']['balanced_or_unbalanced'][
                    'one_or_more']['select_intervention_type']
            treatments = set()
            study_factors = [StudyFactor(name=x.strip()) for x in
                             treatment_plan['study_type'][
                                 'balanced']['multiple_interventions'][
                                 'study_factors'].split(',')]
            for group in \
                    treatment_plan['study_type']['balanced'][
                        'multiple_interventions']['factor_value_groups']:
                factor_values = ()
                for x, y in zip(study_factors, [x.strip() for x in
                                                group['factor_values'].split(
                                                    ',')]):
                    factor_value = FactorValue(factor_name=x, value=y)
                    factor_values = factor_values + (factor_value,)
                treatment = Treatment(treatment_type=intervention_type,
                                      factor_values=factor_values)
                treatments.add(treatment)
            treatment_sequence = TreatmentSequence(ranked_treatments=treatments)
            return treatment_sequence

    def _create_sample_plan(sample_assay_plan, sample_plan_record):

        def _create_nmr_assay_type(assay_plan_record):
            nmr_assay_type = AssayType(
                measurement_type='metabolite profiling',
                technology_type='nmr spectroscopy')
            nmr_top_mods = NMRTopologyModifiers()
            nmr_top_mods.technical_replicates = assay_plan_record[
                'assay_type']['acquisition_mode']['technical_replicates']
            nmr_top_mods.acquisition_modes.add(
                assay_plan_record['assay_type']['acquisition_mode']['acquisition_mode_selector'])
            nmr_top_mods.instruments.add('{} {}'.format(
                assay_plan_record['assay_type']['acquisition_mode']['nmr_instrument'],
                assay_plan_record['assay_type']['acquisition_mode']['magnet']))
            nmr_top_mods.pulse_sequences.add(
                assay_plan_record['assay_type']['acquisition_mode']['pulse_sequence']
            )
            nmr_top_mods.magnet_power = \
                assay_plan_record['assay_type']['acquisition_mode']['magnet']
            nmr_assay_type.topology_modifiers = nmr_top_mods
            return nmr_assay_type

        def _create_ms_assay_type(assay_plan_record):
            ms_assay_type = AssayType(
                measurement_type='metabolite profiling',
                technology_type='mass spectrometry')
            ms_assay_type.topology_modifiers = MSTopologyModifiers(
                sample_fractions=set(map(lambda x: x['sample_fraction'], assay_plan_record['assay_type']['sample_fractions'])))
            injection_modes = ms_assay_type.topology_modifiers.injection_modes
            if len(assay_plan_record['assay_type']['injections']) > 0:
                for inj_mod in assay_plan_record['assay_type']['injections']:
                    injection_mode = MSInjectionMode(
                        injection_mode=inj_mod['injection_mode']['injection_mode_selector'],
                        ms_instrument=inj_mod['injection_mode']['instrument']
                    )
                    if inj_mod['injection_mode']['injection_mode_selector'] in ('LC', 'GC'):
                        injection_mode.chromatography_instrument = inj_mod['injection_mode']['chromatography_instrument']
                    if inj_mod['injection_mode']['injection_mode_selector'] == 'LC':
                        injection_mode.chromatography_column = inj_mod['injection_mode']['chromatography_column']
                    injection_modes.add(injection_mode)
                    for acq_mod in inj_mod['injection_mode']['acquisitions']:
                        injection_mode.acquisition_modes.add(
                            MSAcquisitionMode(
                                acquisition_method=acq_mod['acquisition_mode'],
                                technical_repeats=acq_mod[
                                    'technical_replicates']
                            )
                        )
                        if inj_mod['injection_mode']['injection_mode_selector'] == 'GC':
                            for deriva in inj_mod['injection_mode'][
                                    'derivatizations']:
                                derivatization = deriva['derivatization']
                                if re.match('(.*?) \((.*?)\)', derivatization):
                                    matches = next(iter(
                                        re.findall('(.*?) \((.*?)\)',
                                                   derivatization)))
                                    term, ontoid = matches[0], matches[1]
                                    source_name, accession_id = \
                                    ontoid.split(':')[0], \
                                    ontoid.split(':')[1]
                                    source = OntologySource(name=source_name)
                                    derivatization = OntologyAnnotation(
                                        term=term, term_source=source,
                                        term_accession=accession_id)
                                injection_mode.derivatizations.add(
                                    derivatization)
            return ms_assay_type

        if sample_plan_record['material_type'] == 'user defined':
            sample_type = sample_plan_record['material_type']['sample_type_ud']
        else:
            sample_type = sample_plan_record['material_type']
            if re.match('(.*?) \((.*?)\)', sample_type):
                matches = next(iter(re.findall('(.*?) \((.*?)\)', sample_type)))
                term, ontoid = matches[0], matches[1]
                source_name, accession_id = ontoid.split(':')[0], \
                                            ontoid.split(':')[1]
                source = OntologySource(name=source_name)
                sample_type = OntologyAnnotation(term=term, term_source=source,
                                                 term_accession=accession_id)
        sample_assay_plan.add_sample_type(sample_type)
        sample_size = sample_plan_record['sample_collections']
        sample_assay_plan.add_sample_plan_record(sample_type, sample_size)
        for assay_plan_record in sample_plan_record['assay_plans']:
            tt = assay_plan_record['assay_type']['assay_type_selector']
            if tt == 'nmr':
                assay_type = _create_nmr_assay_type(assay_plan_record)
            elif tt == 'ms':
                assay_type = _create_ms_assay_type(assay_plan_record)
            else:
                raise NotImplementedError('Only MS and NMR assays supported')
            sample_assay_plan.add_assay_type(assay_type)
            sample_assay_plan.add_assay_plan_record(sample_type, assay_type)
        return sample_assay_plan

    def _inject_qcqa_plan(sample_assay_plan, qcqa_record):
        qc_type = qcqa_record['qc_type']['qc_type_selector']
        if qc_type == 'interval_series':
            material_type = qcqa_record['material_type']
            if re.match('(.*?) \((.*?)\)', material_type):
                matches = next(iter(re.findall('(.*?) \((.*?)\)', material_type)))
                term, ontoid = matches[0], matches[1]
                source_name, accession_id = ontoid.split(':')[0], \
                                            ontoid.split(':')[1]
                source = OntologySource(name=source_name)
                material_type = OntologyAnnotation(term=term, term_source=source,
                                                 term_accession=accession_id)
            sample_assay_plan.add_sample_qc_plan_record(
                material_type=material_type,
                injection_interval=qcqa_record['qc_type']['injection_frequency'])
        elif 'dilution_series' in qc_type:
            values = [int(x) for x in qcqa_record['qc_type']['values'].split(',')]
            material_type = qcqa_record['material_type']
            if re.match('(.*?) \((.*?)\)', material_type):
                matches = next(iter(re.findall('(.*?) \((.*?)\)', material_type)))
                term, ontoid = matches[0], matches[1]
                source_name, accession_id = ontoid.split(':')[0], \
                                            ontoid.split(':')[1]
                source = OntologySource(name=source_name)
                material_type = OntologyAnnotation(term=term, term_source=source,
                                                 term_accession=accession_id)
            batch = SampleQCBatch(material=material_type)
            for value in values:
                batch.characteristic_values.append(
                    Characteristic(category=OntologyAnnotation(
                        term='quantity'), value=value)
                )
            if 'pre' in qc_type:
                sample_assay_plan.pre_run_batch = batch
            elif 'post' in qc_type:
                sample_assay_plan.post_run_batch = batch
        else:
            raise NotImplementedError('QC type not recognized!')

        return sample_assay_plan

    # pre-generation checks
    if galaxy_parameters_file:
        galaxy_parameters = json.load(galaxy_parameters_file)
        # print(json.dumps(galaxy_parameters, indent=4))  # for debugging only
    else:
        raise IOError('Could not load Galaxy parameters file!')
    if target_dir:
        if not os.path.exists(target_dir):
            raise IOError('Target path does not exist!')
    if len(galaxy_parameters['sample_and_assay_planning']['sample_plans']) == 0:
        raise IOError('No Sampling plan specified')

    treatment_sequence = _create_treatment_sequence(galaxy_parameters)
    sample_assay_plan = SampleAssayPlan()
    for sample_plan_record in galaxy_parameters['sample_and_assay_planning'][
            'sample_plans']:
        _ = _create_sample_plan(sample_assay_plan, sample_plan_record)
    for qcqa_record in galaxy_parameters['qc_planning']['qc_plans']:
        _ = _inject_qcqa_plan(sample_assay_plan, qcqa_record)
    try:
        sample_assay_plan.group_size = \
            int(galaxy_parameters['treatment_plan']['study_type'][
                'multiple_interventions']['group_size'])
    except KeyError:
        try:
            sample_assay_plan.group_size = \
                int(galaxy_parameters['treatment_plan']['study_type'][
                    'balanced']['study_type']['group_size'])
        except KeyError:
            sample_assay_plan.group_size = \
                int(galaxy_parameters['treatment_plan']['study_type'][
                    'balanced']['multiple_interventions'][
                    'factor_value_groups'][0]['group_size'])

    study_info = galaxy_parameters['study_metadata']

    if len(sample_assay_plan.sample_plan) == 0:
        print('No sample plan defined')
    if len(sample_assay_plan.assay_plan) == 0:
        print('No assay plan defined')

    study_design = StudyDesign()
    study_design.add_single_sequence_plan(treatment_sequence, sample_assay_plan)
    isa_object_factory = IsaModelObjectFactory(study_design)
    if len(sample_assay_plan.sample_plan) == 0:
        s = Study()
    else:
        s = isa_object_factory.create_assays_from_plan()

    c = Person()
    c.affiliation = study_info.get('affiliation')
    c.last_name = study_info.get('last_name')
    c.email = study_info['email']
    c.first_name = study_info['first_name']
    s.contacts = [c]
    s.description = study_info['description']
    s.filename = 's_study.txt'
    s.title = study_info['title']
    s.identifier = 'ISA-{}'.format(uuid.uuid4().hex[:8])
    s.comments = [
        Comment(name='Consent Information (ICO:0000011)',
                value=study_info['study_consent']),
        Comment(name='Data Use Requirement (DUO:0000017)',
                value=study_info['study_use_condition'])
    ]
    i = Investigation()
    i.contacts = [c]
    i.description = ""
    i.title = "Investigation"
    i.identifier = s.identifier
    i.studies = [s]
    try:
        i.ontology_source_references = s.ontology_source_references
    except AttributeError:
        pass
    i.ontology_source_references.append(OntologySource(name='ICO'))
    i.ontology_source_references.append(OntologySource(name='DUO'))

    # generate empty data file stubs
    # for assay in s.assays:
    #     for data_file in assay.data_files:
    #         data_file_path = os.path.join(target_dir, data_file.filename)
    #         with open(data_file_path, 'a'):
    #             os.utime(data_file_path, None)

    def sanitize_filename(filename):
        filename = re.sub('[^\w\s-]', '_', filename).strip().lower()
        filename = re.sub('[-\s]+', '-', filename)
        return filename

    i.filename = sanitize_filename(i.filename)
    for s in i.studies:
        s.filename = sanitize_filename(s.filename)
        for a in s.assays:
            a.filename = sanitize_filename(a.filename)

    isatab.dump(isa_obj=i, output_path=target_dir)


if __name__ == '__main__':
    # TODO: Add flag to arguments to select create mode (e.g. metabo or genomics)
    create_from_galaxy_parameters()
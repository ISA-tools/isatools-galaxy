"""Commandline interface for running ISA API create mode"""
import click
import os

from isatools import isatab
from isatools.create.models import (
    SampleAssayPlan,
    TreatmentSequence,
    INTERVENTIONS,
    BASE_FACTORS,
    TreatmentFactory,
    IsaModelObjectFactory,
    AssayType,
    AssayTopologyModifiers
)
from isatools.model import Investigation


@click.command()
@click.option('--group_size', default=5, prompt='Sample size',
              help='Sample group size.')
@click.option('--agent_levels', default='cocaine, calpol',
              prompt='Agent levels', help='CSV list of agent levels.')
@click.option('--dose_levels', default='low, high', prompt='Dose levels',
              help='CSV list of dose levels.')
@click.option('--duration_of_exposure_levels', default='short, long', prompt='Durations',
              help='CSV list of duration levels.')
@click.option('--sample_types', default='blood', prompt='Sample types',
              help='CSV list of sample types.')
@click.option('--sample_sizes', default='5', prompt='Sample sizes',
              help='CSV list of sample sizes.')
def create_from_plan_parameters(
        group_size, agent_levels, dose_levels, duration_of_exposure_levels,
        sample_types, sample_sizes):
    agent_levels = agent_levels.split(',')
    dose_levels = dose_levels.split(',')
    duration_of_exposure_levels = duration_of_exposure_levels.split(',')
    sample_types = sample_types.split(',')
    sample_sizes = [int(x) for x in sample_sizes.split(',')]

    plan = SampleAssayPlan(
        group_size=group_size)  # if balanced, group_size is fixed
    for sample_type, sample_size in zip(sample_types, sample_sizes):
        plan.add_sample_type(sample_type)
        plan.add_sample_plan_record(sample_type, sample_size)
    treatment_factory = TreatmentFactory(
        intervention_type=INTERVENTIONS['CHEMICAL'], factors=BASE_FACTORS)
    for agent_level in agent_levels:
        treatment_factory.add_factor_value(BASE_FACTORS[0], agent_level.strip())
    for dose_level in dose_levels:
        treatment_factory.add_factor_value(BASE_FACTORS[1], dose_level.strip())
    for duration_of_exposure_level in duration_of_exposure_levels:
        treatment_factory.add_factor_value(BASE_FACTORS[2],
                                           duration_of_exposure_level.strip())
    treatment_sequence = TreatmentSequence(
        ranked_treatments=treatment_factory.compute_full_factorial_design())
    isa_object_factory = IsaModelObjectFactory(plan, treatment_sequence)

    measurement_type = 'metabolite profiling'
    technology_type = 'mass spectrometry'
    instruments = {'Agilent QTOF'}
    technical_replicates = 2
    injection_modes = {'LC'}
    acquisition_modes = {'positive', 'negative'}
    chromatography_instruments = {'Agilent Q12324A'}

    # MSAssayTopologyModifiers class not yet in isatools pip package
    # ms_top_mods = MSAssayTopologyModifiers(
    #    instruments=instruments,
    #    technical_replicates=technical_replicates,
    #    injection_modes=injection_modes,
    #    acquisition_modes=acquisition_modes,
    #    chromatography_instruments=chromatography_instruments)

    ms_top_mods = AssayTopologyModifiers(
        instruments=instruments,
        technical_replicates=technical_replicates)
    ms_assay_type = AssayType(measurement_type=measurement_type,
                              technology_type=technology_type)

    ms_assay_type.topology_modifiers = ms_top_mods
    plan.add_assay_type(ms_assay_type)
    plan.add_assay_plan_record(sample_type, ms_assay_type)

    s = isa_object_factory.create_assays_from_plan()
    i = Investigation()
    s.filename = "s_study.txt"
    i.studies = [s]
    os.mkdir('isa')
    isatab.dump(isa_obj=i, output_path='isa', i_file_name='i_investigation.txt')


if __name__ == '__main__':
    create_from_plan_parameters()
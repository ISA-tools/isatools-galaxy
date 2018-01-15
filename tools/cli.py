"""Commandline interface for running ISA API create mode"""
import click
import io
import json
import os

from isatools import isatab
from isatools.create.models import (
    SampleAssayPlanDecoder,
    TreatmentSequence,
    INTERVENTIONS,
    BASE_FACTORS,
    TreatmentFactory,
    IsaModelObjectFactory,
)
from isatools.model import Investigation


@click.command()
@click.option('--parameters_file',
              help='Path to JSON file containing input Galaxy tool parameters',
              prompt='Path to JSON Galaxy parameters file', nargs=1, type=str,
              default='create_params.json')
def create_from_plan_parameters(parameters_file):
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
        sample_and_assay_plans['sample_plan'].append(sample_plan)
    sample_and_assay_plans['group_size'] = tool_params[
        'treatment_plan']['study_group_size']
    decoder = SampleAssayPlanDecoder()
    plan = decoder.load(io.StringIO(json.dumps(sample_and_assay_plans)))
    treatment_factory = TreatmentFactory(
        intervention_type=INTERVENTIONS['CHEMICAL'], factors=BASE_FACTORS)
    agent_levels = 'calpol, none'
    for agent_level in agent_levels:
        treatment_factory.add_factor_value(BASE_FACTORS[0], agent_level.strip())
    dose_levels = 'low, high'
    for dose_level in dose_levels:
        treatment_factory.add_factor_value(BASE_FACTORS[1], dose_level.strip())
    duration_of_exposure_levels = 'long, short'
    for duration_of_exposure_level in duration_of_exposure_levels:
        treatment_factory.add_factor_value(BASE_FACTORS[2],
                                           duration_of_exposure_level.strip())
    treatment_sequence = TreatmentSequence(
        ranked_treatments=treatment_factory.compute_full_factorial_design())
    isa_object_factory = IsaModelObjectFactory(plan, treatment_sequence)
    s = isa_object_factory.create_assays_from_plan()
    i = Investigation()
    s.filename = "s_study.txt"
    i.studies = [s]
    os.mkdir('isa')
    isatab.dump(isa_obj=i, output_path='isa', i_file_name='i_investigation.txt')


if __name__ == '__main__':
    create_from_plan_parameters()
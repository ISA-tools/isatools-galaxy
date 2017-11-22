import sys
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

"""
<command interpreter="python">
galaxy_runner.py $group_size $agent_levels $dose_levels 
$duration_of_exposure_levels $sample_record_series.sample_types $sample_sizes
</command>
"""


def main():
    # agent_levels = sys.argv[1]  # agent_levels
    # dose_levels = sys.argv[2]  # dose_levels
    # duration_of_exposure_levels = sys.argv[3]  # duration_of_exposure_levels
    # sample_types = sys.argv[4]  # sample_types
    # sample_sizes = sys.argv[5]  # sample_sizes
    group_size = 5
    agent_levels = 'cocaine, calpol'.split(',')
    dose_levels = 'low, high'.split(',')
    duration_of_exposure_levels = 'short, long'.split(',')
    sample_types = 'blood'.split(',')
    sample_sizes = [int(x) for x in '5'.split(',')]

    plan = SampleAssayPlan(group_size=group_size)  # if balanced, group_size is fixed
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

    # ms_top_mods = MSAssayTopologyModifiers(
    #     instruments=instruments,
    #     technical_replicates=technical_replicates,
    #     injection_modes=injection_modes,
    #     acquisition_modes=acquisition_modes,
    #     chromatography_instruments=chromatography_instruments)

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
    s.filename = 's_study.txt'
    i.studies = [s]
    print(isatab.dumps(i))


if __name__ == '__main__':
    main()
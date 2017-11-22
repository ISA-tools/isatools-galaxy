python -c

'
from isatools.create.models import *;
plan = SampleAssayPlan(group_size=${group_size});
for sample_record in ${sample_record_series}:
    plan.add_sample_type(${sample_record.sample_type});
    plan.add_sample_plan_record(${sample_record.sample_type}, ${sample_record.sample_size});
treatment_factory = TreatmentFactory(intervention_type=INTERVENTIONS['CHEMICAL'], factors=BASE_FACTORS);
for agent_level in ${agent_levels}.split(','):
    treatment_factory.add_factor_value(BASE_FACTORS[0], agent_level.strip());
for dose_level in ${dose_levels}.split(','):
    treatment_factory.add_factor_value(BASE_FACTORS[1], dose_level.strip());
for duration_of_exposure_level in ${duration_of_exposure_levels}.split(','):
    treatment_factory.add_factor_value(BASE_FACTORS[2], duration_of_exposure_level.strip());
treatment_sequence = TreatmentSequence(ranked_treatments=treatment_factory.compute_full_factorial_design());
isa_object_factory = IsaModelObjectFactory(plan, treatment_sequence);
import json;
print(json.dumps(plan, cls=SampleAssayPlanEncoder));
'

python -c 'from isatools.create.models import *; plan = SampleAssayPlan(group_size=5); from collections import namedtuple; sample_record = namedtuple(typename="sample_record", field_names=["sample_type", "sample_size"]); sample_record_series = iter([sample_record(sample_type="blood", sample_size=5)]); for sample_record in sample_record_series: plan.add_sample_type(sample_record.sample_type); plan.add_sample_plan_record(sample_record.sample_type, sample_record.sample_size); treatment_factory = TreatmentFactory(intervention_type=INTERVENTIONS["CHEMICAL"], factors=BASE_FACTORS); agent_levels = "cocaine, calpol"; dose_levels = "low, high"; duration_of_exposure_levels = "short, long"; for agent_level in agent_levels.split(","): treatment_factory.add_factor_value(BASE_FACTORS[0], agent_level.strip()); for dose_level in dose_levels.split(","): treatment_factory.add_factor_value(BASE_FACTORS[1], dose_level.strip()); for duration_of_exposure_level in duration_of_exposure_levels.split(","): treatment_factory.add_factor_value(BASE_FACTORS[2], duration_of_exposure_level.strip()); treatment_sequence = TreatmentSequence(ranked_treatments=treatment_factory.compute_full_factorial_design()); isa_object_factory = IsaModelObjectFactory(plan, treatment_sequence); import json; print(json.dumps(plan, cls=SampleAssayPlanEncoder));'


<command interpreter="python">galaxy_runner.py $uniprot_id $output</command>
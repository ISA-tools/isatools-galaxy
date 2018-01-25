#!/usr/bin/env bash

# Set paths
scriptdir=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
testdir=$scriptdir/test-data/
venv=$HOME/.isavenv/
mkdir tmp/
tmp=$scriptdir/tmp

# Set up venv and activate
virtualenv -q -p python3.5 $venv
source $venv/bin/activate
pip install isatools==0.9.4 click==6.7

$scriptdir/glxy2isa_params.py $testdir/galaxy_inputs.json $tmp/
$scriptdir/cli.py --sample_assay_plans_file=$tmp/sample_assay_plans.json --study_info_file=$tmp/study_info.json --treatment_plans_file=$tmp/treatment_plan.json --target_dir=$tmp/


# Deactivate venv and cleanup
deactivate
rm -rf $venv
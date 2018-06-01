#!/bin/bash
# vi: fdm=marker

# Constants {{{1
################################################################

SCRIPT_PATH=$(dirname $BASH_SOURCE)
ISASLICER=$SCRIPT_PATH/../tools/slicer/isaslicer.py
RESDIR=$SCRIPT_PATH/res

# Check data list {{{1
################################################################

check_data_list() {

	local file="$1"
	local nb_data_files_expected=$2

	python3 <<EOF
# @@@BEGIN_PYTHON@@@
import json
import sys
with open('$output_file') as f:
    data_list = json.load(f)
    for elem in data_list:
	    if len(elem['data_files']) != $nb_data_files_expected:
		    print('Found only %d element(s), instead of %d, for sample %s.' % (len(elem['data_files']), $nb_data_files_expected, elem['sample']), file = sys.stderr)
		    sys.exit(1)
# @@@END_PYTHON@@@
EOF
}

# Test isaslicer all data files {{{1
################################################################

test_isaslicer_all_data_files() {

	# Get list of data files
	factor_name=Gender
	factor_value=Female
	study=MTBLS1-isatab
	study_path=$(realpath "$RESDIR/$study")
	output_file=$SCRIPT_PATH/$study-data-files.json
	$ISASLICER 'isa-tab-get-data-list' "$study_path" "$output_file" --json-query "{ \"$factor_name\": \"$factor_value\" }"

	# TODO Take output and read the JSON
	expect_non_empty_file "$output_file"

	# Check number of data files for each sample
	expect_success check_data_list "$output_file" 4
}

# Main {{{1
################################################################

test_context "Testing isaslicer"
test_that "Test that isaslicer outputs list of all data files." test_isaslicer_all_data_files

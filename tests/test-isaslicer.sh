#!/bin/bash
# vi: fdm=marker

# Constants {{{1
################################################################

SCRIPT_PATH=$(dirname $BASH_SOURCE)
ISASLICER=$SCRIPT_PATH/../tools/slicer/isaslicer.py
RESDIR=$SCRIPT_PATH/res

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

	# TODO Check that JSON contains specific fields and several files in data_files fields for each sample. (Write a special script for that or implement some JSON parsing inside bash-testthat?)
}

# Main {{{1
################################################################

test_context "Testing isaslicer"
test_that "Test that isaslicer outputs list of all data files." test_isaslicer_all_data_files

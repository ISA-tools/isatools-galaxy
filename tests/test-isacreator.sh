#!/bin/bash
# vi: fdm=marker

# Constants {{{1
################################################################

SCRIPT_PATH=$(dirname $BASH_SOURCE)
ISACREATOR=$SCRIPT_PATH/../tools/isacreator_metabo/isacreator_metabo.py
RESDIR=$SCRIPT_PATH/res

# Test isacreator fails if no output dir {{{1
################################################################

test_isacreator_fails_if_no_output_dir() {

	local inputs_file="$RESDIR/isacreator_metabo_default_inputs.json"
	local output_dir="$SCRIPT_PATH/test_isacreator_fails_if_no_output_dir.output"

	[[ -d $output_dir ]]  && rm -r "$output_dir"

	expect_failure "$ISACREATOR" "--galaxy_parameters_file=$inputs_file" "--target_dir=$output_dir" || return 1
	mkdir "$output_dir"
	expect_success "$ISACREATOR" "--galaxy_parameters_file=$inputs_file" "--target_dir=$output_dir" || return 1
}

# Test isacreator default inputs {{{1
################################################################

test_isacreator_default_inputs() {

	local inputs_file="$RESDIR/isacreator_metabo_default_inputs.json"
	local output_dir="$SCRIPT_PATH/test_isacreator_default_inputs.output"

	[[ -d $output_dir ]]  && rm -r "$output_dir"

	mkdir "$output_dir"
	expect_success "$ISACREATOR" "--galaxy_parameters_file=$inputs_file" "--target_dir=$output_dir" || return 1

	# Check identifiers
	investigation_file="$output_dir/i_investigation.txt"
	expect_non_empty_file "$investigation_file"
	investigation_id=$(grep '^Investigation Identifier' "$investigation_file" | sed 's/^.*\(ISA[^ ]*\)$/\1/')
	study_id=$(grep '^Study Identifier' "$investigation_file" | sed 's/^.*\(ISA[^ ]*\)$/\1/')
	expect_str_not_null "$investigation_id"
	expect_str_eq "$study_id" "$investigation_id"
}

# Main {{{1
################################################################

test_context "Testing isacreator"
test_that "Test that isacreator fails if output directory does not exist." test_isacreator_fails_if_no_output_dir
test_that "Test that isacreator works correctly on default JSON list of input parameters." test_isacreator_default_inputs

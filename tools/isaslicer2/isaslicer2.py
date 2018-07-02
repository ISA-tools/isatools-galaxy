#!/usr/bin/env python3
"""Commandline interface for running ISA API create mode (metabo flavoured)"""
import click
import os
from isatools import mtbls
import tempfile
import shutil

from isatools import isatab
from isatools.create.models import *
from isatools.model import Investigation, Person


@click.command()
@click.argument('command')
@click.option('--source_dir', help='Input path to read', nargs=1,
              type=click.Path(exists=True), default=None)
@click.option('--galaxy_parameters_file',
              help='Path to JSON file containing input Galaxy JSON',
              type=click.File())
@click.option('--output',
              help='Path to output file to write to',
              type=click.File(mode='w'))
def query_isatab(command, source_dir, galaxy_parameters_file, output):

    debug = True

    if galaxy_parameters_file:
        galaxy_parameters = json.load(galaxy_parameters_file)
        print(json.dumps(galaxy_parameters, indent=4))
    else:
        raise IOError('Could not load Galaxy parameters file!')
    if source_dir:
        if not os.path.exists(source_dir):
            raise IOError('Source path does not exist!')

    query = galaxy_parameters['query']
    if debug:
        print(json.dumps(query, indent=4))  # for debugging only

    if source_dir:
        investigation = isatab.load(source_dir)
    else:
        tmp = tempfile.mkdtemp()
        _ = mtbls.get(galaxy_parameters['input']['mtbls_id'], tmp)
        investigation = isatab.load(tmp)

        shutil.rmtree(tmp)

    # filter assays by mt/tt
    matching_assays = []
    mt = query.get('measurement_type').strip()
    tt = query.get('technology_type').strip()
    if mt and tt:
        for study in investigation.studies:
            matching_assays.extend(
                [x for x in study.assays if x.measurement_type.term == mt
                 and x.technology_type.term == tt])
    elif mt and not tt:
        for study in investigation.studies:
            matching_assays.extend(
                [x for x in study.assays if x.measurement_type.term == mt])
    elif not mt and tt:
        for study in investigation.studies:
            matching_assays.extend(
                [x for x in study.assays if x.technology_type.term == tt])
    else:
        for study in investigation.studies:
            matching_assays.extend(study.assays)
    matching_samples = []
    for assay in matching_assays:
        matching_samples.extend(assay.samples)

    # filter samples by material type
    # material_type = query.get('sample_material_type')
    # for assay in matching_assays:
    #     if material_type:
    #         matching_samples.extend(
    #             [x for x in assay.samples if x.material_type == material_type])
    #     else:
    #         matching_samples.extend(assay.samples)

    #filter samples by fv
    factor_selection = {x.get('factor_name'): x.get('factor_value') for x in
                        query.get('factor_selection', [])}
    fv_samples = set()
    first_pass = True
    samples_to_remove = set()
    for f, v in factor_selection.items():
        if first_pass:
            for sample in matching_samples:
                for fv in [x for x in sample.factor_values if
                           x.factor_name.name == f]:
                    if isinstance(fv.value, OntologyAnnotation):
                        if fv.value.term == v:
                            fv_samples.add(sample)
                    elif fv.value == v:
                        fv_samples.add(sample)
            first_pass = False
        else:
            for sample in fv_samples:
                for fv in [x for x in sample.factor_values if
                           x.factor_name.name == f]:
                    if isinstance(fv.value, OntologyAnnotation):
                        if fv.value.term != v:
                            samples_to_remove.add(sample)
                    elif fv.value != v:
                        samples_to_remove.add(sample)
    final_samples = fv_samples.difference(samples_to_remove)

    print('Total samples: %s' % len(investigation.studies[0].samples))
    print('Matching samples: %s' % len(final_samples))

    results = []
    for sample in final_samples:
        if isinstance(sample, Sample):
            results.append({
                'sample_name': sample.name
            })
    results_json = {
        'query': query,
        'results': results
    }
    json.dump(results_json, output)

if __name__ == '__main__':
    query_isatab()
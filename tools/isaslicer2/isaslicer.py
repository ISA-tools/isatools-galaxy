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
@click.argument('command')
@click.option('--source_dir', help='Input path to read', nargs=1,
              type=click.Path(exists=True), default='./')
@click.option('--galaxy_parameters_file',
              help='Path to JSON file containing input Galaxy JSON',
              type=click.File())
def query_isatab(command, source_dir, galaxy_parameters_file):

    debug = True

    if galaxy_parameters_file:
        galaxy_parameters = json.load(galaxy_parameters_file)
        if debug:
            print(json.dumps(galaxy_parameters, indent=4))  # for debugging only
    else:
        raise IOError('Could not load Galaxy parameters file!')
    if source_dir:
        if not os.path.exists(source_dir):
            raise IOError('Source path does not exist!')

    query = galaxy_parameters['query']
    if debug:
        print(json.dumps(query, indent=4))  # for debugging only

    investigation = isatab.load(source_dir)
    matching_assays = []
    mt = query.get('measurement_type').strip()
    tt = query.get('technology_type').strip()
    if mt and tt:
        for study in investigation.studies:
            matching_assays.extend(
                [x for x in study.assays if x.measurement_type.term == mt
                 and x.technology_type.term == tt])
    elif query.get('measurement_type') and not query.get('technology_type'):
        for study in investigation.studies:
            matching_assays.extend(
                [x for x in study.assays if x.measurement_type.term == mt])
    elif not query.get('measurement_type') and query.get('technology_type'):
        for study in investigation.studies:
            matching_assays.extend(
                [x for x in study.assays if x.technology_type.term == tt])
    else:
        for study in investigation.studies:
            matching_assays.extend(study.assays)
    matching_samples = []
    material_type = query.get('sample_material_type')
    for assay in matching_assays:
        if material_type:
            matching_samples.extend([x for x in assay.samples if x.material_type == material_type])
        else:
            matching_samples.extend(assay.samples)

    print('Total samples: %s' % len(investigation.studies[0].samples))
    print('Matching samples: %s' % len(matching_samples))


if __name__ == '__main__':
    query_isatab()
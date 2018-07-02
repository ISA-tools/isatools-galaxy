#!/usr/bin/env python3
"""Commandline interface for running ISA API create mode (metabo flavoured)"""
import click
import os
from isatools import mtbls
import tempfile
import shutil
import glob

from isatools import isatab
from isatools.create.models import *


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
    assay_samples = []
    for assay in matching_assays:
        assay_samples.extend(assay.samples)

    # filter samples by material type.
    # Only works if Characteristic[Material Type] or Material Type is present
    material_samples = set()
    material_type = query.get('sample_material_type')
    if material_type:
        for sample in assay_samples:
            for c in sample.characteristics:
                if c.category.term == 'Material Type':
                    if isinstance(c.value, OntologyAnnotation):
                        if c.value.term == material_type:
                            material_samples.add(sample)
                    elif c.value == material_type:
                        material_samples.add(sample)
    else:
        material_samples = assay_samples

    #filter samples by fv
    factor_selection = {x.get('factor_name'): x.get('factor_value') for x in
                        query.get('factor_selection', [])}
    fv_samples = set()
    if factor_selection:
        first_pass = True
        samples_to_remove = set()
        for f, v in factor_selection.items():
            if first_pass:
                for sample in material_samples:
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
    else:
        final_samples = fv_samples

    results = []
    all_data_files = []
    for study in investigation.studies:
        for assay in study.assays:
            all_data_files.extend(assay.data_files)
        for sample in final_samples:
            if isinstance(sample, Sample):
                results.append({
                    'sample_name': sample.name,
                    'data_files': [x for x in all_data_files if
                                   x.generated_from == sample]
                })
    for result in results:
        sample_name = result['sample_name']
        for table_file in glob.iglob(os.path.join(source_dir, 'a_*')):
            with open(table_file) as fp:
                df = isatab.load_table(fp)
                data_files = []
                table_headers = list(df.columns.values)
                sample_rows = df.loc[df['Sample Name'] == sample_name]
                data_node_labels = [
                    'Raw Data File', 'Raw Spectral Data File',
                    'Derived Spectral Data File',
                    'Derived Array Data File', 'Array Data File',
                    'Protein Assignment File', 'Peptide Assignment File',
                    'Post Translational Modification Assignment File',
                    'Acquisition Parameter Data File',
                    'Free Induction Decay Data File',
                    'Derived Array Data Matrix File', 'Image File',
                    'Derived Data File', 'Metabolite Assignment File']
                for node_label in data_node_labels:
                    if node_label in table_headers:
                        data_files.extend(list(sample_rows[node_label]))
                result['data_files'] = [i for i in list(data_files) if
                                        str(i) != 'nan']
    results_json = {
        'query': query,
        'results': results
    }
    json.dump(results_json, output, indent=4)

    # if galaxy_parameters['input']['collection_output']:
    #     logger = logging.getLogger()
    #     logger.debug("copying data files to %s", os.path.dirname(output))
    #     for result in results:
    #         for data_file_name in result['data_files']:
    #             logging.info("Copying {}".format(data_file_name))
    #             shutil.copy(os.path.join(source_dir, data_file_name),
    #                         os.path.dirname(output))
    #     logger.info(
    #       "Finished writing data files to {}".format(os.path.dirname(output)))

if __name__ == '__main__':
    query_isatab()
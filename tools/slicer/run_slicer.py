"""Functions for slicing ISA-Tabs, based on the mtbls.py module.
"""
from __future__ import absolute_import
import glob
import logging
import os
import pandas as pd
import re


from isatools import isatab
from isatools.model import OntologyAnnotation


log = logging.getLogger('isatools')

# REGEXES
_RX_FACTOR_VALUE = re.compile('Factor Value\[(.*?)\]')


def get_data_files(input_path, factor_selection=None):
    result = slice_data_files(input_path, factor_selection=factor_selection)
    return result


def slice_data_files(dir, factor_selection=None):
    """
    This function gets a list of samples and related data file URLs for a given
    MetaboLights study, optionally filtered by factor value (currently by
    matching on exactly 1 factor value)

    :param input_path: Input path to ISA-tab
    :param factor_selection: A list of selected factor values to filter on
    samples
    :return: A list of dicts {sample_name, list of data_files} containing
    sample names with associated data filenames


    TODO:  Need to work on more complex filters e.g.:
        {"gender": ["male", "female"]} selects samples matching "male" or
        "female" factor value
        {"age": {"equals": 60}} selects samples matching age 60
        {"age": {"less_than": 60}} selects samples matching age less than 60
        {"age": {"more_than": 60}} selects samples matching age more than 60

        To select samples matching "male" and age less than 60:
        {
            "gender": "male",
            "age": {
                "less_than": 60
            }
        }
    """
    results = []
    # first collect matching samples
    for table_file in glob.iglob(os.path.join(dir, '[a|s]_*')):
        log.info('Loading {table_file}'.format(table_file=table_file))

        with open(os.path.join(dir, table_file)) as fp:
            df = isatab.load_table(fp)

            if factor_selection is None:
                matches = df['Sample Name'].items()

                for indx, match in matches:
                    sample_name = match
                    if len([r for r in results if r['sample'] ==
                            sample_name]) == 1:
                        continue
                    else:
                        results.append(
                            {
                                'sample': sample_name,
                                'data_files': []
                            }
                        )

            else:
                for factor_name, factor_value in factor_selection.items():
                    if 'Factor Value[{}]'.format(factor_name) in list(
                            df.columns.values):
                        matches = df.loc[df['Factor Value[{factor}]'.format(
                            factor=factor_name)] == factor_value][
                            'Sample Name'].items()

                        for indx, match in matches:
                            sample_name = match
                            if len([r for r in results if r['sample'] ==
                                    sample_name]) == 1:
                                continue
                            else:
                                results.append(
                                    {
                                        'sample': sample_name,
                                        'data_files': [],
                                        'query_used': factor_selection
                                    }
                                )

    # now collect the data files relating to the samples
    for result in results:
        sample_name = result['sample']

        for table_file in glob.iglob(os.path.join(dir, 'a_*')):
            with open(table_file) as fp:
                df = isatab.load_table(fp)

                data_files = []

                table_headers = list(df.columns.values)
                sample_rows = df.loc[df['Sample Name'] == sample_name]

                if 'Raw Spectral Data File' in table_headers:
                    data_files = sample_rows['Raw Spectral Data File']

                elif 'Free Induction Decay Data File' in table_headers:
                    data_files = sample_rows['Free Induction Decay Data File']

                result['data_files'] = [i for i in list(data_files) if
                                        str(i) != 'nan']
    return results


def get_factor_names(input_path):
    """
    This function gets the factor names used in a MetaboLights study

    :param input_path: Input path to ISA-tab
    :return: A set of factor names used in the study

    Example usage:
        factor_names = get_factor_names('/path/to/my/study/')
    """

    factors = set()

    for table_file in glob.iglob(os.path.join(input_path, '[a|s]_*')):
        with open(os.path.join(input_path, table_file)) as fp:
            df = isatab.load_table(fp)

            factors_headers = [header for header in list(df.columns.values)
                               if _RX_FACTOR_VALUE.match(header)]

            for header in factors_headers:
                factors.add(header[13:-1])
    return factors


def get_factor_values(input_path, factor_name):
    """
    This function gets the factor values of a factor in a MetaboLights study

    :param input_path: Input path to ISA-tab
    :param factor_name: The factor name for which values are being queried
    :return: A set of factor values associated with the factor and study

    Example usage:
        factor_values = get_factor_values('/path/to/my/study/', 'genotype')
    """

    fvs = set()

    for table_file in glob.iglob(os.path.join(input_path, '[a|s]_*')):
        with open(os.path.join(input_path, table_file)) as fp:
            df = isatab.load_table(fp)

            if 'Factor Value[{factor}]'.format(factor=factor_name) in \
                    list(df.columns.values):
                for _, match in df[
                    'Factor Value[{factor}]'.format(
                        factor=factor_name)].iteritems():
                    try:
                        match = match.item()
                    except AttributeError:
                        pass

                    if isinstance(match, (str, int, float)):
                        if str(match) != 'nan':
                            fvs.add(match)
    return fvs


def get_factors_summary(input_path):
    """
    This function generates a factors summary for a MetaboLights study

    :param input_path: Input path to ISA-tab
    :return: A list of dicts summarising the set of factor names and values
    associated with each sample

    Note: it only returns a summary of factors with variable values.

    Example usage:
        factor_summary = get_factors_summary('/path/to/my/study/')
        [
            {
                "name": "ADG19007u_357",
                "Metabolic syndrome": "Control Group",
                "Gender": "Female"
            },
            {
                "name": "ADG10003u_162",
                "Metabolic syndrome": "diabetes mellitus",
                "Gender": "Female"
            },
        ]


    """
    ISA = isatab.load(input_path)

    all_samples = []
    for study in ISA.studies:
        all_samples.extend(study.samples)

    samples_and_fvs = []

    for sample in all_samples:
        sample_and_fvs = {
                'sources': ';'.join([x.name for x in sample.derives_from]),
                'sample': sample.name,
            }

        for fv in sample.factor_values:
            if isinstance(fv.value, (str, int, float)):
                fv_value = fv.value
                sample_and_fvs[fv.factor_name.name] = fv_value
            elif isinstance(fv.value, OntologyAnnotation):
                fv_value = fv.value.term
                sample_and_fvs[fv.factor_name.name] = fv_value

        samples_and_fvs.append(sample_and_fvs)

    df = pd.DataFrame(samples_and_fvs)
    nunique = df.apply(pd.Series.nunique)
    cols_to_drop = nunique[nunique == 1].index

    df = df.drop(cols_to_drop, axis=1)
    return df.to_dict(orient='records')


def get_study_groups(input_path):
    factors_summary = get_factors_summary(input_path=input_path)
    study_groups = {}

    for factors_item in factors_summary:
        fvs = tuple(factors_item[k] for k in factors_item.keys() if k != 'name')

        if fvs in study_groups.keys():
            study_groups[fvs].append(factors_item['name'])
        else:
            study_groups[fvs] = [factors_item['name']]
    return study_groups


def get_study_groups_samples_sizes(input_path):
    study_groups = get_study_groups(input_path=input_path)
    return list(map(lambda x: (x[0], len(x[1])), study_groups.items()))


def get_sources_for_sample(input_path, sample_name):
    ISA = isatab.load(input_path)
    hits = []

    for study in ISA.studies:
        for sample in study.samples:
            if sample.name == sample_name:
                print('found a hit: {sample_name}'.format(
                    sample_name=sample.name))

                for source in sample.derives_from:
                    hits.append(source.name)
    return hits


def get_data_for_sample(input_path, sample_name):
    ISA = isatab.load(input_path)
    hits = []
    for study in ISA.studies:
        for assay in study.assays:
            for data in assay.data_files:
                if sample_name in [x.name for x in data.generated_from]:
                    log.info('found a hit: {filename}'.format(
                        filename=data.filename))
                    hits.append(data)
    return hits


def get_study_groups_data_sizes(input_path):
    study_groups = get_study_groups(input_path=input_path)
    return list(map(lambda x: (x[0], len(x[1])), study_groups.items()))


def get_characteristics_summary(input_path):
    """
        This function generates a characteristics summary for a MetaboLights
        study

        :param input_path: Input path to ISA-tab
        :return: A list of dicts summarising the set of characteristic names
        and values associated with each sample

        Note: it only returns a summary of characteristics with variable values.

        Example usage:
            characteristics_summary = get_characteristics_summary('/path/to/my/study/')
            [
                {
                    "name": "6089if_9",
                    "Variant": "Synechocystis sp. PCC 6803.sll0171.ko"
                },
                {
                    "name": "6089if_43",
                    "Variant": "Synechocystis sp. PCC 6803.WT.none"
                },
            ]


        """
    ISA = isatab.load(input_path)

    all_samples = []
    for study in ISA.studies:
        all_samples.extend(study.samples)

    samples_and_characs = []
    for sample in all_samples:
        sample_and_characs = {
                'name': sample.name
            }

        for source in sample.derives_from:
            for c in source.characteristics:
                if isinstance(c.value, (str, int, float)):
                    c_value = c.value
                    sample_and_characs[c.category.term] = c_value
                elif isinstance(c.value, OntologyAnnotation):
                    c_value = c.value.term
                    sample_and_characs[c.category.term] = c_value

        samples_and_characs.append(sample_and_characs)

    df = pd.DataFrame(samples_and_characs)
    nunique = df.apply(pd.Series.nunique)
    cols_to_drop = nunique[nunique == 1].index

    df = df.drop(cols_to_drop, axis=1)
    return df.to_dict(orient='records')


def get_study_variable_summary(input_path):
    ISA = isatab.load(input_path)

    all_samples = []
    for study in ISA.studies:
        all_samples.extend(study.samples)

    samples_and_variables = []
    for sample in all_samples:
        sample_and_vars = {
            'sample_name': sample.name
        }

        for fv in sample.factor_values:
            if isinstance(fv.value, (str, int, float)):
                fv_value = fv.value
                sample_and_vars[fv.factor_name.name] = fv_value
            elif isinstance(fv.value, OntologyAnnotation):
                fv_value = fv.value.term
                sample_and_vars[fv.factor_name.name] = fv_value

        for source in sample.derives_from:
            sample_and_vars['source_name'] = source.name
            for c in source.characteristics:
                if isinstance(c.value, (str, int, float)):
                    c_value = c.value
                    sample_and_vars[c.category.term] = c_value
                elif isinstance(c.value, OntologyAnnotation):
                    c_value = c.value.term
                    sample_and_vars[c.category.term] = c_value

        samples_and_variables.append(sample_and_vars)

    df = pd.DataFrame(samples_and_variables)
    nunique = df.apply(pd.Series.nunique)
    cols_to_drop = nunique[nunique == 1].index

    df = df.drop(cols_to_drop, axis=1)
    return df.to_dict(orient='records')


def get_study_group_factors(input_path):
    factors_list = []

    for table_file in glob.iglob(os.path.join(input_path, '[a|s]_*')):
        with open(os.path.join(input_path, table_file)) as fp:
            df = isatab.load_table(fp)

            factor_columns = [x for x in df.columns if x.startswith(
                'Factor Value')]
            if len(factor_columns) > 0:
                factors_list = df[factor_columns].drop_duplicates()\
                    .to_dict(orient='records')
    return factors_list


def get_filtered_df_on_factors_list(input_path):
    factors_list = get_study_group_factors(input_path=input_path)
    queries = []

    for item in factors_list:
        query_str = []

        for k, v in item.items():
            k = k.replace(' ', '_').replace('[', '_').replace(']', '_')
            if isinstance(v, str):
                v = v.replace(' ', '_').replace('[', '_').replace(']', '_')
                query_str.append("{k} == '{v}' and ".format(k=k, v=v))

        query_str = ''.join(query_str)[:-4]
        queries.append(query_str)

    for table_file in glob.iglob(os.path.join(input_path, '[a|s]_*')):
        with open(os.path.join(input_path, table_file)) as fp:
            df = isatab.load_table(fp)

            cols = df.columns
            cols = cols.map(
                lambda x: x.replace(' ', '_') if isinstance(x, str) else x)
            df.columns = cols

            cols = df.columns
            cols = cols.map(
                lambda x: x.replace('[', '_') if isinstance(x, str) else x)
            df.columns = cols

            cols = df.columns
            cols = cols.map(
                lambda x: x.replace(']', '_') if isinstance(x, str) else x)
            df.columns = cols

        for query in queries:
            df2 = df.query(query)  # query uses pandas.eval, which evaluates
                                   # queries like pure Python notation
            if 'Sample_Name' in df.columns:
                print('Group: {query} / Sample_Name: {sample_name}'.format(
                    query=query, sample_name=list(df2['Sample_Name'])))

            if 'Source_Name' in df.columns:
                print('Group: {} / Sources_Name: {}'.format(
                    query, list(df2['Source_Name'])))

            if 'Raw_Spectral_Data_File' in df.columns:
                print('Group: {query} / Raw_Spectral_Data_File: {filename}'
                    .format( query=query[13:-2],
                             filename=list(df2['Raw_Spectral_Data_File'])))
    return queries

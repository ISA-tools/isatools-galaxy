#!/usr/bin/env python3

import sys
import shutil
import argparse
import os
import logging

from isatools.net import mtbls as MTBLS

logger = None

#    run_mtblisa.py <command> <study_id> [ command-specific options ]

def make_parser():
    parser = argparse.ArgumentParser(
        description="ISA slicer - a wrapper for isatools.io.mtbls")

    parser.add_argument('--log-level', choices=[
        'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'],
                        default='INFO', help="Set the desired logging level")

    subparsers = parser.add_subparsers(
        title='Actions',
        dest='command') # specified subcommand will be available in attribute 'command'
    subparsers.required = True

    subparser = subparsers.add_parser(
        'get-study-archive', aliases=['gsa'],
        help="Get ISA study from MetaboLights as zip archive")
    subparser.set_defaults(func=get_study_archive_command)
    subparser.add_argument('study_id')
    subparser.add_argument(
        'output', metavar="OUTPUT",
        help="Name of output archive (extension will be added)")
    subparser.add_argument('--format', metavar="FMT", choices=[
        'zip', 'tar', 'gztar', 'bztar', 'xztar'], default='zip',
                           help="Type of archive to create")

    subparser = subparsers.add_parser('get-study', aliases=['gs'],
                                      help="Get ISA study from MetaboLights")
    subparser.set_defaults(func=get_study_command)
    subparser.add_argument('study_id')
    subparser.add_argument('output', metavar="PATH", help="Name of output")
    subparser.add_argument(
        '-f', '--isa-format', choices=['isa-tab', 'isa-json'],
        metavar="FORMAT", default='isa-tab', help="Desired ISA format")

    subparser = subparsers.add_parser(
        'get-factors', aliases=['gf'],
        help="Get factor names from a study in json format")
    subparser.set_defaults(func=get_factors_command)
    subparser.add_argument('study_id')
    subparser.add_argument(
        'output', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
        help="Output file")

    subparser = subparsers.add_parser(
        'get-factor-values', aliases=['gfv'],
        help="Get factor values from a study in json format")
    subparser.set_defaults(func=get_factor_values_command)
    subparser.add_argument('study_id')
    subparser.add_argument(
        'factor', help="The desired factor. Use `get-factors` to get the list "
                       "of available factors")
    subparser.add_argument(
        'output',nargs='?', type=argparse.FileType('w'), default=sys.stdout,
        help="Output file")

    subparser = subparsers.add_parser('get-data', aliases=['gd'],
                                      help="Get data files in json format")
    subparser.set_defaults(func=get_data_files_command)
    subparser.add_argument('study_id')
    subparser.add_argument('output',nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                           help="Output file")

    subparser.add_argument(
        '--json-query',
        help="Factor query in JSON (e.g., '{\"Gender\":\"Male\"}'")

    subparser = subparsers.add_parser(
        'get-summary', aliases=['gsum'],
        help="Get the variables summary from a study, in json format")
    subparser.set_defaults(func=get_summary_command)
    subparser.add_argument('study_id')
    subparser.add_argument(
        'output', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
        help="Output file")

    return parser


def get_study_archive_command(options):
    study_id = options.study_id

    logger.info("Downloading study %s into archive at path %s.%s",
                study_id, options.output, options.format)

    tmpdir = MTBLS.get(study_id)
    logger.debug("MTBLS.get returned '%s'", tmpdir)
    if tmpdir is not None:
        try:
            shutil.make_archive(
                options.output, options.format, tmpdir, logger=logger)
            logger.info("ISA archive written")
        finally:
            logger.debug("Trying to clean up tmp dir %s", tmpdir)
            shutil.rmtree(tmpdir, ignore_errors=True)
    else:
        raise RuntimeError("Error downloading ISA study")

def get_study_command(options):
    if os.path.exists(options.output):
        raise RuntimeError("Selected output path {} already exists!".format(
            options.output))

    if options.isa_format == "isa-tab":
        tmp_data = None
        try:
            logger.info("Downloading study %s", options.study_id)
            tmp_data = MTBLS.get(options.study_id)
            if tmp_data is None:
                raise RuntimeError("Error downloading ISA study")

            logger.debug(
                "Finished downloading data. Moving to final location %s",
                options.output)
            shutil.move(tmp_data, options.output)
            logger.info("ISA archive written to %s", options.output)
        finally:
            if tmp_data:
                # try to clean up any temporary files left behind
                logger.debug("Deleting %s, if there's anything there", tmp_data)
                shutil.rmtree(tmp_data, ignore_errors=True)
    elif options.isa_format == "isa-json":
        import json
        isajson = MTBLS.getj(options.study_id)
        if isajson is None:
            raise RuntimeError("Error downloading ISA study")

        logger.debug(
            "Finished downloading data. Dumping json to final location %s",
            options.output)
        os.makedirs(options.output)
        json_file = os.path.join(options.output, "{}.json".format(
            isajson['identifier']))
        with open(json_file, 'w') as fd:
            json.dump(isajson, fd)
        logger.info("ISA-JSON written to %s", options.output)
    else:
        raise ValueError("BUG! Got an invalid isa format '{}'".format(
            options.isa_format))

def get_factors_command(options):
    import json

    logger.info("Getting factors for study %s. Writing to %s.",
                options.study_id, options.output.name)
    factor_names = MTBLS.get_factor_names(options.study_id)
    print('FNs: ', list(factor_names))
    if factor_names is not None:
        json.dump(list(factor_names), options.output, indent=4)
        logger.debug("Factor names written")
    else:
        raise RuntimeError("Error downloading factors.")

def get_factor_values_command(options):
    import json
    logger.info("Getting values for factor {factor} in study {study_id}. Writing to {output_file}."
        .format(factor=options.factor, study_id=options.study_id, output_file=options.output.name))

    fvs = MTBLS.get_factor_values(options.study_id, options.factor)
    print('FVs: ', list(fvs))
    if fvs is not None:
        json.dump(list(fvs), options.output, indent=4)
        logger.debug("Factor values written to {}".format(options.output))
    else:
        raise RuntimeError("Error getting factor values")

def get_data_files_command(options):
    import json
    logger.info("Getting data files for study %s. Writing to %s.",
                options.study_id, options.output.name)
    if options.json_query:
        logger.debug("This is the specified query:\n%s", options.json_query)
    else:
        logger.debug("No query was specified")

    if options.json_query is not None:
        json_struct = json.loads(options.json_query)
        data_files = MTBLS.get_data_files(options.study_id, json_struct)
    else:
        data_files = MTBLS.get_data_files(options.study_id)

    logger.debug("Result data files list: %s", data_files)
    if data_files is None:
        raise RuntimeError("Error getting data files with isatools")

    logger.debug("dumping data files to %s", options.output.name)
    json.dump(list(data_files), options.output, indent=4)
    logger.info("Finished writing data files to {}".format(options.output))


def get_summary_command(options):
    import json
    logger.info("Getting summary for study %s. Writing to %s.",
                options.study_id, options.output.name)

    summary = MTBLS.get_study_variable_summary(options.study_id)
    print('summary: ', list(summary))
    if summary is not None:
        json.dump(summary, options.output, indent=4)
        logger.debug("Summary dumped")
    else:
        raise RuntimeError("Error getting study summary")

def _configure_logger(options):
    logging_level = getattr(logging, options.log_level, logging.INFO)
    logging.basicConfig(level=logging_level)

    global logger
    logger = logging.getLogger()
    logger.setLevel(logging_level) # there's a bug somewhere.  The level set through basicConfig isn't taking effect

def _parse_args(args):
    parser = make_parser()
    options = parser.parse_args(args)

    # All subcommands have `study_id`
    # Can we check the format of the study ID here, and raise an informative error
    # if it's invalid?
    if not options.study_id:
        parser.error("study_id argument not provided")

    return options

def main(args):
    options = _parse_args(args)
    _configure_logger(options)

    if not options.study_id.startswith('MTBLS'):
        logger.warning(
            "The study id %s doesn't look like a valid Metabolights id",
            options.study_id)

    # run subcommand
    options.func(options)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
        sys.exit(0)
    except Exception as e:
        logger.exception(e)
        logger.error(e)
        sys.exit(e.code if hasattr(e, "code") else 99)

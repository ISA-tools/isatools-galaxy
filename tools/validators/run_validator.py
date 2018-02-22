#!/usr/bin/env python3
import glob
import json
import os
import sys

isa_path = sys.argv[1]
try:
    from isatools import isatab
except ImportError as e:
    raise RuntimeError('Could not import isatools.isatab package')
if not os.path.exists(isa_path):
    print('File path to ISA files \'{}\' does not exist'.format(isa_path))
    sys.exit(0)
report = None
i_files = glob.glob(os.path.join(isa_path, 'i_*.txt'))
if len(i_files) == 1:
    i_file_name = next(iter(i_files))
    with open(i_file_name) as in_fp:
        json_report = isatab.validate(in_fp)
        if json_report is not None:
            with open('report.json', 'w') as out_fp:
                json.dump(json_report, out_fp, indent=4)

#!/usr/bin/env python3
import glob
import json
import os
import sys
import zipfile
import tempfile

input_path = sys.argv[1]
output_path = sys.argv[2]

try:
    from isatools import isatab
except ImportError as e:
    raise RuntimeError('Could not import isatools.isatab package')

tmp_dir = tempfile.mkdtemp()
with zipfile.ZipFile(input_path) as zfp:
    zfp.extractall(path=tmp_dir)
if not os.path.exists(tmp_dir):
    print('File path to ISA files \'{}\' does not exist'.format(tmp_dir))
    sys.exit(0)
report = None
i_files = glob.glob(os.path.join(tmp_dir, 'i_*.txt'))
if len(i_files) == 1:
    i_file_name = next(iter(i_files))
    with open(i_file_name) as in_fp:
        json_report = isatab.validate(in_fp)
        if json_report is not None:
            with open(output_path, 'w') as out_fp:
                json.dump(json_report, out_fp, indent=4)
import shutil
shutil.rmtree(tmp_dir)
#!/usr/bin/env python3

import json
import shutil
import sys
import tempfile
import zipfile

input_path = sys.argv[1]
output_file_path = sys.argv[2]

try:
    from isatools.convert import isatab2json
except ImportError as e:
    raise RuntimeError('Could not import isatools package')

tmp_dir = tempfile.mkdtemp()
with zipfile.ZipFile(input_path) as zfp:
    zfp.extractall(path=tmp_dir)

    my_json = isatab2json.convert(
        work_dir=tmp_dir, validate_first=False, use_new_parser=True)
    with open(output_file_path, 'w') as out_fp:
        json.dump(my_json, out_fp)
shutil.rmtree(tmp_dir)


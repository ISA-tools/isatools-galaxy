#!/usr/bin/env python3

import sys
import os
import json

src_path = sys.argv[1]

try:
    from isatools.convert import isatab2json
except ImportError as e:
    raise RuntimeError('Could not import isatools package')

if not os.path.exists(src_path):
    print('File path to ISA-Tab files {} does not exist'.format(src_path))
    sys.exit(0)

my_json = isatab2json.convert(
    work_dir=src_path, validate_first=False, use_new_parser=True)
with open('out.json', 'w') as out_fp:
    json.dump(my_json, out_fp)


#!/usr/bin/env python3

import sys

if len(sys.argv) < 3:
    print('Usage: run_mwtab2isa.py mwtab_study_id target_dir')
    sys.exit(0)

mwtab_study_id = sys.argv[1]
target_dir = sys.argv[2]
print("TARGET:", target_dir)
try:
    from isatools.net.mw2isa import mw2isa_convert
    mw2isa_convert(studyid=mwtab_study_id, outputdir=target_dir)
except ImportError:
    raise RuntimeError('Could not import isatools package')

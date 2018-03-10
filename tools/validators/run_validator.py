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


def build_messages(messages):
    messages_table = "<table>"
    messages_table += "<tr><th>Code</th><th>Message</th><th>Supplemental information</th></tr>"
    for message in messages:
        messages_table += "<tr><td>{code}</td><td>{message}</td><td>{supplemental}</td></tr>".format(
            code=message['code'], message=message['message'], supplemental=message['suplemental']
        )
    messages_table += "</table>"
    return messages_table


# now convert to html
report_html = """
<html>
<head>
<title>ISA-Tab validator | Validation report</title>
</head>
<body>

<p>Validation completed: {valdation_finished}</p>

<p>Info messages</p>
<p>
{info_table}
</p>

<p>Warning messages</p>
<p>
{warnings_table}
</p>

<p>Error messages</p>
<p>
{errors_table}
</p>

</body>
</html>
""".format(
    valdation_finished=json_report['validation_finished'],
    info_table=build_messages(json_report['info']),
    warnings_table=build_messages(json_report['warnings']),
    errors_table=build_messages(json_report['errors'])
)

print(report_html)
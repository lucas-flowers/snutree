#!/usr/bin/env python

import sys
import subprocess
from pathlib import Path
from textwrap import indent
from snutree import api
import snutree.readers.csv as reader_csv
import snutree.readers.sql as reader_sql
import snutree.readers.dot as reader_dot
import snutree.schemas.sigmanu as schema_sigmanu
import snutree.writers.dot as writer_dot
from snutree.cerberus import describe_schema

def get_template():
    with Path('README_TEMPLATE.rst').open('r') as f:
        return f.read()

def generate_readme(template):

    # Get usage information
    result = subprocess.run(
            ['./snutree.py', '--help'],
            stdout=subprocess.PIPE,
            universal_newlines=True, # Python 3.5
            # encoding=sys.getdefaultencoding(), # Python 3.6
            )
    return_code = result.returncode
    if return_code:
        sys.exit(return_code)
    usage = result.stdout

    return template.format(
            CLI_HELP=indent(usage, ' '*4),
            CONFIG_API=describe_schema(api.CONFIG_SCHEMA, level=2),
            CONFIG_READER_CSV=describe_schema(reader_csv.CONFIG_SCHEMA, level=2),
            CONFIG_READER_SQL=describe_schema(reader_sql.CONFIG_SCHEMA, level=2),
            CONFIG_READER_DOT=describe_schema(reader_dot.CONFIG_SCHEMA, level=2),
            CONFIG_SCHEMA_SIGMANU=describe_schema(schema_sigmanu.CONFIG_SCHEMA, level=2),
            CONFIG_WRITER_DOT=describe_schema(writer_dot.CONFIG_SCHEMA, level=2),
            )

def write_readme(readme):
    with Path('README.rst').open('w+') as f:
        f.write(readme)

def check_readme():
    return subprocess.run([
        'python',
        'setup.py',
        'check',
        '--restructuredtext',
        '--strict',
        ], stdout=subprocess.DEVNULL).returncode

def main():
    template = get_template()
    readme = generate_readme(template)
    write_readme(readme)
    return_code = check_readme()
    sys.exit(return_code)

if __name__ == '__main__':
    main()

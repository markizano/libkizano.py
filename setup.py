#!/usr/bin/env python3

import os
import sys
from glob import glob
from pprint import pprint
from setuptools import setup

sys.path.insert(0, os.path.abspath('lib'))

setup_opts = {
    'name'                : 'kizano',
    # We change this default each time we tag a release.
    'version'             : '1.0.0',
    'description'         : 'Kizano code for quick access to functions.',
    'author'              : 'Markizano Draconus',
    'author_email'        : 'markizano@markizano.net',
    'url'                 : 'https://markizano.net/',
    'license'             : 'GNU',

    'tests_require'       : ['nose', 'mock', 'coverage'],
    'install_requires'    : [
    ],
    'package_dir'         : { 'kizano': 'lib/kizano' },
    'packages'            : [
      'kizano',
      'kizano.logger'
    ],
    'scripts'             : glob('bin/*'),
    'test_suite'          : 'tests',
}

try:
    import argparse
    HAS_ARGPARSE = True
except:
    HAS_ARGPARSE = False

if not HAS_ARGPARSE: setup_opts['install_requires'].append('argparse')

# I botch this too many times.
if sys.argv[1] == 'test':
    sys.argv[1] = 'nosetests'

if 'DEBUG' in os.environ: pprint(setup_opts)

setup(**setup_opts)


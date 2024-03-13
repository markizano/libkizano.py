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
    'version'             : '1.0.6',
    'description'         : 'Kizano code for quick access to functions.',
    'long_description'    : ('This is a core library that should allow one to import and run with '
                            'pre-built libraries. Common features like logging and configuration '
                            'management should not need to be re-created in every project. This aims '
                            'to minimize this by providing a core library of swiss army knife of'
                            'common functionality.'),
    'long_description_content_type': 'text/markdown',
    'author'              : 'Markizano Draconus',
    'author_email'        : 'markizano@markizano.net',
    'url'                 : 'https://markizano.net/',
    'license'             : 'GNU',

    'tests_require'       : ['nose', 'mock', 'coverage'],
    'install_requires'    : [
      'PyYAML>=6.0.1',
    ],
    'package_dir'         : { 'kizano': 'lib/kizano' },
    'packages'            : [
      'kizano',
      'kizano.logger'
    ],
    'entry_points'        : {
      'console_scripts': [
        'log = kizano.logger:syslogger'
      ]
    },
    'scripts'             : glob('bin/*'),
    'test_suite'          : 'tests',
}

# I botch this too many times.
if sys.argv[1] == 'test':
    sys.argv[1] = 'nosetests'

if 'DEBUG' in os.environ: pprint(setup_opts)

setup(**setup_opts)

if 'sdist' in sys.argv:
    import gnupg, hashlib
    gpg = gnupg.GPG()
    for artifact in glob('dist/*.tar.gz'):
        # Detach sign the artifact in dist/ folder.
        fd = open(artifact, 'rb')
        checksums = open('dist/CHECKSUMS.txt', 'w+b')
        status = gpg.sign_file(fd, detach=True, output=f'{artifact}.asc')
        print(f'Signed {artifact} with {status.fingerprint}')

        # create a MD5, SHA1 and SHA256 hash of the artifact.
        for hashname in ['md5', 'sha1', 'sha256']:
            hasher = getattr(hashlib, hashname)()
            fd.seek(0,0)
            hasher.update(fd.read())
            digest = hasher.hexdigest()
            checksums.write(f'''{hashname.upper()}:
{digest} {artifact}

'''.encode('utf-8'))
            print(f'Got {artifact}.{hashname} as {digest}')
        checksums.seek(0, 0)
        chk_status = gpg.sign_file(checksums, detach=True, output=f'dist/CHECKSUMS.txt.asc')
        checksums.close()
        fd.close()
        print(f'Signed CHECKSUMS.txt with {chk_status.fingerprint}')

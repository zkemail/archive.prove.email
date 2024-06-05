#!/usr/bin/env python

# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the author be held liable for any damages
# arising from the use of this software.
# 
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
# 
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.
# 
# Copyright (c) 2008 Greg Hewgill http://hewgill.com
#
# This has been modified from the original software.
# Copyright (c) 2011,2012,2018 Scott Kitterman <scott@kitterman.com>

from setuptools import setup
import os
import sys

version = "1.1.6"

kw = {}  # Work-around for lack of 'or' requires in setuptools.
try:
    import DNS
    kw['install_requires'] = ['Py3DNS']
except ImportError:  # If PyDNS is not installed, prefer dnspython
    kw['install_requires'] = ['dnspython>=2.0.0']

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name = "dkimpy",
    version = version,
    description = "DKIM (DomainKeys Identified Mail), ARC (Authenticated Receive Chain), and TLSRPT (TLS Report) email signing and verification",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author = "Scott Kitterman",
    author_email = "scott@kitterman.com",
    url = "https://launchpad.net/dkimpy",
    license = "BSD-like",
    packages = ["dkim"],
    entry_points = {
        'console_scripts' : [
            'arcsign = dkim.arcsign:main',
            'arcverify = dkim.arcverify:main',
            'dkimsign = dkim.dkimsign:main',
            'dkimverify = dkim.dkimverify:main',
            'dknewkey = dkim.dknewkey:main'
        ],
    },
    data_files = [(os.path.join('share', 'man', 'man1'),
        ['man/arcsign.1']), (os.path.join('share', 'man', 'man1'),
        ['man/arcverify.1']),(os.path.join('share', 'man', 'man1'),
        ['man/dkimsign.1']), (os.path.join('share', 'man', 'man1'),
        ['man/dkimverify.1']),(os.path.join('share', 'man', 'man1'),
        ['man/dknewkey.1']),],
    classifiers = [
      'Development Status :: 5 - Production/Stable',
      'Environment :: No Input/Output (Daemon)',
      'Intended Audience :: Developers',
      'License :: DFSG approved',
      'Natural Language :: English',
      'Operating System :: OS Independent',
      'Programming Language :: Python :: 3',
      'Topic :: Communications :: Email :: Mail Transport Agents',
      'Topic :: Communications :: Email :: Filters',
      'Topic :: Internet :: Name Service (DNS)',
      'Topic :: Software Development :: Libraries :: Python Modules'
      ],
    zip_safe = False,
    extras_require={
        'testing': [
            'authres',
            'pynacl',
        ],
        'ed25519':  ['pynacl'],
        'ARC': ['authres'],
        'asyncio': ['aiodns']
    },
    **kw
)

if os.name != 'posix':
    data_files = ''

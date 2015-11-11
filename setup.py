#!/usr/bin/python
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import fnmatch
import os
from distutils.core import setup

PROJECT_NAME = 'graphyte'
PROJECT_DIR = os.path.join(PROJECT_NAME, os.path.dirname(__file__))

# Get all path of *.yaml and *.csv
DATA_PATHS = []
for root, _, filenames in os.walk(PROJECT_DIR):
  DATA_PATHS += [os.path.join(root, filename) for filename in
                 fnmatch.filter(filenames, '*.yaml')]
  DATA_PATHS += [os.path.join(root, filename) for filename in
                 fnmatch.filter(filenames, '*.csv')]

setup(
    name=PROJECT_NAME,
    version='0.1',
    description='Graphyte (Google RAdio PHY TEst)',
    url='https://sites.google.com/a/google.com/graphyte/home',
    author='Chih-Yu Huang',
    author_email='akahuang@google.com',
    license='Chromium',
    packages=[PROJECT_NAME],
    package_data={PROJECT_NAME: DATA_PATHS},
    scripts=['graphyte_main.py'],
    install_requires=['pyyaml'],
    )

#!/usr/bin/python
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from setuptools import find_packages
from setuptools import setup
import os

PROJECT_NAME = 'graphyte'
PROJECT_DIR = os.path.join(PROJECT_NAME, os.path.dirname(__file__))
PACKAGES = find_packages()
PACKAGE_DATA = {package: ['*.json'] for package in PACKAGES}
PACKAGE_DATA[PROJECT_NAME].append('config_files/*')

setup(
    name=PROJECT_NAME,
    version='0.2',
    description='Graphyte (Google RAdio PHY TEst)',
    url='https://sites.google.com/a/google.com/graphyte/home',
    author='Chih-Yu Huang',
    author_email='akahuang@google.com',
    license='Chromium',
    packages=PACKAGES,
    package_data=PACKAGE_DATA)

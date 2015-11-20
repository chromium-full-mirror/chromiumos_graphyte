#!/usr/bin/python
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from distutils.core import setup
import os

PROJECT_NAME = 'graphyte'
PROJECT_DIR = os.path.join(PROJECT_NAME, os.path.dirname(__file__))

setup(
    name=PROJECT_NAME,
    version='0.1',
    description='Graphyte (Google RAdio PHY TEst)',
    url='https://sites.google.com/a/google.com/graphyte/home',
    author='Chih-Yu Huang',
    author_email='akahuang@google.com',
    license='Chromium',
    packages=[
        PROJECT_NAME,
        PROJECT_NAME + '.links',
        PROJECT_NAME + '.dut',
        PROJECT_NAME + '.dut.sample_dut',
        PROJECT_NAME + '.inst',
        PROJECT_NAME + '.inst.anritsu_ml2437a',
        PROJECT_NAME + '.inst.sample_inst'],
    package_data={
        PROJECT_NAME: ['config_files/*'],
        PROJECT_NAME + '.dut.sample_dut': ['*.yaml'],
        PROJECT_NAME + '.inst.anritsu_ml2437a': ['*.yaml'],
        PROJECT_NAME + '.inst.sample_inst': ['*.yaml']},
    scripts=['graphyte_main.py'],
    install_requires=['pyyaml'],
    )

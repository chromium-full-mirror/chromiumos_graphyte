#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Store the global settings of the project."""

import logging
import os
import sys

GRAPHYTE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(GRAPHYTE_DIR, 'config_files')
LOG_DIR = os.path.join(GRAPHYTE_DIR, 'log_files')

DEFAULT_CONFIG_FILE = os.path.join(CONFIG_DIR, 'sample_graphyte_config.json')
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, 'graphyte.log')
DEFAULT_RESULT_FILE = os.path.join(LOG_DIR, 'result.csv')

logger = logging.getLogger('Graphyte')  # pylint: disable=invalid-name

# Graphyte input and output stream
GRAPHYTE_IN = sys.stdin
GRAPHYTE_OUT = sys.stdout

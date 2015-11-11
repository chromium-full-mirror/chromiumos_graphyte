#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Utils class and functions. """

import logging
import os

def SearchConfig(filepath, search_dirs=None):
  """Find the config file and return the content.
  The order of searching is:
  1. relative path
  2. config folder
  3. search_dirs
  """
  config_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            'config_files')
  possible_dirs = ['', config_dir]
  if search_dirs is not None:
    if type(search_dirs) != list:
      search_dirs = [search_dirs]
    possible_dirs += search_dirs
  for possible_dir in possible_dirs:
    if os.path.exists(os.path.join(possible_dir, filepath)):
      return os.path.join(possible_dir, filepath)
  logging.error('Cannot find config file: %s', filepath)
  raise IOError

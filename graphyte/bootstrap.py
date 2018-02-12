#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os

import graphyte_common  # pylint: disable=unused-import
from graphyte.default_setting import DEFAULT_LOG_FILE
from graphyte.default_setting import GRAPHYTE_OUT
from graphyte.utils import graphyte_utils

class Bootstrap(object):
  """Bootstrap of graphyte framework

  Initialize some process-wide resources for graphyte framework
  """

  @staticmethod
  def InitLogger(log_file=None, verbose=False, console_output=True):
    log_file = log_file or DEFAULT_LOG_FILE

    level = logging.DEBUG if verbose else logging.INFO
    log_file = graphyte_utils.PrepareOutputFile(log_file)
    if os.path.exists(log_file):
      os.remove(log_file)
    fmt = '[%(levelname)s] %(asctime)s %(filename)s:%(lineno)d %(message)s'
    date_fmt = '%H:%M:%S'
    formatter = logging.Formatter(fmt, date_fmt)

    root_logger = logging.getLogger('')
    root_logger.setLevel(level)
    file_handler = logging.FileHandler(log_file, 'a')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    if console_output:
      console_handler = logging.StreamHandler(GRAPHYTE_OUT)
      console_handler.setFormatter(formatter)
      root_logger.addHandler(console_handler)

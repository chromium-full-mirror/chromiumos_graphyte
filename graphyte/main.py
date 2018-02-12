#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from argparse import ArgumentParser

import graphyte_common  # pylint: disable=unused-import
from graphyte.bootstrap import Bootstrap
from graphyte import controller
from graphyte.default_setting import logger

def main():
  parser = ArgumentParser()
  parser.add_argument('--config-file', dest='config_file', action='store',
                      type=str, help='The path of config file')
  parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                      help='Enable debug logging', default=False)
  parser.add_argument('--log-file', dest='log_file', action='store',
                      type=str, help='The path of log file')
  parser.add_argument('--result-file', dest='result_file', action='store',
                      type=str, help='The path of result file')
  parser.add_argument('--quiet', dest='console_output',
                      action='store_false', default=True,
                      help='Not output to console')
  options = vars(parser.parse_args())

  Bootstrap.InitLogger(
      log_file=options.pop('log_file'),
      verbose=options.pop('verbose'),
      console_output=options.pop('console_output'))

  # Run Graphyte framework
  logger.info('Starting Graphyte....')
  app = controller.Controller(**options)
  app.Run()


if __name__ == '__main__':
  main()

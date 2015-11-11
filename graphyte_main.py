#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from argparse import ArgumentParser

from graphyte.graphyte import DEFAULT_CONFIG_FILE
from graphyte.graphyte import Graphyte


def main():
  parser = ArgumentParser()
  parser.add_argument('--config-file', dest='config_file', action='store',
                      type=str, default=DEFAULT_CONFIG_FILE,
                      help='The path of config file')
  parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                      help='Enable debug logging', default=False)
  options = parser.parse_args()
  app = Graphyte(**vars(options))
  app.Run()


if __name__ == '__main__':
  main()

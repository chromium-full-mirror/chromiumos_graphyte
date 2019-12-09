#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function

import logging
import os
import sys
import tempfile
import time
import unittest

WORKING_DIR = os.path.dirname(os.path.realpath(__file__))


def PassMessage(message):
  print('\033[22;32m%s\033[22;0m' % message)


def FailMessage(message):
  print('\033[22;31m%s\033[22;0m' % message)


def LogFilePath(dir_name, filename):
  return os.path.join(dir_name, filename.replace('/', '_') + '.log')


def main(argv):
  logging.disable(logging.CRITICAL)  # Ignore all logging output from unittest.
  temp_dir = tempfile.mkdtemp()
  total_tests = 0
  passed_tests = 0
  failed_tests = []
  for filename in argv[1:]:
    if not os.path.isfile(filename):
      FailMessage('File is not found: %s' % filename)
      continue
    if not filename.endswith('.py'):
      FailMessage('File is not python file: %s' % filename)
      continue
    filename = os.path.relpath(filename, WORKING_DIR)
    module_name = filename[:-3].replace('/', '.')

    suite = unittest.defaultTestLoader.loadTestsFromName(module_name)
    start_time = time.time()
    log_file = LogFilePath(temp_dir, filename)
    with open(log_file, 'w') as stream:
      result = unittest.TextTestRunner(stream=stream).run(suite)
    duration = time.time() - start_time
    if result.wasSuccessful():
      PassMessage('*** PASS [%.2f s] %s' % (duration, filename))
      passed_tests += 1
    else:
      FailMessage('*** FAIL [%.2f s] %s' % (duration, filename))
      failed_tests.append(filename)
    total_tests += 1

  print('%d/%d tests passed' % (passed_tests, total_tests))
  if failed_tests:
    print('')
    print('Logs of %d failed tests:' % len(failed_tests))
    for failed_test in failed_tests:
      FailMessage(LogFilePath(temp_dir, failed_test))
    print('To re-test failed unittests, run:')
    print('make test UNITTEST_WHITELIST="%s"' % ' '.join(failed_tests))


if __name__ == '__main__':
  main(sys.argv)

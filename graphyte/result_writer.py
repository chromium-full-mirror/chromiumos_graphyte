#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The module for generating the result file."""

import csv

from .utils import IsInBound
from .utils import PrepareOutputFile


class ResultWriter(object):
  CSV_HEADER = ['test_item', 'power_level', 'result_name',
                'lower_bound', 'upper_bound', 'result', 'pass_or_fail']
  def __init__(self, result_file):
    result_file = PrepareOutputFile(result_file)
    self.fout = open(result_file, 'w')
    self.csv_writer = csv.DictWriter(self.fout, self.CSV_HEADER)
    self.csv_writer.writeheader()

  def __del__(self):
    self.fout.close()

  def WriteResult(self, test_case, result):
    for result_name, bound in test_case.result_limit.iteritems():
      value = result.get(result_name)
      data = {
          'test_item': str(test_case),
          'power_level': test_case.args.get('power_level'),
          'result_name': result_name,
          'lower_bound': str(bound[0]),
          'upper_bound': str(bound[1]),
          'result': value,
          'pass_or_fail': PassString(IsInBound(value, bound))}
      self.csv_writer.writerow(data)

  def WriteTotalResult(self, all_tests_pass):
    data = {
        'test_item': 'TOTAL RESULT',
        'pass_or_fail': PassString(all_tests_pass)}
    self.csv_writer.writerow(data)


def PassString(result):
  return 'PASS' if result else 'FAIL'

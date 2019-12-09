#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The module for generating the result file."""

import csv

import graphyte_common  # pylint: disable=unused-import
from graphyte import testplan
from graphyte.utils.graphyte_utils import IsInBound
from graphyte.utils.graphyte_utils import PrepareOutputFile


class ResultWriter(object):
  CSV_HEADER = ['test_item', 'power_level', 'result_name',
                'lower_bound', 'upper_bound', 'result', 'pass_or_fail']
  def __init__(self, result_file):
    result_file = PrepareOutputFile(result_file)
    self.fout = open(result_file, 'w')
    self.csv_writer = csv.DictWriter(self.fout, self.CSV_HEADER)
    self.csv_writer.writeheader()

  def Close(self):
    if self.fout is not None:
      self.fout.close()
      self.fout = None

  def WriteResult(self, test_case, result):
    """Writes the test result to csv file.

    For the multi-antenna case, we record the result of each antenna separately.
    Then the result value is a number, not a dictionary.

    For example:
      test_case: "WLAN TX ANTENNA-01"
      result: {"avg_power" : {0: 10.4, 1:11.2}}

    Then we will output two lines which test_name, result_name and value are:
      "WLAN TX ANTENNA-01-0", "avg_power", 10.4
      "WLAN TX ANTENNA-01-1", "avg_power", 11.2
    """
    if 'chain_mask' not in test_case.args:
      self._WriteResult(test_case, result)
    else:  # Multi-antenna case
      for antenna_idx in testplan.ChainMaskToList(test_case.args['chain_mask']):
        # Create a new test case which name indicates the antenna.
        new_test_case = test_case.Copy()
        new_test_case.name = '%s-%s' % (test_case.name, antenna_idx)
        # Extract the result for this antenna.
        new_result = {}
        for result_name in test_case.result_limit:
          if result_name not in result:
            continue
          if isinstance(result[result_name], dict):
            new_result[result_name] = result[result_name].get(
                antenna_idx, 'None')
          else:
            new_result[result_name] = result[result_name]
        self._WriteResult(new_test_case, new_result)

  def _WriteResult(self, test_case, result):
    for result_name, bound in test_case.result_limit.items():
      value = result.get(result_name, 'None')
      data = {
          'test_item': test_case.name,
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

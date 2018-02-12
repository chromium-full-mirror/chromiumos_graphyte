#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import copy
import csv
import mock
import os
import tempfile
import unittest

import graphyte_common  # pylint: disable=unused-import
from graphyte import result_writer
from graphyte import testplan


class ResultWriterTest(unittest.TestCase):
  def setUp(self):
    self.temp_csv = tempfile.mktemp(suffix='.csv', prefix='testplan_')
    self.writer = result_writer.ResultWriter(self.temp_csv)

  def tearDown(self):
    if os.path.exists(self.temp_csv):
      os.remove(self.temp_csv)

  def _CompareResultList(self, correct_data):
    """Compare the output CSV file and the correct data.

    Because the order of the data is not guaranteed, we search each data from
    the list and remove it. If all data are matched, the list should be empty at
    the end.

    Args:
      correct_data: the list of the data.

    Raise:
      ValueError if any data is not matched.
    """
    del self.writer
    with open(self.temp_csv) as f:
      reader = csv.DictReader(f)
      for data in reader:
        try:
          correct_data.remove(data)
        except ValueError:
          raise ValueError('%s is not in correct data' % data)
      if correct_data:
        raise ValueError('%r are missing' % correct_data)

  def testSingleAntennaResult(self):
    test_case = mock.create_autospec(spec=testplan.TestCase)
    test_case.name = 'FAKE_TEST_CASE'
    test_case.args = {'power_level': 10}
    test_case.result_limit = {'avg_power': (9, 11)}
    test_case.Copy.return_value = copy.copy(test_case)
    result = {'avg_power': 10.1}
    correct_data = [
        {'test_item': 'FAKE_TEST_CASE',
         'power_level': '10',
         'result_name': 'avg_power',
         'result': '10.1',
         'lower_bound': '9',
         'upper_bound': '11',
         'pass_or_fail': 'PASS'}]

    self.writer.WriteResult(test_case, result)
    self._CompareResultList(correct_data)

  def testSingleAntennaMultiResult(self):
    test_case = mock.create_autospec(spec=testplan.TestCase)
    test_case.name = 'FAKE_TEST_CASE'
    test_case.args = {'power_level': 10}
    test_case.result_limit = {
        'avg_power': (9, 11),
        'evm': (None, -25)}
    test_case.Copy.return_value = copy.copy(test_case)
    result = {
        'avg_power': 10.1,
        'evm': 0}
    correct_data = [
        {'test_item': 'FAKE_TEST_CASE',
         'power_level': '10',
         'result_name': 'avg_power',
         'result': '10.1',
         'lower_bound': '9',
         'upper_bound': '11',
         'pass_or_fail': 'PASS'},
        {'test_item': 'FAKE_TEST_CASE',
         'power_level': '10',
         'result_name': 'evm',
         'result': '0',
         'lower_bound': 'None',
         'upper_bound': '-25',
         'pass_or_fail': 'FAIL'},
        ]

    self.writer.WriteResult(test_case, result)
    self._CompareResultList(correct_data)

  def testMultiAntennaSingleResult(self):
    test_case = mock.create_autospec(spec=testplan.TestCase)
    test_case.name = 'FAKE_TEST_CASE ANTENNA-01'
    test_case.args = {
        'power_level': 10,
        'chain_mask': 3}  # 3 => b'0011, which means antenna 0 and 1 enabled.
    test_case.result_limit = {'avg_power': (9, 11)}
    test_case.Copy.return_value = copy.copy(test_case)
    result = {'avg_power': 10.1}
    correct_data = [
        {'test_item': 'FAKE_TEST_CASE ANTENNA-01-0',
         'power_level': '10',
         'result_name': 'avg_power',
         'result': '10.1',
         'lower_bound': '9',
         'upper_bound': '11',
         'pass_or_fail': 'PASS'},
        {'test_item': 'FAKE_TEST_CASE ANTENNA-01-1',
         'power_level': '10',
         'result_name': 'avg_power',
         'result': '10.1',
         'lower_bound': '9',
         'upper_bound': '11',
         'pass_or_fail': 'PASS'},
        ]

    self.writer.WriteResult(test_case, result)
    self._CompareResultList(correct_data)

  def testMultiAntennaResult(self):
    test_case = mock.create_autospec(spec=testplan.TestCase)
    test_case.name = 'FAKE_TEST_CASE ANTENNA-01'
    test_case.args = {
        'power_level': 10,
        'chain_mask': 3}  # 3 => b'0011, which means antenna 0 and 1 enabled.
    test_case.result_limit = {'avg_power': (9, 11)}
    test_case.Copy.return_value = copy.copy(test_case)
    result = {'avg_power': {0: 10.1, 1: 9.9}}
    correct_data = [
        {'test_item': 'FAKE_TEST_CASE ANTENNA-01-0',
         'power_level': '10',
         'result_name': 'avg_power',
         'result': '10.1',
         'lower_bound': '9',
         'upper_bound': '11',
         'pass_or_fail': 'PASS'},
        {'test_item': 'FAKE_TEST_CASE ANTENNA-01-1',
         'power_level': '10',
         'result_name': 'avg_power',
         'result': '9.9',
         'lower_bound': '9',
         'upper_bound': '11',
         'pass_or_fail': 'PASS'},
        ]

    self.writer.WriteResult(test_case, result)
    self._CompareResultList(correct_data)

  def testSingleAntennaMissingResult(self):
    test_case = mock.create_autospec(spec=testplan.TestCase)
    test_case.name = 'FAKE_TEST_CASE'
    test_case.args = {'power_level': 10}
    test_case.result_limit = {'avg_power': (9, 11)}
    test_case.Copy.return_value = copy.copy(test_case)
    result = {}
    correct_data = [
        {'test_item': 'FAKE_TEST_CASE',
         'power_level': '10',
         'result_name': 'avg_power',
         'result': 'None',
         'lower_bound': '9',
         'upper_bound': '11',
         'pass_or_fail': 'FAIL'}]

    self.writer.WriteResult(test_case, result)
    self._CompareResultList(correct_data)

  def testMultiAntennaMissingResult(self):
    test_case = mock.create_autospec(spec=testplan.TestCase)
    test_case.name = 'FAKE_TEST_CASE ANTENNA-01'
    test_case.args = {
        'power_level': 10,
        'chain_mask': 3}  # 3 => b'0011, which means antenna 0 and 1 enabled.
    test_case.result_limit = {'avg_power': (9, 11)}
    test_case.Copy.return_value = copy.copy(test_case)
    result = {'avg_power': {0: 10.1}}
    correct_data = [
        {'test_item': 'FAKE_TEST_CASE ANTENNA-01-0',
         'power_level': '10',
         'result_name': 'avg_power',
         'result': '10.1',
         'lower_bound': '9',
         'upper_bound': '11',
         'pass_or_fail': 'PASS'},
        {'test_item': 'FAKE_TEST_CASE ANTENNA-01-1',
         'power_level': '10',
         'result_name': 'avg_power',
         'result': 'None',
         'lower_bound': '9',
         'upper_bound': '11',
         'pass_or_fail': 'FAIL'},
        ]

    self.writer.WriteResult(test_case, result)
    self._CompareResultList(correct_data)

if __name__ == '__main__':
  unittest.main()

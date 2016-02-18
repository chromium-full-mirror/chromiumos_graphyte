#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import csv
import os
import tempfile
import unittest

from . import testplan


class TestPlanTest(unittest.TestCase):
  def setUp(self):
    self.temp_path = tempfile.mktemp(suffix='.csv', prefix='testplan_')
    self.test_plan = testplan.TestPlan()

    self.valid_args = [
        '@title', 'component_name', 'rf_type', 'test_type', 'center_freq',
        'power_level', 'standard', 'format', 'bandwidth', 'data_rate',
        'chain_mask', 'nss', 'long_preamble']
    self.valid_args_value = [
        '', 'WLAN_2G', 'WLAN', 'TX_MOD', '[2412, 2437]',
        '18', 'B', 'DSSS', '20', '1',
        '[1, 2]', 'None', '0']
    self.valid_results = [
        '@result', 'evm', 'avg_power', 'freq_error', 'lo_leakage',
        'mask_margin', 'spectral_flatness', 'obw', 'phase_noise']
    self.valid_result_value = [
        '', '(None,-25)', '(16,20)', '(0,20)', '(0,20)',
        '(0,20)', '(0,20)', '(0,20)', '(-20,20)']

  def tearDown(self):
    if os.path.exists(self.temp_path):
      os.remove(self.temp_path)

  def _WriteCSVContent(self, content):
    with open(self.temp_path, 'w') as f:
      writer = csv.writer(f)
      writer.writerows(content)

  def testParseValidWLANContent(self):
    self._WriteCSVContent([
        self.valid_args + self.valid_results,
        self.valid_args_value + self.valid_result_value])

    self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 4)

  def testWrongArgumentTitle(self):
    self._WriteCSVContent([
        self.valid_args + ['wrong_arg'] + self.valid_results,
        self.valid_args_value + ['WRONG_VALUE'] + self.valid_result_value])

    with self.assertRaisesRegexp(ValueError, 'wrong_arg'):
      self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testWrongResultTitle(self):
    self._WriteCSVContent([
        self.valid_args + self.valid_results + ['wrong_result'],
        self.valid_args_value + self.valid_result_value + ['WRONG_VALUE']])

    with self.assertRaisesRegexp(ValueError, 'wrong_result'):
      self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testMissingResultTitle(self):
    self._WriteCSVContent([
        self.valid_args,
        self.valid_args_value])

    with self.assertRaisesRegexp(ValueError, '@result'):
      self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testWrongArgumentValue(self):
    # Wrong value for rf_type
    wrong_args_value = self.valid_args_value[:]
    wrong_args_value[2] = 'WRONG_RF_TYPE'
    self._WriteCSVContent([
        self.valid_args + self.valid_results,
        wrong_args_value + self.valid_result_value])

    with self.assertRaisesRegexp(ValueError, 'WRONG_RF_TYPE'):
      self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testWrongArgumentValueInList(self):
    # Wrong valud for center_freq
    wrong_args_value = self.valid_args_value[:]
    wrong_args_value[4] = '[2412, WRONG_VALUE]'
    self._WriteCSVContent([
        self.valid_args + self.valid_results,
        wrong_args_value + self.valid_result_value])

    with self.assertRaisesRegexp(ValueError, 'WRONG_VALUE'):
      self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 2)

  def testWrongResultValue(self):

    self._WriteCSVContent([
        self.valid_args + ['@result', 'avg_power'],
        self.valid_args_value + ['', 'WRONG_RESULT']])

    with self.assertRaisesRegexp(ValueError, 'WRONG_RESULT'):
      self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testMissingValue(self):
    self._WriteCSVContent([
        self.valid_args + self.valid_results,
        self.valid_args_value])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testMissingTitle(self):
    self._WriteCSVContent([
        self.valid_args_value + self.valid_result_value])

    with self.assertRaisesRegexp(ValueError, 'title'):
      self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testParseValidTestplanConfig(self):
    self._WriteCSVContent([
        ['@config', 'KEY', 'VALUE1']])

    self.test_plan.ParseCsvFile(self.temp_path)
    self.assertEquals('VALUE1', self.test_plan.test_config['KEY'])

  def testParseWrongConfigExtraArgument(self):
    self._WriteCSVContent([
        ['@config', 'KEY', 'VALUE1', 'EXTRA_ARG']])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCsvFile(self.temp_path)

  def testParseWrongConfigMissingValue(self):
    self._WriteCSVContent([
        ['@config', 'KEY']])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCsvFile(self.temp_path)

  def testLoadSampleTestPlan(self):
    sample_file = 'sample_testplan.csv'
    self.test_plan = testplan.TestPlan(sample_file)
    self.assertTrue(len(self.test_plan) > 0)

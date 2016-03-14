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


class WLANTestPlanTest(unittest.TestCase):
  def setUp(self):
    self.temp_path = tempfile.mktemp(suffix='.csv', prefix='testplan_')
    self.test_plan = testplan.TestPlan()

    self.valid_args = [
        '@title', 'component_name', 'rf_type', 'test_type', 'center_freq',
        'power_level', 'standard', 'bandwidth', 'data_rate', 'chain_mask',
        'nss', 'long_preamble']
    self.valid_args_value = [
        '', 'WLAN_2G', 'WLAN', 'TX_MOD', '[2412, 2437]',
        '18', 'B', '20', '1', '[1, 2]',
        'None', '0']
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

  def testCommentedContent(self):
    self._WriteCSVContent([
        ['#', 'This is comment'],
        ['#This is also comment', 'hello world'],
        [' # We will ignore the space at the beginning', 'yeah!!'],
        self.valid_args + self.valid_results,
        self.valid_args_value + self.valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 4)

  def testParseValidWLANContent(self):
    self._WriteCSVContent([
        self.valid_args + self.valid_results,
        self.valid_args_value + self.valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 4)

  def testMissingArgumentTitle(self):
    invalid_args = self.valid_args[:-1]
    invalid_args_value = self.valid_args_value[:-1]
    self._WriteCSVContent([
        invalid_args + self.valid_results,
        invalid_args_value + self.valid_result_value])

    with self.assertRaisesRegexp(ValueError, 'missing'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testWrongArgumentTitle(self):
    self._WriteCSVContent([
        self.valid_args + ['wrong_arg'] + self.valid_results,
        self.valid_args_value + ['WRONG_VALUE'] + self.valid_result_value])

    with self.assertRaisesRegexp(ValueError, 'wrong_arg'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testWrongResultTitle(self):
    self._WriteCSVContent([
        self.valid_args + self.valid_results + ['wrong_result'],
        self.valid_args_value + self.valid_result_value + ['WRONG_VALUE']])

    with self.assertRaisesRegexp(ValueError, 'wrong_result'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testMissingResultTitle(self):
    self._WriteCSVContent([
        self.valid_args,
        self.valid_args_value])

    with self.assertRaisesRegexp(ValueError, '@result'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testWrongArgumentValue(self):
    # Wrong value for rf_type
    wrong_args_value = self.valid_args_value[:]
    wrong_args_value[2] = 'WRONG_RF_TYPE'
    self._WriteCSVContent([
        self.valid_args + self.valid_results,
        wrong_args_value + self.valid_result_value])

    with self.assertRaisesRegexp(ValueError, 'WRONG_RF_TYPE'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testWrongArgumentValueInList(self):
    # Wrong valud for center_freq
    wrong_args_value = self.valid_args_value[:]
    wrong_args_value[4] = '[2412, WRONG_VALUE]'
    self._WriteCSVContent([
        self.valid_args + self.valid_results,
        wrong_args_value + self.valid_result_value])

    with self.assertRaisesRegexp(ValueError, 'WRONG_VALUE'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 2)

  def testWrongResultValue(self):

    self._WriteCSVContent([
        self.valid_args + ['@result', 'avg_power'],
        self.valid_args_value + ['', 'WRONG_RESULT']])

    with self.assertRaisesRegexp(ValueError, 'WRONG_RESULT'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testMissingValue(self):
    self._WriteCSVContent([
        self.valid_args + self.valid_results,
        self.valid_args_value])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testMissingTitle(self):
    self._WriteCSVContent([
        self.valid_args_value + self.valid_result_value])

    with self.assertRaisesRegexp(ValueError, 'title'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testParseValidTestplanConfig(self):
    self._WriteCSVContent([
        ['@config', 'KEY', 'VALUE1']])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals('VALUE1', self.test_plan.test_config['KEY'])

  def testParseWrongConfigExtraArgument(self):
    self._WriteCSVContent([
        ['@config', 'KEY', 'VALUE1', 'EXTRA_ARG']])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCSVFile(self.temp_path)

  def testParseWrongConfigMissingValue(self):
    self._WriteCSVContent([
        ['@config', 'KEY']])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCSVFile(self.temp_path)

  def testLoadSampleTestPlan(self):
    sample_file = 'sample_testplan.csv'
    self.test_plan = testplan.TestPlan(sample_file)
    self.assertTrue(len(self.test_plan) > 0)


class BluetoothTestPlanTest(unittest.TestCase):
  def setUp(self):
    self.temp_path = tempfile.mktemp(suffix='.csv', prefix='testplan_')
    self.test_plan = testplan.TestPlan()

    self.valid_args = [
        '@title', 'component_name', 'rf_type', 'test_type', 'center_freq',
        'power_level', 'packet_type']

  def tearDown(self):
    if os.path.exists(self.temp_path):
      os.remove(self.temp_path)

  def _WriteCSVContent(self, content):
    with open(self.temp_path, 'w') as f:
      writer = csv.writer(f)
      writer.writerows(content)

  def testBDRValidValue(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX_MOD', '[2412, 2437]',
        '18', 'DH5']
    valid_results = [
        '@result', 'bandwidth_20db', 'delta_f2_f1']
    valid_result_value = [
        '', '(16,20)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) > 0)

  def testEDRValidValue(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX_MOD', '[2412, 2437]',
        '18', '3DH5']
    valid_results = [
        '@result', 'edr_evm_avg', 'edr_evm_peak', 'edr_extreme_omega_0',
        'edr_extreme_omega_i0', 'edr_omega_i', 'edr_power_diff',
        'edr_prob_evm_99_pass']
    valid_result_value = [
        '', '(0,20)', '(0,20)', '(0,20)', '(0,20)', '(0,20)', '(0,20)', '(0,2)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) > 0)

  def testLEValidValue(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX_MOD', '[2412, 2437]',
        '18', 'LE']
    valid_results = [
        '@result', 'freq_offset', 'delta_f0_fn_max', 'delta_f1_avg',
        'delta_f1_f0', 'delta_f2_f1_avg', 'delta_f2_avg', 'delta_f2_max',
        'delta_fn_fn5_max']
    valid_result_value = [
        '', '(0,20)', '(0,20)', '(0,20)', '(0,20)', '(0,20)', '(0,20)',
        '(0,20)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) > 0)

  def testBDRInvalidValue(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX_MOD', '[2412, 2437]',
        '18', 'DH5']
    invalid_results = [
        '@result', 'edr_evm_avg', 'freq_offset']
    invalid_result_value = [
        '', '(16,20)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + invalid_results,
        valid_args_value + invalid_result_value])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testEDRInvalidValue(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX_MOD', '[2412, 2437]',
        '18', 'DH5']
    invalid_results = [
        '@result', 'bandwidth_20db', 'freq_offset']
    invalid_result_value = [
        '', '(16,20)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + invalid_results,
        valid_args_value + invalid_result_value])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testLEInvalidValue(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX_MOD', '[2412, 2437]',
        '18', 'DH5']
    invalid_results = [
        '@result', 'bandwidth_20db', 'edr_evm_avg']
    invalid_result_value = [
        '', '(16,20)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + invalid_results,
        valid_args_value + invalid_result_value])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testBitPatternPRBS9(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX_MOD', '2412',
        '18', 'DH5']
    valid_results = [
        '@result', 'avg_power', 'bandwidth_20db', 'acp_5', 'acp_4',
        'acp_3', 'acp_2', 'acp_1', 'acp0', 'acp1',
        'acp2', 'acp3', 'acp4', 'acp5']
    valid_result_value = [
        '', '(16,20)', '(0,20)', '(0,20)', '(0,20)',
        '(0,20)', '(0,20)', '(0,20)', '(0,20)', '(0,20)',
        '(0,20)', '(0,20)', '(0,20)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 1)
    self.assertTrue(self.test_plan[0].args['bit_pattern'] == 'PRBS9')

  def testLEBitPatternPRBS9(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX_MOD', '2412',
        '18', 'LE']
    valid_results = [
        '@result', 'avg_power', 'freq_offset', 'acp_5', 'acp_4',
        'acp_3', 'acp_2', 'acp_1', 'acp0', 'acp1',
        'acp2', 'acp3', 'acp4', 'acp5']
    valid_result_value = [
        '', '(16,20)', '(0,20)', '(0,20)', '(0,20)',
        '(0,20)', '(0,20)', '(0,20)', '(0,20)', '(0,20)',
        '(0,20)', '(0,20)', '(0,20)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 1)
    self.assertTrue(self.test_plan[0].args['bit_pattern'] == 'PRBS9')

  def testBitPatternF0(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX_MOD', '2412',
        '18', 'LE']
    valid_results = [
        '@result', 'freq_deviation', 'delta_f1_avg']
    valid_result_value = [
        '', '(16,20)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 1)
    self.assertTrue(self.test_plan[0].args['bit_pattern'] == 'F0')

  def testBitPatternAA(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX_MOD', '2412',
        '18', 'DH1']
    valid_results = [
        '@result', 'delta_f2_f1']
    valid_result_value = [
        '', '(16,20)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 1)
    self.assertTrue(self.test_plan[0].args['bit_pattern'] == 'AA')

  def testLEBitPatternAA(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX_MOD', '2412',
        '18', 'LE']
    valid_results = [
        '@result', 'delta_f2_avg', 'delta_f2_max', 'delta_f1_f0',
        'delta_f2_f1_avg', 'delta_f0_fn_max', 'delta_fn_fn5_max']
    valid_result_value = [
        '', '(16,20)', '(0,20)', '(16,20)',
        '(16,20)', '(0,20)', '(16,20)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 1)
    self.assertTrue(self.test_plan[0].args['bit_pattern'] == 'AA')

  def testSplitByBitPattern(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX_MOD', '2412',
        '18', 'LE']
    valid_results = [
        '@result', 'avg_power',  # bit_pattern is PRBS9
        'freq_deviation', 'delta_f1_avg',  # bit_pattern is F0
        'delta_f2_avg', 'delta_f2_max']  # bit_pattern is AA
    valid_result_value = [
        '', '(16,20)', '(0,20)', '(16,20)', '(0,20)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 3)
    self.assertTrue(set(test.args['bit_pattern'] for test in self.test_plan) ==
                    set(['PRBS9', 'F0', 'AA']))

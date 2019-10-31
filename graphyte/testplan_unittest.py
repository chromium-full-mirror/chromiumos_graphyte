#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import csv
import os
import tempfile
import unittest

import graphyte_common  # pylint: disable=unused-import
from graphyte import testplan

class SampleTestPlanTest(unittest.TestCase):
  def testLoadSampleTestPlan(self):
    sample_file = 'sample_testplan.csv'
    test_plan = testplan.TestPlan(sample_file)
    self.assertTrue(len(test_plan) > 0)


class WLANTestPlanTest(unittest.TestCase):
  def setUp(self):
    self.temp_path = tempfile.mktemp(suffix='.csv', prefix='testplan_')
    self.test_plan = testplan.TestPlan()

    self.valid_args = [
        '@title', 'component_name', 'rf_type', 'test_type', 'center_freq',
        'power_level', 'standard', 'bandwidth', 'data_rate', 'chain_mask',
        'nss', 'long_preamble']
    self.valid_args_value = [
        '', 'WLAN_2G', 'WLAN', 'TX', '[2412, 2437]',
        '18', 'B', '20', '1', '[1, 2]',
        'None', '0']
    self.valid_results = [
        '@result', 'evm', 'avg_power', 'freq_error', 'lo_leakage',
        'mask_margin', 'spectral_flatness', 'obw', 'phase_noise']
    self.valid_result_value = [
        '', '(None,-25)', '(16,20)', '(0,20)', '(None,-15)',
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
    self.assertEquals(4, len(self.test_plan))

  def testParseValidWLANContent(self):
    self._WriteCSVContent([
        self.valid_args + self.valid_results,
        self.valid_args_value + self.valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(4, len(self.test_plan))

  def testMissingArgumentTitle(self):
    invalid_args = self.valid_args[:-1]
    invalid_args_value = self.valid_args_value[:-1]
    self._WriteCSVContent([
        invalid_args + self.valid_results,
        invalid_args_value + self.valid_result_value])

    with self.assertRaisesRegexp(ValueError, 'missing'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(0, len(self.test_plan))

  def testWrongArgumentTitle(self):
    self._WriteCSVContent([
        self.valid_args + ['wrong_arg'] + self.valid_results,
        self.valid_args_value + ['WRONG_VALUE'] + self.valid_result_value])

    with self.assertRaisesRegexp(ValueError, 'wrong_arg'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(0, len(self.test_plan))

  def testWrongResultTitle(self):
    self._WriteCSVContent([
        self.valid_args + self.valid_results + ['wrong_result'],
        self.valid_args_value + self.valid_result_value + ['WRONG_VALUE']])

    with self.assertRaisesRegexp(ValueError, 'wrong_result'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(0, len(self.test_plan))

  def testMissingResultTitle(self):
    self._WriteCSVContent([
        self.valid_args,
        self.valid_args_value])

    with self.assertRaisesRegexp(ValueError, '@result'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(0, len(self.test_plan))

  def testWrongArgumentValue(self):
    # Wrong value for rf_type
    wrong_args_value = self.valid_args_value[:]
    wrong_args_value[2] = 'WRONG_RF_TYPE'
    self._WriteCSVContent([
        self.valid_args + self.valid_results,
        wrong_args_value + self.valid_result_value])

    with self.assertRaisesRegexp(ValueError, 'WRONG_RF_TYPE'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(0, len(self.test_plan))

  def testWrongArgumentValueInList(self):
    # Wrong valud for center_freq
    wrong_args_value = self.valid_args_value[:]
    wrong_args_value[4] = '[2412, WRONG_VALUE]'
    self._WriteCSVContent([
        self.valid_args + self.valid_results,
        wrong_args_value + self.valid_result_value])

    with self.assertRaisesRegexp(ValueError, 'WRONG_VALUE'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(2, len(self.test_plan))

  def testWrongResultValue(self):

    self._WriteCSVContent([
        self.valid_args + ['@result', 'avg_power'],
        self.valid_args_value + ['', 'WRONG_RESULT']])

    with self.assertRaisesRegexp(ValueError, 'WRONG_RESULT'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(0, len(self.test_plan))

  def testMissingValue(self):
    self._WriteCSVContent([
        self.valid_args + self.valid_results,
        self.valid_args_value])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(0, len(self.test_plan))

  def testMissingTitle(self):
    self._WriteCSVContent([
        self.valid_args_value + self.valid_result_value])

    with self.assertRaisesRegexp(ValueError, 'title'):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(0, len(self.test_plan))

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
        '', 'BT', 'BLUETOOTH', 'TX', '[2412, 2437]',
        '18', '1DH5']
    valid_results = [
        '@result', 'bandwidth_20db', 'delta_f2_f1_avg_ratio']
    valid_result_value = [
        '', '(0,1.0)', '(0.8,None)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) > 0)

  def testEDRValidValue(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX', '[2412, 2437]',
        '18', '3DH5']
    valid_results = [
        '@result', 'edr_evm_avg', 'edr_evm_peak', 'edr_extreme_omega_0',
        'edr_extreme_omega_i0', 'edr_omega_i', 'edr_power_diff',
        'edr_prob_evm_99_pass']
    valid_result_value = [
        '', '(0, 13)', '(0, 25)', '(-10, 10)', '(-75, 75)', '(-75, 75)',
        '(-4, 1)', '(0,2)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) > 0)

  def testLEValidValue(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX', '[2412, 2437]',
        '18', 'LE']
    valid_results = [
        '@result', 'freq_offset', 'delta_f0_fn_max', 'delta_f1_avg',
        'delta_f1_f0', 'delta_f2_f1_avg_ratio', 'delta_f2_avg', 'delta_f2_max',
        'delta_fn_fn5_max']
    valid_result_value = [
        '', '(0,20)', '(0,20)', '(225, 275)', '(0,20)', '(0.8, None)', '(0,20)',
        '(182, None)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertTrue(len(self.test_plan) > 0)

  def testBDRInvalidValue(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX', '[2412, 2437]',
        '18', '1DH5']
    invalid_results = [
        '@result', 'edr_evm_avg', 'freq_offset']
    invalid_result_value = [
        '', '(16,20)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + invalid_results,
        valid_args_value + invalid_result_value])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(0, len(self.test_plan))

  def testEDRInvalidValue(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX', '[2412, 2437]',
        '18', '2DH5']
    invalid_results = [
        '@result', 'bandwidth_20db', 'freq_offset']
    invalid_result_value = [
        '', '(16,20)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + invalid_results,
        valid_args_value + invalid_result_value])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(0, len(self.test_plan))

  def testLEInvalidValue(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX', '[2412, 2437]',
        '18', 'LE']
    invalid_results = [
        '@result', 'bandwidth_20db', 'edr_evm_avg']
    invalid_result_value = [
        '', '(16,20)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + invalid_results,
        valid_args_value + invalid_result_value])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(0, len(self.test_plan))

  def testBDRBitPatternPRBS9(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX', '2412',
        '18', '1DH5']
    valid_results = [
        '@result', 'avg_power', 'bandwidth_20db', 'acp_5', 'acp_4',
        'acp_3', 'acp_2', 'acp_1', 'acp0', 'acp1',
        'acp2', 'acp3', 'acp4', 'acp5']
    valid_result_value = [
        '', '(16,20)', '(0, 1.0)', '(None, -40)', '(None, -40)',
        '(None, -40)', '(None, -40)', '(None, -40)', '(None, -40)',
        '(None, -40)', '(None, -40)', '(None, -40)', '(None, -40)',
        '(None, -40)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(1, len(self.test_plan))
    self.assertEquals('PRBS9', self.test_plan[0].args['bit_pattern'])

  def testEDRBitPatternPRBS9(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX', '2412',
        '18', '2DH5']
    valid_results = [
        '@result', 'avg_power', 'freq_deviation', 'edr_evm_avg', 'edr_evm_peak',
        'edr_extreme_omega_0', 'edr_extreme_omega_i0', 'edr_omega_i',
        'edr_power_diff', 'edr_prob_evm_99_pass']
    valid_result_value = [
        '', '(16,20)', '(0,20)', '(0,20)', '(0,20)', '(-10, 10)', '(0,20)',
        '(0,20)', '(-4, 1)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(1, len(self.test_plan))
    self.assertEquals('PRBS9', self.test_plan[0].args['bit_pattern'])

  def testLEBitPatternPRBS9(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX', '2412',
        '18', 'LE']
    valid_results = [
        '@result', 'avg_power', 'freq_offset', 'acp_5', 'acp_4',
        'acp_3', 'acp_2', 'acp_1', 'acp0', 'acp1',
        'acp2', 'acp3', 'acp4', 'acp5']
    valid_result_value = [
        '', '(16,20)', '(0,20)', '(None, -30)', '(None, -30)',
        '(None, -30)', '(None, -30)', '(0,20)', '(None, -30)', '(None, -30)',
        '(None, -30)', '(None, -30)', '(None, -30)', '(None, -30)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(1, len(self.test_plan))
    self.assertEquals('PRBS9', self.test_plan[0].args['bit_pattern'])

  def testBDRBitPatternF0(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX', '2412',
        '18', '1DH5']
    valid_results = [
        '@result', 'delta_f1_avg', 'freq_deviation']
    valid_result_value = [
        '', '(140, 175)', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(1, len(self.test_plan))
    self.assertEquals('F0', self.test_plan[0].args['bit_pattern'])

  def testLEBitPatternF0(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX', '2412',
        '18', 'LE']
    valid_results = [
        '@result', 'delta_f1_avg']
    valid_result_value = [
        '', '(225, 275)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(1, len(self.test_plan))
    self.assertEquals('F0', self.test_plan[0].args['bit_pattern'])

  def testBDRBitPatternAA(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX', '2412',
        '18', '1DH5']
    valid_results = [
        '@result', 'freq_drift', 'delta_f2_avg', 'delta_f2_max']
    valid_result_value = [
        '', '(16,20)', '(16,20)', '(115, None)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(1, len(self.test_plan))
    self.assertEquals('AA', self.test_plan[0].args['bit_pattern'])

  def testLEBitPatternAA(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX', '2412',
        '18', 'LE']
    valid_results = [
        '@result', 'delta_f2_avg', 'delta_f2_max', 'delta_f1_f0',
        'delta_f0_fn_max', 'delta_fn_fn5_max']
    valid_result_value = [
        '', '(16,20)', '(185, None)', '(None, 23)',
        '(None, 50)', '(None, 20)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(1, len(self.test_plan))
    self.assertEquals('AA', self.test_plan[0].args['bit_pattern'])

  def testSplitByBitPattern(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX', '2412',
        '18', 'LE']
    valid_results = [
        '@result', 'avg_power',  # bit_pattern is PRBS9
        'delta_f1_avg',  # bit_pattern is F0
        'delta_f2_avg', 'delta_f2_max']  # bit_pattern is AA
    valid_result_value = [
        '', '(16,20)', '(225, 275)', '(0,20)', '(185, None)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(3, len(self.test_plan))
    self.assertEquals(set(['PRBS9', 'F0', 'AA']),
                      set(test.args['bit_pattern'] for test in self.test_plan))

  def testDeltaF2F1Avg(self):
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'TX', '2412',
        '18', 'LE']
    valid_results = [
        '@result', 'delta_f2_f1_avg_ratio']
    valid_result_value = [
        '', '(0.8,None)']

    self._WriteCSVContent([
        self.valid_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(2, len(self.test_plan))
    self.assertEquals(set(['F0', 'AA']),
                      set(test.args['bit_pattern'] for test in self.test_plan))

  def testValidRxLE(self):
    rx_args = ['rx_num_packets']
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'RX', '2412',
        '-70', 'LE', '10000']
    valid_results = [
        '@result', 'rx_per']
    valid_result_value = [
        '', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + rx_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(1, len(self.test_plan))

  def testValidRxBDR(self):
    rx_args = ['rx_num_bits']
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'RX', '2412',
        '-70', '1DH1', '1600000']
    valid_results = [
        '@result', 'rx_ber']
    valid_result_value = [
        '', '(0,0.1)']

    self._WriteCSVContent([
        self.valid_args + rx_args + valid_results,
        valid_args_value + valid_result_value])

    self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(1, len(self.test_plan))

  def testInvalidRxLE(self):
    rx_args = ['rx_num_bits']
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'RX', '2412',
        '18', 'LE', '10000']
    valid_results = [
        '@result', 'rx_ber']
    valid_result_value = [
        '', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + rx_args + valid_results,
        valid_args_value + valid_result_value])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(0, len(self.test_plan))

  def testInvalidRxBDR(self):
    rx_args = ['rx_num_packets']
    valid_args_value = [
        '', 'BT', 'BLUETOOTH', 'RX', '2412',
        '18', '1DH1', '10000']
    valid_results = [
        '@result', 'rx_per']
    valid_result_value = [
        '', '(0,20)']

    self._WriteCSVContent([
        self.valid_args + rx_args + valid_results,
        valid_args_value + valid_result_value])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCSVFile(self.temp_path)
    self.assertEquals(0, len(self.test_plan))

if __name__ == '__main__':
  unittest.main()

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

  def tearDown(self):
    os.remove(self.temp_path)

  def _WriteCSVContent(self, content):
    with open(self.temp_path, 'w') as f:
      writer = csv.writer(f)
      writer.writerows(content)

  def testParseValidCSVContent(self):
    self._WriteCSVContent([
        ['@title', 'rf_type', 'test_type', '@result', 'evm'],
        ['', 'WLAN', 'TX_MOD', '', '(None, -25)']])

    self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 1)

  def testParseListCSVContent(self):
    self._WriteCSVContent([
        ['@title', 'rf_type', 'test_type', '@result', 'evm'],
        ['', '[WLAN, BLUETOOTH]', '[TX_MOD, RX_PER]', '', '(None, -25)']])

    self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 4)

  def testWrongArgumentTitle(self):
    self._WriteCSVContent([
        ['@title', 'wrong_arg', 'rf_type', 'test_type', '@result', 'evm'],
        ['', 'WRONG_ARG', 'WLAN', 'TX_MOD', '', '(None, -25)']])

    with self.assertRaisesRegexp(ValueError, 'wrong_arg'):
      self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testWrongResultTitle(self):
    self._WriteCSVContent([
        ['@title', 'rf_type', 'test_type', '@result', 'wrong_result'],
        ['', 'WLAN', 'TX_MOD', '', '(None, -25)']])

    with self.assertRaisesRegexp(ValueError, 'wrong_result'):
      self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testMissingResultTitle(self):
    self._WriteCSVContent([
        ['@title', 'rf_type', 'test_type'],
        ['', 'WLAN', 'TX_MOD']])

    with self.assertRaisesRegexp(ValueError, '@result'):
      self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testWrongArgumentValue(self):
    self._WriteCSVContent([
        ['@title', 'rf_type', 'test_type', '@result', 'evm'],
        ['', 'WRONG_ARG', 'TX_MOD', '', '(None, -25)']])

    with self.assertRaisesRegexp(ValueError, 'WRONG_ARG'):
      self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testWrongResultValue(self):
    self._WriteCSVContent([
        ['@title', 'rf_type', 'test_type', '@result', 'evm'],
        ['', 'WLAN', 'TX_MOD', '', 'WRONG_RESULT']])

    with self.assertRaisesRegexp(ValueError, 'WRONG_RESULT'):
      self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testMissingValue(self):
    self._WriteCSVContent([
        ['@title', 'rf_type', 'test_type', '@result', 'evm'],
        ['', 'WLAN', 'TX_MOD']])

    with self.assertRaises(ValueError):
      self.test_plan.ParseCsvFile(self.temp_path)
    self.assertTrue(len(self.test_plan) == 0)

  def testMissingTitle(self):
    self._WriteCSVContent([
        ['', 'WLAN', 'TX_MOD']])

    with self.assertRaises(ValueError):
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

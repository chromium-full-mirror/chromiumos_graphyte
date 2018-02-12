#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import csv
import os
import tempfile
import unittest

import graphyte_common  # pylint: disable=unused-import
from graphyte import port_config


class PathlossTest(unittest.TestCase):
  def setUp(self):
    self.temp_path = tempfile.mktemp(suffix='.csv', prefix='pathloss_')
    self.port_config = port_config.PortConfig()

  def tearDown(self):
    os.remove(self.temp_path)

  def _WriteCSVContent(self, content):
    with open(self.temp_path, 'w') as f:
      writer = csv.writer(f)
      writer.writerows(content)

  def testNormal(self):
    self._WriteCSVContent([
        ['title', 1, 2, 3, 4],
        ['pathloss1', 3, 4, 8, 6],
        ['pathloss2', 9, 6, 2, 7]])

    expected = {1: 3, 2: 4, 3: 8, 4: 6}
    result = self.port_config.LoadPathloss(self.temp_path, 'pathloss1')
    self.assertEquals(expected, result.table)
    expected = {1: 9, 2: 6, 3: 2, 4: 7}
    result = self.port_config.LoadPathloss(self.temp_path, 'pathloss2')
    self.assertEquals(expected, result.table)

  def testMissingEntry(self):
    self._WriteCSVContent([
        ['title', 1, 2, 3, 4],
        ['pathloss1', 3, '', 8, 6],
        ['pathloss2', 9, 6, 2]])

    expected = {1: 3, 3: 8, 4: 6}
    result = self.port_config.LoadPathloss(self.temp_path, 'pathloss1')
    self.assertEquals(expected, result.table)
    expected = {1: 9, 2: 6, 3: 2}
    result = self.port_config.LoadPathloss(self.temp_path, 'pathloss2')
    self.assertEquals(expected, result.table)

  def testMissingValue(self):
    self._WriteCSVContent([
        ['title', 1, 2, 3, 4],
        ['pathloss1'],
        ['pathloss2', 9, 6, 2]])

    with self.assertRaisesRegexp(ValueError, 'empty'):
      self.port_config.LoadPathloss(self.temp_path, 'pathloss1')

  def testMissingPathloss(self):
    self._WriteCSVContent([
        ['title', 1, 2, 3, 4],
        ['pathloss2', 9, 6, 2]])

    with self.assertRaisesRegexp(ValueError, ''):
      self.port_config.LoadPathloss(self.temp_path, 'pathloss1')


class PathLossClassTest(unittest.TestCase):

  def testGetPathloss(self):
    pathloss = {10: 1.0,
                20: 5.0,
                30: 10.0}
    pathloss_table = port_config.PathlossTable(pathloss)

    self.assertTrue(bool(pathloss_table))

    # The point in the table
    self.assertEquals(1.0, pathloss_table[10])
    self.assertEquals(5.0, pathloss_table[20])
    self.assertEquals(10.0, pathloss_table[30])

    # Linear interpolation
    self.assertEquals(3.0, pathloss_table[15])
    self.assertEquals(7.5, pathloss_table[25])

    # The point outside the range
    self.assertEquals(1.0, pathloss_table[5])
    self.assertEquals(10.0, pathloss_table[35])

    with self.assertRaisesRegexp(KeyError, 'negative'):
      pathloss_table[-5]  # pylint: disable=W0104

    with self.assertRaises(TypeError):
      pathloss_table[20.0]  # pylint: disable=W0104

    with self.assertRaises(TypeError):
      pathloss_table['20']  # pylint: disable=W0104

    with self.assertRaises(TypeError):
      pathloss_table[[10, 20]]  # pylint: disable=W0104

  def testEmptyPathlossTable(self):
    pathloss_table = port_config.PathlossTable({})

    self.assertFalse(bool(pathloss_table))
    with self.assertRaisesRegexp(KeyError, 'empty'):
      pathloss_table[10]  # pylint: disable=W0104

if __name__ == '__main__':
  unittest.main()

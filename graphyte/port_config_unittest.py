#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import csv
import os
import tempfile
import unittest

from . import port_config


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
    self.assertEquals(expected, result)
    expected = {1: 9, 2: 6, 3: 2, 4: 7}
    result = self.port_config.LoadPathloss(self.temp_path, 'pathloss2')
    self.assertEquals(expected, result)

  def testMissingEntry(self):
    self._WriteCSVContent([
        ['title', 1, 2, 3, 4],
        ['pathloss1', 3, '', 8, 6],
        ['pathloss2', 9, 6, 2]])

    expected = {1: 3, 3: 8, 4: 6}
    result = self.port_config.LoadPathloss(self.temp_path, 'pathloss1')
    self.assertEquals(expected, result)
    expected = {1: 9, 2: 6, 3: 2}
    result = self.port_config.LoadPathloss(self.temp_path, 'pathloss2')
    self.assertEquals(expected, result)

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

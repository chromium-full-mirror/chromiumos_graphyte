#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import math
import time
import unittest

from . import utils


class IsInBoundTest(unittest.TestCase):
  def testSingleResult(self):
    bound = (None, 10)
    self.assertTrue(utils.IsInBound(10, bound))
    self.assertTrue(utils.IsInBound(10.0, bound))
    self.assertTrue(utils.IsInBound(0.5, bound))
    self.assertFalse(utils.IsInBound(20, bound))
    self.assertFalse(utils.IsInBound(30.1, bound))

    bound = (10, None)
    self.assertTrue(utils.IsInBound(10, bound))
    self.assertTrue(utils.IsInBound(10.0, bound))
    self.assertFalse(utils.IsInBound(0.5, bound))
    self.assertTrue(utils.IsInBound(20, bound))
    self.assertTrue(utils.IsInBound(30.1, bound))

    bound = (0, 10)
    self.assertTrue(utils.IsInBound(0, bound))
    self.assertTrue(utils.IsInBound(0.0, bound))
    self.assertTrue(utils.IsInBound(10, bound))
    self.assertTrue(utils.IsInBound(10.0, bound))
    self.assertTrue(utils.IsInBound(0.5, bound))
    self.assertFalse(utils.IsInBound(20, bound))
    self.assertFalse(utils.IsInBound(30.1, bound))
    self.assertFalse(utils.IsInBound(-20, bound))
    self.assertFalse(utils.IsInBound(-30.1, bound))

  def testDictResult(self):
    bound = (0, 10)
    self.assertTrue(utils.IsInBound({'test1': 0, 'test2': 5.5}, bound))
    self.assertFalse(utils.IsInBound({'test1': -1, 'test2': 5.5}, bound))
    self.assertFalse(utils.IsInBound({'test1': -1, 'test2': 12.4}, bound))

  def testWrongTypeResult(self):
    bound = (0, 10)
    self.assertFalse(utils.IsInBound(None, bound))
    self.assertFalse(utils.IsInBound([1, 2, 3], bound))
    self.assertFalse(utils.IsInBound('TEST', bound))
    self.assertFalse(utils.IsInBound({'test1': 'WRONG RESULT'}, bound))


class CalculateAverageTest(unittest.TestCase):
  def setUp(self):
    self.values = [1.0, 3.0, 8.0]
    self.answer = 4.0

  def testLinearAverage(self):
    self.assertEquals(self.answer,
                      utils.CalculateAverage(self.values, 'Linear'))

  def testLogAverage10(self):
    db_10 = lambda x: 10 * math.log10(x)
    answer = db_10(self.answer)
    values = map(db_10, self.values)
    self.assertEquals(answer, utils.CalculateAverage(values, '10Log10'))

  def testLogAverage20(self):
    db_20 = lambda x: 20 * math.log10(x)
    answer = db_20(self.answer)
    values = map(db_20, self.values)
    self.assertEquals(answer, utils.CalculateAverage(values, '20Log10'))

  def testEmptyList(self):
    ret = utils.CalculateAverage([], 'Linear')
    self.assertTrue(math.isnan(ret))

  def testOneItem(self):
    value = 1234.5678
    ret = utils.CalculateAverage([value], 'Linear')
    self.assertEquals(value, ret)
    ret = utils.CalculateAverage([value], '10Log10')
    self.assertEquals(value, ret)
    ret = utils.CalculateAverage([value], '20Log10')
    self.assertEquals(value, ret)

  def testExtremeValue(self):
    ret = utils.CalculateAverage([-10000, -10000], '10Log10')
    self.assertEquals(float('-inf'), ret)
    ret = utils.CalculateAverage([10000, 10000], '10Log10')
    self.assertTrue(math.isnan(ret))


class WaitForTest(unittest.TestCase):

  def testWaitFor(self):
    def _ReturnTrueAfter(period):
      return time.time() > period

    now = time.time()
    ret = utils.WaitFor(lambda: _ReturnTrueAfter(now + 0.5), timeout_secs=1)
    self.assertEquals(True, ret)

    now = time.time()
    with self.assertRaises(utils.TimeoutError):
      utils.WaitFor(lambda: _ReturnTrueAfter(now + 1), timeout_secs=0.5)


class EnumTest(unittest.TestCase):
  def testArgsEnum(self):
    ret = utils.Enum('A', 'B', 'C')
    self.assertEquals(ret.A, 0)
    self.assertEquals(ret.B, 1)
    self.assertEquals(ret.C, 2)

  def testKwargsEnum(self):
    ret = utils.Enum(A='a', B=1, C=False)
    self.assertEquals(ret.A, 'a')
    self.assertEquals(ret.B, 1)
    self.assertEquals(ret.C, False)

  def testArgsAndKwargsEnum(self):
    ret = utils.Enum('foo', 'bar', A='a', B=1, C=None)
    self.assertEquals(ret.foo, 0)
    self.assertEquals(ret.bar, 1)
    self.assertEquals(ret.A, 'a')
    self.assertEquals(ret.B, 1)
    self.assertEquals(ret.C, None)

  def testEnumImmutable(self):
    ret = utils.Enum('foo')
    with self.assertRaises(AttributeError):
      ret.foo = 'NO WAY!!'

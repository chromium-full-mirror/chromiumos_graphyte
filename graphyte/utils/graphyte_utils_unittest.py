#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import math
import mock
import unittest

import graphyte_common  # pylint: disable=unused-import
from graphyte.utils import graphyte_utils


class IsInBoundTest(unittest.TestCase):
  def testSingleResult(self):
    bound = (None, 10)
    self.assertTrue(graphyte_utils.IsInBound(10, bound))
    self.assertTrue(graphyte_utils.IsInBound(10.0, bound))
    self.assertTrue(graphyte_utils.IsInBound(0.5, bound))
    self.assertFalse(graphyte_utils.IsInBound(20, bound))
    self.assertFalse(graphyte_utils.IsInBound(30.1, bound))

    bound = (10, None)
    self.assertTrue(graphyte_utils.IsInBound(10, bound))
    self.assertTrue(graphyte_utils.IsInBound(10.0, bound))
    self.assertFalse(graphyte_utils.IsInBound(0.5, bound))
    self.assertTrue(graphyte_utils.IsInBound(20, bound))
    self.assertTrue(graphyte_utils.IsInBound(30.1, bound))

    bound = (0, 10)
    self.assertTrue(graphyte_utils.IsInBound(0, bound))
    self.assertTrue(graphyte_utils.IsInBound(0.0, bound))
    self.assertTrue(graphyte_utils.IsInBound(10, bound))
    self.assertTrue(graphyte_utils.IsInBound(10.0, bound))
    self.assertTrue(graphyte_utils.IsInBound(0.5, bound))
    self.assertFalse(graphyte_utils.IsInBound(20, bound))
    self.assertFalse(graphyte_utils.IsInBound(30.1, bound))
    self.assertFalse(graphyte_utils.IsInBound(-20, bound))
    self.assertFalse(graphyte_utils.IsInBound(-30.1, bound))

  def testDictResult(self):
    bound = (0, 10)
    self.assertTrue(
        graphyte_utils.IsInBound({'test1': 0, 'test2': 5.5}, bound))
    self.assertFalse(
        graphyte_utils.IsInBound({'test1': -1, 'test2': 5.5}, bound))
    self.assertFalse(
        graphyte_utils.IsInBound({'test1': -1, 'test2': 12.4}, bound))

  def testWrongTypeResult(self):
    bound = (0, 10)
    self.assertFalse(graphyte_utils.IsInBound(None, bound))
    self.assertFalse(graphyte_utils.IsInBound([1, 2, 3], bound))
    self.assertFalse(graphyte_utils.IsInBound('TEST', bound))
    self.assertFalse(graphyte_utils.IsInBound({'test1': 'WRONG RESULT'}, bound))


class MakeMockPassResultTest(unittest.TestCase):
  def testNormalLimit(self):
    key = 'TEST1'
    bound = (0, 10)
    ret = graphyte_utils.MakeMockPassResult({key: bound})
    self.assertTrue(key in ret)
    self.assertTrue(graphyte_utils.IsInBound(ret, bound))

  def testNoLowerBoundLimit(self):
    key = 'TEST1'
    bound = (None, 10)
    ret = graphyte_utils.MakeMockPassResult({key: bound})
    self.assertTrue(key in ret)
    self.assertTrue(graphyte_utils.IsInBound(ret, bound))

  def testNoUpperBoundLimit(self):
    key = 'TEST1'
    bound = (0, None)
    ret = graphyte_utils.MakeMockPassResult({key: bound})
    self.assertTrue(key in ret)
    self.assertTrue(graphyte_utils.IsInBound(ret, bound))

  def testNoBoundLimit(self):
    key = 'TEST1'
    bound = (None, None)
    ret = graphyte_utils.MakeMockPassResult({key: bound})
    self.assertTrue(key in ret)
    self.assertTrue(graphyte_utils.IsInBound(ret, bound))

class CalculateAverageTest(unittest.TestCase):
  def setUp(self):
    self.values = [1.0, 3.0, 8.0]
    self.answer = 4.0

  def testLinearAverage(self):
    self.assertEquals(self.answer,
                      graphyte_utils.CalculateAverage(self.values, 'Linear'))

  def testLogAverage10(self):
    db_10 = lambda x: 10 * math.log10(x)
    answer = db_10(self.answer)
    values = map(db_10, self.values)
    self.assertEquals(
        answer, graphyte_utils.CalculateAverage(values, '10Log10'))

  def testLogAverage20(self):
    db_20 = lambda x: 20 * math.log10(x)
    answer = db_20(self.answer)
    values = map(db_20, self.values)
    self.assertEquals(
        answer, graphyte_utils.CalculateAverage(values, '20Log10'))

  def testEmptyList(self):
    ret = graphyte_utils.CalculateAverage([], 'Linear')
    self.assertTrue(math.isnan(ret))

  def testOneItem(self):
    value = 1234.5678
    ret = graphyte_utils.CalculateAverage([value], 'Linear')
    self.assertEquals(value, ret)
    ret = graphyte_utils.CalculateAverage([value], '10Log10')
    self.assertEquals(value, ret)
    ret = graphyte_utils.CalculateAverage([value], '20Log10')
    self.assertEquals(value, ret)

  def testExtremeValue(self):
    ret = graphyte_utils.CalculateAverage([-10000, -10000], '10Log10')
    self.assertEquals(float('-inf'), ret)
    ret = graphyte_utils.CalculateAverage([10000, 10000], '10Log10')
    self.assertTrue(math.isnan(ret))

  def testDictResults(self):
    results = {0: self.values, 1: self.values}
    answer = {0: self.answer, 1: self.answer}
    self.assertEquals(
        answer, graphyte_utils.CalculateAverageResult(results, 'Linear'))


@graphyte_utils.LogFunc
def FakeFunction(*args, **kwargs):
  del args, kwargs


class LogFuncTest(unittest.TestCase):
  @graphyte_utils.LogFunc
  def FakeMethod(self, *args, **kwargs):
    del args, kwargs

  @mock.patch(__name__ + '.graphyte_utils.logger')
  def testArgsAndKwargsMethod(self, mock_logger):
    self.FakeMethod('foo', 'bar', a=1, b=2)
    mock_logger.debug.assert_called_with(
        'Calling %s(%s)', 'FakeMethod', 'foo, bar, a=1, b=2')

  @mock.patch(__name__ + '.graphyte_utils.logger')
  def testArgsAndKwargsFunction(self, mock_logger):
    FakeFunction('foo', 'bar', a=1, b=2)
    mock_logger.debug.assert_called_with(
        'Calling %s(%s)', 'FakeFunction', 'foo, bar, a=1, b=2')


@graphyte_utils.LogAllMethods
class FakeClass(object):
  def Foo(self, *args):
    pass
  def _Bar(self, *args):
    pass


class LogAllMethodsTest(unittest.TestCase):
  @mock.patch(__name__ + '.graphyte_utils.logger')
  def testArgsAndKwargsMethod(self, mock_logger):
    obj = FakeClass()
    obj._Bar(1, 2)  # pylint: disable=protected-access
    mock_logger.debug.assert_not_called()
    obj.Foo(3)
    mock_logger.debug.assert_called_with('Calling %s(%s)', 'FakeClass.Foo', '3')

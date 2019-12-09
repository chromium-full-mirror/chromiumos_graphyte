#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

import graphyte_common  # pylint: disable=unused-import
from graphyte import data_parser


class ParseTest(unittest.TestCase):
  def testConvertEmpty(self):
    self.assertEqual(None, data_parser.Parse(''))
    self.assertEqual(None, data_parser.Parse('  '))

  def testConvertNone(self):
    self.assertEqual(None, data_parser.Parse('None'))
    self.assertEqual(None, data_parser.Parse('none'))
    self.assertEqual(None, data_parser.Parse('null'))

  def testConvertInt(self):
    self.assertEqual(2015, data_parser.Parse('2015'))
    self.assertEqual(-50, data_parser.Parse('-50'))

  def testConvertFloat(self):
    self.assertEqual(3.05, data_parser.Parse('3.05'))
    self.assertEqual(-1.38, data_parser.Parse('-1.38'))

  def testConvertString(self):
    self.assertEqual('RECOMMEND_STYLE', data_parser.Parse('RECOMMEND_STYLE'))
    self.assertEqual('321_Hello_World', data_parser.Parse('321_Hello_World'))

  def testInvalidString(self):
    self.assertRaises(ValueError, data_parser.Parse, 'space inside')
    self.assertRaises(ValueError, data_parser.Parse, '1-1')
    self.assertRaises(ValueError, data_parser.Parse, '"comma,inside"')
    self.assertRaises(ValueError, data_parser.Parse, '"I\'m happy"')

  def testConvertList(self):
    self.assertEqual(['string', 123, None],
                     data_parser.Parse('[string, 123, None]'))
    self.assertEqual(['string', 123, None],
                     data_parser.Parse(' [ string , 123 , None ] '))
    self.assertEqual([None, 123, None],
                     data_parser.Parse(' [ , 123 , None ] '))

  def testConvertTuple(self):
    self.assertEqual(('string', 123, None),
                     data_parser.Parse('(string, 123, None)'))
    self.assertEqual(('string', 123, None),
                     data_parser.Parse('  ( string , 123 , None )  '))
    self.assertEqual((None, 123, None),
                     data_parser.Parse('  ( , 123 , None )  '))


class LiteralCheckerTest(unittest.TestCase):
  def setUp(self):
    self.checker = data_parser.LiteralChecker([int, 'a', None])

  def testCheckerStr(self):
    self.assertEqual(
        "LiteralChecker([%s, 'a', None])" % int, str(self.checker))

  def testValidData(self):
    self.assertTrue(self.checker.CheckData(123))
    self.assertTrue(self.checker.CheckData(-55))
    self.assertTrue(self.checker.CheckData('a'))
    self.assertTrue(self.checker.CheckData(None))

  def testInvalidData(self):
    self.assertFalse(self.checker.CheckData(123.45))
    self.assertFalse(self.checker.CheckData('hello'))
    self.assertFalse(self.checker.CheckData(''))


class ListCheckerTest(unittest.TestCase):
  def setUp(self):
    self.checker = data_parser.ListChecker([int, 'a', None])

  def testCheckerStr(self):
    self.assertEqual(
        "ListChecker([%s, 'a', None])" % int, str(self.checker))

  def testValidData(self):
    self.assertTrue(self.checker.CheckData([123, -55, 'a', None]))
    self.assertTrue(self.checker.CheckData(123))
    self.assertTrue(self.checker.CheckData([]))

  def testInvalidData(self):
    self.assertFalse(self.checker.CheckData(123.45))
    self.assertFalse(self.checker.CheckData([123.45, -55, 'a', None]))


class TupleCheckerTest(unittest.TestCase):
  def setUp(self):
    self.checker = data_parser.TupleChecker([[int, None], ['hello', float]])

  def testCheckerStr(self):
    self.assertEqual(
        "TupleChecker([%s, None], ['hello', %s])" % (int, float),
        str(self.checker))

  def testValidData(self):
    self.assertTrue(self.checker.CheckData((None, 'hello')))
    self.assertTrue(self.checker.CheckData((123, -44.5)))

  def testInvalidData(self):
    self.assertFalse(self.checker.CheckData([123, -44.5]))
    self.assertFalse(self.checker.CheckData((123, -44.5, 'hello')))
    self.assertFalse(self.checker.CheckData(123))
    self.assertFalse(self.checker.CheckData(('hello', 123)))

if __name__ == '__main__':
  unittest.main()

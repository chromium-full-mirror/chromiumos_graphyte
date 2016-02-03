#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

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


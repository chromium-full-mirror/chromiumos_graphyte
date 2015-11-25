#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The module is for parsing data in the test plan.
We implement a parse function to convert string to required data type, and data
checkers for checking the data is valid.
"""

import logging
import re
import types


LEFT_BRACKETS = ['[', '(']
RIGHT_BRACKETS_DICT = {'[': ']', '(': ')'}
BUILDER_DICT = {'[': list, '(': tuple}


def Parse(string, checker=None):
  """Convert the string to the python type. We only support tuple, list, None,
  int, float, and str. There are some restrictions for input:
  1. str only contains [0-9A-Za-z_]
  2. nested structure is not allowed.
  3. Ignore all space.
  """
  def _ParseLiteral(string):
    string = string.strip()
    if string in ['', 'None', 'none', 'null']:
      return None
    try:
      return int(string)
    except ValueError:
      pass
    try:
      return float(string)
    except ValueError:
      pass
    match = re.match(r'\w+', string)
    if not match or match.group(0) != string:
      raise ValueError
    return string

  def _Parse(string):
    string = string.strip()
    if string == '':
      return None
    if string[0] not in LEFT_BRACKETS:
      return _ParseLiteral(string)
    else:
      left, items, right = string[0], string[1:-1], string[-1]
      if right != RIGHT_BRACKETS_DICT[left]:
        raise ValueError
      return BUILDER_DICT[left](map(_ParseLiteral, items.split(',')))

  result = _Parse(string)
  if checker is not None and checker.CheckData(result) is False:
    logging.error('result %s is not in checker %s', result, checker)
    raise ValueError
  return result


class CheckerBase(object):
  """Virtual class for data checker."""
  def CheckData(self, data):
    raise NotImplementedError


class LiteralChecker(CheckerBase):
  """Check whether the literal data matches one of the rules.
  Data should not be list or tuple.
  Each rule might be a type (ex: int, str) or a value.

  For example:
    LiteralChecker([int, 'foo']) would check whether data is a integer or 'foo'.
  """
  def __init__(self, rules):
    if type(rules) != list:
      rules = [rules]
    self.rules = rules

  def __str__(self):
    return str(self.rules)

  @staticmethod
  def _IsMatch(data, rule):
    if type(rule) == type:
      return type(data) == rule
    if type(rule) == types.FunctionType:
      return rule(data)
    return data == rule

  def CheckData(self, data):
    return any([self._IsMatch(data, rule) for rule in self.rules])


class TupleChecker(CheckerBase):
  """Check whether every field of the data matches the corresponding rules.
  Data type should be tuple, the length of the tuple should be the same as the
  length of the rules_list.

  For example:
    TupleChecker([[int, 'foo'], [float, None]]) means the valid data should
    be 2-field tuple. First field should be a integer or 'foo', and the second
    field should be a float or None.
  """
  def __init__(self, rules_list):
    self.checkers = []
    for rules in rules_list:
      self.checkers.append(LiteralChecker(rules))

  def CheckData(self, data):
    if type(data) != tuple or len(data) != len(self.checkers):
      return False
    return all([checker.CheckData(item)
                for checker, item in zip(self.checkers, data)])


class ListChecker(CheckerBase):
  """Check whether all items in the data matches the rules.
  Data type should be list or literal, the length of the data is not limited.

  For example:
    ListChecker([int, 'foo']) means the valid data should be contain integer or
    'foo' only.
  """
  def __init__(self, rules):
    self.checker = LiteralChecker(rules)

  def CheckData(self, data):
    if type(data) != list:
      data = [data]
    return all(map(self.checker.CheckData, data))

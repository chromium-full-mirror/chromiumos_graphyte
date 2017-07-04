#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Utils class and functions. """

import collections
import inspect
import json
import math
import os

from ..default_setting import CONFIG_DIR
from ..default_setting import LOG_DIR
from ..default_setting import logger


def LoadConfig(filepath):
  with open(filepath, 'r') as f:
    return json.load(f)


def OverrideConfig(base, overrides):
  """Recursively overrides non-mapping values inside a mapping object.

  Args:
    base: A mapping object with existing data.
    overrides: A mapping to override values in base.

  Returns:
    The new mapping object with values overridden.
  """
  for key, val in overrides.iteritems():
    if isinstance(val, collections.Mapping):
      base[key] = OverrideConfig(base.get(key, {}), val)
    else:
      base[key] = overrides[key]
  return base


def SearchConfig(filepath, search_dirs=None):
  """Finds the config file and returns the content.

  The order of searching is:
  1. relative path
  2. config folder
  3. search_dirs
  """
  possible_dirs = ['', CONFIG_DIR]
  if search_dirs is not None:
    if type(search_dirs) != list:
      search_dirs = [search_dirs]
    possible_dirs += search_dirs
  for possible_dir in possible_dirs:
    path = os.path.abspath(os.path.join(possible_dir, filepath))
    if os.path.exists(path):
      return path
  logger.error('Cannot find config file: %s', filepath)
  raise IOError


def PrepareOutputFile(file_path):
  """Confirms the output file path is ok.

  1. If the file_path is not absolute, then assign it to default log folder.
  2. Check if the directory exists. If not, create the folder first.
  """
  if not os.path.isabs(file_path):
    logger.debug('file path %s is not absolute, assign to default log folder',
                 file_path)
    file_path = os.path.join(LOG_DIR, file_path)
  dir_path = os.path.dirname(file_path)
  if not os.path.isdir(dir_path):
    logger.debug('%s folder is not existed, create it.', dir_path)
    os.mkdir(os.path.dirname(file_path))
  return file_path


def IsInBound(results, bound):
  """Checks the results meet the bound or not.

  Args:
    results: A number for SISO case, or a dict for MIMO case. The values of the
      dict should be numbers.
    bound: A tuple of the lower bound and uppper bound. The bound is a value or
      None.

  Returns:
    True if all the result are between the lower bound and upper bound.
  """
  def _CheckNumberType(value):
    return isinstance(value, int) or isinstance(value, float)

  def _OneValueInBound(value, bound):
    if value is None:
      return False
    lower_bound, upper_bound = bound
    return ((lower_bound is None or value >= lower_bound) and
            (upper_bound is None or value <= upper_bound))

  if isinstance(results, dict):
    value_list = results.values()
  else:
    value_list = [results]
  if not all([_CheckNumberType(value) for value in value_list]):
    logger.error('The type of the result %s is invalid.', results)
    return False
  return all([_OneValueInBound(value, bound) for value in value_list])


def MakeMockPassResult(result_limit):
  """Makes the result that pass all limit."""
  def _MakeInBoundValue(bound):
    lower, upper = bound
    return lower or upper or 0
  return dict([(key, _MakeInBoundValue(bound))
               for key, bound in result_limit.iteritems()])


def CalculateAverage(values, average_type='Linear'):
  """Calculates the average value.

  Args:
    values: A list of float value.
    average_type: one of 'Linear', '10Log10', '20Log10'.

  Returns:
    the average value.
  """
  length = len(values)
  values = map(float, values)
  if length == 0:
    return float('nan')
  if length == 1:
    return values[0]
  if average_type == 'Linear':
    return sum(values) / length
  else:
    denominator = {
        '10Log10': 10,
        '20Log10': 20}[average_type]
    try:
      actual_values = [math.pow(10, value / denominator) for value in values]
      average_value = sum(actual_values) / length
      return denominator * math.log10(average_value)
    except ValueError:
      return float('-inf')
    except OverflowError:
      logger.warning('The values exceed the range. Return NaN.')
      return float('nan')


def CalculateAverageResult(results, average_type='Linear'):
  """Calculates the average results.

  For WLAN multi-antenna case, the result would be a dict where the key is the
  antenna index. So we handle this kind of situation in this method.

  Args:
    results: a list of float values, or a dict, where the key is antenna index
             and the value is a list of float values. For example:
      [150.12, 149.88, 151.22] or
      {0: [150.12, 149.88, 151.22],
       1: [148.14, 151.79, 150.24]}
    average_type: one of 'Linear', '10Log10', '20Log10'.

  Returns:
    the average results, a float value or a dict where the key is antenna
    index and the value is a float value. For example:
      150.41 or
      {0: 150.41,
       1: 150.06}
  """
  if isinstance(results, list):
    return CalculateAverage(results, average_type)
  elif isinstance(results, dict):
    return {ant_idx: CalculateAverage(values, average_type)
            for ant_idx, values in results.items()}
  else:
    raise TypeError('The type should be list or a dict. %s' % results)


def LogFunc(func, prefix=''):
  """The decorator for logging the function call."""
  def Wrapper(*args, **kwargs):
    args_name = inspect.getargspec(func).args
    if args_name and args_name[0] in ['self', 'cls']:
      real_args = args[1:]
    else:
      real_args = args[:]
    arg_str = ', '.join(map(str, real_args) +
                        ['%s=%r' % (key, val) for key, val in kwargs.items()])
    logger.debug('Calling %s(%s)', prefix + func.__name__, arg_str)
    return func(*args, **kwargs)
  return Wrapper


def LogAllMethods(cls):
  """The class decorator that Logs all the public methods."""
  prefix = cls.__name__ + '.'
  for func_name, func in inspect.getmembers(cls, inspect.ismethod):
    if not func_name.startswith('_'):
      setattr(cls, func_name, LogFunc(func, prefix))
  return cls

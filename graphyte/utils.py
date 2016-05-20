#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Utils class and functions. """

import collections
from contextlib import contextmanager
import inspect
import itertools
import math
import os
import tempfile
import time

from .default_setting import CONFIG_DIR
from .default_setting import LOG_DIR
from .default_setting import logger


def Enum(*args, **kwargs):
  """Create the immutable enumeration set.

  Usage:
    1. C-style enum. The value starts from 0 and increase orderly.
      A = Enum('foo', 'bar')
      then A.foo == 0, A.bar == 1
    2. Key-value pair enum.
      B = Enum(foo='FOO', bar='BAR')
      then B.foo == 'FOO', B.bar == 'BAR'
  """
  fields = dict(zip(args, itertools.count()), **kwargs)
  enum_type = collections.namedtuple('Enum', fields.keys())
  return enum_type(**fields)


def SearchConfig(filepath, search_dirs=None):
  """Find the config file and return the content.
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
  """ Confirm the output file path is ok.
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


@contextmanager
def UnopenedTemporaryFile(**kwargs):
  """Yields an unopened temporary file.

  The file is not opened, and it is deleted when the context manager
  is closed if it still exists at that moment.

  Args:
    Any allowable arguments to tempfile.mkstemp (e.g., prefix,
      suffix, dir).
  """
  f, path = tempfile.mkstemp(**kwargs)
  os.close(f)
  try:
    yield path
  finally:
    if os.path.exists(path):
      os.unlink(path)


def IsInBound(results, bound):
  """Check the results meet the bound or not.

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


def CalculateAverage(values, average_type='Linear'):
  """Calculate the average value.

  Args:
    values: A list of float value.
    average_type: one of 'Linear', '10Log10', '20Log10'.
  Returns: the average value.
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
    deno = {'10Log10': 10,
            '20Log10': 20}[average_type]
    try:
      actual_values = [math.pow(10, value / deno) for value in values]
      average_value = sum(actual_values) / length
      return deno * math.log10(average_value)
    except ValueError:
      return float('-inf')
    except OverflowError:
      logger.warning('The values exceed the range. Return NaN.')
      return float('nan')


class TimeoutError(Exception):
  """Timeout error."""
  def __init__(self, message, output=None):
    Exception.__init__(self)
    self.message = message
    self.output = output

  def __str__(self):
    return repr(self.message)


def WaitFor(condition, timeout_secs, poll_interval_secs=0.1):
  """Wait for the given condition for at most the specified time.

  Args:
    condition: A function object.
    timeout_secs: Timeout value in seconds.
    poll_interval_secs: Interval to poll condition in seconds.

  Raises:
    ValueError: If condition is not a function.
    TimeoutError: If cond does not become True after timeout_secs seconds.
  """
  if not callable(condition):
    raise ValueError('condition must be a callable object')

  condition_name = condition.__name__
  if condition_name == '<lambda>':
    try:
      condition_name = inspect.getsource(condition).strip()
    except IOError:
      pass

  end_time = time.time() + timeout_secs if timeout_secs else float('inf')
  while True:
    if not math.isinf(end_time):
      logger.info('[%ds left] %s', end_time - time.time(), condition_name)
    ret = condition()
    if ret:
      return ret
    if time.time() + poll_interval_secs > end_time:
      error_msg = 'Timeout waiting for condition: %s' % condition_name
      logger.error(error_msg)
      raise TimeoutError(error_msg, ret)
    time.sleep(poll_interval_secs)

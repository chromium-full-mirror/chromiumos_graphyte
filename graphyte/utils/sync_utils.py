# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Syncronization-related utilities (waiting for state change)."""

from __future__ import print_function

from contextlib import contextmanager
import inspect
import logging
import signal
import time

import graphyte_common  # pylint: disable=unused-import
from graphyte.utils import time_utils
from graphyte.utils import type_utils


DEFAULT_TIMEOUT_SECS = 10
DEFAULT_POLL_INTERVAL_SECS = 0.1


def PollForCondition(poll_method, condition_method=None,
                     timeout_secs=DEFAULT_TIMEOUT_SECS,
                     poll_interval_secs=DEFAULT_POLL_INTERVAL_SECS,
                     condition_name=None):
  """Polls for every poll_interval_secs until timeout reached or condition met.

  It is a blocking call. If the condition is met, poll_method's return value
  is passed onto the caller. Otherwise, a TimeoutError is raised.

  Args:
    poll_method: a method to be polled. The method's return value will be passed
        into condition_method.
    condition_method: a method to decide if poll_method's return value is valid.
        None for standard Python if statement.
    timeout_secs: maximum number of seconds to wait, None means forever.
    poll_interval_secs: interval to poll condition.
    condition_name: description of the condition. Used for TimeoutError when
        timeout_secs is reached.

  Returns:
    poll_method's return value.

  Raises:
    type_utils.TimeoutError when timeout_secs is reached but condition has not
        yet been met.
  """
  if condition_method == None:
    condition_method = lambda ret: ret
  end_time = time_utils.MonotonicTime() + timeout_secs if timeout_secs else None
  while True:
    if condition_name and end_time is not None:
      logging.debug('[%ds left] %s', end_time - time_utils.MonotonicTime(),
                    condition_name)
    ret = poll_method()
    if condition_method(ret):
      return ret
    if ((end_time is not None) and
        (time_utils.MonotonicTime() + poll_interval_secs > end_time)):
      if condition_name:
        condition_name = 'Timed out waiting for condition: %s' % condition_name
      else:
        condition_name = 'Timed out waiting for unnamed condition'
      logging.error(condition_name)
      raise type_utils.TimeoutError(condition_name, ret)
    time.sleep(poll_interval_secs)


def WaitFor(condition, timeout_secs, poll_interval=0.1):
  """Wait for the given condition for at most the specified time.

  Args:
    condition: A function object.
    timeout_secs: Timeout value in seconds.
    poll_interval: Interval to poll condition.

  Raises:
    ValueError: If condition is not a function.
    TimeoutError: If cond does not become True after timeout_secs seconds.
  """
  if not callable(condition):
    raise ValueError('condition must be a callable object')

  def _GetConditionString():
    condition_string = condition.__name__
    if condition.__name__ == '<lambda>':
      try:
        condition_string = inspect.getsource(condition).strip()
      except IOError:
        pass
    return condition_string

  return PollForCondition(poll_method=condition,
                          timeout_secs=timeout_secs,
                          poll_interval_secs=poll_interval,
                          condition_name=_GetConditionString())


# TODO(akahuang): Update the function from latest factory repo.
def Retry(max_retry_times, interval, target, condition=None, *args, **kwargs):
  """Retries the function until the condition is satisfied.

  Args:
    max_retry_times: the maximum retry times.
    interval: the time interval between each try, unit in second.
    target: the target function.
    condition: a method to decide if target's return value is valid.
               None for standard Python if statement.
    args: the arguments passed into the target function.
    kwargs: the keyword arguments passed into the target function.

  Returns:
    the result of the target function.
  """
  if condition is None:
    condition = lambda x: x
  result = None
  for retry_time in range(max_retry_times):
    try:
      result = target(*args, **kwargs)
    except Exception:
      pass
    if condition(result):
      logging.info('Get result after %d retries', retry_time)
      return result
    else:
      logging.warning('Retrying...[%d/%d]', retry_time + 1, max_retry_times)
      time.sleep(interval)
  # All results failed. Return the last result.
  return result


@contextmanager
def Timeout(secs):
  """Timeout context manager.

  It will raise TimeoutError after timeout is reached, interrupting execution
  of the thread.  It does not support nested "with Timeout" blocks, and can only
  be used in the main thread of Python.

  Args:
    secs: Number of seconds to wait before timeout.

  Raises:
    TimeoutError if timeout is reached before execution has completed.
    ValueError if not run in the main thread.
  """
  def Handler(signum, frame):
    del signum, frame
    raise type_utils.TimeoutError('Timeout')

  if secs:
    if signal.alarm(secs):
      raise type_utils.TimeoutError('Alarm was already set')

  signal.signal(signal.SIGALRM, Handler)

  try:
    yield
  finally:
    if secs:
      signal.alarm(0)
      signal.signal(signal.SIGALRM, lambda signum, frame: None)

#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The testplans module.

The test plan module will go through the CSV file (the format of which is
defined below) and put them to a dictionary. The testplan can also use the
dut plugin and instrument plugin to verify the port mapping and the names used
in the testplan.

The format of the CSV file.
The first column is '#' is for the config.
The format: #, key, value

The first column is '@' is for the header containing the names of arguments and
result. There is another '@' between the arguments and the results.
The format: @, arg_key1, arg_key2, ..., @, result_key1, result_key2, ...

Other rows contain a test case. Before these row there should be a valid header.
The format: , arg_value1, arg_value2, ...,, result_value1, result_value2, ...

We probably can add a line starting with a comment character. If that appears
in the first column, we ignore the rest of the line.
"""

import csv
import itertools
import logging


class TestPlan(object):
  def __init__(self, config_file):
    self.test_cases = []
    self.test_config = {}
    self.ParseCsvFile(config_file)

    order_by = self.test_config.get('order_by', None)
    if order_by is not None:
      cmp_key = lambda test_case: test_case.ResolveAttr(order_by)
      self.test_cases.sort(key=cmp_key)

  def __getitem__(self, index):
    return self.test_cases[index]

  def ParseCsvFile(self, config_file):
    logging.info('Loading test config file: %s', config_file)
    with open(config_file) as csv_file:
      reader = csv.reader(csv_file)
      header = None
      split_idx = None
      for row in reader:
        row = StripRow(row)
        if len(row) == 0:
          continue

        # General config starts with #
        if row[0] == '#':
          self.test_config[row[1]] = ConvertType(row[2])
          logging.debug('test_config: %s', self.test_config)
        # Header starts with @, arguments and results is splitted by @
        elif row[0] == '@':
          header = row[1:]
          try:
            split_idx = header.index('@')
          except ValueError:
            logging.error('The header should have second @ for result')
            header = None
            continue
        # Each line represents a group of test cases
        else:
          if header is None:
            logging.error('There should be valid header before content.')
            continue
          value = map(ConvertType, row[1:])
          arg_table = dict(zip(header[:split_idx], value[:split_idx]))
          result_limit = dict(zip(header[split_idx+1:], value[split_idx+1:]))
          # Generate the test cases with all combination of arguments
          for key in arg_table:
            if type(arg_table[key]) is not list:
              arg_table[key] = [arg_table[key]]
          arg_keys = arg_table.keys()
          logging.debug('arg_keys: %s', arg_keys)
          for arg_values in itertools.product(*arg_table.values()):
            logging.debug('arg_values: %s', arg_values)
            args = dict(zip(arg_keys, arg_values))
            self.test_cases.append(TestCase(args, result_limit))


class TestCase(object):
  """The test case. It contains the arguments of a RF test."""

  def __init__(self, args, result_limit):
    self.rf_type = args['rf_type']
    self.test_type = args['test_type']
    self.tx_or_rx = self.test_type.split('_')[0]
    self.args = args
    self.result_limit = result_limit

  def __str__(self):
    return 'RF: %s, Type: %s\nArgs: %s\nResults: %s' % (
        self.rf_type, self.test_type, self.args, self.result_limit)

  def ResolveAttr(self, arg_keys):
    """Returns the value in args. It's used for sorting the test cases."""
    try:
      return tuple([self.args[arg_key] for arg_key in arg_keys])
    except KeyError:
      logging.exception('test_case does not have attribute: %s', arg_keys)

  def IsTestPass(self, result):
    """Check the result meets the result or not."""
    for key in self.result_limit.keys():
      # Check required result is at the result
      if key not in result:
        logging.error('The result of %s is missing.', key)
        return False

      # Check the result meets the result
      lower_bound, upper_bound = self.result_limit[key]
      value = result[key]
      if ((lower_bound is not None and value < lower_bound) or
          (upper_bound is not None and value > upper_bound)):
        logging.info('The test in result %s failed. %s not in (%s, %s)',
                     key, result[key], lower_bound, upper_bound)
        return False
    return True

  def ToDict(self):
    """Return a dictionary containing all arguments of the class. It is for
    expanding the arguments of the function. For example:

    def foo(component_name, **kwargs):
      pass
    foo(**test_case.ToDict())
    """
    ret = self.args
    ret['result_limit'] = self.result_limit
    return ret


def StripRow(row):
  row = [item.strip() for item in row]
  while len(row) > 0 and len(row[-1]) == 0:
    row.pop()
  return row


def ConvertType(data):
  if data.startswith('('):
    return tuple(map(ConvertType, data[1:-1].split(',')))
  if data.startswith('['):
    return list(map(ConvertType, data[1:-1].split(',')))
  if data.strip() in ['None', 'none', 'null']:
    return None
  try:
    return int(data)
  except ValueError:
    return data.strip()


def main():
  logging.basicConfig(level=logging.INFO)
  config_file = 'sample_testplan.csv'
  test_plan = TestPlan(config_file)
  for test_case in test_plan:
    logging.info('test_case: %s', test_case)


if __name__ == '__main__':
  main()

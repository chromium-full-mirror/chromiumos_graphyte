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

from .data_parser import ListChecker
from .data_parser import TupleChecker
from .data_parser import Parse
from .utils import IsInBound
from .utils import SearchConfig


_RESULT_CHECKER = TupleChecker(([None, int, float],  # lower bound
                                [None, int, float])) # upper bound
# TODO(akahuang): Update after we support MIMO
ARG_CHECKER = {
    'component_name': ListChecker([str]),
    'rf_type':        ListChecker(['WLAN', 'BLUETOOTH', '802_15_4']),
    'standard':       ListChecker(['A', 'AC', 'B', 'G', 'N']),
    'format':         ListChecker(['DSSS', 'CCK', 'OFDM', 'O_QPSK']),
    'test_type':      ListChecker(['TX_MOD', 'RX_PER']),
    'center_freq':    ListChecker([lambda freq: 2400 < freq < 6000]),
    'bandwidth':      ListChecker([20, 40, 80, 160]),
    'data_rate':      ListChecker([int] + ['MCS' + str(i) for i in range(10)]),
    'nss':            ListChecker([None, 1, 2, 3, 4]),
    'chain_mask':     ListChecker([1, 2, 4, 8]),
    'power_level':    ListChecker([int]),
    'evm':            _RESULT_CHECKER,
    'avg_power':      _RESULT_CHECKER,
    'freq_error':     _RESULT_CHECKER,
    'rx_per':         _RESULT_CHECKER}
HEADER_CHECKER = {
    'order_by': ListChecker(ARG_CHECKER.keys())}


class TestPlan(object):
  def __init__(self, config_file):
    self.test_cases = []
    self.test_config = {}
    try:
      self.ParseCsvFile(config_file)
    except ValueError:
      logging.exception('Parsing csv file %s error.', config_file)
      self.test_cases = []

    order_by = self.test_config.get('order_by', None)
    if order_by is not None:
      cmp_key = lambda test_case: test_case.ResolveAttr(order_by)
      self.test_cases.sort(key=cmp_key)

  def __getitem__(self, index):
    return self.test_cases[index]

  def ParseCsvFile(self, config_file):
    logging.info('Loading test config file: %s', config_file)
    with open(SearchConfig(config_file)) as csv_file:
      reader = csv.reader(csv_file)
      header = None
      split_idx = None
      for row in reader:
        row = StripRow(row)
        if len(row) == 0:
          continue

        # General config starts with #
        if row[0] == '#':
          key, value = row[1], row[2]
          data = Parse(value, HEADER_CHECKER.get(key))
          self.test_config[key] = data
          logging.debug('test_config: %s', self.test_config)
        # Header starts with @, arguments and results is splitted by @
        elif row[0] == '@':
          header = row[1:]
          try:
            split_idx = header.index('@')
            arg_header, result_header = header[:split_idx], header[split_idx+1:]
          except ValueError:
            logging.error('The header should have second @ for result')
            header = None
            continue
        # Each line represents a group of test cases
        else:
          if header is None:
            logging.error('There should be valid header before content.')
            continue
          value = row[1:]
          arg_data = map(Parse, value[:split_idx],
                         map(ARG_CHECKER.get, arg_header))
          arg_table = dict(zip(arg_header, arg_data))
          result_data = map(Parse, value[split_idx+1:],
                            map(ARG_CHECKER.get, result_header))
          result_limit = dict(zip(result_header, result_data))
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

  def GetCanonicalName(self):
    """Return the name of the test case. It should contain important arguments
    information in a certain order.
    """
    arg_order = ['component_name', 'test_type', 'rf_type', 'center_freq',
                 'format', 'standard', 'data_rate', 'bandwidth', 'chain_mask']
    # TODO(akahung): confirm the argument below needed or not.
    #        'power_level', 'rx_num_packets', 'nss'
    args = self.ToDict()
    if args.get('bandwidth'):
      args['bandwidth'] = 'BW-' + str(args['bandwidth'])
    if args.get('chain_mask'):
      chain_list = ChainMaskToList(args['chain_mask'])
      args['chain_mask'] = 'ANTENNA-' + ','.join(map(str, chain_list))
    arg_values = [args.get(key) for key in arg_order if args.get(key)]
    return ' '.join(map(str, arg_values))

  def ResolveAttr(self, arg_keys):
    """Returns the value in args. It's used for sorting the test cases."""
    return tuple([self.args.get(arg_key) for arg_key in arg_keys])

  def IsTestPass(self, result):
    """Check the result meets the result or not."""
    for key in self.result_limit.keys():
      # Check required result is at the result
      if key not in result:
        logging.error('The result of %s is missing.', key)
        return False
      # Check the result meets the result
      if not IsInBound(result[key], self.result_limit[key]):
        logging.info('The test in result %s failed. %s not in %s',
                     key, result[key], self.result_limit[key])
        return False
    return True

  def ToDict(self):
    """Return a dictionary containing all arguments of the class. It is for
    expanding the arguments of the function. For example:

    def foo(component_name, **kwargs):
      pass
    foo(**test_case.ToDict())
    """
    ret = self.args.copy()
    ret['result_limit'] = self.result_limit.copy()
    return ret


def ChainMaskToList(chain_mask):
  """Convert the chain mask to the list of active antenna, starts from 0.
  If the chain_mask is None, it means there is only 1 antenna.
  """
  if chain_mask is None:
    return [0]
  ret = []
  antenna_idx = 0
  while chain_mask > 0:
    if chain_mask & 1:
      ret.append(antenna_idx)
    chain_mask >>= 1
    antenna_idx += 1
  return ret


def StripRow(row):
  """Strip every item in the row, and remove the right side of empty item."""
  row = [item.strip() for item in row]
  while len(row) > 0 and len(row[-1]) == 0:
    row.pop()
  return row


def main():
  logging.basicConfig(level=logging.INFO)
  config_file = 'sample_testplan.csv'
  test_plan = TestPlan(config_file)
  for test_case in test_plan:
    logging.info('test_case: %s', test_case)


if __name__ == '__main__':
  main()

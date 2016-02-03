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
The first column is '@config' is for the config.
The format: @config, key, value

The first column is '@title' is for the header containing the names of arguments
and result. There is another '@result' between the arguments and the results.
The format:
  @title, arg_key1, arg_key2, ..., @result, result_key1, result_key2, ...

Other rows contain a test case. Before these row there should be a valid header.
The format:
  , arg_value1, arg_value2, ...,, result_value1, result_value2, ...

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


CONFIG_MARKER = '@config'
TITLE_MARKER = '@title'
RESULT_MARKER = '@result'


REQUIRED_ARG_CHECKER = {
    'component_name': ListChecker([str]),
    'rf_type':        ListChecker(['WLAN', 'BLUETOOTH', '802_15_4']),
    'test_type':      ListChecker(['TX_MOD', 'RX_PER']),
    'center_freq':    ListChecker([lambda freq: 2400 < freq < 6000]),
    'power_level':    ListChecker([int, float])}
RF_ARG_CHECKER = {
    'WLAN': {
        'standard':       ListChecker(['A', 'AC', 'B', 'G', 'N']),
        'bandwidth':      ListChecker([20, 40, 80, 160]),
        'data_rate':      ListChecker([1, 2, 5.5, 11,
                                       6, 9, 12, 18, 24, 36, 48, 54] +
                                      ['MCS' + str(i) for i in range(10)]),
        'chain_mask':     ListChecker(range(1, 16)),  # 4x4 MIMO supported
        'nss':            ListChecker([None, 1, 2, 3, 4]),
        'long_preamble':  ListChecker([0, 1]),
        'rx_num_packets': ListChecker([int])},
    'BLUETOOTH': {
        'packet_type': ListChecker(
            ['NULL', 'POLL', 'FHS', 'DM1', 'DH1', '2DH1', 'HV1', 'HV2', '2EV3',
             'HV3', 'EV3', '3EV3', 'DV', '3DH1', 'AUX1', 'DM3', '2DH3', 'DH3',
             '3DH3', 'EV4', '2EV5', 'EV5', '3EV5', 'DM5', '2DH5', 'DH5', '3DH5',
             'LE', 'ID', 'IDLE'])},
    '802_15_4': {}}

def _GenerateResultChecker(results):
  result_checker = TupleChecker(([None, int, float],  # lower bound
                                 [None, int, float])) # upper bound
  return dict((result, result_checker) for result in results)

RF_RESULT_CHECKER = {
    'WLAN': _GenerateResultChecker(
        ['evm', 'avg_power', 'freq_error', 'lo_leakage', 'mask_margin',
         'spectral_flatness', 'obw', 'phase_noise', 'rx_per']),
    'BLUETOOTH': _GenerateResultChecker(['avg_power']),
    '802_15_4': _GenerateResultChecker(['avg_power'])}

HEADER_CHECKER = {
    'order_by': ListChecker(REQUIRED_ARG_CHECKER.keys())}


class TestPlan(object):
  """Generate the test plan from CSV file.

  The class parse the CSV file and generate a list of test cases.

  Usage:
    test_plan = TestPlan(config_file)
    if not test_plan:
      print 'Error: Failed to load the config file.'
    for test_case in test_plan:
      print 'test_case: %s' % test_case.GetCanonicalName()
  """

  def __init__(self, config_file=None):
    self.test_cases = []
    self.test_config = {}
    if config_file:
      self.LoadConfigFile(config_file)

  def __len__(self):
    """Return the count of the test cases.

    we implement __len__ and __getitem__ to make TestPlan behave like a
    read-only list.
    """
    return len(self.test_cases)

  def __getitem__(self, index):
    return self.test_cases[index]

  def LoadConfigFile(self, config_file):
    try:
      self.ParseCsvFile(config_file)
    except ValueError:
      logging.exception('Parsing csv file %s error.', config_file)
      self.test_cases = []

    order_by = self.test_config.get('order_by', None)
    if order_by is not None:
      cmp_key = lambda test_case: test_case.ResolveAttr(order_by)
      self.test_cases.sort(key=cmp_key)

  def ParseCsvFile(self, config_file):
    def _LogErrorAndRaise(row_idx, msg):
      msg = 'Row %d: %s' % (row_idx, msg)
      logging.error(msg)
      raise ValueError(msg)

    logging.info('Loading test config file: %s', config_file)
    with open(SearchConfig(config_file)) as csv_file:
      reader = csv.reader(csv_file)
      header = None
      split_idx = None
      for row_idx, row in enumerate(reader, start=1):
        row = StripRow(row)
        if len(row) == 0:
          continue

        # General config starts with '@config'
        if row[0] == CONFIG_MARKER:
          if len(row) != 3:
            _LogErrorAndRaise(row_idx,
                              'The format of config row should be: '
                              '@config, <key>, <value>')
          key, value = row[1], row[2]
          data = Parse(value, HEADER_CHECKER.get(key))
          self.test_config[key] = data
          logging.debug('test_config: %s', self.test_config)
        # Header starts with '@title', arguments and results is splitted by
        # '@result'
        elif row[0] == TITLE_MARKER:
          header = row[1:]
          try:
            split_idx = header.index(RESULT_MARKER)
          except ValueError:
            _LogErrorAndRaise(row_idx, '%s is missing' % RESULT_MARKER)
          arg_header, result_header = header[:split_idx], header[split_idx+1:]
        # Each line represents a group of test cases
        else:
          if header is None:
            _LogErrorAndRaise(
                row_idx, 'There should be valid title before content.')
          value = row[1:]
          if len(value) != len(header):
            _LogErrorAndRaise(
                row_idx, 'The length of data is different from the header.')
          try:
            arg_data = [Parse(data) for data in value[:split_idx]]
            arg_table = dict(zip(arg_header, arg_data))
            result_data = [Parse(data) for data in value[split_idx+1:]]
            result_limit = dict(zip(result_header, result_data))
          except ValueError as ex:
            _LogErrorAndRaise(row_idx, str(ex))
          # Generate the test cases with all combination of arguments
          for key in arg_table:
            if not isinstance(arg_table[key], list):
              arg_table[key] = [arg_table[key]]
          arg_keys = arg_table.keys()
          logging.debug('arg_keys: %s', arg_keys)
          for arg_values in itertools.product(*arg_table.values()):
            logging.debug('arg_values: %s', arg_values)
            args = dict(zip(arg_keys, arg_values))
            try:
              self.test_cases.append(TestCase(args, result_limit))
            except ValueError as ex:
              _LogErrorAndRaise(row_idx, str(ex))


class TestCase(object):
  """The test case. It contains the arguments of a RF test."""

  def __init__(self, args, result_limit):
    """Initialize the test case.

    Arg:
      args: A dict of the test arguments. The key 'rf_type', 'test_type' and
          'component_name' are essential.
          Example:
          {
            'component_name': 'WLAN_2G',
            'rf_type': 'WLAN',
            'test_type': 'TX_MOD',
            'center_freq': 2412
          }
      result_limit: A dict of the test result. The values are a tuple of lower
          bound and upper bound.
          Example:
          {
            'evm': (None, -25),
            'avg_power': (16, 20)
          }
    """
    self.rf_type = args.get('rf_type', 'MISSING')
    self.test_type = args.get('test_type', 'MISSING')
    self.tx_or_rx = self.test_type.split('_')[0]
    self.args = args
    self.result_limit = result_limit
    self.Verify()

  def __str__(self):
    return 'RF: %s, Type: %s\nArgs: %s\nResults: %s' % (
        self.rf_type, self.test_type, self.args, self.result_limit)

  def Verify(self):
    """Verify the test case is valid or not.

    1. Check the RF type is valid.
    2. Check all required arguments are existed.
    3. Check all required and the RF-specific arguments and valid.
    4. Check there is result and all results are valid.

    Raises:
      ValueError if the test case is not valid.
    """
    def _VerifyData(checker, data):
      for key, value in data.items():
        if key not in checker:
          raise ValueError('%s is not a valid result for %s.' %
                           (key, self.rf_type))
        if not checker[key].CheckData(value):
          raise ValueError('"%s" is not valid for %s.' % (value, key))

    # Check the RF type is valid.
    if not REQUIRED_ARG_CHECKER['rf_type'].CheckData(self.rf_type):
      raise ValueError('%s is not a valid RF type.' % self.rf_type)
    # Check all required arguments are existed.
    unknown_args = set(REQUIRED_ARG_CHECKER.keys()) - set(self.args.keys())
    if unknown_args:
      raise ValueError('%s is not a valid argument.' % unknown_args)
    # Check all required and the RF-specific arguments and valid.
    arg_checker = REQUIRED_ARG_CHECKER.copy()
    arg_checker.update(RF_ARG_CHECKER[self.rf_type])
    _VerifyData(arg_checker, self.args)
    # Check there is result and all results are valid.
    if not self.result_limit:
      raise ValueError('There is no result.')
    result_checker = RF_RESULT_CHECKER[self.rf_type]
    _VerifyData(result_checker, self.result_limit)

  def GetCanonicalName(self):
    """Return the name of the test case. It should contain important arguments
    information in a certain order.
    """
    rf_arg_order = {
        'WLAN': ['format', 'standard', 'data_rate', 'bandwidth', 'chain_mask'],
        'BLUETOOTH': ['format', 'data_rate'],
        '802_15_4': []}
    arg_order = ['rf_type', 'component_name', 'test_type', 'center_freq']
    arg_order += rf_arg_order[self.rf_type]
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
    logging.info('test_case: %s', test_case.GetCanonicalName())


if __name__ == '__main__':
  main()

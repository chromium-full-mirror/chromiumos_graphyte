#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The testplan module.

The testplan module will go through the CSV file (the format of which is
defined below) and put them to a TestPlan object, which acts like a read-only
list of the TestCase.

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

We use the number sign(#) as the comment character.
If the first column starts from #, we ignore the rest of the line.
"""

import csv
import itertools
import logging

from .data_parser import ListChecker
from .data_parser import TupleChecker
from .data_parser import Parse
from .default_setting import logger
from .utils.graphyte_utils import IsInBound
from .utils.graphyte_utils import SearchConfig


CONFIG_MARKER = '@config'
TITLE_MARKER = '@title'
RESULT_MARKER = '@result'


HEADER_CHECKER = {
    'order_by': ListChecker(['component_name', 'rf_type', 'test_type',
                             'center_freq', 'power_level'])}


class TestPlan(object):
  """Generates the test plan from CSV file.

  The class parses the CSV file and generates a list of test cases.

  Usage:
    test_plan = TestPlan(config_file)
    if not test_plan:
      print 'Error: Failed to load the config file.'
    for test_case in test_plan:
      print 'test_case: %s' % str(test_case)
  """

  def __init__(self, config_file=None, search_dirs=None):
    self.test_cases = []
    self.test_config = {}
    if config_file:
      self.LoadConfigFile(config_file, search_dirs)

  def __len__(self):
    """Returns the count of the test cases.

    we implement __len__ and __getitem__ to make TestPlan behave like a
    read-only list.
    """
    return len(self.test_cases)

  def __getitem__(self, index):
    return self.test_cases[index]

  def LoadConfigFile(self, config_file, search_dirs=None):
    try:
      self.ParseCSVFile(config_file, search_dirs)
    except ValueError:
      logger.exception('Parsing csv file %s error.', config_file)
      self.test_cases = []

    order_by = self.test_config.get('order_by', None)
    if order_by is not None:
      cmp_key = lambda test_case: test_case.ResolveAttr(order_by)
      self.test_cases.sort(key=cmp_key)

  def ParseCSVFile(self, config_file, search_dirs=None):
    def _LogErrorAndRaise(row_idx, msg):
      msg = 'Row %d: %s' % (row_idx, msg)
      logger.error(msg)
      raise ValueError(msg)

    logger.info('Loading test config file: %s', config_file)
    with open(SearchConfig(config_file, search_dirs)) as csv_file:
      reader = csv.reader(csv_file)
      header = None
      split_idx = None
      for row_idx, row in enumerate(reader, start=1):
        row = StripRow(row)
        if len(row) == 0:
          continue

        if row[0].startswith('#'):
          continue
        # General config starts with '@config'
        elif row[0] == CONFIG_MARKER:
          if len(row) != 3:
            _LogErrorAndRaise(row_idx,
                              'The format of config row should be: '
                              '@config, <key>, <value>')
          key, value = row[1], row[2]
          data = Parse(value, HEADER_CHECKER.get(key))
          self.test_config[key] = data
          logger.debug('test_config: %s', self.test_config)
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
          logger.debug('arg_keys: %s', arg_keys)
          for arg_values in itertools.product(*arg_table.values()):
            logger.debug('arg_values: %s', arg_values)
            args = dict(zip(arg_keys, arg_values))
            try:
              self.test_cases.extend(CreateTestCase(args, result_limit))
            except ValueError as ex:
              _LogErrorAndRaise(row_idx, str(ex))


def CreateTestCase(args, result_limit):
  """Creates the test case according to the RF type.

  Since the verification and the generation of the test case for each RF type
  are slightly different, we use the simple factory pattern to create the test
  case.

  Args:
    args: the arguments of the test case.
    result_limit: the result limit of the test case.

  Return:
    a list of the test case.
  """
  factory_map = {
      'WLAN': WLANTestCaseFactory(),
      'BLUETOOTH': BluetoothTestCaseFactory(),
      '802_15_4': ZigbeeTestCaseFactory()}
  try:
    factory = factory_map[args['rf_type']]
  except KeyError:
    raise ValueError('Invalid args %s: unsupported RF type.' % args)
  return factory.Create(args, result_limit)


class TestCaseFactory(object):
  """The abstract class for generating a test case of the certain RF type.

  The class is mainly for verifying the arguments and the result limit are
  valid, and then creating the test case.
  """

  def Create(self, args, result_limit):
    self._VerifyArgAndResult(args, result_limit)
    return self._Create(args, result_limit)

  def _VerifyArgAndResult(self, args, result_limit):
    """Verifies the test case is valid or not.

    1. Check the RF type is correct.
    2. Check all required arguments exist and are valid.
    3. Check there is at least one result and all results are valid.

    Raises:
      KeyError if the required arguments are missing.
      ValueError if the test case is not valid.
    """
    raise NotImplementedError

  def _Create(self, args, result_limit):
    name = self._GenerateCanonicalName(args)
    return [TestCase(name, args, result_limit)]

  @property
  def canonical_arg_order(self):
    """The argument order of the canonical name.

    Returns:
      a list of the argument name.
    """
    raise NotImplementedError

  def _GenerateCanonicalName(self, args):
    arg_values = [args[key] for key in self.canonical_arg_order if key in args]
    return ' '.join(map(str, arg_values))

  @staticmethod
  def VerifyArguments(checker_dict, args):
    """Verifies all arguments are valid.

    If the keys of args are not the same as checker_dict, or there is any value
    is not valid, then raise the ValueError exception.

    Args:
      checker_dict: a dict which keys are the valid args and values are
                    corresponding data checkers. For example:
        {
          'rf_type': ListChecker(['WLAN', 'BLUETOOTH', '802_15_4']),
          'test_type': ListChecker(['TX', 'RX'])
        }
      args: the arguments of the test case.

    Raises:
      ValueError if args does not pass the verification.
    """
    if set(args.keys()) != set(checker_dict.keys()):
      missing_keys = list(set(checker_dict.keys()) - set(args.keys()))
      unknown_keys = list(set(args.keys()) - set(checker_dict.keys()))
      err_str = 'The keys of arguments are not valid.'
      if missing_keys:
        err_str += ' The keys %s are missing.' % (missing_keys)
      if unknown_keys:
        err_str += ' The keys %s are unknown.' % (unknown_keys)
      raise ValueError(err_str)
    for key, value in args.items():
      if not checker_dict[key].CheckData(value):
        raise ValueError('"%s" is not valid for %s.' % (value, key))

  @staticmethod
  def _VerifyResults(result_list, result_limit):
    """Verifies all results are valid.

    If there is key of result_limit not in result_list, or the value is not
    valid, then raise the ValueError exception.

    Args:
      result_list: a list of all valid result keys.
      result_limit: the result limit of the test case.

    Raises:
      ValueError if data is not passed the verification.
    """
    result_checker = TupleChecker(([None, int, float],  # lower bound
                                   [None, int, float]))  # upper bound

    if not result_limit:
      raise ValueError('There is no result.')
    unknown_keys = set(result_limit.keys()) - set(result_list)
    if unknown_keys:
      raise ValueError('The keys %s are unknown.' % list(unknown_keys))
    for key, value in result_limit.items():
      if not result_checker.CheckData(value):
        raise ValueError('"%s" is not valid for %s.' % (value, key))


class WLANTestCaseFactory(TestCaseFactory):
  RF_TYPE = 'WLAN'

  REQUIRED_ARG_CHECKER = {
      'rf_type':        ListChecker([RF_TYPE]),
      'component_name': ListChecker([str]),
      'test_type':      ListChecker(['TX', 'RX']),
      'center_freq':    ListChecker([lambda freq: 2400 < freq < 6000]),
      'power_level':    ListChecker([int, float]),
      'standard':       ListChecker(['A', 'AC', 'B', 'G', 'N']),
      'bandwidth':      ListChecker([20, 40, 80, 160]),
      'data_rate':      ListChecker([1, 2, 5.5, 11,
                                     6, 9, 12, 18, 24, 36, 48, 54] +
                                    ['MCS' + str(i) for i in range(32)]),
      'chain_mask':     ListChecker(range(1, 16)),  # 4x4 MIMO supported
      'nss':            ListChecker([None, 1, 2, 3, 4]),
      'long_preamble':  ListChecker([0, 1])}
  RX_ARG_CHECKER = {
      'rx_num_packets': ListChecker([int])}
  TX_RESULTS = ['evm', 'avg_power', 'freq_error', 'lo_leakage', 'mask_margin',
                'spectral_flatness', 'obw', 'phase_noise']
  RX_RESULTS = ['rx_per']

  def _VerifyArgAndResult(self, args, result_limit):
    # TODO(akahuang): standard to data_rate mapping
    # Check the RF type is valid.
    if self.RF_TYPE != args['rf_type']:
      raise ValueError('%s is not a valid RF type.' % args['rf_type'])
    # Check all required arguments are valid.
    arg_checker = self.REQUIRED_ARG_CHECKER.copy()
    if args['test_type'] == 'RX':
      arg_checker.update(self.RX_ARG_CHECKER)
    TestCaseFactory.VerifyArguments(arg_checker, args)
    # Check there is result and all results are valid.
    if args['test_type'] == 'TX':
      result_list = self.TX_RESULTS
    else:
      result_list = self.RX_RESULTS
    TestCaseFactory._VerifyResults(result_list, result_limit)

  @property
  def canonical_arg_order(self):
    return [
        'rf_type', 'component_name', 'test_type', 'center_freq',
        'standard', 'data_rate', 'bandwidth', 'chain_mask']

  def _GenerateCanonicalName(self, args):
    args = args.copy()  # do not change the original argument.
    args['bandwidth'] = 'BW-' + str(args['bandwidth'])
    chain_list = ChainMaskToList(args['chain_mask'])
    args['chain_mask'] = 'ANTENNA-' + ''.join(map(str, chain_list))
    return super(WLANTestCaseFactory, self)._GenerateCanonicalName(args)


class BluetoothTestCaseFactory(TestCaseFactory):
  RF_TYPE = 'BLUETOOTH'
  REQUIRED_ARG_CHECKER = {
      'rf_type':        ListChecker([RF_TYPE]),
      'component_name': ListChecker([str]),
      'test_type':      ListChecker(['TX', 'RX']),
      'center_freq':    ListChecker([lambda freq: 2400 < freq < 2500]),
      'power_level':    ListChecker([int, float]),
      'packet_type':    ListChecker(['1DH1', '1DH3', '1DH5', '2DH1', '2DH3',
                                     '2DH5', '3DH1', '3DH3', '3DH5', 'LE'])}
  LE_RX_ARG_CHECKER = {
      'rx_num_packets': ListChecker([int])}
  BT_RX_ARG_CHECKER = {
      'rx_num_bits': ListChecker([int])}
  COMMON_RESULTS = [
      'avg_power', 'acp_5', 'acp_4', 'acp_3', 'acp_2',
      'acp_1', 'acp0', 'acp1', 'acp2', 'acp3', 'acp4', 'acp5']
  FORMAT_RESULT_CHECKER = {
      'BDR': ['bandwidth_20db', 'freq_deviation', 'freq_drift', 'delta_f1_avg',
              'delta_f2_avg', 'delta_f2_max', 'delta_f2_f1_avg_ratio'],
      'EDR': ['freq_deviation', 'edr_evm_avg', 'edr_evm_peak',
              'edr_extreme_omega_0', 'edr_extreme_omega_i0', 'edr_omega_i',
              'edr_power_diff', 'edr_prob_evm_99_pass'],
      'LE': ['freq_offset', 'delta_f1_avg', 'delta_f2_avg',
             'delta_f2_max', 'delta_f0_fn_max', 'delta_f1_f0',
             'delta_fn_fn5_max', 'delta_f2_f1_avg_ratio']}
  LE_RX_RESULTS = ['rx_per']
  BT_RX_RESULTS = ['rx_ber']

  # For a Bluetooth test case, each result needs different bit pattern.
  # This dict records the relation between results and bit patterns.
  # NOTE1: This dict only for BDR and LE. EDR only uses PRBS9 pattern.
  # That is, EDR freq_deviation still uses PRBS9.
  # NOTE2: delta_f2_f1_avg_ratio is the ratio of delta_f2_avg and delta_f1_avg,
  # so it needs 'F0' and 'AA' patterns.
  BIT_PATTERN_RESULTS = {
      'PRBS9': ['avg_power', 'bandwidth_20db', 'acp_5', 'acp_4', 'acp_3',
                'acp_2', 'acp_1', 'acp0', 'acp1', 'acp2', 'acp3', 'acp4',
                'acp5', 'freq_offset', 'rx_ber', 'rx_per'],
      'F0': ['freq_deviation', 'delta_f1_avg', 'delta_f2_f1_avg_ratio'],
      'AA': ['freq_drift', 'delta_f2_avg', 'delta_f2_max', 'delta_f1_f0',
             'delta_f2_f1_avg_ratio', 'delta_f0_fn_max', 'delta_fn_fn5_max']}

  # The maximum number of bytes for each BDR and EDR packet type.
  # In Rx test, the instrument should transmit the largest packet.
  # Ref: Bluetooth Core Specification 4.0 Table 6.9: ACL packets.
  MAX_PACKET_LENGTH = {
      '1DH1': 27,
      '1DH3': 183,
      '1DH5': 339,
      '2DH1': 54,
      '2DH3': 367,
      '2DH5': 679,
      '3DH1': 83,
      '3DH3': 552,
      '3DH5': 1021}

  def _DetermineFormat(self, packet_type):
    """Determines the bluetooth format of the packet type.

    Args:
      packet_type: the Bluetooth packet type.

    Returns:
      one of 'LE', 'BDR', or 'EDR'.
    """
    if packet_type == 'LE':
      return 'LE'
    # The Bluetooth packet types are in the format: nXYm
    # n indicates modulation type. 1 is 1Mbps (basic data rate).
    # 2 is 2Mbps, 3 is 3Mbps modulation (enhanced data rate).
    # Hence the packet type starts from '2' or '3' is EDR, otherwise is BDR.
    if packet_type[0] in ['2', '3']:
      return 'EDR'
    return 'BDR'

  def _VerifyArgAndResult(self, args, result_limit):
    # Check the RF type is valid.
    if self.RF_TYPE != args['rf_type']:
      raise ValueError('%s is not a valid RF type.' % args['rf_type'])
    # Check all required arguments are valid.
    arg_checker = self.REQUIRED_ARG_CHECKER.copy()
    if args['test_type'] == 'RX':
      if args['packet_type'] == 'LE':
        arg_checker.update(self.LE_RX_ARG_CHECKER)
      else:
        arg_checker.update(self.BT_RX_ARG_CHECKER)
    TestCaseFactory.VerifyArguments(arg_checker, args)
    # Check there is result and all results are valid.
    if args['test_type'] == 'TX':
      result_list = self.COMMON_RESULTS[:]
      packet_format = self._DetermineFormat(args['packet_type'])
      result_list += self.FORMAT_RESULT_CHECKER[packet_format]
    elif args['packet_type'] == 'LE':
      result_list = self.LE_RX_RESULTS
    else:
      result_list = self.BT_RX_RESULTS
    TestCaseFactory._VerifyResults(result_list, result_limit)

  def _Create(self, args, result_limit):
    """Creates the bluetooth test case.

    For BDR and LE, the bit pattern of the packet are different from results.
    We add the 'bit_pattern' argument and split into different test cases.
    There is only 'PRBS9' bit pattern for EDR.
    """
    name = self._GenerateCanonicalName(args)
    packet_format = self._DetermineFormat(args['packet_type'])
    # Convert rx_num_bits to rx_num_packets. Add 10% packets for some loss.
    if args['test_type'] == 'RX' and packet_format != 'LE':
      args['rx_num_packets'] = int(1.1 * args['rx_num_bits'] / 8 /
                                   self.MAX_PACKET_LENGTH[args['packet_type']])
    if packet_format == 'EDR':
      args['bit_pattern'] = 'PRBS9'
      return [TestCase(name, args, result_limit)]
    # Split the test case by the bit pattern.
    ret = []
    for bit_pattern, result_list in self.BIT_PATTERN_RESULTS.items():
      filtered_result = dict(
          (k, v) for k, v in result_limit.items() if k in result_list)
      if filtered_result:
        copy_args = args.copy()
        copy_args['bit_pattern'] = bit_pattern
        ret.append(TestCase(name, copy_args, filtered_result))
    return ret

  @property
  def canonical_arg_order(self):
    return ['rf_type', 'component_name', 'test_type', 'center_freq',
            'packet_type']


class ZigbeeTestCaseFactory(TestCaseFactory):
  RF_TYPE = '802_15_4'
  REQUIRED_ARG_CHECKER = {
      'rf_type':        ListChecker([RF_TYPE]),
      'component_name': ListChecker([str]),
      'test_type':      ListChecker(['TX', 'RX']),
      'center_freq':    ListChecker([lambda freq: 2400 < freq < 6000]),
      'power_level':    ListChecker([int, float])}
  RX_ARG_CHECKER = {
      'rx_num_packets': ListChecker([int])}

  TX_RESULTS = ['avg_power', 'evm_all', 'evm_offset', 'freq_error']
  RX_RESULTS = ['rx_per']

  def _VerifyArgAndResult(self, args, result_limit):
    # Check the RF type is valid.
    if self.RF_TYPE != args['rf_type']:
      raise ValueError('%s is not a valid RF type.' % args['rf_type'])
    # Check all required arguments are valid.
    arg_checker = self.REQUIRED_ARG_CHECKER.copy()
    if args['test_type'] == 'RX':
      arg_checker.update(self.RX_ARG_CHECKER)
    TestCaseFactory.VerifyArguments(arg_checker, args)
    # Check there is result and all results are valid.
    if args['test_type'] == 'TX':
      result_list = self.TX_RESULTS
    else:
      result_list = self.RX_RESULTS
    TestCaseFactory._VerifyResults(result_list, result_limit)

  @property
  def canonical_arg_order(self):
    return ['rf_type', 'component_name', 'test_type', 'center_freq']


class TestCase(object):
  """The test case. It contains the arguments of a RF test."""

  def __init__(self, name, args, result_limit):
    """Initializes the test case.

    Arg:
      name: A string that should contain important arguments information.
      args: A dict of the test arguments. The key 'rf_type', 'test_type' and
          'component_name' are essential.
          Example:
          {
            'component_name': 'WLAN_2G',
            'rf_type': 'WLAN',
            'test_type': 'TX',
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
    self.rf_type = args['rf_type']
    self.test_type = args['test_type']
    self.args = args
    self.result_limit = result_limit
    self.name = name

  def __str__(self):
    return self.name

  def ResolveAttr(self, arg_keys):
    """Returns the value in args. It's used for sorting the test cases."""
    return tuple([self.args.get(arg_key) for arg_key in arg_keys])

  def CheckTestPasses(self, result):
    """Checks the result meets the result limit of the test case or not.

    The method verifies that each item in the `result_limit` is included in the
    result dict, and verifies that the result value meets the limit.

    Args:
      result: A dict in which keys should contain all the keys of
          `self.result_limit`, and the values are the result values.

    Returns:
      True if every result value meets the result limit.
    """
    is_pass = True
    for key in self.result_limit.keys():
      # Check there are all the required items in the result.
      if key not in result:
        logger.error('The result of %s is missing.', key)
        is_pass = False
      # Check the result value meets the result limit.
      if not IsInBound(result[key], self.result_limit[key]):
        logger.info('The test in result %s failed. %s not in %s',
                    key, result[key], self.result_limit[key])
        is_pass = False
    return is_pass

  def ToDict(self):
    """Returns a dictionary containing all arguments of the class.

    It is for expanding the arguments of the function. For example:

      def foo(component_name, **kwargs):
        pass
      foo(**test_case.ToDict())
    """
    ret = self.args.copy()
    ret['result_limit'] = self.result_limit.copy()
    ret['name'] = self.name
    return ret

  def Copy(self):
    return TestCase(self.name, self.args.copy(), self.result_limit.copy())


def ChainMaskToList(chain_mask):
  """Converts the chain mask to the list of active antenna, starts from 0.

  The chain mask is the indicator of the activated antenna in binary
  representation. LSB means the first antenna and we called it antenna #0. For
  example:
    1 (b’0001) means the first antenna is activated.
    2 (b’0010) means the second antenna is activated.
    3 (b’0011) means the first and the second antenna are activated.
  If the chain_mask is None, it means there is only 1 antenna.

  Args:
    chain_mask: None or integer.

  Returns:
    A list of integer which contains the activated antenna indices.
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
  """Strips every item in the row, and remove the right side of empty item."""
  row = [item.strip() for item in row]
  while len(row) > 0 and len(row[-1]) == 0:
    row.pop()
  return row

# TODO(akahuang): Implement the CSV file check and CSV template generation.
def main():
  logger.setLevel(level=logging.INFO)
  config_file = 'sample_testplan.csv'
  test_plan = TestPlan(config_file)
  for test_case in test_plan:
    logger.info('test_case: %s', str(test_case))


if __name__ == '__main__':
  main()

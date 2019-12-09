#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
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

import graphyte_common  # pylint: disable=unused-import
from graphyte.data_parser import ListChecker
from graphyte.data_parser import TupleChecker
from graphyte.data_parser import Parse
from graphyte.default_setting import logger
from graphyte.utils.graphyte_utils import AssertRangeContain
from graphyte.utils.graphyte_utils import IsInBound
from graphyte.utils.graphyte_utils import SearchConfig


CONFIG_MARKER = '@config'
TITLE_MARKER = '@title'
RESULT_MARKER = '@result'


HEADER_CHECKER = {
    'order_by': ListChecker(['component_name', 'rf_type', 'test_type',
                             'center_freq', 'power_level'])}
SUPPORTED_RF_TYPES = ['WLAN', 'BLUETOOTH', '802_15_4']
SUPPORTED_TEST_TYPES = ['TX', 'RX']

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

  # The limitations are from ieee 802.11-2016. The title is Part 11: Wireless
  # LAN Medium Access Control (MAC) and Physical Layer (PHY) Specifications.
  # B is in chapter 15 and chapter 16.
  # A is in chapter 17.
  # G is in chapter 18.
  # N is in chapter 19.
  # AC is in chapter 21.

  # 16.3.6.5 and 16.3.6.6.
  # 17.2.2.3 and 17.2.3.4. Note that Graphyte does not support 10MHz or 5MHz.
  # 19.3.5. Note that Graphyte does not support UEQM so no MCS[33,76].
  # 21.3.5.
  DATA_RATE_A_G = [6, 9, 12, 18, 24, 36, 48, 54]
  DATA_RATE_AC = ['MCS' + str(i) for i in range(10)]
  DATA_RATE_B = [1, 2, 5.5, 11]
  DATA_RATE_N = ['MCS' + str(i) for i in range(32)]
  REQUIRED_ARG_CHECKER = {
      'rf_type':        ListChecker([RF_TYPE]),
      'component_name': ListChecker([str]),
      'test_type':      ListChecker(SUPPORTED_TEST_TYPES),
      'center_freq':    ListChecker([lambda freq: 2400 < int(freq) < 6000]),
      'power_level':    ListChecker([int, float, 'auto']),
      'standard':       ListChecker(['A', 'AC', 'B', 'G', 'N']),
      'bandwidth':      ListChecker([20, 40, 80, 160]),
      'data_rate':      ListChecker(DATA_RATE_B +
                                    DATA_RATE_A_G +
                                    DATA_RATE_N +
                                    DATA_RATE_AC),
      'chain_mask':     ListChecker(list(range(1, 16))),  # 4x4 MIMO supported
      'nss':            ListChecker([None, 1, 2, 3, 4]),
      'long_preamble':  ListChecker([0, 1])}

  STANDARD_ARG_CHECKERS = {
      'A': {'data_rate': ListChecker(DATA_RATE_A_G),
            'bandwidth': ListChecker([20]),
            'nss': ListChecker([None])},
      'AC': {'data_rate': ListChecker(DATA_RATE_AC),
             'bandwidth': ListChecker([20, 40, 80, 160]),
             'nss': ListChecker([1, 2, 3, 4])},
      'B': {'data_rate': ListChecker(DATA_RATE_B),
            'bandwidth': ListChecker([20]),
            'nss': ListChecker([None])},
      'G': {'data_rate': ListChecker(DATA_RATE_A_G),
            'bandwidth': ListChecker([20]),
            'nss': ListChecker([None])},
      'N': {'data_rate': ListChecker(DATA_RATE_N),
            'bandwidth': ListChecker([20, 40]),
            'nss': ListChecker([None])}}
  # The indices of different modulation scheme.
  MODULATION_INDEX = {
      'A': dict(zip(DATA_RATE_A_G, range(1, 9))),
      'AC': dict(zip(DATA_RATE_AC, [1, 3, 4, 5, 6, 7, 8, 9, 10, 11])),
      'B': {data_rate: 0 for data_rate in DATA_RATE_B},
      'G': dict(zip(DATA_RATE_A_G, range(1, 9))),
      'N': {'MCS' + str(i): [1, 3, 4, 5, 6, 7, 8, 9][i % 8]
            for i in range(32)}}
  # 15.4.5.10 Transmit modulation accuracy
  # 17.3.9.7.4 Transmitter constellation error
  # 19.3.18.7.3 Transmitter constellation error
  # 21.3.17.4.3 Transmitter constellation error
  STANDARD_EVM_UPPER_BOUNDS = [-9.1, -5, -8, -10, -13, -16, -19, -22, -25, -27,
                               -30, -32]
  # 15.4.6.2 Receiver minimum input level sensitivity
  # 16.3.8.2 Receiver minimum input level sensitivity
  # 17.3.10.2 Receiver minimum input sensitivity
  # 19.3.19.1 Receiver minimum input sensitivity
  # 21.3.18.1 Receiver minimum input sensitivity
  STANDARD_SENSITIVITY = {
      20: [-76, -82, -81, -79, -77, -74, -70, -66, -65, -64, -59, -57],
      40: [None, -79, None, -76, -74, -71, -67, -63, -62, -61, -56, -54],
      80: [None, -76, None, -73, -71, -68, -64, -60, -59, -58, -53, -51],
      160: [None, -73, None, -70, -68, -65, -61, -57, -56, -55, -50, -48]}

  RX_ARG_CHECKER = {
      'rx_num_packets': ListChecker([int])}
  TX_RESULTS = ['evm', 'avg_power', 'freq_error', 'lo_leakage', 'mask_margin',
                'spectral_flatness', 'obw', 'phase_noise']
  RX_RESULTS = ['rx_per']
  # 15.4.5.6 Transmit center frequency tolerance
  # 17.3.9.5 Transmit center frequency tolerance
  # 19.3.18.4 Transmit center frequency tolerance
  # 21.3.17.3 Transmit center frequency and symbol clock frequency tolerance
  STANDARD_FREQ_ERROR = {
      'A': (-20, 20),
      'AC': (-20, 20),
      'B': (-25, 25),
      'G': (-20, 20),
      'N': (-20, 20),
      'N5': (-25, 25)}
  # 15.4.5.9 RF carrier suppression
  # 17.3.9.7.2 Transmitter center frequency leakage
  # 19.3.18.7.2 Transmit center frequency leakage
  # 21.3.17.4.2 Transmit center frequency leakage
  STANDARD_LO_LEAKAGE = {
      'A': {20: (None, -15.0)},
      'AC': {20: (None, -17.5), 40: (None, -20.6),
             80: (None, -23.8), 160: (None, -26.8)},
      'B': {20: (None, -15.0)},
      'G': {20: (None, -15.0)},
      'N': {20: (None, -15.0), 40: (None, -20.0)}}
  # 15.4.6.2 Receiver minimum input level sensitivity
  # 16.3.8.2 Receiver minimum input level sensitivity
  # 17.3.10.2 Receiver minimum input sensitivity
  # 19.3.19.1 Receiver minimum input sensitivity
  # 21.3.18.1 Receiver minimum input sensitivity
  STANDARD_RX_PER = {
      'A': (0, 10),
      'AC': (0, 10),
      'B': (0, 8),
      'G': (0, 10),
      'N': (0, 10)}

  def _VerifyArgAndResult(self, args, result_limit):
    # Check the RF type is valid.
    if self.RF_TYPE != args['rf_type']:
      raise ValueError('%s is not a valid RF type.' % args['rf_type'])
    # Check all required arguments are valid.
    arg_checker = self.REQUIRED_ARG_CHECKER.copy()
    if args['test_type'] == 'RX':
      arg_checker.update(self.RX_ARG_CHECKER)
    TestCaseFactory.VerifyArguments(arg_checker, args)
    # Check if the arguments are valid in the specified standard.
    bandwidth = args['bandwidth']
    center_freq = int(args['center_freq'])
    data_rate = args['data_rate']
    standard = args['standard']
    TestCaseFactory.VerifyArguments(
        self.STANDARD_ARG_CHECKERS[standard],
        {'data_rate': data_rate,
         'bandwidth': bandwidth,
         'nss': args['nss']})
    modulation_index = self.MODULATION_INDEX[standard][data_rate]
    if args['test_type'] == 'RX':
      standard_limit = (None,
                        self.STANDARD_SENSITIVITY[bandwidth][modulation_index])
      AssertRangeContain('standard %s with data rate %s and bandwidth %d'
                         % (standard, data_rate, bandwidth),
                         'power_level',
                         standard_limit,
                         (None, args['power_level']))
    # Check there is result and all results are valid.
    if args['test_type'] == 'TX':
      result_list = self.TX_RESULTS
    else:
      result_list = self.RX_RESULTS
    TestCaseFactory._VerifyResults(result_list, result_limit)
    # Check if the results are valid in the specified standard.
    if 'evm' in result_limit:
      AssertRangeContain('standard %s with data rate %s'
                         % (standard, data_rate),
                         'evm',
                         (None,
                          self.STANDARD_EVM_UPPER_BOUNDS[modulation_index]),
                         result_limit['evm'])
    if 'freq_error' in result_limit:
      index = standard if standard != 'N' or center_freq < 3000 else 'N5'
      AssertRangeContain('standard %s with frequency %f'
                         % (standard, center_freq),
                         'freq_error',
                         self.STANDARD_FREQ_ERROR[index],
                         result_limit['freq_error'])
    if 'lo_leakage' in result_limit:
      AssertRangeContain('standard %s with bandwidth %s'
                         % (standard, bandwidth),
                         'lo_leakage',
                         self.STANDARD_LO_LEAKAGE[standard][bandwidth],
                         result_limit['lo_leakage'])
    if 'obw' in result_limit:
      AssertRangeContain('all conditions',
                         'obw',
                         (0, None),
                         result_limit['obw'])
    if 'rx_per' in result_limit:
      AssertRangeContain('standard %s' % standard,
                         'rx_per',
                         self.STANDARD_RX_PER[standard],
                         result_limit['rx_per'])

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

  # The standard test limits are from
  # https://www.bluetooth.com/specifications/qualification-test-requirements/.
  # Current reference revisions are RF.TS.5.1.0 and RF-PHY.TS.5.1.1.
  # RF.TS.5.1.0 describes tests for BDR or EDR.
  # RF-PHY.TS.5.1.1 describes tests for LE.
  # Each test is named by something like RF-PHY/TRM/BV-03-C.
  REQUIRED_ARG_CHECKER = {
      'rf_type':        ListChecker([RF_TYPE]),
      'component_name': ListChecker([str]),
      'test_type':      ListChecker(SUPPORTED_TEST_TYPES),
      'center_freq':    ListChecker([lambda freq: 2400 < freq < 2500]),
      'power_level':    ListChecker([int, float, 'auto']),
      'packet_type':    ListChecker(['1DH1', '1DH3', '1DH5', '2DH1', '2DH3',
                                     '2DH5', '3DH1', '3DH3', '3DH5', 'LE'])}
  LE_RX_ARG_CHECKER = {
      'rx_num_packets': ListChecker([int])}
  BT_RX_ARG_CHECKER = {
      'rx_num_bits': ListChecker([int])}
  ADJACENT_CHANNELS = ['acp_5', 'acp_4', 'acp_3', 'acp_2', 'acp_1',
                       'acp0', 'acp1', 'acp2', 'acp3', 'acp4', 'acp5']
  COMMON_RESULTS = ['avg_power'] + ADJACENT_CHANNELS
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
      'PRBS9': ['avg_power', 'bandwidth_20db', 'freq_offset', 'rx_ber',
                'rx_per'] + ADJACENT_CHANNELS,
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

  # The limits of adjacent channel power are defined in RF-PHY/TRM/BV-03-C and
  # RF/TRM/CA/BV-06-C.
  ADJACENT_CHANNEL_POWER = {
      'LE': dict(zip(
          ADJACENT_CHANNELS,
          [-30, -30, -30, -20, None, None, None, -20, -30, -30, -30])),
      'BDR': dict(zip(
          ADJACENT_CHANNELS,
          [-40, -40, -40, -20, None, None, None, -20, -40, -40, -40])),
      'EDR': dict(zip(
          ADJACENT_CHANNELS,
          [-40, -40, -40, -20, None, None, None, -20, -40, -40, -40]))}

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

  def _VerifyArgAndResultStandardRX(self, packet_format, args, result_limit):
    """Check if Bluetooth RX test limits are better than standard."""
    AssertRangeContain('all packets', 'power_level',
                       (None, -70), (None, args['power_level']))
    if packet_format == 'LE':
      # The limits of power_level, rx_num_packets, and rx_per for LE are defined
      # in RF-PHY/RCV/BV-01-C.
      AssertRangeContain(packet_format, 'rx_num_packets',
                         (1500, None), (args['rx_num_packets'], None))
      AssertRangeContain(packet_format, 'rx_per',
                         (0, 30.8), result_limit['rx_per'])
    elif packet_format == 'BDR':
      # The limits of power_level, rx_num_bits, and rx_ber for BDR are defined
      # in RF/RCV/CA/BV-02-C.
      AssertRangeContain(packet_format, 'rx_num_bits',
                         (1600000, None), (args['rx_num_bits'], None))
      AssertRangeContain(packet_format, 'rx_ber',
                         (0, 0.1), result_limit['rx_ber'])
    else:  # packet_format == EDR
      # The limits of power_level, rx_num_bits, and rx_ber for EDR are defined
      # in RF/RCV/CA/BV-07-C.
      standard_ber_level_0 = 0.007
      standard_ber_level_1 = 0.01
      AssertRangeContain(packet_format, 'rx_ber',
                         (0, standard_ber_level_1), result_limit['rx_ber'])
      if result_limit['rx_ber'][1] <= standard_ber_level_0:
        message = 'EDR with rx_ber in [0, %f]' % standard_ber_level_0
        standard_bits = (1600000, None)
      else:
        message = 'EDR with rx_ber in (%f, %f]' % (standard_ber_level_0,
                                                   standard_ber_level_1)
        standard_bits = (16000000, None)
      AssertRangeContain(message, 'rx_num_bits', standard_bits,
                         (args['rx_num_bits'], None))

  def _VerifyArgAndResultStandardTX(self, packet_format, packet_type,
                                    result_limit):
    """Check if Bluetooth TX test limits are better than standard."""
    standard_acp_list = self.ADJACENT_CHANNEL_POWER[packet_format]
    for channel, standard_acp in standard_acp_list.items():
      if channel in result_limit:
        AssertRangeContain(
            packet_format, channel, (None, standard_acp), result_limit[channel])
    STANDARD_BT_TX = {
        # The limits of delta_f1_avg, delta_f2_max, and delta_f2_f1_avg_ratio
        # are defined in RF-PHY/TRM/BV-05-C and RF/TRM/CA/BV-07-C.
        'delta_f1_avg': (225, 275) if packet_format == 'LE' else (140, 175),
        'delta_f2_max': (182, None) if packet_format == 'LE' else (115, None),
        'delta_f2_f1_avg_ratio': (0.8, None),
        # The limits of delta_f0_fn_max, delta_f1_f0, delta_fn_fn5_max, and
        # freq_offset are defined in RF-PHY/TRM/BV-06-C.
        'delta_f0_fn_max': (None, 50),
        'delta_f1_f0': (None, 23),
        'delta_fn_fn5_max': (None, 20),
        'freq_offset': (-150, 150),
        # The limits of freq_drift are defined in RF/TRM/CA/BV-09-C.
        'freq_drift': (-25, 25) if packet_type == '1DH1' else (-40, 40),
        # The limits of edr_power_diff are defined in RF/TRM/CA/BV-10-C.
        'edr_power_diff': (-4, 1),
        # The limits of edr_evm_avg, edr_evm_peak, edr_prob_evm_99_pass,
        # edr_extreme_omega_0, edr_extreme_omega_i0, and edr_omega_i are defined
        # in RF/TRM/CA/BV-11-C.
        'edr_evm_avg': (0, 20) if packet_type[0] == '2' else (0, 13),
        'edr_evm_peak': (0, 35) if packet_type[0] == '2' else (0, 25),
        'edr_prob_evm_99_pass': (0, 30) if packet_type[0] == '2' else (0, 20),
        'edr_extreme_omega_0': (-10, 10),
        'edr_extreme_omega_i0': (-75, 75),
        'edr_omega_i': (-75, 75),
        # The limits of bandwidth_20db are defined in RF/TRM/CA/BV-05-C.
        'bandwidth_20db': (0, 1.0)
    }
    for arg_name, limits in STANDARD_BT_TX.items():
      if arg_name in result_limit:
        AssertRangeContain(
            packet_type, arg_name, limits, result_limit[arg_name])

  def _VerifyArgAndResult(self, args, result_limit):
    # Check the RF type is valid.
    if self.RF_TYPE != args['rf_type']:
      raise ValueError('%s is not a valid RF type.' % args['rf_type'])
    # Check all required arguments are valid.
    arg_checker = self.REQUIRED_ARG_CHECKER.copy()
    test_type = args['test_type']
    packet_type = args['packet_type']
    packet_format = self._DetermineFormat(packet_type)
    if test_type == 'RX':
      if packet_format == 'LE':
        arg_checker.update(self.LE_RX_ARG_CHECKER)
      else:
        arg_checker.update(self.BT_RX_ARG_CHECKER)
    TestCaseFactory.VerifyArguments(arg_checker, args)
    # Check there is result and all results are valid.
    if test_type == 'TX':
      result_list = (self.COMMON_RESULTS +
                     self.FORMAT_RESULT_CHECKER[packet_format])
    elif packet_format == 'LE':
      result_list = self.LE_RX_RESULTS
    else:
      result_list = self.BT_RX_RESULTS
    TestCaseFactory._VerifyResults(result_list, result_limit)
    if test_type == 'RX':
      self._VerifyArgAndResultStandardRX(packet_format, args, result_limit)
    else:
      self._VerifyArgAndResultStandardTX(
          packet_format, packet_type, result_limit)

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
      'test_type':      ListChecker(SUPPORTED_TEST_TYPES),
      'center_freq':    ListChecker([lambda freq: 2400 < freq < 6000]),
      'power_level':    ListChecker([int, float, 'auto'])}
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
      elif not IsInBound(result[key], self.result_limit[key]):
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
    1 (b0001) means the first antenna is activated.
    2 (b0010) means the second antenna is activated.
    3 (b0011) means the first and the second antenna are activated.
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

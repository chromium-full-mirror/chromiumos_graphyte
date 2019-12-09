#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The mock DUT class. """

import os
import tempfile

import graphyte_common  # pylint: disable=unused-import
from graphyte.dut import DUTBase
from graphyte.default_setting import GRAPHYTE_DIR
from graphyte.default_setting import logger
from graphyte.utils.graphyte_utils import MakeMockPassResult
from graphyte.utils import graphyte_utils
from graphyte.utils import process_utils

# DUT_JAIL makes the classes it decorates share the same working directory.
# It protects working directory from being changed by other plugins and also
# prevents working directory of other plugins being changed.
DUT_JAIL = graphyte_utils.IsolateCWD()

@DUT_JAIL.IsolateAllMethods
class DUT(DUTBase):
  name = 'Mock DUT Plugin'

  def __init__(self, **kwargs):
    super(DUT, self).__init__(**kwargs)
    self.temp_dir = None
    self.controllers = {
        'WLAN': self.WlanController(self),
        'BLUETOOTH': self.BluetoothController(self),
        '802_15_4': self.ZigbeeController(self)}

  def _Initialize(self):
    logger.info('DUT Initialize')
    # Change to other working directory if you want.
    self.temp_dir = tempfile.mkdtemp('_DUT')
    logger.info('DUT Change diretory to %r', self.temp_dir)
    os.chdir(self.temp_dir)

  def _Terminate(self):
    logger.info('DUT Terminate at %r', os.getcwd())
    os.chdir(GRAPHYTE_DIR)
    if self.temp_dir:
      os.rmdir(self.temp_dir)

  def GetVersion(self):
    logger.info('DUT GetVersion')
    return process_utils.CheckOutput(['uname', '-a']).strip()

  @DUT_JAIL.IsolateAllMethods
  class WlanController(DUTBase.WlanControllerBase):
    def _Initialize(self):
      logger.info('DUT Wlan Initialize')

    def _Terminate(self):
      logger.info('DUT Wlan Terminate')

    def _TxStart(self, component_name, center_freq,
                 power_level, standard, bandwidth, data_rate, chain_mask, nss,
                 long_preamble, **kwargs):
      logger.info('DUT Wlan TxStart')

    def _TxStop(self, **kwargs):
      logger.info('DUT Wlan TxStop')

    def _RxClearResult(self, component_name, center_freq,
                       power_level, standard, bandwidth, data_rate, chain_mask,
                       nss, long_preamble, rx_num_packets, **kwargs):
      logger.info('DUT Wlan RxClearResult')

    def _RxGetResult(self, result_limit, **kwargs):
      logger.info('DUT Wlan RxGetResult')
      return MakeMockPassResult(result_limit)

  @DUT_JAIL.IsolateAllMethods
  class BluetoothController(DUTBase.BluetoothControllerBase):
    def _Initialize(self):
      logger.info('DUT Bluetooth Initialize')

    def _Terminate(self):
      logger.info('DUT Bluetooth Terminate')

    def _TxStart(self, component_name, center_freq,
                 power_level, packet_type, bit_pattern, **kwargs):
      logger.info('DUT Bluetooth TxStart')

    def _TxStop(self, **kwargs):
      logger.info('DUT Bluetooth TxStop')

    def _RxClearResult(self, component_name, center_freq,
                       power_level, packet_type, bit_pattern, **kwargs):
      logger.info('DUT Bluetooth RxClearResult')

    def _RxGetResult(self, result_limit, **kwargs):
      logger.info('DUT Bluetooth RxGetResult')
      return MakeMockPassResult(result_limit)

  @DUT_JAIL.IsolateAllMethods
  class ZigbeeController(DUTBase.ZigbeeControllerBase):
    def _Initialize(self):
      logger.info('DUT Zigbee Initialize')

    def _Terminate(self):
      logger.info('DUT Zigbee Terminate')

    def _TxStart(self, component_name, center_freq,
                 power_level, **kwargs):
      logger.info('DUT Zigbee TxStart')

    def _TxStop(self, **kwargs):
      logger.info('DUT Zigbee TxStop')

    def _RxClearResult(self, component_name, center_freq,
                       power_level, rx_num_packets, **kwargs):
      logger.info('DUT Zigbee RxClearResult')

    def _RxGetResult(self, result_limit, **kwargs):
      logger.info('DUT Zigbee RxGetResult')
      return MakeMockPassResult(result_limit)

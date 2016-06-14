#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The mock DUT class. """

from .. import DUTBase
from ...default_setting import logger
from ...utils import MakeMockPassResult


class DUT(DUTBase):
  name = 'Mock DUT Plugin'

  def __init__(self, **kwargs):
    super(DUT, self).__init__(**kwargs)
    self.controllers = {
        'WLAN': self.WlanController(self),
        'BLUETOOTH': self.BluetoothController(self),
        '802_15_4': self.ZigbeeController(self)}

  def Initialize(self):
    logger.info('DUT Initialize')

  def Terminate(self):
    logger.info('DUT Terminate')

  class WlanController(DUTBase.WlanControllerBase):
    def _Initialize(self):
      logger.info('DUT Wlan Initialize')

    def _Terminate(self):
      logger.info('DUT Wlan Terminate')

    def _TxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, standard, bandwidth, data_rate, chain_mask, nss,
                  long_preamble, **kwargs):
      logger.info('DUT Wlan TxConfig')

    def _TxStart(self, component_name, rf_type, test_type, center_freq,
                 power_level, standard, bandwidth, data_rate, chain_mask, nss,
                 long_preamble, **kwargs):
      logger.info('DUT Wlan TxStart')

    def _TxStop(self, **kwargs):
      logger.info('DUT Wlan TxStop')

    def _RxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, standard, bandwidth, data_rate, chain_mask, nss,
                  long_preamble, rx_num_packets, **kwargs):
      logger.info('DUT Wlan RxConfig')

    def _RxClearResult(self, component_name, rf_type, test_type, center_freq,
                       power_level, standard, bandwidth, data_rate, chain_mask,
                       nss, long_preamble, rx_num_packets, **kwargs):
      logger.info('DUT Wlan RxClearResult')

    def _RxGetResult(self, result_limit, **kwargs):
      logger.info('DUT Wlan RxGetResult')
      return MakeMockPassResult(result_limit)

  class BluetoothController(DUTBase.BluetoothControllerBase):
    def _Initialize(self):
      logger.info('DUT Bluetooth Initialize')

    def _Terminate(self):
      logger.info('DUT Bluetooth Terminate')

    def _TxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, packet_type, bit_pattern, **kwargs):
      logger.info('DUT Bluetooth TxConfig')

    def _TxStart(self, component_name, rf_type, test_type, center_freq,
                 power_level, packet_type, bit_pattern, **kwargs):
      logger.info('DUT Bluetooth TxStart')

    def _TxStop(self, **kwargs):
      logger.info('DUT Bluetooth TxStop')

    def _RxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, packet_type, bit_pattern, **kwargs):
      logger.info('DUT Bluetooth RxConfig')

    def _RxClearResult(self, component_name, rf_type, test_type, center_freq,
                       power_level, packet_type, bit_pattern, **kwargs):
      logger.info('DUT Bluetooth RxClearResult')

    def _RxGetResult(self, result_limit, **kwargs):
      logger.info('DUT Bluetooth RxGetResult')
      return MakeMockPassResult(result_limit)

  class ZigbeeController(DUTBase.ZigbeeControllerBase):
    def _Initialize(self):
      logger.info('DUT Zigbee Initialize')

    def _Terminate(self):
      logger.info('DUT Zigbee Terminate')

    def _TxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, **kwargs):
      logger.info('DUT Zigbee TxConfig')

    def _TxStart(self, component_name, rf_type, test_type, center_freq,
                 power_level, **kwargs):
      logger.info('DUT Zigbee TxStart')

    def _TxStop(self, **kwargs):
      logger.info('DUT Zigbee TxStop')

    def _RxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, rx_num_packets, **kwargs):
      logger.info('DUT Zigbee RxConfig')

    def _RxClearResult(self, component_name, rf_type, test_type, center_freq,
                       power_level, rx_num_packets, **kwargs):
      logger.info('DUT Zigbee RxClearResult')

    def _RxGetResult(self, result_limit, **kwargs):
      logger.info('DUT Zigbee RxGetResult')
      return MakeMockPassResult(result_limit)

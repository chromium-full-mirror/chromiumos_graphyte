#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The mock DUT class. """

import logging

from .. import DutBase


class Dut(DutBase):
  def __init__(self, args):
    logging.debug('Mock DUT __init__()')
    super(Dut, self).__init__(args)
    self.name = 'Mock DUT Plugin'
    self.controllers = {
        'WLAN': self.WlanController(self),
        'BLUETOOTH': self.BluetoothController(self),
        'ZIGBEE': self.ZigbeeController(self)}

  class WlanController(DutBase.WlanControllerBase):
    def _Initialize(self, component_name, **kwargs):
      logging.info('DUT Wlan Initialize: %s', component_name)

    def _Terminate(self, **kwargs):
      logging.info('DUT Wlan Terminate')

    def _TxSetMode(self, **kwargs):
      logging.info('DUT Wlan TxSetMode')

    def _TxSetPower(self, power_level=0, **kwargs):
      logging.info('DUT Wlan TxSetPower. Power level: %s', power_level)

    def _TxStart(self, **kwargs):
      logging.info('DUT Wlan TxStart')

    def _TxStop(self, **kwargs):
      logging.info('DUT Wlan TxStop')

    def _RxSetMode(self, **kwargs):
      logging.info('DUT Wlan RxSetMode')

    def _RxClearResult(self, **kwargs):
      logging.info('DUT Wlan RxClearResult')

    def _RxGetResult(self, result_limit, **kwargs):
      logging.info('DUT Wlan RxGetResult')
      results = dict([(key, 0) for key in result_limit.keys()])
      return results

  class BluetoothController(DutBase.BluetoothControllerBase):
    def _Initialize(self, component_name, **kwargs):
      logging.info('DUT Bluetooth Initialize: %s', component_name)

    def _Terminate(self, **kwargs):
      logging.info('DUT Bluetooth Terminate')

    def _TxSetMode(self, **kwargs):
      logging.info('DUT Bluetooth TxSetMode')

    def _TxSetPower(self, power_level=0, **kwargs):
      logging.info('DUT Bluetooth TxSetPower. Power level: %s', power_level)

    def _TxStart(self, **kwargs):
      logging.info('DUT Bluetooth TxStart')

    def _TxStop(self, **kwargs):
      logging.info('DUT Bluetooth TxStop')

    def _RxSetMode(self, **kwargs):
      logging.info('DUT Bluetooth RxSetMode')

    def _RxClearResult(self, **kwargs):
      logging.info('DUT Bluetooth RxClearResult')

    def _RxGetResult(self, result_limit, **kwargs):
      logging.info('DUT Bluetooth RxGetResult')
      results = dict([(key, 0) for key in result_limit.keys()])
      return results

  class ZigbeeController(DutBase.ZigbeeControllerBase):
    def _Initialize(self, component_name, **kwargs):
      logging.info('DUT Zigbee Initialize: %s', component_name)

    def _Terminate(self, **kwargs):
      logging.info('DUT Zigbee Terminate')

    def _TxSetMode(self, **kwargs):
      logging.info('DUT Zigbee TxSetMode')

    def _TxSetPower(self, power_level=0, **kwargs):
      logging.info('DUT Zigbee TxSetPower. Power level: %s', power_level)

    def _TxStart(self, **kwargs):
      logging.info('DUT Zigbee TxStart')

    def _TxStop(self, **kwargs):
      logging.info('DUT Zigbee TxStop')

    def _RxSetMode(self, **kwargs):
      logging.info('DUT Zigbee RxSetMode')

    def _RxClearResult(self, **kwargs):
      logging.info('DUT Zigbee RxClearResult')

    def _RxGetResult(self, result_limit, **kwargs):
      logging.info('DUT Zigbee RxGetResult')
      results = dict([(key, 0) for key in result_limit.keys()])
      return results

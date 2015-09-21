#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The mock instrument class. """

import logging

from inst import InstBase


class Inst(InstBase):
  def __init__(self, args):
    logging.debug('Mock inst __init__()')
    super(Inst, self).__init__(args)
    self.name = 'Mock inst Plugin'
    self.controllers = {
        'WLAN': self.WlanController(self),
        'BLUETOOTH': self.BluetoothController(self),
        'ZIGBEE': self.ZigbeeController(self)}

  def Initialize(self):
    logging.info('Inst Initialize')

  def Terminate(self):
    logging.info('Inst Terminate')

  def SelfCalibrate(self, calibration_type='full'):
    logging.info('Inst SelfCalibrate')

  def AutoLevel(self, ports):
    logging.info('Inst AutoLevel')

  def InitPathloss(self, loss_table):
    logging.info('Inst InitPathloss')

  def SetPassloss(self, port, table_indice):
    logging.info('Inst SetPassloss')

  def LockInstrument(self):
    logging.info('Inst LockInstrument')

  def UnlockInstrument(self):
    logging.info('Inst UnlockInstrument')

  class WlanController(InstBase.WlanControllerBase):
    def _TxConfig(self, **kwargs):
      logging.info('Wlan TxConfig')

    def _TxMeasure(self, **kwargs):
      logging.info('Wlan TxMeasure')

    def _TxGetResult(self, result_limit, **kwargs):
      logging.info('Wlan TxGetResult. Result limit: %s', result_limit)
      results = dict([(key, 0) for key in result_limit.keys()])
      return results

    def _RxConfig(self, **kwargs):
      logging.info('Wlan RxConfig')

    def _RxGenerate(self, rx_num_packets, power_level, **kwargs):
      logging.info('Wlan RxGenerate. Rx num packets: %s, power level: %s',
                   rx_num_packets, power_level)

    def _RxStop(self, **kwargs):
      logging.info('Wlan RxStop')

  class BluetoothController(InstBase.BluetoothControllerBase):
    def _TxConfig(self, **kwargs):
      logging.info('Bluetooth TxConfig')

    def _TxMeasure(self, **kwargs):
      logging.info('Bluetooth TxMeasure')

    def _TxGetResult(self, result_limit, **kwargs):
      logging.info('Bluetooth TxGetResult. Result limit: %s', result_limit)
      results = dict([(key, 0) for key in result_limit.keys()])
      return results

    def _RxConfig(self, **kwargs):
      logging.info('Bluetooth RxConfig')

    def _RxGenerate(self, rx_num_packets, power_level, **kwargs):
      logging.info('Bluetooth RxGenerate. Rx num packets: %s, power level: %s',
                   rx_num_packets, power_level)

    def _RxStop(self, **kwargs):
      logging.info('Bluetooth RxStop')

  class ZigbeeController(InstBase.ZigbeeControllerBase):
    def _TxConfig(self, **kwargs):
      logging.info('Zigbee TxConfig')

    def _TxMeasure(self, **kwargs):
      logging.info('Zigbee TxMeasure')

    def _TxGetResult(self, result_limit, **kwargs):
      logging.info('Zigbee TxGetResult. Result limit: %s', result_limit)
      results = dict([(key, 0) for key in result_limit.keys()])
      return results

    def _RxConfig(self, **kwargs):
      logging.info('Zigbee RxConfig')

    def _RxGenerate(self, rx_num_packets, power_level, **kwargs):
      logging.info('Zigbee RxGenerate. Rx num packets: %s, power level: %s',
                   rx_num_packets, power_level)

    def _RxStop(self, **kwargs):
      logging.info('Zigbee RxStop')

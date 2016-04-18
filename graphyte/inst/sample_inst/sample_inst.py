#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The mock instrument class. """


from .. import InstBase
from ...testplan import ChainMaskToList
from ...default_setting import logger


def _MakePassResult(result_limit):
  """Make the result that pass all limit."""
  def _MakeInBoundValue(bound):
    lower, upper = bound
    if lower is None:
      return upper - 1
    if upper is None:
      return lower + 1
    return (lower + upper) / 2
  return dict([(key, _MakeInBoundValue(bound))
               for key, bound in result_limit.iteritems()])


class Inst(InstBase):
  name = 'Mock inst Plugin'

  def SetRFController(self):
    self.controllers = {
        'WLAN': self.WlanController(self),
        'BLUETOOTH': self.BluetoothController(self),
        '802_15_4': self.ZigbeeController(self)}

  def Initialize(self):
    logger.info('Inst Initialize')

  def Terminate(self):
    logger.info('Inst Terminate')

  def SelfCalibrate(self, calibration_type='full'):
    logger.info('Inst SelfCalibrate')

  def _SetPortConfig(self, port_mapping, pathloss):
    logger.info('Inst _SetPortConfig')

  def LockInstrument(self):
    logger.info('Inst LockInstrument')

  def UnlockInstrument(self):
    logger.info('Inst UnlockInstrument')

  class WlanController(InstBase.WlanControllerBase):
    def __init__(self, inst):
      super(Inst.WlanController, self).__init__(inst)
      self.chain_list = None

    def _TxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, standard, bandwidth, data_rate, chain_mask, nss,
                  long_preamble, **kwargs):
      logger.info('Wlan TxConfig')
      self.chain_list = ChainMaskToList(kwargs.get('chain_mask'))

    def _TxMeasure(self, component_name, rf_type, test_type, center_freq,
                   power_level, standard, bandwidth, data_rate, chain_mask,
                   nss, long_preamble, result_limit, **kwargs):
      logger.info('Wlan TxMeasure')

    def _TxGetResult(self, component_name, rf_type, test_type, center_freq,
                     power_level, standard, bandwidth, data_rate, chain_mask,
                     nss, long_preamble, result_limit, **kwargs):
      logger.info('Wlan TxGetResult. Result limit: %s', result_limit)
      result = _MakePassResult(result_limit)
      if len(self.chain_list) > 1:
        for key, value in result.iteritems():
          result[key] = {idx: value for idx in self.chain_list}
      return result

    def _RxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, standard, bandwidth, data_rate, chain_mask, nss,
                  long_preamble, rx_num_packets, **kwargs):
      logger.info('Wlan RxConfig')

    def _RxGenerate(self, component_name, rf_type, test_type, center_freq,
                    power_level, standard, bandwidth, data_rate, chain_mask,
                    nss, long_preamble, rx_num_packets, **kwargs):
      logger.info('Wlan RxGenerate. Rx num packets: %s, power level: %s',
                  rx_num_packets, power_level)

    def _RxStop(self, **kwargs):
      logger.info('Wlan RxStop')

  class BluetoothController(InstBase.BluetoothControllerBase):
    def _TxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, packet_type, bit_pattern, **kwargs):
      logger.info('Bluetooth TxConfig')

    def _TxMeasure(self, component_name, rf_type, test_type, center_freq,
                   power_level, packet_type, bit_pattern, result_limit,
                   **kwargs):
      logger.info('Bluetooth TxMeasure')

    def _TxGetResult(self, component_name, rf_type, test_type, center_freq,
                     power_level, packet_type, bit_pattern, result_limit,
                     **kwargs):
      logger.info('Bluetooth TxGetResult. Result limit: %s', result_limit)
      return _MakePassResult(result_limit)

    def _RxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, packet_type, bit_pattern, **kwargs):
      logger.info('Bluetooth RxConfig')

    def _RxGenerate(self, component_name, rf_type, test_type, center_freq,
                    power_level, packet_type, bit_pattern, **kwargs):
      logger.info('Bluetooth RxGenerate. power level: %s', power_level)

    def _RxStop(self, **kwargs):
      logger.info('Bluetooth RxStop')

  class ZigbeeController(InstBase.ZigbeeControllerBase):
    def _TxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, **kwargs):
      logger.info('Zigbee TxConfig')

    def _TxMeasure(self, component_name, rf_type, test_type, center_freq,
                   power_level, result_limit, **kwargs):
      logger.info('Zigbee TxMeasure')

    def _TxGetResult(self, component_name, rf_type, test_type, center_freq,
                     power_level, result_limit, **kwargs):
      logger.info('Zigbee TxGetResult. Result limit: %s', result_limit)
      return _MakePassResult(result_limit)

    def _RxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, rx_num_packets, **kwargs):
      logger.info('Zigbee RxConfig')

    def _RxGenerate(self, component_name, rf_type, test_type, center_freq,
                    power_level, rx_num_packets, **kwargs):
      logger.info('Zigbee RxGenerate. Rx num packets: %s, power level: %s',
                  rx_num_packets, power_level)

    def _RxStop(self, **kwargs):
      logger.info('Zigbee RxStop')

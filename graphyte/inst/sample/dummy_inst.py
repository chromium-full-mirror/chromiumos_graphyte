#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The mock instrument class. """

import os
import tempfile

import graphyte_common  # pylint: disable=unused-import
from graphyte.inst import InstBase
from graphyte.testplan import ChainMaskToList
from graphyte.default_setting import GRAPHYTE_DIR
from graphyte.default_setting import logger
from graphyte.utils.graphyte_utils import MakeMockPassResult
from graphyte.utils import graphyte_utils
from graphyte.utils import process_utils

# INST_JAIL makes the classes it decorates share the same working directory.
# It protects working directory from being changed by other plugins and also
# prevents working directory of other plugins being changed.
INST_JAIL = graphyte_utils.IsolateCWD()

@INST_JAIL.IsolateAllMethods
class Inst(InstBase):
  name = 'Mock inst Plugin'
  VALID_PORT_NAMES = ['dummy_port']

  def __init__(self, **kwargs):
    super(Inst, self).__init__(**kwargs)
    self.temp_dir = None
    self.controllers = {
        'WLAN': self.WlanController(self),
        'BLUETOOTH': self.BluetoothController(self),
        '802_15_4': self.ZigbeeController(self)}

  def _Initialize(self):
    logger.info('Inst Initialize')
    # Change to other working directory if you want.
    self.temp_dir = tempfile.mkdtemp('_Inst')
    logger.info('Inst Change diretory to %r', self.temp_dir)
    os.chdir(self.temp_dir)

  def _Terminate(self):
    logger.info('Inst Terminate at %r', os.getcwd())
    os.chdir(GRAPHYTE_DIR)
    if self.temp_dir:
      os.rmdir(self.temp_dir)

  def _SetPortConfig(self, port_mapping, pathloss):
    logger.info('Inst _SetPortConfig')

  def LockInstrument(self):
    logger.info('Inst LockInstrument')

  def UnlockInstrument(self):
    logger.info('Inst UnlockInstrument')

  def GetVersion(self):
    logger.info('Inst GetVersion')
    return process_utils.CheckOutput(['uname', '-a']).strip()

  @INST_JAIL.IsolateAllMethods
  class WlanController(InstBase.WlanControllerBase):
    def __init__(self, inst):
      super(Inst.WlanController, self).__init__(inst)
      self.chain_list = None

    def _Initialize(self):
      logger.info('Inst WLAN Initialize')

    def _Terminate(self):
      logger.info('Inst WLAN Terminate')

    def _TxMeasure(self, component_name, center_freq,
                   power_level, standard, bandwidth, data_rate, chain_mask,
                   nss, long_preamble, result_limit, **kwargs):
      logger.info('Wlan TxMeasure')
      self.chain_list = ChainMaskToList(kwargs.get('chain_mask'))

    def _TxGetResult(self, component_name, center_freq,
                     power_level, standard, bandwidth, data_rate, chain_mask,
                     nss, long_preamble, result_limit, **kwargs):
      logger.info('Wlan TxGetResult. Result limit: %s', result_limit)
      result = MakeMockPassResult(result_limit)
      if len(self.chain_list) > 1:
        for key, value in result.iteritems():
          result[key] = {idx: value for idx in self.chain_list}
      return result

    def _RxGenerate(self, component_name, center_freq,
                    power_level, standard, bandwidth, data_rate, chain_mask,
                    nss, long_preamble, rx_num_packets, **kwargs):
      logger.info('Wlan RxGenerate. Rx num packets: %s, power level: %s',
                  rx_num_packets, power_level)

    def _RxStop(self, **kwargs):
      logger.info('Wlan RxStop')

  @INST_JAIL.IsolateAllMethods
  class BluetoothController(InstBase.BluetoothControllerBase):
    def _Initialize(self):
      logger.info('Inst Bluetooth Initialize')

    def _Terminate(self):
      logger.info('Inst Bluetooth Terminate')

    def _TxMeasure(self, component_name, center_freq,
                   power_level, packet_type, bit_pattern, result_limit,
                   **kwargs):
      logger.info('Bluetooth TxMeasure')

    def _TxGetResult(self, component_name, center_freq,
                     power_level, packet_type, bit_pattern, result_limit,
                     **kwargs):
      logger.info('Bluetooth TxGetResult. Result limit: %s', result_limit)
      return MakeMockPassResult(result_limit)

    def _RxGenerate(self, component_name, center_freq,
                    power_level, packet_type, bit_pattern, **kwargs):
      logger.info('Bluetooth RxGenerate. power level: %s', power_level)

    def _RxStop(self, **kwargs):
      logger.info('Bluetooth RxStop')

  @INST_JAIL.IsolateAllMethods
  class ZigbeeController(InstBase.ZigbeeControllerBase):
    def _Initialize(self):
      logger.info('Inst Zigbee Initialize')

    def _Terminate(self):
      logger.info('Inst Zigbee Terminate')

    def _TxMeasure(self, component_name, center_freq,
                   power_level, result_limit, **kwargs):
      logger.info('Zigbee TxMeasure')

    def _TxGetResult(self, component_name, center_freq,
                     power_level, result_limit, **kwargs):
      logger.info('Zigbee TxGetResult. Result limit: %s', result_limit)
      return MakeMockPassResult(result_limit)

    def _RxGenerate(self, component_name, center_freq,
                    power_level, rx_num_packets, **kwargs):
      logger.info('Zigbee RxGenerate. Rx num packets: %s, power level: %s',
                  rx_num_packets, power_level)

    def _RxStop(self, **kwargs):
      logger.info('Zigbee RxStop')

#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The Anritsu ML2437A power meter. """

import re

from .. import InstBase
from ...default_setting import logger
from ...testplan import ChainMaskToList
from ...utils import CalculateAverage

class InstrumentNotReady(Exception):
  pass


class RFController(InstBase.ControllerBase):
  def __init__(self, inst=None):
    super(RFController, self).__init__(inst)
    self.result = None

  def _Initialize(self):
    pass

  def _Terminate(self):
    pass

  def _TxConfig(self, center_freq, **kwargs):
    self.inst.SetFrequency(center_freq)

  def _TxMeasure(self, center_freq, **kwargs):
    power = self.inst.FetchPower()
    if 'chain_mask' in kwargs:  # WLAN case
      antenna_indice = ChainMaskToList(kwargs['chain_mask'])
      result = {}
      for idx in antenna_indice:
        result[idx] = power + self.inst.current_pathloss[idx][center_freq]
    else:
      result = power + self.inst.current_pathloss[0][center_freq]

    self.result = {'avg_power': result}

  def _TxGetResult(self, result_limit, **kwargs):
    return self.result

  def _RxConfig(self, **kwargs):
    raise NotImplementedError

  def _RxGenerate(self, rx_num_packets, power_level, **kwargs):
    raise NotImplementedError

  def _RxStop(self, **kwargs):
    raise NotImplementedError


class Inst(InstBase):
  name = 'Anritsu ML2437A'
  need_link = True

  def __init__(self, sample_number=5, **kwargs):
    super(Inst, self).__init__(**kwargs)
    self.current_pathloss = None
    self.sample_number = sample_number

    self.controllers = {
        'WLAN': RFController(self),
        'BLUETOOTH': RFController(self),
        '802_15_4': RFController(self)}

  def Initialize(self):
    logger.info('Inst Initialize')
    if not self.link.IsReady():
      raise InstrumentNotReady
    self.link.CheckCall('*RST')

  def Terminate(self):
    pass

  def SelfCalibrate(self, calibration_type='full'):
    pass

  def _SetPortConfig(self, port_mapping, pathloss):
    self.current_pathloss = pathloss

  def LockInstrument(self):
    pass

  def UnlockInstrument(self):
    pass

  def SetFrequency(self, freq_mhz):
    logger.info('Set frequency to %d MHz', freq_mhz)
    self.link.CheckCall('CFFRQ A, %s' % (freq_mhz * 1e6))
    output = self.link.CheckOutput('CFFRQ? A')
    try:
      fetch_freq = float(re.match('CFFRQ A,(.+)', output).group(1))
      return int(fetch_freq / 1e6) == freq_mhz
    except Exception:
      return False

  def FetchPower(self):
    results = []
    try:
      for _ in range(self.sample_number):
        results.append(float(self.link.CheckOutput('O 1')))
      logger.debug('Fetch power: %s', results)
    except Exception:
      return None
    return CalculateAverage(results, '10Log10')

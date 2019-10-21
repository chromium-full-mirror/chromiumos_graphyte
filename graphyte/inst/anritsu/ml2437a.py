#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The plugin of Anritsu ML2437A power meter.

Reference: ML2430A series power meter operation manual."""

import re
import time

import graphyte_common  # pylint: disable=unused-import
from graphyte.inst import InstBase
from graphyte.default_setting import logger
from graphyte.testplan import ChainMaskToList
from graphyte.utils.graphyte_utils import CalculateAverage


class RFController(InstBase.PowerMeterControllerBase):
  def __init__(self, inst=None, duty_cycle=None):
    super(RFController, self).__init__(inst)
    self.result = None
    self.duty_cycle = duty_cycle
    self.inst.SetDutyCycle(self.duty_cycle)

  def _TxMeasure(self, center_freq, **kwargs):
    self.inst.SetFrequency(center_freq)
    time.sleep(2)  # Wait for power meter stable
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

  def _RxGenerate(self, rx_num_packets, power_level, **kwargs):
    raise NotImplementedError

  def _RxStop(self, **kwargs):
    raise NotImplementedError


class Inst(InstBase):
  name = 'Anritsu ML2437A'
  need_link = True
  VALID_PORT_NAMES = ['A']

  def __init__(self, sample_number=5, wlan_duty_cycle=None,
               bluetooth_duty_cycle=None, zigbee_duty_cycle=None, **kwargs):
    super(Inst, self).__init__(**kwargs)
    self.current_pathloss = None
    self.sample_number = sample_number

    self.controllers = {
        'WLAN': RFController(self, wlan_duty_cycle),
        'BLUETOOTH': RFController(self, bluetooth_duty_cycle),
        '802_15_4': RFController(self, zigbee_duty_cycle)}

  def _Initialize(self):
    logger.info('Inst Initialize')
    self.link.CheckCall('*RST')

  def _Terminate(self):
    pass

  def _SetPortConfig(self, port_mapping, pathloss):
    self.current_pathloss = pathloss

  def LockInstrument(self):
    pass

  def UnlockInstrument(self):
    pass

  def GetVersion(self):
    return self.name

  def SetFrequency(self, freq_mhz):
    logger.info('Set frequency to %d MHz', freq_mhz)
    self.link.CheckCall('CFFRQ A, %s' % (freq_mhz * 1e6))
    output = self.link.CheckOutput('CFFRQ? A')
    try:
      fetch_freq = float(re.match('CFFRQ A,(.+)', output).group(1))
      return int(fetch_freq / 1e6) == freq_mhz
    except Exception:
      return False

  def SetDutyCycle(self, duty_cycle):
    """Applies a duty cycle to the sensor.

    When the signal is continuous carrier wave, we should turn off the duty
    cycle and set the sensor measurement mode to default. On the other hand, if
    the signal is modulated signal, we should turn on the duty cycle setting and
    set the sensor measurement mode to modulated average.

    Args:
      duty_cycle: None to turn of duty cycle, or a number between 0 and 100.
    """
    if duty_cycle is None:
      self.link.CheckCall('DUTYS A,OFF')
      self.link.CheckCall('SENMM A,DEFAULT')
    else:
      self.link.CheckCall('DUTYS A,ON')
      self.link.CheckCall('DUTY A,%d' % duty_cycle)
      self.link.CheckCall('SENMM A,MOD')

  def FetchPower(self):
    results = []
    try:
      for _ in range(self.sample_number):
        results.append(float(self.link.CheckOutput('O 1')))
      logger.debug('Fetch power: %s', results)
    except Exception:
      return None
    return CalculateAverage(results, '10Log10')

#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The Keysight N1914a power meter.

Reference: Keysight official document
  N1913A/N1914A EPM series Power Meter Programming Guide.
"""

import graphyte_common  # pylint: disable=unused-import
from graphyte.inst import InstBase
from graphyte.default_setting import logger
from graphyte.testplan import ChainMaskToList

# The mapping from the port name to the index. The port name is recorded at
# the port_mapping config file, and the index is used for calling SCPI command.
PORT_INDEX_MAPPING = {
    'A': 1,
    'B': 2}

DEFAULT_LINK_OPTIONS = {
    'link_class': 'SCPILink',
    'host': '10.3.0.60',
    'port': 5025
}


class Inst(InstBase):
  name = 'Keysight N1914a'
  need_link = True
  VALID_PORT_NAMES = ['A', 'B']

  def __init__(self, range_setting='AUTO', avg_count=0,
               continuous_trigger=False, trigger_source='IMMediate', **kwargs):
    """Initialize method.

    Args:
      range_setting: 0, 1, or 'AUTO'.
      avg_count: integer or 'AUTO'.
      continuous_trigger: enable continuous trigger or not. boolean.
      trigger_source: the trigger source. string.
    """
    kwargs.setdefault('link_options', {})
    for key, value in DEFAULT_LINK_OPTIONS.items():
      kwargs['link_options'].setdefault(key, value)
    super(Inst, self).__init__(**kwargs)
    self.port_mapping = None
    self.current_pathloss = None

    assert range_setting in [0, 1, 'AUTO']
    assert isinstance(avg_count, int) or avg_count == 'AUTO'

    self.range_setting = range_setting
    self.avg_count = avg_count
    self.continuous_trigger = continuous_trigger
    self.trigger_source = trigger_source

    self.controllers = {rf_type: RFController(self)
                        for rf_type in ['WLAN', 'BLUETOOTH', '802_15_4']}

  def _Initialize(self):
    logger.info('Inst Initialize')
    # Choose SCPI language
    self.SendCommand('SYSTem:LANGuage SCPI')
    self.SendCommand('*RST')

    # Set range and average filter
    self.SendCommand('FORM ASCii')
    for port_idx in PORT_INDEX_MAPPING.values():
      self.SendCommand('UNIT%d:POWer DBM' % port_idx)
      self._SetRange(self.range_setting, port_idx)
      self._SetAverageFilter(self.avg_count, port_idx)
      self._SetContinuousTrigger(self.continuous_trigger, port_idx)
      self._SetTriggerMode(self.trigger_source, port_idx)

  def _Terminate(self):
    pass

  def _SetPortConfig(self, port_mapping, pathloss):
    self.port_mapping = port_mapping
    self.current_pathloss = pathloss

  def LockInstrument(self):
    # Multi-DUT testing is not supported, ignore this method.
    pass

  def UnlockInstrument(self):
    # Multi-DUT testing is not supported, ignore this method.
    pass

  def GetVersion(self):
    return self.name

  def QueryCommand(self, command):
    self.link.CheckCall('*CLS')
    output = self.link.CheckOutput(command)
    # *ESR? returns the error string. We do this to make sure that we can
    # detect an unknown header rather than just waiting forever.
    check_str = self.link.CheckOutput('*ESR?')
    if ',' in check_str:
      raise ValueError('Error issuing command %s while calling *ESR?: %s' %
                       (command, check_str))
    # Success! Get SYST:ERR, which should be +0
    check_str = self.link.CheckOutput('SYST:ERR?')
    if check_str != '+0,"No error"':
      raise ValueError('Error issuing command %s while calling SYST:ERR?: %s' %
                       (command, check_str))
    return output

  def SendCommand(self, command):
    self.link.CheckCall('*CLS')
    self.link.CheckCall(command)
    # Success! Get SYST:ERR, which should be +0
    check_str = self.link.CheckOutput('SYST:ERR?')
    if check_str != '+0,"No error"':
      raise ValueError('Error issuing command %s while calling SYST:ERR?: %s' %
                       (command, check_str))
    check_str = self.link.CheckOutput('*OPC?')
    if int(check_str) != 1:
      raise ValueError('Expected 1 after *OPC? but got %s' % check_str)

  def _SetRange(self, range_setting, port_idx):
    """Selects a sensor's range (lower or upper).

    Args:
      range_setting: None to enable auto-range feature. To speed up the
        measurement, caller can specify the range manually based on the
        expected power. To manually set the range, use 0 to indicate a
        lower range and 1 for the upper range. Because range definition
        varies from sensor to sensor, check the manual before using this
        function.
      port_idx: the index of the selected port. 1 or 2.
    """
    assert range_setting in ['AUTO', 0, 1]
    if range_setting == 'AUTO':
      self.SendCommand('SENSe%d:POWer:AC:RANGe:AUTO 1' % port_idx)
    else:
      self.SendCommand('SENSe%d:POWer:AC:RANGe:AUTO 0' % port_idx)
      self.SendCommand('SENSe%d:POWer:AC:RANGe %d' %
                       (port_idx, range_setting))

  def _SetAverageFilter(self, avg_count, port_idx):
    """Sets the average filter.

    There are three different average filters available, averaging disable,
    auto averaging and average with a specific window length.

    Args:
      avg_length: Use 'AUTO' for auto averaging, 0 for averaging disable, and
        other positive numbers for specific window length.
      port_idx: the index of the selected port. 1 or 2.
    """
    if avg_count == 'AUTO':
      self.SendCommand('SENSe%d:AVERage:COUNt:AUTO ON' % port_idx)
    elif avg_count == 0:
      # Disable the average filter.
      self.SendCommand('SENSe%d:AVERage:STATe 0' % port_idx)
    elif isinstance(avg_count, int):
      self.SendCommand('SENSe%d:AVERage:COUNt:AUTO OFF' % port_idx)
      self.SendCommand('SENSe%d:AVERage:COUNt %d' % (port_idx, avg_count))
    else:
      raise ValueError('Invalid avg_count setting [%s]' % avg_count)

  def _SetContinuousTrigger(self, enable, port_idx):
    status = 'ON' if enable else 'OFF'
    self.SendCommand('INITiate%d:CONTinuous %s' % (port_idx, status))

  def _SetTriggerMode(self, trigger_source, port_idx):
    self.SendCommand('TRIGger%d:SOURce %s' % (port_idx, trigger_source))

  def SetFrequency(self, freq_mhz, port_idx):
    logger.info('Set frequency to %d MHz', freq_mhz)
    self.SendCommand('SENSe%d:FREQuency %sMHz' % (port_idx, freq_mhz))
    self.SendCommand('SENSe%d:CORRection:GAIN2:STATe 0' % port_idx)

  def FetchPower(self, port_idx):
    try:
      self.SendCommand('INITiate%d:IMMediate' % port_idx)
      result = float(self.QueryCommand('FETch%d?' % port_idx))
      logger.debug('Fetch power: %s', result)
      return result
    except Exception:
      logger.exception('Fetch power failed.')
      return float('-inf')


class RFController(InstBase.PowerMeterControllerBase):
  def __init__(self, inst):
    super(RFController, self).__init__(inst)
    self.result = None

  def _TxMeasure(self, center_freq, **kwargs):
    self.inst.SendCommand('ABORt')
    for port_idx in PORT_INDEX_MAPPING.values():
      self.inst.SetFrequency(center_freq, port_idx)
    def _MeasurePower(antenna_index):
      port_name = self.inst.port_mapping[antenna_index]
      logger.debug('Measure power for antenna %s, port name is %s',
                   antenna_index, port_name)
      port_idx = PORT_INDEX_MAPPING[port_name]
      power = self.inst.FetchPower(port_idx)
      return power + self.inst.current_pathloss[antenna_index][center_freq]

    if 'chain_mask' in kwargs:  # WLAN case
      antenna_indice = ChainMaskToList(kwargs['chain_mask'])
      result = {}
      for idx in antenna_indice:
        result[idx] = _MeasurePower(idx)
    else:
      # SISO case.
      assert len(self.inst.port_mapping) == 1
      result = _MeasurePower(0)

    self.result = {'avg_power': result}

  def _TxGetResult(self, result_limit, **kwargs):
    ret = self.result
    self.result = None
    return ret

  def _RxGenerate(self, rx_num_packets, power_level, **kwargs):
    raise NotImplementedError

  def _RxStop(self, **kwargs):
    raise NotImplementedError

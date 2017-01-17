#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The Virtual Instrument module.
This is the virtual instrument class which every instrument plugin should
implement.
"""

from .. import link
from ..default_setting import logger


class InstBase(object):
  """The abstract instrument class that every instrument plugin should inherit
  it. It contains several RF controllers, and each controller corresponds one RF
  chip. We can control different RF chip by assigning the rf_type, and delegate
  to the assigned controller."""

  name = 'Virtual instrument Plugin'
  need_link = False

  def __init__(self, **kwargs):
    """Abstract init method. The init method of each child class shoule be:

    def __init__(self, arg1, **kwargs):
      # Call parent's __init__
      super(Inst, self).__init__(**kwargs)
      # Set the child arguments
      self.arg1 = arg1
      # Set the RF controllers
      self.controllers = {
          'WLAN': ChildWlanController(self),
          'BLUETOOTH': ChildBluetoothController(self),
      }
    """
    self.rf_type = None
    self.controllers = {}
    self.link = link.Create(kwargs['link_options']) if self.need_link else None
    # Active component record the current (component_name, test_type)
    # for port mapping and pathloss.
    self.port_config_table = None
    self.active_component = (None, None)

  def __getattr__(self, name):
    """Delegate to the active controller, that is recorded at rf_type."""
    try:
      return getattr(self.controllers[self.rf_type], name)
    except:
      logger.exception('Failed in InstBase __getattr__')
      raise NotImplementedError

  def SetRF(self, rf_type):
    if self.rf_type is not None:
      self.controllers[self.rf_type].Terminate()
    self.rf_type = rf_type
    self.controllers[self.rf_type].Initialize()

  def Initialize(self):
    """Initialize the instrument.

    The method would be called only once before all tests items are executed.
    """
    raise NotImplementedError

  def Terminate(self):
    """Terminate the instrument.

    The method would be called only once after all tests items are executed.
    """
    raise NotImplementedError

  def SelfCalibrate(self, calibration_type='full'):
    raise NotImplementedError

  def InitPortConfig(self, port_config_table):
    self.port_config_table = port_config_table

  def SetPortConfig(self, test):
    component_name = test.args['component_name']
    test_type = test.test_type

    if self.active_component == (component_name, test_type):
      logger.debug('The port config is the same, ignored')
      return
    logger.info('Set the port config for component: %s %s',
                component_name, test_type)
    self.active_component = (component_name, test_type)
    active_port_config = self.port_config_table.QueryPortConfig(
        component_name, test_type)
    port_mapping = [config['port_mapping'] for config in active_port_config]
    pathloss = [config['pathloss'] for config in active_port_config]
    logger.debug('Port mapping: %s', port_mapping)
    logger.debug('Path loss: %s', pathloss)
    self._SetPortConfig(port_mapping, pathloss)

  def _SetPortConfig(self, port_mapping, pathloss):
    """Set the port mapping and the pathloss table for the active component.
    Because a component might be multiple antenna, the port mapping and the path
    loss are the list.
    Arg:
      port_mapping: The port name for each antenna.
        The format is <port name>:<port number>
        Example:
          ['VSA0:0', 'VSA1:0', 'VSA2:0']
      pathloss: A list of port_config.PathlossTable for each antenna.
        Example:
          [PathlossTable({'2440': '20.4', '2412': '20.4'}),
           PathlossTable({'2440': '20.2', '2412': '20.5'}),
           PathlossTable({'2440': '20.1', '2412': '20.6'})]
    """
    raise NotImplementedError

  def LockInstrument(self):
    raise NotImplementedError

  def UnlockInstrument(self):
    raise NotImplementedError

  class ControllerBase(object):
    def __init__(self, inst=None):
      self.inst = inst

    def Initialize(self):
      """Initialize the RF interface."""
      return self._Initialize()

    def _Initialize(self):
      raise NotImplementedError

    def Terminate(self):
      """Disconnect/unconfigure the interface that was being used."""
      return self._Terminate()

    def _Terminate(self, **kwargs):
      raise NotImplementedError

    def TxConfig(self, test):
      return self._TxConfig(**test.ToDict())

    def _TxConfig(self, **kwargs):
      raise NotImplementedError

    def TxMeasure(self, test):
      return self._TxMeasure(**test.ToDict())

    def _TxMeasure(self, **kwargs):
      raise NotImplementedError

    def TxGetResult(self, test):
      results = self._TxGetResult(**test.ToDict())
      # TODO(akahuang): Check the structure of the results.
      return (test.CheckTestPasses(results), results)

    def _TxGetResult(self, result_limit, **kwargs):
      """Wait for measurement to be completed and return the test result.

      Args:
        result_limit: A dict of the test result.
        The values are a tuple of the lower bound and upper bound.
        Example:
          {
            'test_result1': (None, -25),
            'test_result2': (16, 20)
          }
        kwargs: The remaining arguments of the test case.

      Returns:
        A dict which keys are the same as the result_limit.
        The values is one number for SISO case, or a dict mapping from
        the antenna index to value for MIMO case. If a value is returned for
        MIMO case, we consider the results for each antenna are all the same.
        Example for SISO case:
        {
          'test_result1': -20,
          'test_result2': 21
        }
        Example for 2x2 MIMO case:
        {
          'test_result1': {
            0: -20,
            1: -30
          },
          'test_result2': {
            0: 17,
            1: 18
          }
        }
      """
      raise NotImplementedError

    def RxConfig(self, test):
      return self._RxConfig(**test.ToDict())

    def _RxConfig(self, **kwargs):
      raise NotImplementedError

    def RxGenerate(self, test):
      return self._RxGenerate(**test.ToDict())

    def _RxGenerate(self, rx_num_packets, power_level, **kwargs):
      raise NotImplementedError

    def RxStop(self, test):
      return self._RxStop(**test.ToDict())

    def _RxStop(self, **kwargs):
      raise NotImplementedError

  class WlanControllerBase(ControllerBase):
    def _TxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, standard, bandwidth, data_rate, chain_mask, nss,
                  long_preamble, **kwargs):
      raise NotImplementedError

    def _TxMeasure(self, component_name, rf_type, test_type, center_freq,
                   power_level, standard, bandwidth, data_rate, chain_mask,
                   nss, long_preamble, result_limit, **kwargs):
      raise NotImplementedError

    def _TxGetResult(self, component_name, rf_type, test_type, center_freq,
                     power_level, standard, bandwidth, data_rate, chain_mask,
                     nss, long_preamble, result_limit, **kwargs):
      raise NotImplementedError

    def _RxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, standard, bandwidth, data_rate, chain_mask, nss,
                  long_preamble, rx_num_packets, **kwargs):
      raise NotImplementedError

    def _RxGenerate(self, component_name, rf_type, test_type, center_freq,
                    power_level, standard, bandwidth, data_rate, chain_mask,
                    nss, long_preamble, rx_num_packets, **kwargs):
      raise NotImplementedError

  class BluetoothControllerBase(ControllerBase):
    def __init__(self, inst):
      InstBase.ControllerBase.__init__(self, inst)
      self.inst = inst
      # Store the delta_f1_avg and delta_f2_avg for delta_f2_f1_avg_ratio
      self._delta_f1_avg_results = {}
      self._delta_f2_avg_results = {}

    def _TxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, packet_type, bit_pattern, **kwargs):
      raise NotImplementedError

    def _TxMeasure(self, component_name, rf_type, test_type, center_freq,
                   power_level, packet_type, bit_pattern, result_limit,
                   **kwargs):
      raise NotImplementedError

    def TxGetResult(self, test):
      """Calculate Bluetooth Tx result.

      delta_f2_f1_avg_ratio is the ratio of delta_f2_avg and delta_f1_avg, but
      two results come from different bit pattern, F0 and AA. So we measure both
      results separately and store them. While both results are measured, then
      we calculate the delta_f2_f1_avg_ratio.
      """
      # We don't ask the inst plugin to measure delta_f2_f1_avg_ratio. Instead
      # we need to ensure we would measure delta_f1_avg and delta_f2_avg.
      modified_test = test.Copy()
      if 'delta_f2_f1_avg_ratio' in modified_test.result_limit:
        modified_test.result_limit.pop('delta_f2_f1_avg_ratio')
        if modified_test.args['bit_pattern'] == 'F0':
          modified_test.result_limit.setdefault('delta_f1_avg', (None, None))
        elif modified_test.args['bit_pattern'] == 'AA':
          modified_test.result_limit.setdefault('delta_f2_avg', (None, None))

      results = self._TxGetResult(**modified_test.ToDict())

      if 'delta_f2_f1_avg_ratio' in test.result_limit:
        if test.args['bit_pattern'] == 'F0':
          self._delta_f1_avg_results[test.name] = results['delta_f1_avg']
        elif test.args['bit_pattern'] == 'AA':
          self._delta_f2_avg_results[test.name] = results['delta_f2_avg']

        if (test.name in self._delta_f1_avg_results and
            test.name in self._delta_f2_avg_results):
          # Both results are measured, calculate the delta_f2_f1_avg_ratio.
          results['delta_f2_f1_avg_ratio'] = (
              self._delta_f2_avg_results[test.name] /
              self._delta_f1_avg_results[test.name])
        else:
          # Not both results are measured, we don't check the it at this time.
          test.result_limit.pop('delta_f2_f1_avg_ratio')

      return (test.CheckTestPasses(results), results)

    def _TxGetResult(self, component_name, rf_type, test_type, center_freq,
                     power_level, packet_type, bit_pattern, result_limit,
                     **kwargs):
      raise NotImplementedError

    def _RxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, packet_type, bit_pattern,
                  rx_num_packets=None, rx_num_bits=None, **kwargs):
      raise NotImplementedError

    def _RxGenerate(self, component_name, rf_type, test_type, center_freq,
                    power_level, packet_type, bit_pattern,
                    rx_num_packets=None, rx_num_bits=None, **kwargs):
      raise NotImplementedError

  class ZigbeeControllerBase(ControllerBase):
    def _TxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, **kwargs):
      raise NotImplementedError

    def _TxMeasure(self, component_name, rf_type, test_type, center_freq,
                   power_level, result_limit, **kwargs):
      raise NotImplementedError

    def _TxGetResult(self, component_name, rf_type, test_type, center_freq,
                     power_level, result_limit, **kwargs):
      raise NotImplementedError

    def _RxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, rx_num_packets, **kwargs):
      raise NotImplementedError

    def _RxGenerate(self, component_name, rf_type, test_type, center_freq,
                    power_level, rx_num_packets, **kwargs):
      raise NotImplementedError

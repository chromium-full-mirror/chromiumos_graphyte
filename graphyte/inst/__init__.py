#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The Virtual Instrument module.
This is the virtual instrument class which every instrument plugin should
implement.
"""

import logging

from .. import link


class InstBase(object):
  """The abstract instrument class that every instrument plugin should inherit
  it. It contains several RF controllers, and each controller corresponds one RF
  chip. We can control different RF chip by assigning the rf_type, and delegate
  to the assigned controller."""

  name = 'Virtual instrument Plugin'
  need_link = False

  def __init__(self, args):
    self.args = args
    if self.need_link:
      self.link = link.Create(args['link_options'])
    self.rf_type = None
    self.controllers = {}
    self.SetRFController()

    # Active component record the current (component_name, tx_or_rx)
    # for port mapping and pathloss.
    self.port_config_table = None
    self.active_component = (None, None)

  def __getattr__(self, name):
    """Delegate to the active controller, that is recorded at rf_type."""
    try:
      return getattr(self.controllers[self.rf_type], name)
    except:
      logging.exception('Failed in InstBase __getattr__')
      raise NotImplementedError

  def SetRF(self, rf_type):
    self.rf_type = rf_type

  def Info(self):
    """
    Right now not much useful. It may be used to print information about
    the plugin itself.
    """
    logging.info(self.name)

  def SetRFController(self):
    """Set the controller for supported RF type.

    Every child class should implement this method."""
    self.controllers = {
        'WLAN': self.WlanControllerBase(self),
        'BLUETOOTH': self.BluetoothControllerBase(self),
        '802_15_4': self.ZigbeeControllerBase(self)}

  def Initialize(self):
    raise NotImplementedError

  def Terminate(self):
    raise NotImplementedError

  def SelfCalibrate(self, calibration_type='full'):
    raise NotImplementedError

  def AutoLevel(self, ports):
    raise NotImplementedError

  def InitPortConfig(self, port_config_table):
    self.port_config_table = port_config_table

  def SetPortConfig(self, test):
    component_name = test.args['component_name']
    tx_or_rx = test.tx_or_rx

    if self.active_component == (component_name, tx_or_rx):
      logging.debug('The port config is the same, ignored')
      return
    logging.info('Set the port config for component: %s %s',
                 component_name, tx_or_rx)
    self.active_component = (component_name, tx_or_rx)
    active_port_config = self.port_config_table.QueryPortConfig(
        component_name, tx_or_rx)
    port_mapping = [config['port_mapping'] for config in active_port_config]
    pathloss = [config['pathloss'] for config in active_port_config]
    logging.debug('Port mapping: %s', port_mapping)
    logging.debug('Path loss: %s', pathloss)
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
      return (test.IsTestPass(results), results)

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
    def _TxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, packet_type, bit_pattern, **kwargs):
      raise NotImplementedError

    def _TxMeasure(self, component_name, rf_type, test_type, center_freq,
                   power_level, packet_type, bit_pattern, result_limit,
                   **kwargs):
      raise NotImplementedError

    def _TxGetResult(self, component_name, rf_type, test_type, center_freq,
                     power_level, packet_type, bit_pattern, result_limit,
                     **kwargs):
      raise NotImplementedError

    def _RxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, packet_type, bit_pattern, **kwargs):
      raise NotImplementedError

    def _RxGenerate(self, component_name, rf_type, test_type, center_freq,
                    power_level, packet_type, bit_pattern, **kwargs):
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

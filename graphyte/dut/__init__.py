#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The DUT base class.
This is the virtual DUT class which every DUT plugin should implement.
"""

from .. import link
from ..default_setting import logger

class DUTBase(object):
  """The abstract DUT class that every DUT plugin should inherit it.
  It contains several RF controllers, and each controller corresponds one RF
  chip. We can control different RF chip by assigning the rf_type, and delegate
  to the assigned controller."""

  name = 'Virtual DUT Plugin'
  need_link = False

  def __init__(self, **kwargs):
    """Abstract init method. The init method of each child class should be:

    def __init__(self, arg1, **kwargs):
      # Call parent's __init__
      super(DUT, self).__init__(**kwargs)
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

  def __getattr__(self, name):
    """Delegate to the active controller, that is recorded at rf_type."""
    try:
      return getattr(self.controllers[self.rf_type], name)
    except:
      logger.exception('Failed in DUTBase __getattr__')
      raise NotImplementedError

  def Initialize(self):
    """Initialize the DUT device."""
    raise NotImplementedError

  def Terminate(self):
    """Terminate the DUT device."""
    raise NotImplementedError

  def SetRF(self, rf_type):
    if self.rf_type is not None:
      self.controllers[self.rf_type].Terminate()
    self.rf_type = rf_type
    self.controllers[self.rf_type].Initialize()

  class ControllerBase(object):
    """The abstract DUT controller class that every controller in DUT plugin
    should inherit it. We use wrapped function for each API, that give us
    flexibility to do some pre-processing or post-processing."""

    def __init__(self, dut=None):
      self.dut = dut

    def Initialize(self):
      """Initialize the controller."""
      return self._Initialize()

    def _Initialize(self):
      raise NotImplementedError

    def Terminate(self):
      """Disconnect/unconfigure the interface that was being used."""
      return self._Terminate()

    def _Terminate(self):
      raise NotImplementedError

    def TxConfig(self, test):
      """The test case details are passed in the test_params dictionary.
      However, we can decide to have other parameters in case someone
      wants to override (Not sure if we will keep these parameters going ahead).

      If the test_params is NULL/False, then the rest of the parameters
      can be used
      """
      return self._TxConfig(**test.ToDict())

    def _TxConfig(self, **kwargs):
      raise NotImplementedError

    def TxStart(self, test):
      """Start the TX on the interface.

      NOTE: Its up to the plugin to block until its ready to transmit.
      The graphyte is not going to wait until the DUT is ready to transfer.
      It assumes that the interface is ready when this call returns.
      """
      return self._TxStart(**test.ToDict())

    def _TxStart(self, **kwargs):
      raise NotImplementedError

    def TxStop(self, test):
      """Stop the TX."""
      return self._TxStop(**test.ToDict())

    def _TxStop(self, **kwargs):
      raise NotImplementedError

    def RxConfig(self, test):
      return self._RxConfig(**test.ToDict())

    def _RxConfig(self, **kwargs):
      raise NotImplementedError

    def RxClearResult(self, test):
      return self._RxClearResult(**test.ToDict())

    def _RxClearResult(self, **kwargs):
      raise NotImplementedError

    def RxGetResult(self, test):
      results = self._RxGetResult(**test.ToDict())
      return (test.CheckTestPasses(results), results)

    def _RxGetResult(self, result_limit, **kwargs):
      raise NotImplementedError

  class WlanControllerBase(ControllerBase):
    def _TxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, standard, bandwidth, data_rate, chain_mask, nss,
                  long_preamble, **kwargs):
      raise NotImplementedError

    def _TxStart(self, component_name, rf_type, test_type, center_freq,
                 power_level, standard, bandwidth, data_rate, chain_mask, nss,
                 long_preamble, **kwargs):
      raise NotImplementedError

    def _RxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, standard, bandwidth, data_rate, chain_mask, nss,
                  long_preamble, rx_num_packets, **kwargs):
      raise NotImplementedError

    def _RxClearResult(self, component_name, rf_type, test_type, center_freq,
                       power_level, standard, bandwidth, data_rate, chain_mask,
                       nss, long_preamble, rx_num_packets, **kwargs):
      raise NotImplementedError

    def _RxGetResult(self, component_name, rf_type, test_type, center_freq,
                     power_level, standard, bandwidth, data_rate, chain_mask,
                     nss, long_preamble, rx_num_packets, **kwargs):
      raise NotImplementedError

  class BluetoothControllerBase(ControllerBase):
    def _TxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, packet_type, bit_pattern, **kwargs):
      raise NotImplementedError

    def _TxStart(self, component_name, rf_type, test_type, center_freq,
                 power_level, packet_type, bit_pattern, **kwargs):
      raise NotImplementedError

    def _RxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, packet_type, bit_pattern,
                  rx_num_packets=None, rx_num_bits=None, **kwargs):
      raise NotImplementedError

    def _RxClearResult(self, component_name, rf_type, test_type, center_freq,
                       power_level, packet_type, bit_pattern,
                       rx_num_packets=None, rx_num_bits=None, **kwargs):
      raise NotImplementedError

    def _RxGetResult(self, component_name, rf_type, test_type, center_freq,
                     power_level, packet_type, bit_pattern,
                     rx_num_packets=None, rx_num_bits=None, **kwargs):
      raise NotImplementedError

  class ZigbeeControllerBase(ControllerBase):
    def _TxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, **kwargs):
      raise NotImplementedError

    def _TxStart(self, component_name, rf_type, test_type, center_freq,
                 power_level, **kwargs):
      raise NotImplementedError

    def _RxConfig(self, component_name, rf_type, test_type, center_freq,
                  power_level, rx_num_packets, **kwargs):
      raise NotImplementedError

    def _RxClearResult(self, component_name, rf_type, test_type, center_freq,
                       power_level, rx_num_packets, **kwargs):
      raise NotImplementedError

    def _RxGetResult(self, component_name, center_freq,
                     power_level, rx_num_packets, **kwargs):
      raise NotImplementedError

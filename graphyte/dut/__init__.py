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
from .. import device

class DUTBase(object):
  """The abstract DUT class that every DUT plugin should inherit it.

  It contains several RF controllers, and each controller corresponds one RF
  chip. We can control different RF chip by assigning the rf_type, and delegate
  to the assigned controller.
  """

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
    """Delegates to the active controller, that is recorded at rf_type."""
    try:
      return getattr(self.controllers[self.rf_type], name)
    except:
      logger.exception('Failed in DUTBase __getattr__')
      raise NotImplementedError

  def Initialize(self):
    """Initializes the DUT device."""
    raise NotImplementedError

  def Terminate(self):
    """Terminates the DUT device."""
    raise NotImplementedError

  def SetRF(self, rf_type):
    if self.rf_type is not None:
      self.controllers[self.rf_type].Terminate()
    self.rf_type = rf_type
    self.controllers[self.rf_type].Initialize()

  class ControllerBase(device.ControllerBase):
    """The abstract DUT RF controller class.

    Every controller in DUT plugin should inherit it. We use wrapped function
    for each API, that give us flexibility to do pre-processing or
    post-processing.
    """

    def __init__(self, dut=None):
      self.dut = dut

    def Initialize(self):
      return self._Initialize()

    def _Initialize(self):
      """Initializes the controller."""
      raise NotImplementedError

    def Terminate(self):
      return self._Terminate()

    def _Terminate(self):
      """Disconnects/unconfigures the interface that was being used."""
      raise NotImplementedError

    def TxConfig(self, test):
      test_case = self._CheckTestArgument(test.ToDict(), 'TX')
      return self._TxConfig(**test_case)

    def _TxConfig(self, **kwargs):
      """Configures the DUT for the test case.

      Configures the transmission settings to the DUT without arming trigger.
      """
      # TODO(akahuang): Decide whether this function should be removed.
      pass

    def TxStart(self, test):
      test_case = self._CheckTestArgument(test.ToDict(), 'TX')
      return self._TxStart(**test_case)

    def _TxStart(self, **kwargs):
      """Starts the TX on the interface.

      NOTE: It is up to the plugin to block until its ready to transmit.
      The graphyte is not going to wait until the DUT is ready to transfer.
      It assumes that the interface is ready when this call returns.
      """
      raise NotImplementedError

    def TxStop(self, test):
      test_case = self._CheckTestArgument(test.ToDict(), 'TX')
      return self._TxStop(**test_case)

    def _TxStop(self, **kwargs):
      """Stops the TX."""
      raise NotImplementedError

    def RxConfig(self, test):
      test_case = self._CheckTestArgument(test.ToDict(), 'RX')
      return self._RxConfig(**test_case)

    def _RxConfig(self, **kwargs):
      """Configures the DUT for the receiving test case."""
      # TODO(akahuang): Decide whether this function should be removed.
      pass

    def RxClearResult(self, test):
      test_case = self._CheckTestArgument(test.ToDict(), 'RX')
      return self._RxClearResult(**test_case)

    def _RxClearResult(self, **kwargs):
      """Measures the signal transmitted by the instrument.

      The method would be called before the instrument starts transmitting
      signal.
      """
      raise NotImplementedError

    def RxGetResult(self, test):
      test_case = self._CheckTestArgument(test.ToDict(), 'RX')
      results = self._RxGetResult(**test_case)
      return (test.CheckTestPasses(results), results)

    def _RxGetResult(self, result_limit, **kwargs):
      """Returns the test result of the test case.

      Retrieves the outcome of each required result. The keys of the returned
      value should be contain all the keys of the result_limit. The method would
      be called after the instrument finish transmitting signal.
      """
      raise NotImplementedError

  class WlanControllerBase(ControllerBase):
    RF_TYPE = 'WLAN'

    def _TxConfig(self, component_name, center_freq,
                  power_level, standard, bandwidth, data_rate, chain_mask, nss,
                  long_preamble, **kwargs):
      pass

    def _TxStart(self, component_name, center_freq,
                 power_level, standard, bandwidth, data_rate, chain_mask, nss,
                 long_preamble, **kwargs):
      raise NotImplementedError

    def _RxConfig(self, component_name, center_freq,
                  power_level, standard, bandwidth, data_rate, chain_mask, nss,
                  long_preamble, rx_num_packets, **kwargs):
      pass

    def _RxClearResult(self, component_name, center_freq,
                       power_level, standard, bandwidth, data_rate, chain_mask,
                       nss, long_preamble, rx_num_packets, **kwargs):
      raise NotImplementedError

    def _RxGetResult(self, component_name, rf_type, test_type, center_freq,
                     power_level, standard, bandwidth, data_rate, chain_mask,
                     nss, long_preamble, rx_num_packets, **kwargs):
      raise NotImplementedError

  class BluetoothControllerBase(ControllerBase):
    RF_TYPE = 'BLUETOOTH'

    def _TxConfig(self, component_name, center_freq,
                  power_level, packet_type, bit_pattern, **kwargs):
      pass

    def _TxStart(self, component_name, center_freq,
                 power_level, packet_type, bit_pattern, **kwargs):
      raise NotImplementedError

    def _RxConfig(self, component_name, center_freq,
                  power_level, packet_type, bit_pattern,
                  rx_num_packets=None, rx_num_bits=None, **kwargs):
      pass

    def _RxClearResult(self, component_name, center_freq,
                       power_level, packet_type, bit_pattern,
                       rx_num_packets=None, rx_num_bits=None, **kwargs):
      raise NotImplementedError

    def _RxGetResult(self, component_name, center_freq,
                     power_level, packet_type, bit_pattern,
                     rx_num_packets=None, rx_num_bits=None, **kwargs):
      raise NotImplementedError

  class ZigbeeControllerBase(ControllerBase):
    RF_TYPE = '802_15_4'

    def _TxConfig(self, component_name, center_freq,
                  power_level, **kwargs):
      pass

    def _TxStart(self, component_name, center_freq,
                 power_level, **kwargs):
      raise NotImplementedError

    def _RxConfig(self, component_name, center_freq,
                  power_level, rx_num_packets, **kwargs):
      pass

    def _RxClearResult(self, component_name, center_freq,
                       power_level, rx_num_packets, **kwargs):
      raise NotImplementedError

    def _RxGetResult(self, component_name, center_freq,
                     power_level, rx_num_packets, **kwargs):
      raise NotImplementedError

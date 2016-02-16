#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The DUT base class.
This is the virtual DUT class which every DUT plugin should implement.
"""

import logging

from .. import link

class DUTBase(object):
  """The abstract DUT class that every DUT plugin should inherit it.
  It contains several RF controllers, and each controller corresponds one RF
  chip. We can control different RF chip by assigning the rf_type, and delegate
  to the assigned controller."""

  name = 'Virtual DUT Plugin'
  need_link = False

  def __init__(self, args):
    self.args = args
    self.rf_type = None
    if self.need_link:
      self.link = link.Create(args['link_options'])
    self.controllers = {}
    self.SetRFController()

  def __getattr__(self, name):
    """Delegate to the active controller, that is recorded at rf_type."""
    try:
      return getattr(self.controllers[self.rf_type], name)
    except:
      logging.exception('Failed in DUTBase __getattr__')
      raise NotImplementedError

  def SetRF(self, rf_type):
    self.rf_type = rf_type

  def SetRFController(self):
    """Set the controller for supported RF type.

    Create the controllers for each supported RF type, and place them into
    self.controllers.

    For example:
      def SetRFController(self):
        self.controllers = {
            'WLAN': self.WlanControllerBase(self),
            'BLUETOOTH': self.BluetoothControllerBase(self),
            '802_15_4': self.ZigbeeControllerBase(self)}
    """
    raise NotImplementedError

  # TODO(akahuang): confirm the API of each function
  class ControllerBase(object):
    """The abstract DUT controller class that every controller in DUT plugin
    shoule inherit it. We use wrapped function for each API, that give us
    flexibility to do some pre-processing or post-processing."""

    def __init__(self, dut=None):
      self.dut = dut

    def Initialize(self, test):
      """Initialize the given interface."""
      return self._Initialize(**test.ToDict())

    def _Initialize(self, component_name, **kwargs):
      raise NotImplementedError

    def Terminate(self):
      """Disconnect/unconfigure the interface that was being used."""
      return self._Terminate()

    def _Terminate(self, **kwargs):
      raise NotImplementedError

    def TxSetMode(self, test):
      """The test case details are passed in the test_params dictionary.
      However, we can decide to have other parameters in case someone
      wants to override (Not sure if we will keep these parameters going ahead).

      If the test_params is NULL/False, then the rest of the parameters
      can be used
      """
      return self._TxSetMode(**test.ToDict())

    def _TxSetMode(self, **kwargs):
      raise NotImplementedError

    def TxSetPower(self, test):
      """Set the power of the interface to power, if its not zero.
      If power=0, then use it from the params passed in the test_params.
      """
      return self._TxSetPower(**test.ToDict())

    def _TxSetPower(self, power_level=0, **kwargs):
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

    def RxSetMode(self, test):
      return self._RxSetMode(**test.ToDict())

    def _RxSetMode(self, **kwargs):
      raise NotImplementedError

    def RxClearResult(self, test):
      return self._RxClearResult(**test.ToDict())

    def _RxClearResult(self, **kwargs):
      raise NotImplementedError

    def RxGetResult(self, test):
      results = self._RxGetResult(**test.ToDict())
      return (test.IsTestPass(results), results)

    def _RxGetResult(self, result_limit, **kwargs):
      raise NotImplementedError

  class WlanControllerBase(ControllerBase):
    def _TxSetMode(self, channel=0, signal_type=None, chain_mask=0, payload=0,
                   **kwargs):
      raise NotImplementedError

    def _RxSetMode(self, channel=0, signal_type=None, chain_mask=0, payload=0,
                   **kwargs):
      raise NotImplementedError

  class BluetoothControllerBase(ControllerBase):
    def _TxSetMode(self, channel=0, packet_type=None, payload=0,
                   payload_type=None, **kwargs):
      raise NotImplementedError

    def _RxSetMode(self, channel=0, packet_type=None, **kwargs):
      raise NotImplementedError

  class ZigbeeControllerBase(ControllerBase):
    def _TxSetMode(self, channel=0, packet_type=None, payload=0, **kwargs):
      raise NotImplementedError

    def _RxSetMode(self, channel=0, packet_type=None, **kwargs):
      raise NotImplementedError


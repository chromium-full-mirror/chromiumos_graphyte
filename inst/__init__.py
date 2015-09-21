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


# TODO(akahuang): confirm the API of each function
class InstBase(object):
  """The abstract instrument class that every instrument plugin should inherit
  it. It contains several RF controllers, and each controller corresponds one RF
  chip. We can control different RF chip by assigning the rf_type, and delegate
  to the assigned controller."""

  def __init__(self, args):
    self.name = 'Virtual instrument Plugin'
    self.args = args
    self.controllers = {
        'WLAN': self.WlanControllerBase(self),
        'BLUETOOTH': self.BluetoothControllerBase(self),
        'ZIGBEE': self.ZigbeeControllerBase(self)}
    self.rf_type = None

  def __getattr__(self, name):
    """Delegate to the active controller, that is recorded at rf_type."""
    try:
      return getattr(self.controllers[self.rf_type], name)
    except:
      logging.exception('Failed in InstBase __getattr__')
      raise NotImplementedError

  def SetRf(self, rf_type):
    self.rf_type = rf_type

  def Info(self):
    """
    Right now not much useful. It may be used to print information about
    the plugin itself.
    """
    logging.info(self.name)

  def Initialize(self):
    raise NotImplementedError

  def Terminate(self):
    raise NotImplementedError

  def SelfCalibrate(self, calibration_type='full'):
    raise NotImplementedError

  def AutoLevel(self, ports):
    raise NotImplementedError

  def InitPathloss(self, loss_table):
    raise NotImplementedError

  def SetPassloss(self, port, table_indice):
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
      return test.IsTestPass(results)

    def _TxGetResult(self, result_limit, **kwargs):
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

  # pylint: disable=W0223
  class WlanControllerBase(ControllerBase):
    pass

  # pylint: disable=W0223
  class BluetoothControllerBase(ControllerBase):
    pass

  # pylint: disable=W0223
  class ZigbeeControllerBase(ControllerBase):
    pass

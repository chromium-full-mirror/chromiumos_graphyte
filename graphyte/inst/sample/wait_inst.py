#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The mock instrument class. """

import time

import graphyte_common  # pylint: disable=unused-import
from graphyte.inst import InstBase
from graphyte.default_setting import logger
from graphyte.default_setting import GRAPHYTE_IN
from graphyte.default_setting import GRAPHYTE_OUT


class WaitController(InstBase.ControllerBase):
  def _TxMeasure(self, **kwargs):
    logger.info('TxMeasure')
    self.inst.wait_func()

  def _TxGetResult(self, **kwargs):
    return {}

  def _RxGenerate(self, **kwargs):
    pass

  def _RxStop(self, **kwargs):
    pass


class Inst(InstBase):
  name = 'Wait Mock Instrument'
  VALID_PORT_NAMES = ['dummy_port']

  def __init__(self, wait_func='keypress', wait_secs=10, **kwargs):
    """Determine the wait method.

    Args:
      wait_func: 'keypress' to wait until pressing enter.
                 'period' to wait a fixed time period.
      wait_secs: The stop period for each item. It is only valid when wait_func
                 is 'period'.
    """
    super(Inst, self).__init__(**kwargs)
    if wait_func == 'keypress':
      self.wait_func = self._WaitKeypress
    elif wait_func == 'period':
      self.wait_func = self._WaitPeriod
      self.wait_secs = wait_secs
    self.controllers = {
        'WLAN': WaitController(self),
        'BLUETOOTH': WaitController(self),
        '802_15_4': WaitController(self)}

  def _WaitKeypress(self):
    GRAPHYTE_OUT.write('Press Enter to continue...\n')
    GRAPHYTE_IN.readline()

  def _WaitPeriod(self):
    logger.info('Wait %s seconds', self.wait_secs)
    time.sleep(self.wait_secs)

  def _SetPortConfig(self, port_mapping, pathloss):
    pass

  def LockInstrument(self):
    pass

  def UnlockInstrument(self):
    pass

  def GetVersion(self):
    return self.name

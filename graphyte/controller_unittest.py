#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import

import sys
import unittest

if sys.version_info.major < 3:
  import mock
else:
  import unittest.mock as mock

import graphyte_common  # pylint: disable=unused-import
from graphyte import controller
from graphyte import testplan


class ControllerTest(unittest.TestCase):
  def setUp(self):
    self.controller_obj = controller.Controller()

    # Mock DUT and Inst plugin.
    self.mock = mock.Mock()
    self.mock.dut = mock.MagicMock()
    self.mock.inst = mock.MagicMock()
    self.controller_obj.dut = self.mock.dut
    self.controller_obj.inst = self.mock.inst
    self.mock.dut.active_controller.RxGetResult = mock.MagicMock(
        return_value=(True, {'fake_rx_result': 'VALUE'}))
    self.mock.inst.active_controller.TxGetResult = mock.MagicMock(
        return_value=(True, {'fake_tx_result': 'VALUE'}))

    # Make fake port config and test plan.
    self.fake_wlan_tx_test = testplan.TestCase(
        'WLAN TX',
        {'rf_type': 'WLAN', 'test_type': 'TX'},
        {})
    self.fake_wlan_rx_test = testplan.TestCase(
        'WLAN RX',
        {'rf_type': 'WLAN', 'test_type': 'RX'},
        {})
    self.fake_bt_tx_test = testplan.TestCase(
        'BLUETOOTH TX',
        {'rf_type': 'BLUETOOTH', 'test_type': 'TX'},
        {})
    self.fake_bt_rx_test = testplan.TestCase(
        'BLUETOOTH RX',
        {'rf_type': 'BLUETOOTH', 'test_type': 'RX'},
        {})
    self.controller_obj.testplan = [
        self.fake_wlan_tx_test,
        self.fake_wlan_rx_test,
        self.fake_bt_tx_test,
        self.fake_bt_rx_test]
    self.controller_obj.port_config = 'FAKE_PORT_CONFIG'

  def testE2E(self):
    self.controller_obj.Run()

    self.mock.assert_has_calls([
        # Initialization.
        mock.call.inst.Initialize(),
        mock.call.inst.LockInstrument(),
        mock.call.inst.InitPortConfig(self.controller_obj.port_config),
        mock.call.dut.Initialize(),

        # Run WLAN Tx Test case.
        mock.call.dut.SetRF('WLAN'),
        mock.call.inst.SetRF('WLAN'),
        mock.call.inst.SetPortConfig(self.fake_wlan_tx_test),
        mock.call.dut.active_controller.TxStart(self.fake_wlan_tx_test),
        mock.call.inst.active_controller.TxMeasure(self.fake_wlan_tx_test),
        mock.call.inst.active_controller.TxGetResult(self.fake_wlan_tx_test),
        mock.call.dut.active_controller.TxStop(self.fake_wlan_tx_test),

        # Run WLAN Rx Test case.
        mock.call.dut.SetRF('WLAN'),
        mock.call.inst.SetRF('WLAN'),
        mock.call.inst.SetPortConfig(self.fake_wlan_rx_test),
        mock.call.dut.active_controller.RxClearResult(self.fake_wlan_rx_test),
        mock.call.inst.active_controller.RxGenerate(self.fake_wlan_rx_test),
        mock.call.dut.active_controller.RxGetResult(self.fake_wlan_rx_test),
        mock.call.inst.active_controller.RxStop(self.fake_wlan_rx_test),

        # Run Bluetooth Tx Test case.
        mock.call.dut.SetRF('BLUETOOTH'),
        mock.call.inst.SetRF('BLUETOOTH'),
        mock.call.inst.SetPortConfig(self.fake_bt_tx_test),
        mock.call.dut.active_controller.TxStart(self.fake_bt_tx_test),
        mock.call.inst.active_controller.TxMeasure(self.fake_bt_tx_test),
        mock.call.inst.active_controller.TxGetResult(self.fake_bt_tx_test),
        mock.call.dut.active_controller.TxStop(self.fake_bt_tx_test),

        # Run Bluetooth Rx Test case.
        mock.call.dut.SetRF('BLUETOOTH'),
        mock.call.inst.SetRF('BLUETOOTH'),
        mock.call.inst.SetPortConfig(self.fake_bt_rx_test),
        mock.call.dut.active_controller.RxClearResult(self.fake_bt_rx_test),
        mock.call.inst.active_controller.RxGenerate(self.fake_bt_rx_test),
        mock.call.dut.active_controller.RxGetResult(self.fake_bt_rx_test),
        mock.call.inst.active_controller.RxStop(self.fake_bt_rx_test),

        # Termination.
        mock.call.inst.UnlockInstrument(),
        mock.call.inst.Terminate(),
        mock.call.dut.Terminate()])

if __name__ == '__main__':
  unittest.main()

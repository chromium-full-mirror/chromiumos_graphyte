#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function

import mock
import unittest

import graphyte_common  # pylint: disable=unused-import
from graphyte import bootstrap
from graphyte import controller
from graphyte import plugin_shell
from graphyte import testplan


class PluginShellTest(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    print("=== Plugin shell testing starts ===")
    print("NOTE: It's normal if some texts is printed out.")
    print('')

  @classmethod
  def tearDownClass(cls):
    print('')
    print("=== Plugin shell testing finished ===")

  def setUp(self):
    self.controller_obj = controller.Controller()
    self.plugin_shell = plugin_shell.PluginShell(self.controller_obj)

    # Mock DUT and Inst plugin.
    self.mock = mock.Mock()
    self.mock.dut = mock.MagicMock()
    self.mock.inst = mock.MagicMock()
    self.controller_obj.dut = self.mock.dut
    self.controller_obj.inst = self.mock.inst
    self.mock.dut.active_controller.RxGetResult = mock.MagicMock(
        return_value=(True, {'fake_rx_result': 'VALUE'}))
    self.mock.inst.active_controller.TxGetResult = mock.MagicMock(
        return_value=(True, {'fake_rx_result': 'VALUE'}))

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

  def testInitialize(self):
    # Initialize DUT.
    self.controller_obj.dut.reset_mock()
    self.plugin_shell.do_dut(None)
    self.plugin_shell.do_initialize(None)
    self.controller_obj.dut.Initialize.assert_called_once_with()
    self.assertEquals(plugin_shell.DEVICE_STATUS.IDLE,
                      self.plugin_shell.device_status['DUT'])

    # Initialize DUT again. We should ignore this case.
    self.controller_obj.dut.reset_mock()
    self.plugin_shell.do_initialize(None)
    self.assertFalse(self.controller_obj.dut.called)

    # Initialize instrument.
    self.controller_obj.inst.reset_mock()
    self.plugin_shell.do_inst(None)
    self.plugin_shell.do_initialize(None)
    self.controller_obj.inst.assert_has_calls([
        mock.call.Initialize(),
        mock.call.LockInstrument(),
        mock.call.InitPortConfig(self.controller_obj.port_config)])

  def testTerminate(self):
    # Terminate DUT when DUT is not initialized yet. Nothing happens.
    self.plugin_shell.do_dut(None)
    self.controller_obj.dut.reset_mock()
    self.plugin_shell.do_terminate(None)
    self.assertFalse(self.controller_obj.dut.called)

    # Terminate DUT after DUT is initialized.
    self.plugin_shell.do_initialize(None)
    self.controller_obj.dut.reset_mock()
    self.plugin_shell.do_terminate(None)
    self.controller_obj.dut.Terminate.assert_called_once_with()
    self.assertEquals(plugin_shell.DEVICE_STATUS.STOP,
                      self.plugin_shell.device_status['DUT'])

  def testDutTx(self):
    self.plugin_shell.test_case = self.fake_wlan_tx_test.Copy()
    self.plugin_shell.do_dut(None)
    self.plugin_shell.do_initialize(None)

    self.plugin_shell.do_start(None)
    self.controller_obj.dut.SetRF.assert_called_once()
    self.controller_obj.dut.active_controller.TxStart.assert_called_once()

    self.plugin_shell.do_stop(None)
    self.controller_obj.dut.active_controller.TxStop.assert_called_once()

  def testDutRx(self):
    self.plugin_shell.test_case = self.fake_wlan_rx_test.Copy()
    self.plugin_shell.do_dut(None)
    self.plugin_shell.do_initialize(None)

    self.plugin_shell.do_start(None)
    self.controller_obj.dut.SetRF.assert_called_once()
    self.controller_obj.dut.active_controller.RxClearResult.assert_called_once()

    self.plugin_shell.do_stop(None)
    self.controller_obj.dut.active_controller.RxGetResult.assert_called_once()

  def testInstTx(self):
    self.plugin_shell.test_case = self.fake_wlan_tx_test.Copy()
    self.plugin_shell.do_inst(None)
    self.plugin_shell.do_initialize(None)

    self.plugin_shell.do_start(None)
    self.controller_obj.inst.SetRF.assert_called_once()
    self.controller_obj.inst.active_controller.TxMeasure.assert_called_once()

    self.plugin_shell.do_stop(None)
    self.controller_obj.inst.active_controller.TxGetResult.assert_called_once()

  def testInstRx(self):
    self.plugin_shell.test_case = self.fake_wlan_rx_test.Copy()
    self.plugin_shell.do_inst(None)
    self.plugin_shell.do_initialize(None)

    self.plugin_shell.do_start(None)
    self.controller_obj.inst.SetRF.assert_called_once()
    self.controller_obj.inst.active_controller.RxGenerate.assert_called_once()

    self.plugin_shell.do_stop(None)
    self.controller_obj.inst.active_controller.RxStop.assert_called_once()

if __name__ == '__main__':
  bootstrap.Bootstrap.InitLogger(
      verbose=True,
      console_output=True)
  unittest.main()

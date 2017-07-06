#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function

import mock
import unittest

from . import graphyte
from . import plugin_shell
from . import testplan


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
    self.graphyte_obj = graphyte.Graphyte()
    self.plugin_shell = plugin_shell.PluginShell(self.graphyte_obj)

    # Mock DUT and Inst plugin.
    self.mock = mock.Mock()
    self.mock.dut = mock.MagicMock()
    self.mock.inst = mock.MagicMock()
    self.graphyte_obj.dut = self.mock.dut
    self.graphyte_obj.inst = self.mock.inst
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
    self.graphyte_obj.testplan = [
        self.fake_wlan_tx_test,
        self.fake_wlan_rx_test,
        self.fake_bt_tx_test,
        self.fake_bt_rx_test]
    self.graphyte_obj.port_config = 'FAKE_PORT_CONFIG'

  def testInitialize(self):
    # Initialize DUT.
    self.graphyte_obj.dut.reset_mock()
    self.plugin_shell.do_dut(None)
    self.plugin_shell.do_initialize(None)
    self.graphyte_obj.dut.Initialize.assert_called_once_with()
    self.assertEquals(plugin_shell.DEVICE_STATUS.IDLE,
                      self.plugin_shell.device_status['DUT'])

    # Initialize DUT again. We should ignore this case.
    self.graphyte_obj.dut.reset_mock()
    self.plugin_shell.do_initialize(None)
    self.assertFalse(self.graphyte_obj.dut.called)

    # Initialize instrument.
    self.graphyte_obj.inst.reset_mock()
    self.plugin_shell.do_inst(None)
    self.plugin_shell.do_initialize(None)
    self.graphyte_obj.inst.assert_has_calls([
        mock.call.Initialize(),
        mock.call.LockInstrument(),
        mock.call.InitPortConfig(self.graphyte_obj.port_config)])

  def testTerminate(self):
    # Terminate DUT when DUT is not initialized yet. Nothing happens.
    self.plugin_shell.do_dut(None)
    self.graphyte_obj.dut.reset_mock()
    self.plugin_shell.do_terminate(None)
    self.assertFalse(self.graphyte_obj.dut.called)

    # Terminate DUT after DUT is initialized.
    self.plugin_shell.do_initialize(None)
    self.graphyte_obj.dut.reset_mock()
    self.plugin_shell.do_terminate(None)
    self.graphyte_obj.dut.Terminate.assert_called_once_with()
    self.assertEquals(plugin_shell.DEVICE_STATUS.STOP,
                      self.plugin_shell.device_status['DUT'])

  def testDutTx(self):
    self.plugin_shell.do_set_test_type('WLAN TX')
    self.plugin_shell.do_dut(None)
    self.plugin_shell.do_initialize(None)

    self.plugin_shell.do_start(None)
    self.graphyte_obj.dut.SetRF.assert_called_once()
    self.graphyte_obj.dut.active_controller.TxStart.assert_called_once()

    self.plugin_shell.do_stop(None)
    self.graphyte_obj.dut.active_controller.TxStop.assert_called_once()

  def testDutRx(self):
    self.plugin_shell.do_set_test_type('WLAN RX')
    self.plugin_shell.do_dut(None)
    self.plugin_shell.do_initialize(None)

    self.plugin_shell.do_start(None)
    self.graphyte_obj.dut.SetRF.assert_called_once()
    self.graphyte_obj.dut.active_controller.RxClearResult.assert_called_once()

    self.plugin_shell.do_stop(None)
    self.graphyte_obj.dut.active_controller.RxGetResult.assert_called_once()

  def testInstTx(self):
    self.plugin_shell.do_set_test_type('WLAN TX')
    self.plugin_shell.do_inst(None)
    self.plugin_shell.do_initialize(None)

    self.plugin_shell.do_start(None)
    self.graphyte_obj.inst.SetRF.assert_called_once()
    self.graphyte_obj.inst.active_controller.TxMeasure.assert_called_once()

    self.plugin_shell.do_stop(None)
    self.graphyte_obj.inst.active_controller.TxGetResult.assert_called_once()

  def testInstRx(self):
    self.plugin_shell.do_set_test_type('WLAN RX')
    self.plugin_shell.do_inst(None)
    self.plugin_shell.do_initialize(None)

    self.plugin_shell.do_start(None)
    self.graphyte_obj.inst.SetRF.assert_called_once()
    self.graphyte_obj.inst.active_controller.RxGenerate.assert_called_once()

    self.plugin_shell.do_stop(None)
    self.graphyte_obj.inst.active_controller.RxStop.assert_called_once()

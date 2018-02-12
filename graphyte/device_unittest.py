#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import mock
import unittest

import graphyte_common  # pylint: disable=unused-import
from graphyte import device


class DeviceTest(unittest.TestCase):
  def setUp(self):
    self.device = device.DeviceBase()

    # Mock RF controller.
    self.mock = mock.Mock()
    self.mock.wlan_controller = mock.MagicMock()
    self.mock.bt_controller = mock.MagicMock()
    self.device.controllers = {
        'WLAN': self.mock.wlan_controller,
        'BLUETOOTH': self.mock.bt_controller}

  def testSetRF(self):
    # Set RF to WLAN. WLAN controller should be initialized.
    self.device.SetRF('WLAN')
    self.mock.wlan_controller.Initialize.assert_called_once_with()

    # Set RF to WLAN again. WLAN controller should do nothing.
    self.mock.wlan_controller.reset_mock()
    self.device.SetRF('WLAN')
    self.assertFalse(self.mock.wlan_controller.called)

    # Set RF to Bluetooth.
    self.mock.wlan_controller.reset_mock()
    self.mock.bt_controller.reset_mock()
    self.device.SetRF('BLUETOOTH')
    self.mock.wlan_controller.Terminate.assert_called_once_with()
    self.mock.bt_controller.Initialize.assert_called_once_with()

    # Set RF to None.
    self.mock.bt_controller.reset_mock()
    self.device.SetRF(None)
    self.mock.bt_controller.Terminate.assert_called_once_with()

if __name__ == '__main__':
  unittest.main()

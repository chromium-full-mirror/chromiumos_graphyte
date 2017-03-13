# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

class ControllerBase(object):
  """The abstract RF controller class.

  The class hierarchy of the RF controller is:
    device.ControllerBase
    - dut.ControllerBase
      - dut.WlanControllerBase
      - dut.BluetoothControllerBase
      - dut.ZigbeeControllerBase
    - inst.ControllerBase
      - inst.PowerMeterControllerBase
      - inst.WlanControllerBase
      - inst.BluetoothControllerBase
      - inst.ZigbeeControllerBase
  """

  # The RF type of the controller. Child class should override this.
  RF_TYPE = ''

  def _CheckTestArgument(self, test_case, required_test_type):
    """Checks the test case has correct test type and RF type.

    Args:
      test_case: a dict containing the test arguments.
      required_test_type: the required test type. 'TX' or 'RX'.

    Returns:
      the test case.
    """
    assert test_case['test_type'] == required_test_type
    assert self.RF_TYPE == 'ALL' or test_case['rf_type'] == self.RF_TYPE
    return test_case

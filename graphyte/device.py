# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from . import link
from .default_setting import logger


class DeviceType(object):
  """Used to select device in action."""
  DUT = 'DUT'
  INST = 'INST'
  ALL = 'ALL'

  @classmethod
  def IsDUT(cls, device):
    return device in [cls.DUT, cls.ALL]

  @classmethod
  def IsInst(cls, device):
    return device in [cls.INST, cls.ALL]


class DeviceBase(object):
  """The abstract device class.

  The class hierarchy of the device is:
    DeviceBase
    - dut.DUTBase
    - inst.InstBase
  """

  name = 'Plugin Name'
  need_link = False

  def __init__(self, **kwargs):
    """Abstract init method. The init method of each child class should be:

    def __init__(self, arg1, **kwargs):
      # Call parent's __init__
      super(ChildClassName, self).__init__(**kwargs)
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

  @property
  def active_controller(self):
    if self.rf_type not in self.controllers:
      raise KeyError('rf_type "%s" is not supported.' % self.rf_type)
    return self.controllers[self.rf_type]

  @active_controller.setter
  def active_controller(self, value):
    del value
    raise ValueError(
        'Update `rf_type` value instead of updating `active_controller`.')

  def Initialize(self):
    """Initializes the device."""
    logger.debug('device.Initialize')
    if self.need_link:
      self.link.Open()
      self.link.CheckReady()
    return self._Initialize()

  def _Initialize(self):
    pass

  def Terminate(self):
    """Terminates the device."""
    logger.debug('device.Terminate')
    if self.rf_type is not None:
      self.controllers[self.rf_type].Terminate()
      self.rf_type = None
    self._Terminate()
    if self.link is not None:
      self.link.Close()

  def _Terminate(self):
    pass

  def SetRF(self, rf_type):
    """Set the RF type."""
    if self.rf_type == rf_type:
      return
    if self.rf_type is not None:
      self.active_controller.Terminate()
    self.rf_type = rf_type
    if self.rf_type is not None:
      self.active_controller.Initialize()


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

  def Initialize(self):
    return self._Initialize()

  def _Initialize(self):
    """Initializes the controller."""
    pass

  def Terminate(self):
    return self._Terminate()

  def _Terminate(self):
    """Disconnects/unconfigures the interface that was being used."""
    pass

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

# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Implementation of GPIB interface wrapper.

This module depends on PyVISA and PyVISA-py python module, and the linux-gpib
backend driver.
"""

import time
import visa

import graphyte_common  # pylint: disable=unused-import
from graphyte import link
from graphyte.default_setting import logger


class GPIBLink(link.DeviceLink):
  """A DUT target that is connected via GPIB interface.

  link_options example:
    {
      'link_class': 'GPIBLink',
      'minor': 0,
      'primary': 0
    }
  """

  def __init__(self, minor=0, primary=0, timeout=3, query_delay=0.0):
    """Create the GPIB resource with pyvisa.

    Args:
      minor: specify which device file to be used. 0 correspondes to /dev/gpib0
      primary: the primary GPIB address. Valid address are 0 to 30.
      timeout: the timeout for each call, unit in seconds.
      query_delay: the delay between write and read command, unit in seconds.
    """
    if query_delay < 0:
      raise ValueError('query_delay should not be negative.')
    self.query_delay = query_delay
    self.minor = minor
    self.primary = primary
    self.timeout = timeout
    self.device = None

  def Open(self):
    try:
      resource_manager = visa.ResourceManager()  # Use NI backend
    except OSError:
      resource_manager = visa.ResourceManager('@py')  # Use Linux-GPIB
    except OSError:
      raise OSError('Cannot find the GPIB backend. For Windows platform '
                    'please install NI-488.2 driver. For Linux platform '
                    'please install linux-gpib and PyVisa-Py module.')
    try:
      name = u'GPIB%d::%d::INSTR' % (self.minor, self.primary)
      self.device = resource_manager.open_resource(name)
      # PyVisa will set the smallest valid timeout that BIGGER than
      # the value we set. For example, the valid timeouts are 1000, 3000, 10000.
      # When we set 1000~2999, PyVisa would set 3000. When we set 3000~9999,
      # PyVisa would set 10000. So we minus 0.1 to let PyVisa set the smallest
      # valid timeout that SAME OR BIGGER than the value we set.
      self.device.timeout = (self.timeout * 1000) - 0.1
    except Exception as ex:
      raise ValueError('GPIBLink Init failed. %s' % ex)

  def Close(self):
    if self.device is not None:
      self.device.close()
      self.device = None

  def Push(self, local, remote):
    raise NotImplementedError

  def Pull(self, remote, local=None):
    raise NotImplementedError

  def Shell(self, command, stdin=None, stdout=None, stderr=None):
    raise NotImplementedError

  def IsReady(self):
    try:
      info = self.CallOutput('*IDN?')
      return info != ''
    except ValueError:
      return False

  # pylint: disable=W0221
  def Call(self, command, stdin=None, stdout=None, stderr=None):
    """Send command with GPIB interface.

    Write the command to the device. If stdout is not None, then read the result
    back and store into stdout. Since it is not a real linux shell, other
    standard streams are not supported.

    Args:
      command: a string or a list, to be write to device.
    Returns: the return code.
    """
    if (stdin, stderr) != (None, None):
      raise NotImplementedError('Standard input and error are not supported.')

    if isinstance(command, list):
      command = ' '.join([str(arg) for arg in command])
    logger.debug('GPIB Write: %s', command)
    return_code = self.device.write(command)
    # The return value should be (byte size, Status code), but PyVisa-py only
    # returns the status code while successful.
    if not isinstance(return_code, int):
      return_code = int(return_code[1])

    if stdout is not None and return_code == 0:
      time.sleep(self.query_delay)
      output = self.device.read()
      stdout.write(output)
    return return_code

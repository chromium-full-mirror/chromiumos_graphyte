#!/usr/bin/python
#
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The vistual DUT class

This class defines the method that every DUT plugin has to implement.

Almost all the functions return a tuple. The first element is the return value
True/False. The rest of the elements can be different (Usually a dictionary)
"""


class Vdut(object):
  def __init__(self, app):
    """
    The constructor is passed the app object, which is the reference to graphyte
    module. This has to be stored by the dut plugin, which can be used to access
    the graphyte methods or the instrument (Useful for calibration)
    """
    self.name = "Virtual DUT Plugin"
    self.app = app
    print self.name

  def Info(self):
    """
    Right now not much useful. It may be used to print information about
    the plugin itself.
    """
    print self.name

  def WlanInitialize(self, component_name):
    """
    Initialize the given interface.
    """
    raise NotImplementedError

  def WlanDisconnect(self):
    """
    Disconnect/unconfigure the interface that was being used.
    """
    return (True,)

  def WlanTxSetMode(self, test_params=None, channel=0, signal_type=None,
                    chain_mask=0, payload=0, ifs=0):
    """
    The test case details are passed in the test_params dictionary.
    However, we can decide to have other parameters in case someone
    wants to override (Not sure if we will keep these parameters going ahead).

    If the test_params is NULL/False, then the rest of the parameters
    can be used
    """
    raise NotImplementedError

  def WlanTxSetPower(self, power=0):
    """
    Set the power of the interface to power, if its not zero.
    If power=0, then use it from the params passed in the test_params.
    """
    if power == 0:
      return (True,)

    return (True,)

  def WlanTxOn(self):
    """
    Start the TX on the interface.

    NOTE: Its up to the plugin to block until its ready to transmit.
    The graphyte is not going to wait until the DUT is ready to transfer.
    It assumes that the interface is ready when this call returns.
    """
    return (True,)

  def WlanTxOff(self):
    """
    Stop the TX
    """
    return (True,)

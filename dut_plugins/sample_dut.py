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

import vdut

class Dut(vdut.Vdut):
  def __init__(self, app):
    super(Dut, self).__init__(app)
    self.name = "Sample DUT Plugin"
    self.app = app
    print "Initializing " + self.name

  def Info(self):
    print "It's the " + self.name

  def WlanInitialize(self, component_name): # pylint: disable=W0613
    return (True,)

  def WlanDisconnect(self):
    return (True,)

  # pylint: disable=W0613
  def WlanTxSetMode(self, test_params=None, channel=0, signal_type=None,
                    chain_mask=0, payload=0, ifs=0):
    if test_params is None:
      #Interpret the other arguments, else use the dictionary
      pass

    return (True,)

  def WlanTxSetPower(self, power=0):
    if power == 0:
      return (True,)

    return (True,)

  def WlanTxOn(self):
    return (True,)

  def WlanTxOff(self):
    return (True,)

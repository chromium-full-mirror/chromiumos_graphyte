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

import vinst

class Dut(vinst.Vinst):
  def __init__(self, app):
    super(Dut, self).__init__(app)
    self.name = "Sample INST Plugin"
    self.app = app
    print "Initializing " + self.name

  def Info(self):
    print "It's the " + self.name

  def WlanInitialize(self):
    return (True,)

  def WlanDisconnect(self):
    return (True,)

  def WlanTxConfig(self, test_params=None, frequency=0, trigger_level=0,
                   ref_level=0, rf_ports=None, signal_type=None,
                   measurement=None):
    if test_params is None:
      #Interpret the other arguments, else use the dictionary
      pass

    return (True,)

  def WlanTxMeasure(self):
    return (True,)

  def WlanTxGetResults(self):
    results = {'TX Result':'Everything is fine'}
    return (True, results)

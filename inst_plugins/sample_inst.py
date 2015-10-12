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

class dut(vinst.vinst):
  def __init__(self, app):
    self.name = "Sample INST Plugin"
    self.app = app
    print "Initializing " + self.name

  def info(self):
    print "It's the " + self.name

  def wlan_initialize(self):
    return (True,)

  def wlan_disconnect(self):
    return (True,)

  def wlan_tx_config(self, test_params={}, frequency=0, trigger_level=0,
                ref_level=0, rf_ports={}, signal_type={}, measurement={}):
    if bool(test_params) == False:
      #Interpret the other arguments, else use the dictionary
      pass

    return (True,)

  def wlan_tx_measure(self):
    return (True,)

  def wlan_tx_get_results(self):
    results = {'TX Result':'Everything is fine'}
    return (True, results)

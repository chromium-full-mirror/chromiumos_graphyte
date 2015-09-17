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

"""The Virtual Instrument module.

This is the virtual instrument class which every instrument plugin should
implement.

Almost all the functions return a tuple. The first element is the return value
True/False. The rest of the elements can be different (Usually a dictionary)
"""

class Vinst(object):
  def __init__(self, app):
    """
    The constructor is passed the app object, which is the reference to graphyte
    module. This has to be stored by the inst plugin, which can be used to
    access the graphyte methods or the dut (Useful for calibration).
    This will also give the plugins the ability to talk to each other
    directly.
    """
    self.name = "Virtual Inst Plugin"
    self.app = app
    print self.name

  def Info(self):
    """
    Right now not much useful. It may be used to print information about
    the plugin itself.
    """
    print self.name

  def WlanInitialize(self):
    """
    Initialize the instrument.
    """
    return (True,)

  def WlanDisconnect(self):
    """"
    Disconnect from the instrument
    """
    return (True,)

  def WlanTxConfig(self, test_params=None, frequency=0, trigger_level=0,
                   ref_level=0, rf_ports=None, signal_type=None,
                   measurement=None):
    """
    The test case details are passed in the test_params dictionary.
    However, we can decide to have other parameters in case someone
    wants to override (Not sure if we will keep these parameters going ahead).

    If the test_params is NULL/False, then the rest of the parameters
    can be used
    """
    raise NotImplementedError

  def WlanTxMeasure(self):
    """
    The instrument should block in this call until its done with the
    measurement.  The graphyte assumes that when the call returns the
    measurement is done and is ready to be read. graphyte will not wait to make
    the next call once this function returns.
    """
    return (True,)

  def WlanTxGetResults(self):
    """
    Read results from the instruments
    """
    results = {}
    return (True, results)

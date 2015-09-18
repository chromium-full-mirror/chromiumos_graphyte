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

"""The Google RF Test Framework module.

This is the main application module from which the execution starts.
This will drive the other modules. This module can be directly launched.

This module can also be imported and an instance of graphyte created from there.

Typical Usage (Standalone)
  ./graphyte.py

Typicak Usage (Import to other modules):
  import graphyte
  app = graphyte.graphyte()

NOTE: Check the flow diagram.

"""


import imp
import ConfigParser
import testplan

# All functions return a tuple. The tuple has atleast one element at index 0,
# which will be the return value of the function (success True and failure is
# False)
_RETVAL = 0

# IDEAS:
# The functions can always return a dictionary. The first element can always be
# the return value and then the rest can be values that are returned.

"""
The graphyte module.

Instantiating the class does everything now. Refer to the constructor below.


"""

class Graphyte(object):
  def __init__(self):
    """
    The constructor for this module does most of it right now.
    - Load the graphyte.settings file to find the modules to load.
    - Load the plugins
    - Load test plans
    - Execute the TX test.

    Most of the error conditions are ignored and values are hardcoded.

    The graphyte.settings file follows the settings understood by ConfigParser
    https://docs.python.org/2/library/configparser.html

    Right now the configuration file has only one section called [plugins] and
    two entries "dut=" and "inst=". These entries are initialized to
    sample_dut.py and sample_inst.py. The dut pluings are searched under
    ./dut-plugins/ and the instrument plugins are searched under ./inst_plugins/

    Once the plugins are found, they are loaded.

    The testplans module is responsible for reading the CSV file which defines
    the testplans and generate a dictionary that can be passed to inst and dut
    plugins.

    Right now the testplan module has only one test case.

    The interaction with the dut and the instrument plugin is dipicted in
    the flow diagram.
    """
    self.inst = None
    self.inst_module = None
    self.inst_module_info = None
    self.dut = None
    self.dut_module = None
    self.dut_module_info = None
    self.tp = None

    print "Starting Graphyte...."

    self.config = ConfigParser.ConfigParser()
    self.config.read('graphyte.settings')

    self.dut_plugin_name = self.config.get('plugins', 'dut')
    self.inst_plugin_name = self.config.get('plugins', 'inst')

    self._LoadDutPlugin()
    self._LoadInstPlugin()

    self.testplans = testplan.TestPlan()

  def __del__(self):
    if (self.dut.wlan_disconnect()[_RETVAL] == False or
        self.inst.wlan_disconnect()[_RETVAL] == False):
      print "Failed to disconnect from Inst/Dut"

  def _LoadDutPlugin(self):
    self.dut_module_info = imp.find_module(self.dut_plugin_name,
                                           ['./dut_plugins'])
    self.dut_module = imp.load_module(self.dut_plugin_name,
                                      *self.dut_module_info)
    self.dut = self.dut_module.Dut(self)

  def _LoadInstPlugin(self):
    self.inst_module_info = imp.find_module(self.inst_plugin_name,
                                            ['./inst_plugins'])
    self.inst_module = imp.load_module(self.inst_plugin_name,
                                       *self.inst_module_info)
    self.inst = self.inst_module.Dut(self)

  def Run(self):
    #TODO(akahuang): Currently the code is broken because the implementation
    # of TestPlan changed. Should implement new test runner later.

    # For now, only one test plan.
    self.tp = self.testplans.GetNextTest()

    if self.tp[_RETVAL] == False:
      # Raise exception instead?
      print "No test cases to execute"
      return

    # Configure the instrument && DUT
    if (self.inst.WlanInitialize()[_RETVAL] == False or
        self.dut.WlanInitialize(self.tp[1]['Component Name'])[_RETVAL]
        == False):
      print "Failed to initialize the instrument/DUT"
      return

    # Note for tx_set_power:
    # If nothing  is passed (then the function assumes it to be 0),
    # then the dut plugin should use the value passed in
    # wlan_tx_set_mode. If the value is not 0 (or not passed),
    # then that would be overriding the value thats already passed.
    if (self.dut.WlanTxSetMode(test_params=self.tp)[_RETVAL] == False or
        self.dut.WlanTxSetPower()[_RETVAL] == False):
      print "Failed to set TX mode/power on dut"
      return

    port_map = {'vsa':0, 'port':0}

    if not self.inst.WlanTxConfig(
        test_params=self.tp, rf_ports=port_map)[_RETVAL]:
      print "Failed to load instrument tx config"
      return

    if self.dut.WlanTxOn()[_RETVAL] == False:
      print "DUT TX On Failed"
    else:
      if self.inst.WlanTxMeasure()[_RETVAL] == False:
        print "Inst TX Measure failed"
      else:
        result = self.inst.WlanTxGetResults()
        if result[_RETVAL] == False:
          print "Inst: Failed to get results"
        else:
          print result[1]

    if self.dut.WlanTxOff()[_RETVAL] == False:
      print "Failed to do TX Off"


def main():
  app = Graphyte()
  app.Run()


if __name__ == '__main__':
  main()

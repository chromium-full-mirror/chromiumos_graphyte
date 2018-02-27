#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The Google RF Test Framework module.

This is the main application module that will drive the other modules.
This module can also be imported and an instance of graphyte created from there.

Typical Usage (Import to other modules):
  from graphyte.graphyte import Graphyte
  app = Graphyte()
Please refer to graphyte_main.py.
"""

import json
import os

import graphyte_common  # pylint: disable=unused-import
from graphyte.default_setting import DEFAULT_CONFIG_FILE
from graphyte.default_setting import DEFAULT_RESULT_FILE
from graphyte.default_setting import GRAPHYTE_DIR
from graphyte.default_setting import logger
from graphyte.device import DeviceType
from graphyte.port_config import PortConfig
from graphyte.result_writer import ResultWriter
from graphyte.testplan import TestPlan
from graphyte.utils import graphyte_utils
from graphyte.utils import sync_utils

class Controller(object):
  """The controller controls the flow to perform tests.

  Instantiating the class does everything now. Refer to the constructor below.
  """
  def __init__(self, config_file=None, result_file=None):
    """Instantiate a controller to perform all the tests, which includes:

    - Load the graphyte.settings file to find the modules to load.
    - Load the plugins
    - Load test plans
    - Execute all the tests in the test plan.

    The configuration file graphyte_config.sample.json follows the json format.
    The file has the dut and inst module name and config file.
    These entries are initialized to sample_dut.py and sample_inst.py. The dut
    pluings are searched under ./dut/ and the instrument plugins are searched
    under ./inst/. Once the plugins are found, they are loaded.

    The testplan module is responsible for reading the CSV file which defines
    the testplan and generate a list of the test case, that can be passed to
    inst and dut plugins.

    The interaction with the dut and the instrument plugin is dipicted in
    the flow diagram.
    """
    config_file = config_file or DEFAULT_CONFIG_FILE
    result_file = result_file or DEFAULT_RESULT_FILE

    config_path = graphyte_utils.SearchConfig(config_file, GRAPHYTE_DIR)
    config_dir = os.path.dirname(config_path)
    with open(config_path, 'r') as f:
      graphyte_config = json.load(f)

    # Load DUT and Inst class
    self.dut = self._LoadDevice(graphyte_config, 'dut', config_dir)
    self.inst = self._LoadDevice(graphyte_config, 'inst', config_dir)

    # Load test plan
    self.testplan = TestPlan(graphyte_config['test_plan'], config_dir)
    if not self.testplan:
      raise ValueError('Load test plan failed.')

    # Load port config, including port mapping and path loss
    self.port_config = PortConfig(graphyte_config['port_config'], config_dir)

    # Load the test argument
    self.retries = graphyte_config.get('retries', 1)

    # Open a result writer
    self.result_writer = ResultWriter(result_file)

    # Record all tests are pass or not
    self.all_tests_pass = None

  def Close(self):
    self.result_writer.Close()
    self.TerminateDevices()

  def _LoadDevice(self, graphyte_config, device_type, config_dir):
    """Dynamically load the device instance by the global config.

    Args:
      graphyte_config: the global config.
      device_type: 'dut' or 'inst'
      config_dir: the directory of the graphyte config file.
    Returns:
      The device instance.
    """
    class_name_mapping = {'dut': 'DUT',
                          'inst': 'Inst'}
    module_name = graphyte_config[device_type]
    class_name = class_name_mapping[device_type]
    module = __import__('%s.%s' % (device_type, module_name),
                        globals(), level=1, fromlist=[class_name])
    # Load config file.
    default_config_file = module_name.replace('.', os.path.sep) + '.json'
    default_config_path = os.path.join(GRAPHYTE_DIR, device_type,
                                       default_config_file)
    device_config = graphyte_utils.LoadConfig(default_config_path)

    config_key = '%s_config_file' % device_type
    if config_key in graphyte_config:
      config_file = graphyte_utils.SearchConfig(
          graphyte_config[config_key], [config_dir])
      device_config = graphyte_utils.OverrideConfig(
          device_config, graphyte_utils.LoadConfig(config_file))
    config_key = '%s_config' % device_type
    if config_key in graphyte_config:
      device_config = graphyte_utils.OverrideConfig(
          device_config, graphyte_config[config_key])

    logger.info('Loading %s: %s, device config: %s',
                device_type, module_name, device_config)
    return module.__dict__[class_name](**device_config)


  def Run(self):
    """The main method of the class.

    It returns whether all tests are passed or not.
    """
    # Initialize the test environment.
    self.all_tests_pass = True
    self.InitialzeDevices()

    # Iteratively execute every test case.
    for test_case in self.testplan:
      self.RunTest(test_case)
    logger.info('All tests are pass? %s', self.all_tests_pass)
    self.result_writer.WriteTotalResult(self.all_tests_pass)

    # Terminate the test environment.
    self.Close()
    return self.all_tests_pass

  def InitialzeDevices(self, device=DeviceType.ALL):
    if DeviceType.IsInst(device):
      try:
        self.inst.Initialize()
        self.inst.LockInstrument()
        self.inst.InitPortConfig(self.port_config)
      except Exception:
        logger.error('Failed to initialize instrumenet.')
        raise

    if DeviceType.IsDUT(device):
      try:
        self.dut.Initialize()
      except Exception:
        logger.error('Failed to initialize DUT.')
        raise

  def TerminateDevices(self, device=DeviceType.ALL):
    if DeviceType.IsInst(device):
      try:
        self.inst.UnlockInstrument()
        self.inst.Terminate()
      except Exception:
        logger.exception('Failed to terminate the instrument device.')

    if DeviceType.IsDUT(device):
      try:
        self.dut.Terminate()
      except Exception:
        logger.exception('Failed to terminate DUT.')

  def SetRF(self, rf_type, device=DeviceType.ALL):
    logger.info('Set RF type: %s', rf_type)
    if DeviceType.IsDUT(device):
      self.dut.SetRF(rf_type)
    if DeviceType.IsInst(device):
      self.inst.SetRF(rf_type)

  def OnFailure(self, device=DeviceType.ALL):
    if DeviceType.IsDUT(device):
      self.dut.OnFailure()
    if DeviceType.IsInst(device):
      self.inst.OnFailure()

  def RunTest(self, test_case):
    logger.info('Running test: %s', test_case)
    logger.info('Test arguments: %r', test_case.args)
    logger.info('Test limit: %r', test_case.result_limit)
    self.SetRF(test_case.rf_type)

    self.inst.SetPortConfig(test_case)
    function_map = {
        'TX': self.RunTxTest,
        'RX': self.RunRxTest}

    def _RunTest():
      try:
        ret = function_map[test_case.test_type](test_case)
      except Exception:
        logger.exception('RunTest error. test_case: %s', test_case)
        self.OnFailure()
        return False, {}

      if not ret[0]:
        self.OnFailure()

      return ret

    def _Condition(ret):
      # ret is (is_pass, result)
      return ret[0]

    # pylint: disable=W0633
    is_pass, result = sync_utils.Retry(self.retries, 0, _RunTest, _Condition)
    self.all_tests_pass &= is_pass
    self.result_writer.WriteResult(test_case, result)

  def RunTxTest(self, test_case):
    self.dut.active_controller.TxStart(test_case)
    self.inst.active_controller.TxMeasure(test_case)
    result = self.inst.active_controller.TxGetResult(test_case)
    self.dut.active_controller.TxStop(test_case)
    return result

  def RunRxTest(self, test_case):
    self.dut.active_controller.RxClearResult(test_case)
    self.inst.active_controller.RxGenerate(test_case)
    result = self.dut.active_controller.RxGetResult(test_case)
    self.inst.active_controller.RxStop(test_case)
    return result

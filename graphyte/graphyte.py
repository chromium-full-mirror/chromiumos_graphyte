#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
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
import logging
import os

from .default_setting import DEFAULT_CONFIG_FILE
from .default_setting import DEFAULT_LOG_FILE
from .default_setting import DEFAULT_RESULT_FILE
from .default_setting import GRAPHYTE_DIR
from .default_setting import GRAPHYTE_OUT
from .default_setting import logger
from .port_config import PortConfig
from .result_writer import ResultWriter
from .testplan import TestPlan
from .utils import graphyte_utils
from .utils import sync_utils


class Graphyte(object):
  """The graphyte module.

  Instantiating the class does everything now. Refer to the constructor below.
  """
  def __init__(self, config_file=None, log_file=None, result_file=None,
               verbose=False, console_output=False):
    """The constructor for this module does most of it right now.

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
    log_file = log_file or DEFAULT_LOG_FILE
    result_file = result_file or DEFAULT_RESULT_FILE

    self.SetLogging(log_file, verbose, console_output)
    logger.info('Starting Graphyte....')

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
    self.rf_type = None

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

  def SetLogging(self, log_file, verbose, console_output):
    level = logging.DEBUG if verbose else logging.INFO
    log_file = graphyte_utils.PrepareOutputFile(log_file)
    if os.path.exists(log_file):
      os.remove(log_file)
    fmt = '[%(levelname)s] %(asctime)s %(filename)s:%(lineno)d %(message)s'
    date_fmt = '%H:%M:%S'
    formatter = logging.Formatter(fmt, date_fmt)

    root_logger = logging.getLogger('')
    root_logger.setLevel(level)
    file_handler = logging.FileHandler(log_file, 'a')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    if console_output:
      console_handler = logging.StreamHandler(GRAPHYTE_OUT)
      console_handler.setFormatter(formatter)
      root_logger.addHandler(console_handler)

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

  def InitialzeDevices(self):
    try:
      self.inst.Initialize()
      self.inst.LockInstrument()
      self.inst.InitPortConfig(self.port_config)
      self.dut.Initialize()
    except Exception:
      logger.exception('Initialize devices failed.')

  def TerminateDevices(self):
    try:
      self.inst.UnlockInstrument()
      self.inst.Terminate()
      self.dut.Terminate()
    except Exception:
      logger.exception('Terminate devices failed.')

  def SetRF(self, rf_type):
    logger.info('Set RF type: %s', rf_type)
    if rf_type != self.rf_type:
      self.rf_type = rf_type
      self.dut.SetRF(rf_type)
      self.inst.SetRF(rf_type)

  def RunTest(self, test_case):
    logger.info('Running test: \n%s', test_case)
    self.SetRF(test_case.rf_type)

    self.inst.SetPortConfig(test_case)
    function_map = {
        'TX': self.RunTxTest,
        'RX': self.RunRxTest}

    def _RunTest():
      try:
        return function_map[test_case.test_type](test_case)
      except Exception:
        logger.exception('RunTest error. test_case: %s', test_case)
        return False, {}
    def _Condition(ret):
      # ret is (is_pass, result)
      return ret[0]

    # pylint: disable=W0633
    is_pass, result = sync_utils.Retry(self.retries, 0, _RunTest, _Condition)
    self.all_tests_pass &= is_pass
    self.result_writer.WriteResult(test_case, result)

  def RunTxTest(self, test_case):
    self.dut.TxConfig(test_case)
    self.inst.TxConfig(test_case)
    self.dut.TxStart(test_case)
    self.inst.TxMeasure(test_case)
    self.dut.TxStop(test_case)
    result = self.inst.TxGetResult(test_case)
    return result

  def RunRxTest(self, test_case):
    self.dut.RxConfig(test_case)
    self.inst.RxConfig(test_case)
    self.dut.RxClearResult(test_case)
    self.inst.RxGenerate(test_case)
    result = self.dut.RxGetResult(test_case)
    self.inst.RxStop(test_case)
    return result

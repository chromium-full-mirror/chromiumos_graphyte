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

import logging
import os
import yaml

from .port_config import PortConfig
from .testplan import TestPlan
from .utils import SearchConfig


GRAPHYTE_DIR = os.path.dirname(os.path.realpath(__file__))
DEFAULT_CONFIG_FILE = 'graphyte_config.sample.yaml'


class Graphyte(object):
  """The graphyte module.
  Instantiating the class does everything now. Refer to the constructor below.
  """
  def __init__(self, config_file=DEFAULT_CONFIG_FILE, verbose=False):
    """
    The constructor for this module does most of it right now.
    - Load the graphyte.settings file to find the modules to load.
    - Load the plugins
    - Load test plans
    - Execute all the tests in the test plan.

    The configuration file graphyte_config.sample.yaml follows the yaml format.
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
    self.SetLogging(verbose)
    logging.info('Starting Graphyte....')

    config_path = SearchConfig(config_file, GRAPHYTE_DIR)
    with open(config_path, 'r') as f:
      graphyte_config = yaml.load(f)

    # Load Dut and Inst class
    dut_name = graphyte_config['dut']
    module = __import__('dut.%s.%s' % (dut_name, dut_name), globals(),
                        level=1, fromlist=['Dut'])
    dut_dir = os.path.join(GRAPHYTE_DIR, 'dut', dut_name)
    dut_config_file = SearchConfig(graphyte_config['dut_config'], dut_dir)
    with open(dut_config_file, 'r') as f:
      dut_config = yaml.load(f)
    logging.info('DUT %s, config: %s', dut_name, dut_config)
    self.dut = module.Dut(dut_config)

    inst_name = graphyte_config['inst']
    module = __import__('inst.%s.%s' % (inst_name, inst_name), globals(),
                        level=1, fromlist=['Inst'])
    inst_dir = os.path.join(GRAPHYTE_DIR, 'inst', inst_name)
    inst_config_file = SearchConfig(graphyte_config['inst_config'], inst_dir)
    with open(inst_config_file, 'r') as f:
      inst_config = yaml.load(f)
    logging.info('Inst %s, config: %s', inst_name, inst_config)
    self.inst = module.Inst(inst_config)

    # Load test plan
    self.testplans = TestPlan(graphyte_config['test_plan'])
    self.rf_type = None

    # Load port config, including port mapping and path loss
    self.port_config = PortConfig(graphyte_config['port_config'])

  def __del__(self):
    self.TerminateDevices()

  def SetLogging(self, verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='[%(levelname)s] %(filename)s:%(lineno)d %(message)s',
        datefmt='%H:%M:%S')

  def Run(self):
    self.InitialzeDevices()
    for test_case in self.testplans:
      self.RunTest(test_case)
    self.TerminateDevices()

  def InitialzeDevices(self):
    try:
      self.inst.Initialize()
      self.inst.LockInstrument()
      self.inst.SelfCalibrate()
      self.inst.InitPortConfig(self.port_config)
    except Exception:
      logging.exception('Initialize devices failed')

  def TerminateDevices(self):
    try:
      self.inst.UnlockInstrument()
      self.inst.Terminate()
      self.dut.Terminate()
    except Exception:
      logging.exception('Terminate devices failed')

  def SetRf(self, rf_type):
    logging.info('Set RF type: %s', rf_type)
    self.rf_type = rf_type
    self.dut.SetRf(rf_type)
    self.inst.SetRf(rf_type)

  def RunTest(self, test_case):
    logging.info('Running test: \n%s', test_case)
    # Initialize the device if the RF is changed.
    if test_case.rf_type != self.rf_type:
      if self.rf_type is not None:
        self.dut.Terminate()
      self.SetRf(test_case.rf_type)
      self.dut.Initialize(test_case)

    self.inst.SetPortConfig(test_case)
    function_map = {
        'TX': self.RunTxTest,
        'RX': self.RunRxTest}
    function_map[test_case.tx_or_rx](test_case)

  def RunTxTest(self, test_case):
    try:
      self.dut.TxSetMode(test_case)
      self.dut.TxSetPower(test_case)
      self.inst.TxConfig(test_case)
      self.dut.TxStart(test_case)
      self.inst.TxMeasure(test_case)
      self.inst.TxGetResult(test_case)
      self.dut.TxStop(test_case)
    except Exception:
      logging.exception('RunTxTest error. test_case: %s', test_case)

  def RunRxTest(self, test_case):
    try:
      self.dut.RxSetMode(test_case)
      self.dut.RxClearResult(test_case)
      self.inst.RxConfig(test_case)
      self.inst.RxGenerate(test_case)
      self.dut.RxGetResult(test_case)
    except Exception:
      logging.exception('RunRxTest error. test_case: %s', test_case)

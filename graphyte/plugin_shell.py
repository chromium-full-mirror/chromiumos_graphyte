#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""This is an interactive shell for Graphyte framework

This interactive shell provides the capability to interact
with Graphyte framework step by step, make it easier to
diagnosis problems on test station, DUT, or instrument.

Preparation:
  1. Setup your DUT and/or instrument, and prepare the config file.
  2. Prepare a test plan with at least one test case. This script
     will use one of those test cases for interactive diagnosis.
"""

from __future__ import print_function
import argparse
import cmd
import sys

import graphyte_common  # pylint: disable=unused-import
from graphyte import controller
from graphyte import testplan
from graphyte.bootstrap import Bootstrap
from graphyte.default_setting import logger
from graphyte.device import DeviceType
from graphyte.utils import type_utils

DEVICE_STATUS = type_utils.Enum([
    'STOP',  # Device is not initialized.
    'IDLE',  # Device is initiailized but not running.
    'RUNNING'])  # Device starts running the test case.


def CheckIn(name, item, arr):
  if item not in arr:
    print('Error: %s is now "%s", but it should be one of %r.' % (
        name, item, arr))
    return False
  return True


# pylint: disable=invalid-name
class PluginShell(cmd.Cmd):
  intro = """=== Graphyte Plugin Runner ===
Welcome to Graphyte Plugin Runner
This tool will help you to check if your DUT and instrument are
correctly set up, to make sure it's ready for graphyte framework.

General usage:
  1. Use command 'choose' to choose a test case
  2. Use command 'set_test_arg' to tweak test arguments
  3. Use command 'status' to check all settings
  4. Use command 'run' to start the test step-by-step.

Commands for the active device:
  1. Use commands 'dut' or 'inst' to choose DUT or instrument.
  2. Type command 'initialize'
  3. Type command 'start'
  4. Type command 'stop'
  5. Type command 'terminate'

For a Tx test:
  0. Prepare: dut; initialize; inst; initialize
  1. Start DUT: dut; start;
  2. Start instrument: inst; start
  3. Stop instrument: inst; stop
  4. Stop DUT: dut; stop
  5. Terminate: dut; terminate; inst; terminate

For a Rx test, swap steps 3 & 4

Type command after prompt. Use 'help' for more details ===
"""

  def __init__(self, controller_obj):
    cmd.Cmd.__init__(self)

    self.controller_obj = controller_obj
    # Assume the testplan is not empty. Select the first test case.
    self.test_case = controller_obj.testplan[0]
    self.active_device = DeviceType.DUT
    self.device_status = {
        DeviceType.DUT: DEVICE_STATUS.STOP,
        DeviceType.INST: DEVICE_STATUS.STOP}

  @property
  def prompt(self):
    return ("=== Active Device: %s [%s] | Test Case: %s ===\n>> " % (
        self.active_device, self.device_status[self.active_device],
        self._TestCaseName()))

  def do_help(self, args):
    """Get help information"""
    if len(args) == 0:
      print(self.intro)
    cmd.Cmd.do_help(self, args)

  def do_EOF(self, _):
    """Process the end-of-file marker to exit in a clean way."""
    return True

  def do_status(self, _):
    """Prints the current status."""
    print('')
    print('DUT: %s' % (
        '(active)' if self.active_device == DeviceType.DUT else ''))
    print('  Status: %s' % self.device_status[DeviceType.DUT])
    print('  Details: %s' % '\n    '.join(
        str(self.controller_obj.dut).splitlines()))

    print('')
    print('Instrument: %s' % (
        '(active)' if self.active_device == DeviceType.INST else ''))
    print('  Status: %s' % self.device_status[DeviceType.INST])
    print('  Details: %s' % '\n    '.join(
        str(self.controller_obj.inst).splitlines()))

    print('')
    print('Test case:')
    print('  Name: %s' % self._TestCaseName())
    print('  RF type: %s' % str(self.test_case.rf_type))

    print('  Arguments:')
    for key, val in self.test_case.args.iteritems():
      print('    %s: %s' % (key, val))

    print('  Result limitations:')
    for key, val in self.test_case.result_limit.iteritems():
      print('    %s: %s' % (key, val))

    print('')

  def do_dut(self, _):
    """Swtichs the active device to DUT."""
    self.active_device = DeviceType.DUT
    print("[SUCCESS] Active device switched to DUT")

  def do_inst(self, _):
    """Swtichs the active device to INST."""
    self.active_device = DeviceType.INST
    print("[SUCCESS] Active device switched to INST")

  def help_choose(self):
    print('Choose the active test case with the given test type.')
    print('')
    print('Usage: choose [RF type] [Test type]')
    print('')
    print('Available RF types: ' + ', '.join(testplan.SUPPORTED_RF_TYPES))
    print('Available test types: ' + ', '.join(testplan.SUPPORTED_TEST_TYPES))

  def do_choose(self, type_str):
    args = type_str.upper().split()

    if len(args) > 2:
      print('[FAILED] Number of the arguments should be less or equal to 2.')
      self.help_choose()
      return

    rf_type = args[0] if len(args) > 0 else None
    test_type = args[1] if len(args) > 1 else None

    if rf_type:
      if not CheckIn('RF type', rf_type, testplan.SUPPORTED_RF_TYPES):
        print('Invalid RF type: %s' % rf_type)
        self.help_choose()
        return

    if test_type:
      if not CheckIn('Test type', test_type, testplan.SUPPORTED_TEST_TYPES):
        print('Invalid test type: %s' % test_type)
        self.help_choose()
        return

    candidates = []
    for test_case in self.controller_obj.testplan:
      if rf_type and test_case.rf_type != rf_type:
        continue
      if test_type and test_case.test_type != test_type:
        continue
      candidates.append(test_case)

    if not candidates:
      print('No any test plan available.')
      return

    for idx, test_case in enumerate(candidates):
        print('[%d] %s' % (idx, test_case))

    try:
      choose_idx = int(raw_input("Enter the index of the test case: "))
      self.test_case = candidates[choose_idx].Copy()
      print('[SUCCESS] Test case switched to %s' % self._TestCaseName())
    except Exception as ex:
      print('Failed to set the active test case: %s' % ex)

  def help_set_test_arg(self):
    print("Sets the argument of the test case.")
    print('')
    print('Usage: set_test_arg (argument name) (argument value)')
    print('')
    print('Available argument names: \n  %s' % '\n  '.join(self.test_case.args))

  def do_set_test_arg(self, test_arg):
    args = test_arg.split()

    if len(args) != 2:
      print('[FAILED] The number of the arguments should be 2.')
      self.help_set_test_arg()
      return

    arg_name, arg_value = args[0].lower(), args[1].upper()

    if not self._CheckActiveDevice([DEVICE_STATUS.STOP, DEVICE_STATUS.IDLE]):
      print("[FAILED] Active device should be in stop/idle state")
      return

    if not CheckIn('Argument', arg_name, self.test_case.args):
      print("[FAILED] Invalid argument name '%s'" % arg_name)
      self.help_set_test_arg()
      return

    self.test_case.args[arg_name] = arg_value
    print("[SUCCESS] Argument '%s' has been changed to '%s'" % (
        arg_name, str(arg_value)))

  def do_run(self, arg):
    """Run the test step-by-step."""
    calls = []
    if self.test_case.test_type == 'TX':
      calls = [
          ('Initialize DUT', [self.do_dut, self.do_initialize]),
          ('Initialize Instrument', [self.do_inst, self.do_initialize]),
          ('DUT Start', [self.do_dut, self.do_start]),
          ('Instrument Start', [self.do_inst, self.do_start]),
          ('Instrument Stop', [self.do_inst, self.do_stop]),
          ('DUT Stop', [self.do_dut, self.do_stop]),
          ('Terminate DUT', [self.do_dut, self.do_terminate]),
          ('Terminate Instrument', [self.do_inst, self.do_terminate])]
    elif self.test_case.test_type == 'RX':
      calls = [
          ('Initialize DUT', [self.do_dut, self.do_initialize]),
          ('Initialize Instrument', [self.do_inst, self.do_initialize]),
          ('DUT Start', [self.do_dut, self.do_start]),
          ('Instrument Start', [self.do_inst, self.do_start]),
          ('DUT Stop', [self.do_dut, self.do_stop]),
          ('Instrument Stop', [self.do_inst, self.do_stop]),
          ('Terminate DUT', [self.do_dut, self.do_terminate]),
          ('Terminate Instrument', [self.do_inst, self.do_terminate])]
    else:
      print("Unknown test type: %s" % self.test_case.test_type)
      return

    print("Start running test step-by-step.")
    for op, funcs in calls:
      print()

      msg = "Next command is '%s'. " % op
      msg += "Press 'r' to run; 's' to skip; 'q' to quit: "

      while True:
        action = raw_input(msg)
        if action == 'r':
          for func in funcs:
            func(arg)
          break
        elif action == 's':
          break
        elif action == 'q':
          print('Stop step-by-step run.')
          return
        else:
          print('Unknown input: "%s"' % action)
    print("Step-by-step run is finished.")

  def do_initialize(self, _):
    """Initializes the active device."""
    if not self._CheckActiveDevice([DEVICE_STATUS.STOP]):
      return

    try:
      self.controller_obj.InitialzeDevices(self.active_device)
      self.device_status[self.active_device] = DEVICE_STATUS.IDLE
    except Exception as ex:
      print('')
      logger.exception(ex)
      print("[FAILED] An exception is caught '%s'" % str(ex))
      return

  def do_terminate(self, _):
    """Terminates the active device."""
    if not self._CheckActiveDevice([DEVICE_STATUS.IDLE, DEVICE_STATUS.RUNNING]):
      return

    try:
      self.controller_obj.TerminateDevices(self.active_device)
      self.device_status[self.active_device] = DEVICE_STATUS.STOP
    except Exception as ex:
      print('')
      logger.exception(ex)
      print("[FAILED] An exception is caught '%s'" % str(ex))
      return

  def do_start(self, _):
    """Starts the test."""
    # Check the test case is valid.
    if not self._CheckActiveDevice([DEVICE_STATUS.IDLE]):
      return

    try:
      # Set RF type.
      self.controller_obj.SetRF(self.test_case.rf_type, self.active_device)

      # Call the start function.
      if self.active_device == DeviceType.DUT:
        active_controller = self.controller_obj.dut.active_controller
        if self.test_case.test_type == 'TX':
          active_controller.TxStart(self.test_case)
        else:
          active_controller.RxClearResult(self.test_case)
      elif self.active_device == DeviceType.INST:
        self.controller_obj.inst.SetPortConfig(self.test_case)
        active_controller = self.controller_obj.inst.active_controller
        if self.test_case.test_type == 'TX':
          active_controller.TxMeasure(self.test_case)
        else:
          active_controller.RxGenerate(self.test_case)
    except Exception as ex:
      print('')
      logger.exception(ex)
      print("[FAILED] An exception is caught '%s'" % str(ex))
      return

    # Change the state to TX or RX depending on the test case.
    self.device_status[self.active_device] = DEVICE_STATUS.RUNNING

  def do_stop(self, _):
    """Stops the test."""
    # Check if the active device is already assigned, and the state is running.
    if not self._CheckActiveDevice([DEVICE_STATUS.RUNNING]):
      return

    def _CheckResult(result):
      print('Test result: %s' % str(result))

      try:
        is_pass = result[0]
      except Exception:
        print("[FAILED] Cannot decide if result is passed or not.")
        return

      if is_pass != True:
        print("[FAILED] Result is not pass.")

    try:
      # Call the stop function.
      if self.active_device == DeviceType.DUT:
        active_controller = self.controller_obj.dut.active_controller
        if self.test_case.test_type == 'TX':
          active_controller.TxStop(self.test_case)
        else:
          _CheckResult(active_controller.RxGetResult(self.test_case))
      elif self.active_device == DeviceType.INST:
        active_controller = self.controller_obj.inst.active_controller
        if self.test_case.test_type == 'TX':
          _CheckResult(active_controller.TxGetResult(self.test_case))
        else:
          active_controller.RxStop(self.test_case)
    except Exception as ex:
      print('')
      logger.exception(ex)
      print("[FAILED] An exception is caught '%s'" % str(ex))
      return

    # Change the state to IDLE depending on the test case.
    self.device_status[self.active_device] = DEVICE_STATUS.IDLE

  def do_exit(self, _):
    """Exits the shell."""
    print('Exit')
    sys.exit(0)

  def _TestCaseName(self):
    return str(self.test_case)

  def _CheckActiveDevice(self, valid_statuses):
    """Checks the status of the active device.

    Args:
      valid_statuses: the list of valid statuses.
    """
    return CheckIn('Active device (%s) status' % self.active_device,
                   self.device_status[self.active_device],
                   valid_statuses)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('config_file',
                      type=str, help='The path of config file.')
  parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                      help='Enable debug logging', default=False)
  options = parser.parse_args()

  Bootstrap.InitLogger(
      verbose=options.verbose,
      console_output=True)
  logger.info('Starting Shell....')

  try:
    controller_obj = controller.Controller(options.config_file, '/dev/null')
  except Exception:
    logger.exception('Failed to Initialize Graphyte instance.')
    return

  PluginShell(controller_obj).cmdloop()


if __name__ == '__main__':
  main()

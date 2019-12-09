# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import inspect
import subprocess
import tempfile

import graphyte_common  # pylint: disable=unused-import
from graphyte.default_setting import logger
from graphyte.utils import file_utils

CalledProcessError = subprocess.CalledProcessError

MODULE_PATH_MAPPING = {
    'ADBLink': 'graphyte.links.adb',
    'SSHLink': 'graphyte.links.ssh',
    'SCPILink': 'graphyte.links.scpi',
    'GPIBLink': 'graphyte.links.gpib'}


class LinkNotReady(Exception):
  """Exception for link is not ready."""


class LinkOptionsError(Exception):
  """Exception for invalid link options."""


class DeviceLink(object):
  """An abstract class for Device (DUT and instrument) Links."""

  def Open(self):
    """Opens the connection of the link

    This method should be called before any operation.
    """
    pass

  def Close(self):
    """Closes the connection of the link.

    This method should be explicitly called before the device is destroyed.
    """
    pass

  def Push(self, local, remote):
    """Uploads a local file to DUT.

    Args:
      local: A string for local file path.
      remote: A string for remote file path on DUT.
    """
    raise NotImplementedError

  def Pull(self, remote, local=None):
    """Downloads a file from DUT to local.

    Args:
      remote: A string for file path on remote DUT.
      local: A string for local file path to receive downloaded content, or
             None to return the contents directly.

    Returns:
      If local is None, return a string as contents in remote file.
      Otherwise, do not return anything.
    """
    raise NotImplementedError

  def Shell(self, command, stdin=None, stdout=None, stderr=None):
    """Executes a command on DUT.

    The calling convention is similar to subprocess.Popen, but only a subset of
    parameters are supported due to platform limitation.

    Args:
      command: A string or a list of strings for command to execute.
      stdin: A file object to override standard input.
      stdout: A file object to override standard output.
      stderr: A file object to override standard error.

    Returns:
      An object representing the process, similar to subprocess.Popen.
    """
    raise NotImplementedError

  def CheckReady(self):
    if not self.IsReady():
      raise LinkNotReady

  def IsReady(self):
    """Checks if DUT is ready for connection.

    Returns:
      A boolean indicating if target DUT is ready.
    """
    raise NotImplementedError

  def Call(self, *args, **kargs):
    """Executes a command on DUT, using subprocess.call convention.

    The arguments are explained in Shell.

    Returns:
      Exit code from executed command.
    """
    process = self.Shell(*args, **kargs)
    process.wait()
    return process.returncode

  def CheckCall(self, command, stdin=None, stdout=None, stderr=None):
    """Executes a command on DUT, using subprocess.check_call convention.

    Args:
      command: A string or a list of strings for command to execute.
      stdin: A file object to override standard input.
      stdout: A file object to override standard output.
      stderr: A file object to override standard error.

    Returns:
      Exit code from executed command.

    Raises:
      CalledProcessError if the exit code is non-zero.
    """
    exit_code = self.Call(command, stdin, stdout, stderr)
    if exit_code != 0:
      raise CalledProcessError(returncode=exit_code, cmd=command)
    return exit_code

  def CheckOutput(self, command, stdin=None, stderr=None):
    """Executes a command on DUT, using subprocess.check_output convention.

    Args:
      command: A string or a list of strings for command to execute.
      stdin: A file object to override standard input.
      stdout: A file object to override standard output.
      stderr: A file object to override standard error.

    Returns:
      The output on STDOUT from executed command.

    Raises:
      CalledProcessError if the exit code is non-zero.
    """
    with tempfile.TemporaryFile() as stdout:
      exit_code = self.Call(command, stdin, stdout, stderr)
      stdout.flush()
      stdout.seek(0)
      output = stdout.read().decode('utf-8')
    if exit_code != 0:
      raise CalledProcessError(
          returncode=exit_code, cmd=command, output=output)
    return output

  def CallOutput(self, *args, **kargs):
    """Runs the command on DUT and return data from standard output if success.

    Returns:
      If command exits with zero (success), return the standard output;
      otherwise None. If the command didn't output anything then the result is
      empty string.
    """
    try:
      return self.CheckOutput(*args, **kargs)
    except CalledProcessError as ex:
      logger.debug('Failed to run command: %s', str(ex))
      return None

  def WriteFile(self, path, content):
    """Writes some content into file on DUT.

    Args:
      path: A string for file path on DUT.
      content: A string to be written into file.
    """
    with file_utils.UnopenedTemporaryFile() as temp_path:
      with open(temp_path, 'w') as f:
        f.write(content)
      self.Push(temp_path, path)

  def ReadFile(self, path):
    with file_utils.UnopenedTemporaryFile() as temp_path:
      self.Pull(path, temp_path)
      return open(temp_path, 'r').read()

  def ReadSpecialFile(self, path, count=None, skip=None):
    cmd = ['dd', 'bs=1', 'if=%s' % path]
    if count:
      cmd += ['count=%d' % count]
    if skip:
      cmd += ['skip=%d' % skip]
    return self.CheckOutput(cmd)

def _GetLinkClass(class_name):
  """Loads and returns a class object specified from the arguments.

  The module and class will be constructed based on the arguments.
  For example, ADBLink would load the class like
    from graphyte.links.adb import ADBLink

  Args:
    class_name: A string for name of the class to load, or a class object.

  Returns:
    A class constructor from the arguments.
  """
  if class_name not in MODULE_PATH_MAPPING:
    raise LinkOptionsError('Unknown class name: %s' % class_name)
  module_path = MODULE_PATH_MAPPING[class_name]
  try:
    return getattr(__import__(module_path, globals(), fromlist=[class_name]),
                   class_name)
  except:
    raise LinkOptionsError('Failed to load %s.%s' % (module_path, class_name))


def _ExtractArgs(func, kargs):
  spec = inspect.getargspec(func)
  if spec.keywords is None:
    # if the function accepts ** arguments, we can just pass everything into it
    # so we only need to filter kargs if spec.keywords is None
    kargs = {k: v for (k, v) in kargs.items() if k in spec.args}
  return kargs


def Create(options):
  """Creates a link object.

  Args:
    options: Options to setup Device link.

  Returns:
    An instance of the sub-classed DeviceLink.
  """
  link_name = options.pop('link_class')
  link_class = _GetLinkClass(link_name)
  link_args = _ExtractArgs(link_class.__init__, options)
  return link_class(**link_args)

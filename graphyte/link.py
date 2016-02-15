#!/usr/bin/env python
# Copyright 2016 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import inspect


MODULE_PATH_MAPPING = {
    'ADBLink': 'links.adb',
    'SSHLink': 'links.ssh'}


class LinkOptionsError(Exception):
  """Exception for invalid DUT options."""
  pass


class DeviceLink(object):
  """An abstract class for Device (DUT and instrument) Links."""

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

  def IsReady(self):
    """Checks if DUT is ready for connection.

    Returns:
      A boolean indicating if target DUT is ready.
    """
    raise NotImplementedError


def _GetLinkClass(class_name):
  """Loads and returns a class object specified from the arguments.

  The module and class will be constructed based on the arguments.
  For example, ADBLink would load the class like
    from .links.adb import ADBLink

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
    kargs = {k: v for (k, v) in kargs.iteritems() if k in spec.args}
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

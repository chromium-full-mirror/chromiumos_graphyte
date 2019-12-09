# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Implementation of SCPI-over-TCP interface wrapper."""

import socket
import time

import graphyte_common  # pylint: disable=unused-import
from graphyte import link
from graphyte.default_setting import logger
from graphyte.utils import sync_utils


class SCPILinkError(Exception):
  pass


class SCPILink(link.DeviceLink):
  """A target that is connected via SCPI-over-TCP interface.

  link_options example:
    {
      'link_class': 'SCPILink',
      'host': '192.168.1.100',
      'port': 5025,
    }
  """

  def __init__(self, host, port=5025, timeout=3, retries=5, initial_delay=1):
    """Connects to a device using SCPI-over-TCP.

    Parameters:
        host: Host to connect to.
        port: Port to connect to.
        timeout: Timeout in seconds. (Uses the ALRM signal.)
        retries: Maximum attempts to connect to the host.
        initial_delay: Delay in seconds before issuing the first command.
    """
    self.timeout = timeout
    self.initial_delay = initial_delay
    self.host = host
    self.port = port
    self.retries = retries;
    self.rfile = None
    self.wfile = None
    self.socket = None
    self.id = None

  def Open(self):
    if not sync_utils.Retry(self.retries, interval=1, target=self._Connect):
      raise SCPILinkError('Failed to connect %s:%d after %d tries' %
                          (self.host, self.port, self.retries))

  def Push(self, local, remote):
    raise NotImplementedError

  def Pull(self, remote, local=None):
    raise NotImplementedError

  def Shell(self, command, stdin=None, stdout=None, stderr=None):
    raise NotImplementedError

  def IsReady(self):
    try:
      info = self.CallOutput('*IDN?')
      return info != ''
    except ValueError:
      return False

  # pylint: disable=arguments-differ
  def Call(self, command, stdin=None, stdout=None, stderr=None):
    """Sends command with SCPI interface.

    Write the command to the device. If stdout is not None, then read the result
    back and write into stdout. Since it is not a real linux shell, other
    standard streams are not supported.

    Args:
      command: A string or a list, to be written to device.

    Returns:
      The return code.
    """
    if (stdin, stderr) != (None, None):
      raise NotImplementedError(
          'Redirecting standard input and error are not supported.')
    if isinstance(command, list):
      command = ' '.join([str(arg) for arg in command])

    try:
      if self._IsQueryCommand(command):
        output = self._Query(command)
        if stdout:
          stdout.write(output.encode('utf-8'))
      else:
        self._Send(command)
      return 0
    except SCPILinkError:
      logger.exception('Call command %s error', command)
      return 1

  def _Connect(self):
    try:
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

      with sync_utils.Timeout(self.timeout):
        logger.debug('Connecting to %s:%d...', self.host, self.port)
        self.socket.connect((self.host, self.port))

      self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
      self.rfile = self.socket.makefile('rb', -1)  # Default buffering
      self.wfile = self.socket.makefile('wb', 0)  # No buffering

      logger.info('Connected')

      # Give equipment time to warm up if required so.
      time.sleep(self.initial_delay)
      self.id = self._Query('*IDN?')
    except Exception:
      logger.exception('Unable to connect to %s:%d.', self.host, self.port)
      self.Close()
      return False
    return True

  def Close(self):
    logger.info('Close the SCPI socket.')
    if self.rfile:
      self.rfile.close()
      self.rfile = None
    if self.wfile:
      self.wfile.close()
      self.wfile = None
    if self.socket:
      self.socket.close()
      self.socket = None

  def _Send(self, command):
    """Sends a command to the device.

    Args:
      command: A SCPI command to send to the device (string).
    """
    self._WriteLine(command)

  def _Query(self, command):
    """Issues a query, returning the result.

    Args:
      command: A SCPI command to send to the device (string).
    """
    self._WriteLine(command)
    output = self._ReadLine()
    return output

  def _ReadLine(self):
    """Reads a single line, timing out in self.timeout seconds."""
    with sync_utils.Timeout(self.timeout):
      if not self.timeout:
        logger.debug('Waiting for reading...')
      ret = self.rfile.readline().decode('utf-8').rstrip('\n')
      logger.debug('Read: %s', ret)
      return ret

  def _WriteLine(self, command):
    """Writes a single line."""
    if '\n' in command:
      raise SCPILinkError('Newline in command: %r' % command)
    logger.debug('Write: %s', command)
    self.wfile.write((command + '\n').encode('utf-8'))

  def _IsQueryCommand(self, command):
    return '?' in command

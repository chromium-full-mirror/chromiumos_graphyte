#!/usr/bin/env python
# Copyright 2016 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Implementation of graphyte.link.DeviceLink using SSH."""

import pipes
import platform
import shlex
import subprocess

from .. import link
from ..default_setting import logger
from ..utils import UnopenedTemporaryFile


class ClientNotExistError(Exception):
  def __str__(self):
    return 'There is no DHCP client registered.'


class SSHLink(link.DeviceLink):
  """A DUT target that is connected via SSH interface.

  Properties:
    host: A string for SSH host IP.
    user: A string for the user accont to login. Defaults to 'root'.
    port: An integer for the SSH port on remote host.
    identify: An identity file to specify credential.

  link_options example:
    {
      'link_class': 'SSHLink',
      'host': '1.2.3.4',
      'identity': '/path/to/identity/file'
    }
  """

  def __init__(self, host, user='root', port=22, identity=None):
    self.host = host
    self.user = user
    self.port = port
    self.identity = identity

  def _Signature(self, is_scp=False):
    """Generates the ssh command signature.

    Args:
      is_scp: A boolean flag indicating if the signature is made for scp.

    Returns:
      A pair of signature in (sig, options). The 'sig' is a string representing
      remote ssh user and host. 'options' is a list of required command line
      parameters.
    """
    if self.user:
      sig = '%s@%s' % (self.user, self.host)
    else:
      sig = self.host

    options = ['-o', 'UserKnownHostsFile=/dev/null',
               '-o', 'StrictHostKeyChecking=no']
    if self.port:
      options += ['-P' if is_scp else '-p', str(self.port)]
    if self.identity:
      options += ['-i', self.identity]
    return sig, options

  def Push(self, local, remote):
    """See DUTLink.Push"""
    remote_sig, options = self._Signature(True)
    return subprocess.check_call(['scp'] + options +
                                 [local, '%s:%s' % (remote_sig, remote)])

  def Pull(self, remote, local=None):
    """See DUTLink.Pull"""
    if local is None:
      with UnopenedTemporaryFile() as path:
        self.Pull(remote, path)
        with open(path) as f:
          return f.read()

    remote_sig, options = self._Signature(True)
    subprocess.check_call(['scp'] + options +
                          ['%s:%s' % (remote_sig, remote), local])

  def Shell(self, command, stdin=None, stdout=None, stderr=None):
    """See DUTLink.Shell"""
    remote_sig, options = self._Signature(False)

    if isinstance(command, basestring):
      # since the shell command is passed through SSH client,
      # the entire command is argument for SSH command
      # e.g. command = 'VAR=xxx cmd arg0 arg1...'
      # will become: 'ssh' <SSH OPTIONS> 'VAR=xxx' 'cmd' 'arg0' 'arg1' ...
      command = shlex.split(command)

    shell = False
    command = ['ssh'] + options + [remote_sig] + map(pipes.quote, command)

    logger.debug('SSHLink: Run [%r]', command)
    close_fds = True
    if (platform.system() == 'Windows' and
        (stdin, stdout, stderr) != (None, None, None)):
      close_fds = False
    return subprocess.Popen(command, shell=shell, close_fds=close_fds,
                            stdin=stdin, stdout=stdout, stderr=stderr)

  def IsReady(self):
    """See DUTLink.IsReady"""
    try:
      return subprocess.call(['ping', '-w', '1', '-c', '1', self.host]) == 0
    except ClientNotExistError:
      return False

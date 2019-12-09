#!/usr/bin/env python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Implementation of graphyte.link.DeviceLink using SSH."""

import os
import pipes
import platform
import shlex
import subprocess
import threading
import time

import six
from six.moves import queue

import graphyte_common  # pylint: disable=unused-import
from graphyte import link
from graphyte.default_setting import logger
from graphyte.utils.file_utils import UnopenedTemporaryFile
from graphyte.utils import graphyte_utils
from graphyte.utils import process_utils
from graphyte.utils import sync_utils
from graphyte.utils import type_utils


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
    connect_timeout: An integer for ssh(1) connection timeout in seconds.
    control_persist: An integer for ssh(1) to keep master connection remain
              opened for given seconds, or None to not using master control.

  link_options example:
    {
      'link_class': 'SSHLink',
      'host': '1.2.3.4',
      'identity': '/path/to/identity/file'
    }
  """

  def __init__(self, host, user='root', port=22, identity=None,
               connect_timeout=5, control_persist=300):
    self.host = host
    self.user = user
    self.port = port
    self.identity = identity
    self.connect_timeout = connect_timeout
    self.control_persist = control_persist

    if self.identity is not None:
      try:
        self.identity = graphyte_utils.SearchConfig(self.identity)
        os.chmod(self.identity, 0o600)
      except Exception:
        logger.error('SSHLink: Failed to locate identity file "%s"',
                     self.identity)
        self.identity = None

  def __str__(self):
    return "SSH to %s@%s:%s with identity='%s'" % (
        self.user, self.host, self.port, self.identity)

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
               '-o', 'StrictHostKeyChecking=no',
               '-o', 'ConnectTimeout=%d' % self.connect_timeout]
    if self.control_persist is not None:
      options += ['-o', 'ControlMaster=auto',
                  '-o', 'ControlPath=/tmp/.ssh-%r@%h:%p',
                  '-o', 'ControlPersist=%s' % self.control_persist]
    if self.port:
      options += ['-P' if is_scp else '-p', str(self.port)]
    if self.identity:
      options += ['-i', self.identity]
    return sig, options

  def _ToUnixPath(self, path):
    if platform.system() != 'Windows':
      return path  # assume that we are in Unix machine already

    path = os.path.abspath(path)
    drive, path = os.path.splitdrive(path)
    return '/' + drive[0] + path.replace(os.path.sep, '/')

  def Push(self, local, remote):
    """See DUTLink.Push"""
    remote_sig, options = self._Signature(True)
    local = self._ToUnixPath(local)
    return subprocess.check_call(['scp'] + options +
                                 [local, '%s:%s' % (remote_sig, remote)])

  def Pull(self, remote, local=None):
    """See DUTLink.Pull"""
    if local is None:
      with UnopenedTemporaryFile() as path:
        self.Pull(remote, path)
        with open(path) as f:
          return f.read()

    local = self._ToUnixPath(local)
    remote_sig, options = self._Signature(True)
    subprocess.check_call(['scp'] + options +
                          ['%s:%s' % (remote_sig, remote), local])

  def _StartWatcher(self, subproc):
    watcher = self.__class__.ControlMasterWatcher(self)
    watcher.Start()  # make sure the watcher is running
    watcher.AddProcess(subproc.pid, os.getpid())

  def Shell(self, command, stdin=None, stdout=None, stderr=None):
    """See DUTLink.Shell"""
    remote_sig, options = self._Signature(False)

    if isinstance(command, six.string_types):
      # since the shell command is passed through SSH client,
      # the entire command is argument for SSH command
      # e.g. command = 'VAR=xxx cmd arg0 arg1...'
      # will become: 'ssh' <SSH OPTIONS> 'VAR=xxx' 'cmd' 'arg0' 'arg1' ...
      command = shlex.split(command)
    else:
      command = [pipes.quote(c) for c in command]
    command = ['ssh'] + options + [remote_sig] + command
    shell = False

    logger.debug('SSHLink: Run [%r]', command)
    close_fds = True
    if (platform.system() == 'Windows' and
        (stdin, stdout, stderr) != (None, None, None)):
      close_fds = False
    proc = subprocess.Popen(command, shell=shell, close_fds=close_fds,
                            stdin=subprocess.PIPE,
                            stdout=stdout, stderr=stderr)
    self._StartWatcher(proc)
    return proc

  def IsReady(self):
    """See DUTLink.IsReady"""
    try:
      return subprocess.call(['ping', '-w', '1', '-c', '1', self.host]) == 0
    except ClientNotExistError:
      return False

  class ControlMasterWatcher(object):
    __metaclass__ = type_utils.Singleton

    def __init__(self, link_instance):
      assert isinstance(link_instance, SSHLink)

      self._link = link_instance
      self._thread = threading.Thread(target=self.Run)
      self._proc_queue = queue.Queue()

      self._user = self._link.user
      self._host = self._link.host
      self._port = self._link.port
      self._link_class_name = self._link.__class__.__name__

    def IsRunning(self):
      if not self._thread:
        return False
      if not self._thread.is_alive():
        self._thread = None
        return False
      return True

    def Start(self):
      if self.IsRunning():
        return

      if self._link.control_persist is None:
        logger.debug('%s %s@%s:%s is not using control master, don\'t start',
                     self._link_class_name, self._user, self._host, self._port)
        return

      self._thread = process_utils.StartDaemonThread(target=self.Run)

    def AddProcess(self, pid, ppid=None):
      """Add an SSH process to monitor.

      If any of added SSH process is still running, ControlMasterWatcher will
      keep monitoring network connectivity.  If network is down, control master
      will be killed.

      Args:
        pid: PID of process using SSH
        ppid: parent PID of given process
      """
      if not self.IsRunning():
        logger.warning('Watcher is not running, %d is not added', pid)
        return
      self._proc_queue.put((pid, ppid))

    def Run(self):
      logger.info('start monitoring control master')

      # an alias to prevent duplicated pylint warnings
      # pylint: disable=protected-access
      _GetLinkSignature = self._link._Signature

      def _IsControlMasterRunning():
        sig, options = _GetLinkSignature(False)
        return subprocess.call(
            ['ssh', '-O', 'check'] + options + [sig, 'true'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE) == 0

      def _StopControlMaster():
        sig, options = _GetLinkSignature(False)
        subprocess.call(['ssh', '-O', 'exit'] + options + [sig, 'true'])

      def _CallTrue():
        sig, options = _GetLinkSignature(False)
        proc = subprocess.Popen(['ssh'] + options + [sig, 'true'])
        time.sleep(1)
        returncode = proc.poll()
        if returncode != 0:
          proc.kill()
          return False
        else:
          return True

      def _PollingCallback(is_process_alive):
        if not is_process_alive:
          return True  # returns True to stop polling

        try:
          if not _IsControlMasterRunning():
            logger.info('control master is not running, skipped')
            return

          if not _CallTrue():
            logger.info('loss connection, stopping control master')
            _StopControlMaster()
        except Exception:
          logger.info('monitoring %s to %s@%s:%s',
                      self._link_class_name,
                      self._user, self._host, self._port, exc_info=True)

      while True:
        # get a new process from queue to monitor
        # since Queue.get will block if queue is empty, we don't need to sleep
        pid, ppid = self._proc_queue.get()
        logger.debug('start monitoring control master until %d terminates', pid)

        sync_utils.PollForCondition(
            lambda: process_utils.IsProcessAlive(pid, ppid),
            condition_method=_PollingCallback,
            timeout_secs=None,
            poll_interval_secs=1)

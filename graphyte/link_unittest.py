#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import subprocess
import tempfile
import unittest

import graphyte_common  # pylint: disable=unused-import
from graphyte import link


class LoadLinkTest(unittest.TestCase):
  def testLoadSSHLink(self):
    link_options = {
        'link_class': 'SSHLink',
        'host': '1.2.3.4',
        'identity': '/fake/path'}
    link_instance = link.Create(link_options)
    self.assertTrue(isinstance(link_instance, link.DeviceLink))

  def testLoadADBLink(self):
    link_options = {
        'link_class': 'ADBLink'}
    link_instance = link.Create(link_options)
    self.assertTrue(isinstance(link_instance, link.DeviceLink))

  def testLoadUnknownLink(self):
    link_options = {
        'link_class': 'UNKNOWN'}
    with self.assertRaises(link.LinkOptionsError):
      link.Create(link_options)


class ShellAPITest(unittest.TestCase):
  def setUp(self):
    self.link_instance = link.DeviceLink()
    self.link_instance.Shell = self._MockShell
    self.temp_fd, self.temp_file = tempfile.mkstemp(suffix='.sh')

  def tearDown(self):
    os.close(self.temp_fd)
    if os.path.exists(self.temp_file):
      os.remove(self.temp_file)

  def _MockShell(self, command, stdin=None, stdout=None, stderr=None):
    return subprocess.Popen(command, stdin=stdin, stdout=stdout, stderr=stderr)

  def _WriteScript(self, script):
    os.write(self.temp_fd, script.encode('utf-8'))

  def testNormalCall(self):
    self._WriteScript('exit 0')

    ret = self.link_instance.Call(['sh', self.temp_file])
    self.assertEquals(0, ret)
    ret = self.link_instance.CheckCall(['sh', self.temp_file])
    self.assertEquals(0, ret)

  def testErrorCall(self):
    self._WriteScript('exit 1')

    ret = self.link_instance.Call(['sh', self.temp_file])
    self.assertEquals(1, ret)
    with self.assertRaises(subprocess.CalledProcessError):
      ret = self.link_instance.CheckCall(['sh', self.temp_file])

  def testNormalOutput(self):
    self._WriteScript('echo "hello"')

    ret = self.link_instance.CallOutput(['sh', self.temp_file])
    self.assertEquals('hello\n', ret)
    ret = self.link_instance.CheckOutput(['sh', self.temp_file])
    self.assertEquals('hello\n', ret)

  def testErrorOutput(self):
    self._WriteScript('echo "hello"; exit 1')

    ret = self.link_instance.CallOutput(['sh', self.temp_file])
    self.assertEquals(None, ret)
    with self.assertRaises(subprocess.CalledProcessError):
      ret = self.link_instance.CheckOutput(['sh', self.temp_file])

  def testCallWithStandardStream(self):
    self._WriteScript('read a; echo "output $a"; >&2 echo "error $a"')

    with tempfile.NamedTemporaryFile() as stdin, \
        tempfile.NamedTemporaryFile() as stdout, \
        tempfile.NamedTemporaryFile() as stderr:
      stdin.write(b'hello')
      stdin.flush()
      stdin.seek(0)
      ret = self.link_instance.Call(['sh', self.temp_file], stdin=stdin,
                                    stdout=stdout, stderr=stderr)
      self.assertEqual(0, ret)
      stdout.seek(0)
      stderr.seek(0)
      out_str = stdout.read()
      err_str = stderr.read()
      self.assertEqual(b"output hello\n", out_str)
      self.assertEqual(b"error hello\n", err_str)

if __name__ == '__main__':
  unittest.main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from . import link


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

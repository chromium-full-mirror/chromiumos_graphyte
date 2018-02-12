#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Unit tests for SCPI link module.

It starts a local server to mock the test equipment.
"""

import logging
import threading
import unittest

import graphyte_common  # pylint: disable=unused-import
from graphyte.links.scpi import SCPILink
from graphyte.links.scpi_mock import MockServerHandler
from graphyte.links.scpi_mock import MockTestServer

_LOCALHOST = '127.0.0.1'
_ARBITRARY_UNUSED_PORT = 0

class SCPITest(unittest.TestCase):
  EXPECTED_MODEL = 'FAKE_MODEL'

  def setUp(self):
    self.mock_server, server_port = self._StartMockServer()
    self.scpi_link = SCPILink(host=_LOCALHOST, port=server_port)
    self.scpi_link.Open()

  def tearDown(self):
    self.mock_server.shutdown()

  def _StartMockServer(self):
    """Starts a thread for the mock equipment."""
    MockServerHandler.ResetLookup()
    MockServerHandler.AddLookup('*CLS', None)
    MockServerHandler.AddLookup('*IDN?', self.EXPECTED_MODEL + '\n')
    mock_server = MockTestServer((_LOCALHOST, _ARBITRARY_UNUSED_PORT),
                                 MockServerHandler)
    server_port = mock_server.server_address[1]
    # pylint: disable=E1101
    server_thread = threading.Thread(target=mock_server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    logging.info('Server loop running in thread %s with port %d',
                 server_thread.name, server_port)
    return (mock_server, server_port)

  def testBasicConnect(self):
    self.assertTrue(self.scpi_link.IsReady())

  def testSend(self):
    self.assertEqual(self.scpi_link.CheckCall('*CLS'), 0)

  def testQuery(self):
    self.assertEqual(self.scpi_link.CheckOutput('*IDN?'), self.EXPECTED_MODEL)

if __name__ == '__main__':
  unittest.main()

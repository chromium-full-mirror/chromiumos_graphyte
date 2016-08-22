# Copyright 2016 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Utility functions to mock SCPI device over TCP.

Example Usage:
  MockServerHandler.AddLookup(r'*CLS', None)
  SetupLookupTable()
  SERVER_PORT = 5025
  MockTestServer(('0.0.0.0', SERVER_PORT), MockServerHandler).serve_forever()
"""

import logging
import inspect
import re
import types
import SocketServer


class MockTestServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
  allow_reuse_address = True


class MockServerHandler(SocketServer.StreamRequestHandler):
  """A mocking handler for socket.

  This handler responses client based on its pre-defined lookup table.
  Lookup table is a list of tuple where the first of each tuple is a regular
  expression and the second is response. Response could be one of None, string
  or function.

  Exceptions will be raised if input cannot match any of the regular expression
  from keys.
  """
  responses_lookup = list()

  @classmethod
  def ResetLookup(cls):
    cls.responses_lookup = list()

  @classmethod
  def AddLookup(cls, request, response):
    """Add a request-response pair into the lookup table.

    Args:
      request: A string or a compiled regular expression object.
      response: None, a string or a function.
    """
    # Check if the response is one of the known types.
    is_known_types = False
    if (isinstance(response, types.StringType) or
        isinstance(response, types.NoneType)):
      is_known_types = True
    elif inspect.isfunction(response) or inspect.ismethod(response):
      is_known_types = True
    assert is_known_types, (
        'type %r of response is not supported' % type(response))
    cls.responses_lookup.append((request, response))

  def __init__(self, *args, **kwargs):
    self.lookup = list(self.responses_lookup)
    SocketServer.StreamRequestHandler.__init__(self, *args, **kwargs)

  def handle(self):
    regex_type = type(re.compile(''))
    while True:
      line = self.rfile.readline().rstrip('\r\n')
      if not line:
        break
      for rule, response in self.lookup:
        if isinstance(rule, str) and line == rule:
          logging.info('Input %r matched.', line)
        elif isinstance(rule, regex_type) and rule.match(line):
          logging.info('Input %r matched with regexp %s', line, rule.pattern)
        else:
          continue

        if inspect.isfunction(response) or inspect.ismethod(response):
          response = response(line)
        if isinstance(response, types.StringType):
          self.wfile.write(response)
        break  # Only the first match will be used.
      else:
        raise ValueError('Input %r is not matching any.' % line)

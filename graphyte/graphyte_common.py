# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""A helper module to set up sys.path so that cros.factory.* can be located."""

import os
import sys


def _GetPackagePath():
  # graphyte_common.py is located at the top level of Graphyte code, e.g.,
  # ./graphyte/graphyte/graphyte_common.py. The package path is the parent
  # folder, which is ./graphyte.
  filepath = os.path.realpath(__file__.replace('.pyc', '.py'))
  top_dir = os.path.dirname(filepath)
  package_dir = os.path.dirname(top_dir)
  return package_dir

def _AddToSysPath(path):
  if path is None:
    return
  if path in sys.path:
    return
  sys.path.insert(0, path)

# For platforms without symlink (i.e., Windows), we need to derive the top level
# by environment variable.
_AddToSysPath(os.getenv('GRAPHYTE_PY_MAIN', _GetPackagePath()))

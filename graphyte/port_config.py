#!/usr/bin/python
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Handles the port config, including the port mapping and the pathloss.

We load the port config from json file, which format is:
{
  <component_name>: [ // List is represented for the multiple antenna
    { // First antenna
      TX: {
        port_mapping: <RF name:port number>,
        pathloss: [<pathloss csv file>, <pathloss title>]
      },
      RX: {
        port_mapping: <RF name:port number>,
        pathloss: [<pathloss csv file>, <pathloss title>]
      }
    }
  ]
}

Then we load the pathloss from the corresponding csv file.
The format of csv is:
  'title',   <frequency 1>, <frequency 2>, ...
  <title 1>, [pathloss 1],  [pathloss 2],  ...
  <title 2>, [pathloss 1],  [pathloss 2],  ...

If the value is empty, we just ignore it. For example:
  'title',2402,2404,2406
  'path1',20.0,,19.9
  'path2',21.0,20.3,

It means that path1 is {2402: 20.0, 2406: 19.9},
path2 is {2402: 21.0, 2404: 20.3}.
"""

from __future__ import print_function

import csv
import json
import math
import os
import sys

import graphyte_common  # pylint: disable=unused-import
from graphyte.default_setting import logger
from graphyte.utils.graphyte_utils import SearchConfig

class PortConfig(object):
  def __init__(self, config_file=None, search_dirs=None):
    self.config_dir = None
    self.port_config = None
    self._pathloss_table = {}
    if config_file:
      self.LoadConfigFile(config_file, search_dirs)

  def LoadConfigFile(self, config_file, search_dirs):
    file_path = SearchConfig(config_file, search_dirs)
    self.config_dir = os.path.dirname(file_path)
    logger.info('Load port config file: %s', file_path)
    with open(file_path, 'r') as f:
      config = json.load(f)
    self.port_config = config['port_config']

    # Load the pathloss table for each antenna
    for component_config in self.port_config.values():
      for antenna_config in component_config:
        for config_table in antenna_config.values():
          filename, title = config_table['pathloss']
          config_table['pathloss'] = self.LoadPathloss(filename, title)

  def LoadPathloss(self, filename, title):
    """Lazy loading the pathloss file."""
    if filename not in self._pathloss_table:
      self._pathloss_table[filename] = {}
      with open(SearchConfig(filename, self.config_dir), 'r') as csv_file:
        for table in csv.DictReader(csv_file):
          _title = table['title']
          del table['title']
          table = self._ConvertPathloss(table)
          if not table:
            raise ValueError('%s Pathloss %s is empty.' % (filename, _title))
          self._pathloss_table[filename][_title] = table

    if title not in self._pathloss_table[filename]:
      raise ValueError('Pathloss %s is not found in %s' % (title, filename))
    return self._pathloss_table[filename][title]

  def _ConvertPathloss(self, pathloss):
    """Converts a dict to a PathlossTable.

    Filters the empty entry, converts the frequency to int, and converts
    pathloss to float.
    """
    ret = {}
    for key, value in pathloss.items():
      if not value:
        continue
      ret[int(key)] = float(value)
    return PathlossTable(ret)

  def QueryPortConfig(self, component_name, test_type):
    """Returns the port config of the certain component.

    Args:
      component_name: the coponent name.
      test_type: 'TX' or 'RX'

    Return:
      List of the port config, for multiple antenna.
    """
    try:
      return [antenna_config[test_type]
              for antenna_config in self.port_config[component_name]]
    except KeyError as ex:
      logger.exception('There is no component "%s", TX/RX "%s" in port config',
                       component_name, test_type)
      raise ex

  def GetPortConfig(self, component_name, test_type, antenna_idx=0):
    try:
      return self.port_config[component_name][antenna_idx][test_type]
    except KeyError as ex:
      logger.exception('There is no component "%s", antenna_idx "%s",'
                       'TX/RX "%s" in port config',
                       component_name, antenna_idx, test_type)
      raise ex

  def GetPortMapping(self, **kwarg):
    return self.GetPortConfig(**kwarg)['port_mapping']

  def GetPathloss(self, **kwarg):
    return self.GetPortConfig(**kwarg)['pathloss']

  def GetIterator(self):
    return self.port_config.items()


class PathlossTable(object):
  """The pathloss table which can calculate the pathloss by frequency.

  The format is a dict which key is frequency unit in MHz, and the value is
  power loss in dB.

  Usage:
    table = PathlossTable({2000: 1.0, 2400: 3.1})
    pathloss = table[2014]
  """
  def __init__(self, table):
    self.table = table

  def __nonzero__(self):
    return len(self.table) > 0

  __bool__ = __nonzero__

  def __getitem__(self, freq):
    """Returns the pathloss of the frequency.

    If the frequency is recorded at the table, then return the value directly.
    If not, calculate the value using the linear interpolation with the nearest
    points.

    Args:
      freq: the frequency unit in MHz, int type.
    """
    if not self.table:
      raise KeyError('Table is empty.')
    if not isinstance(freq, int):
      raise TypeError('Frequency should be int type')
    if freq <= 0:
      raise KeyError('Frequency cannot be negative.')
    if freq in self.table:
      return self.table[freq]

    try:
      upper_dist = math.inf
      lower_dist = math.inf
    except AttributeError:
      upper_dist = sys.maxint
      lower_dist = sys.maxint
    upper_freq = None
    lower_freq = None
    for k in self.table:
      if k > freq and k - freq < upper_dist:
        upper_dist = k - freq
        upper_freq = k
      elif k < freq and freq - k < lower_dist:
        lower_dist = freq - k
        lower_freq = k

    if upper_freq is None:
      return self.table[lower_freq]
    if lower_freq is None:
      return self.table[upper_freq]

    loss = (self.table[upper_freq] * lower_dist +
            self.table[lower_freq] * upper_dist) / (lower_dist + upper_dist)
    return loss


def main():
  port_config = PortConfig('sample_port_config.json')
  for component_name, antennas_config in port_config.GetIterator():
    print('Component: %s' % component_name)
    for antenna_idx, antenna_config in enumerate(antennas_config):
      print(' Antenna %d:' % antenna_idx)
      for test_type in ['TX', 'RX']:
        print('  port Config for %s: ' % test_type)
        print('  pathloss: %s' % antenna_config[test_type]['pathloss'])
        print('  port_mapping: %s' % antenna_config[test_type]['port_mapping'])

  print(port_config.QueryPortConfig('WLAN_2G', 'TX'))


if __name__ == '__main__':
  main()

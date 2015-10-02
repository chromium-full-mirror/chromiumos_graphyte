#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Handle the port config, including the port mapping and the pathloss.
We load the port config from yaml file, which format is:
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
The format of csv is
  'title',   <frequency 1>, <frequency 2>, ...
  <title 1>, [pathloss 1],  [pathloss 2],  ...
  <title 2>, [pathloss 1],  [pathloss 2],  ...
If the value is empty, we just ignore it. For example:
  'title',2402,2404,2406
  'path1',20.0,,19.9
  'path2',21.0,20.3,
It means that path1 is {2402: 20.0, 2406: 19.9},
path2 is {2402: 21.0, 2404: 20.3}
"""

import csv
import logging
import yaml


class PortConfig(object):
  def __init__(self, config_file):
    with open(config_file, 'r') as f:
      config = yaml.load(f)
    self.port_config = config['port_config']

    # Load the pathloss table for each antenna
    self._pathloss_table = {}
    for component_config in self.port_config.itervalues():
      for antenna_config in component_config:
        for config_table in antenna_config.itervalues():
          filename, title = config_table['pathloss']
          config_table['pathloss'] = self.Loadpathloss(filename, title)

  def Loadpathloss(self, filename, title):
    """Lazy loading the pathloss file."""
    if filename not in self._pathloss_table:
      self._pathloss_table[filename] = {}
      with open(filename, 'r') as csv_file:
        for table in csv.DictReader(csv_file):
          title = table['title']
          del table['title']
          self._pathloss_table[filename][title] = self._ConvertPathloss(table)
    return self._pathloss_table[filename].get(title, None)

  def _ConvertPathloss(self, pathloss):
    """Filter the empty entry, then convert the frequency to int, and convert
    pathloss to float."""
    ret = {}
    for key, value in pathloss.iteritems():
      if not value:
        continue
      ret[int(key)] = float(value)
    return ret

  def QueryPortConfig(self, component_name, tx_or_rx):
    """Return the port config of the certain component.
    Args:
      component_name: the coponent name.
      tx_or_rx: 'TX' or 'RX'
    Return:
      List of the port config, for multiple antenna.
    """
    try:
      return [antenna_config[tx_or_rx]
              for antenna_config in self.port_config[component_name]]
    except KeyError as ex:
      logging.exception('There is no component "%s", TX/RX "%s" in port config',
                        component_name, tx_or_rx)
      raise ex

  def GetIterator(self):
    return self.port_config.iteritems()


def main():
  port_config = PortConfig('sample_port_config.yaml')
  for component_name, antennas_config in port_config.GetIterator():
    print 'Component: %s' % component_name
    for antenna_idx, antenna_config in enumerate(antennas_config):
      print ' Antenna %d:' % antenna_idx
      for tx_or_rx in ['TX', 'RX']:
        print '  port Config for %s: ' % tx_or_rx
        print '  pathloss: %s' % antenna_config[tx_or_rx]['pathloss']
        print '  port_mapping: %s' % antenna_config[tx_or_rx]['port_mapping']

  print port_config.QueryPortConfig('WLAN_2G', 'TX')


if __name__ == '__main__':
  main()

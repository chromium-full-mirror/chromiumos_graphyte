#!/usr/bin/python
"""The testplans module.

The test plan module will go through the CVS file (the format of which is
defined below) and put them to a dictionary. The testplan can also use the
dut plugin and instrument plugin to verify the port mapping and the names used
in the testplan.

The format of the CSV file.
The very first row and first column should indivate the version number of the
CSV file format (just integers as 1, 2, 3,....)
The first col is empty for all the rows which contain a test case.
The first col of first row has version number.
The rows with labels will have the first column with some single character
string like # or @ etc. This tells the CVS reader that its a line with labels.
The labels are read and used a dictionary labels.
We probably can add a line starting with a comment character. If that appears
in the first column, we ignore the rest of the line.

However, right not this module hardcodes only one test case
"""


class TestPlan(object):
  def __init__(self):
    # When implementation is complete, we will actually read the testplan file
    # in the constructor.
    self.tp = None

  def GetNextTest(self):
    """
    Returns the next test case from the test plan. Fasle otherwise.

    The return value is a tuple. First element is the return value and the
    second element is a dictionary with the values from the CSV file
    """
    self.tp = {
        'Component Name': 'wlan_5g',
        'Group': 'RF',
        'Class':'WLAN',
        'Standard':'AC',
        'Format':'OFDM',
        'Test Type':'Tx_MOD',
        'Center Freq':5210,
        'Bandwidth':80,
        'Date Rate':'MCS9',
        'NSS':1,
        'Chain Mask':1,
        'Power Level':20,
        'Rx Num Packets':0
        }
    return (True, self.tp)

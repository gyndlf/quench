# -*- coding: utf-8 -*-
"""
Created Sat Jun 01 11:16 pm 2024

Fake class for the Si CMOS. (For code linting purposes)

@author: jzingel
"""

from qcodes_measurements.device.gate import Gate


class CMOSfake:
    """
    A dummy class that contains the gates of the Si CMOS device. Does nothing
    """
    def __init__(self):
        self.ST = Gate()
        self.P1 = Gate()
        self.P2 = Gate()
        self.SLB = Gate()
        self.SRB = Gate()
        self.SETB = Gate()


class GBfake:
    """
    Dummy class that fakes the gooseberry gates
    """
    def __init__(self):
        self.VICL = Gate()


if __name__ == '__main__':
    si = CMOSfake()
    si.ST()
    si.ST(1.2)




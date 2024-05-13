# -*- coding: utf-8 -*-
"""
Created on Fri May 10 15:23:43 2024

Proportional based feedback. Keep a value fixed where desired

@author: jzingel
"""

from qcodes_measurements.device.gate import Gate
from qcodes.instrument_drivers.stanford_research.SR860 import SR860

def feedback(gate: Gate, lockin: SR860, target: float, stepsize: float):
    """
    Proportionally change the gate based on the distance the lockin is from the target   
    """
    r = lockin.R()
    
    error = (target - r) * stepsize
    g = gate() + error
    
    if g > 2.0:
        raise Exception(f"Aborting; correction voltage exceeds threshold, {g} > 2.0")
    elif g < 1.0:
        raise Exception(f"Aborting; correction voltage fails to meet threshold, {g} < 1.0")
    else:
        print(f"Adjusted {gate.name} voltage by {error} V (did not set)")

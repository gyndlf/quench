# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 14:04:24 2024

Fix the SET to be constant regardless of cross talk from other gates

@author: jzingel
"""

from qcodes_measurements.device.gate import Gate
from qcodes.instrument_drivers.stanford_research.SR860 import SR860
import numpy as np
import time


def waitforfeedback(gate: Gate, lockin: SR860, target: float, tol: float = 1e-12, stepsize=0.001, slope="down"):
    """
    Proportionally change the gate voltage based on how far away we are until we are within threshold
    Wait until this occurs.

    Slope = "up" or "down". Indicates the direction of the Coulomb potential that we're locked onto and directs which direction the feedback should operate in.
    """

    if slope == "up":
        sgn = 1
    elif slope == "down":
        sgn = -1
    else:
        raise (f"Unknown slope '{slope}'. Must be either 'up' or 'down'")

    waiting = np.abs(lockin.R() - target) > tol
    while waiting:
        r = lockin.R()

        error = (target - r) * sgn
        adjust = error * stepsize / target  # normalised error func

        if np.abs(error) < tol:
            break  # early exiting

        # print(f"Difference of {error} adjusting by {adjust}")
        g = gate() + adjust  # new gate voltage

        if g > 4.0:  # upper bound
            print(f"Aborting feedback: correction voltage exceeds threshold, {g} > 4.0. No change to ST.")
            break
        elif g < 3.5:  # lower bound
            print(f"Aborting feedback: correction voltage fails to meet threshold, {g} < 3.5. No change to ST.")
            break
        else:
            # print(f"Adjusting {gate.name} voltage to {g} V")
            gate(g)
            time.sleep(0.15)  # delay after changing ST


def feedback(gate: Gate, lockin: SR860, target: float, stepsize=0.001, slope="down"):
    """
    Apply proportional based feedback always.
    This will result in some jumping around near the target but should hopefully not be too much.

    Parameters
    ----------
    target : float
        lockin.R value to match
    stepsize : TYPE, optional
        How large a step should be taken in the direction of the error. The default is 0.001.
    slope : TYPE, optional
        Indicates the direction of the Coulomb potential that we're locked onto and directs which direction the feedback should operate in. Either "up" or "down". The default is "down".
    """
    if slope == "up":
        sgn = 1
    elif slope == "down":
        sgn = -1
    else:
        raise (f"Unknown slope '{slope}'. Must be either 'up' or 'down'")

    r = lockin.R()
    error = (target - r) * sgn
    adjust = error / target * stepsize  # normalised error func
    g = gate() + adjust  # new gate voltage

    if g > 4.0:  # upper bound
        print(f"Aborting feedback: correction voltage exceeds threshold, {g} > 4.0. No change to ST.")
    elif g < 3.5:  # lower bound
        print(f"Aborting feedback: correction voltage fails to meet threshold, {g} < 3.5. No change to ST.")
    else:
        gate(g)


class Feedback():
    """
    Continuously apply feedback while taking into account the history of the applications
    """
    def __init__(self, gate: Gate, lockin: SR860, target: float, stepsize=0.001, slope="down"):
        self.gate = gate
        self.lockin = lockin
        self.target = target
        self.stepsize = stepsize

        if slope == "up":
            self.sgn = 1
        elif slope == "down":
            self.sgn = -1
        else:
            raise (f"Unknown slope '{slope}'. Must be either 'up' or 'down'")

        self.clearhistory()

    def dofeedback(self):
        """Apply one round of feedback"""

    def clearhistory(self):
        """Clear the history of previous feedback actions"""



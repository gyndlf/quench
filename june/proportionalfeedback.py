# -*- coding: utf-8 -*-
"""
Created Sat Jun 06 10:23 pm 2024

Apply proportional feedback. Very simple PID algorithm.

Definition file.

@author: jzingel
"""

from qcodes_measurements.device.gate import Gate
from qcodes.instrument_drivers.stanford_research.SR860 import SR860
import numpy as np
import time

# These methods are lifted from development in may/load_e.py
# It was found that approximating the coulomb blocking as linear is sufficient. No need for higher degree polynomials.


def feedback(ST: Gate, lockin: SR860, target: float, stepsize, slope="up", max_ST=3.5, min_ST=3.0):
    """
    Apply proportional feedback. Adjust ST to make lockin.R() match target.

    Choose slope from "up" and "down" depending on the slope of the coulomb peak we are locking onto.

    Choose an appropriate step size; too small and the feedback is not enough to overcome gate crosstalk.
    Too large and there is excessive oscillations around the target. Around 12e-4 usually works well.
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
    g = ST() + adjust  # new gate voltage

    if g > max_ST:  # upper bound
        print(f"Aborting feedback: correction voltage exceeds threshold, {g} > {max_ST}. No change to ST.")
    elif g < min_ST:  # lower bound
        print(f"Aborting feedback: correction voltage fails to meet threshold, {g} < {min_ST}. No change to ST.")
    else:
        ST(g)
        time.sleep(0.5)


def gettotarget(ST: Gate, lockin: SR860, target: float, slope="up", stepsize=0.001, tol: float = 0.001e-10):
    """
    Super handy function that runs feedback as much as necessary until we are within target
    """
    print(f"Target = {target:.4e}, tol = {tol}, initial ST = {ST()}")
    while np.abs(lockin.R() - target) > tol:
        feedback(ST, lockin, target, stepsize, slope=slope)
        print(f"\rST = {ST():.4e}, lockin = {lockin.R():.4e}, delta = {np.abs(lockin.R() - target):.4e}", end="")
        time.sleep(0.1)
    print(f"\nFinal ST = {ST()}")

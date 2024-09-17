# -*- coding: utf-8 -*-
"""
Controller class for feedback to package everything in one place

Based upon functions found in may/dc.ipynb

Created on Mon Sep 16 11:20 2024

@author: james
"""

import time
import numpy as np

from qcodes.instrument_drivers.stanford_research.SR860 import SR860  # Lockin
from MDAC import MDAC
from qcodes_measurements.device import Device, Gate


class Retort:
    def __init__(self, target, stepsize=5e-4, tol=1e-11, slope="up", bounds=(3.0, 3.8)):
        """Setup the feedback parameters"""
        self.target = target
        self.stepsize = stepsize
        self.tol = tol

        if slope == "up":
            self.slope = 1
        elif slope == "down":
            self.slope = -1
        else:
            raise (f"Unknown slope '{slope}'. Must be either 'up' or 'down'")

        self.upper_bound = bounds[1]
        self.lower_bound = bounds[0]

    def feedback(self, si: Device, lockin: SR860, stepsize=None):
        """Perform one step of feedback"""
        stepsize = stepsize if stepsize is not None else self.stepsize

        r = lockin.R()
        error = (self.target - r) * self.slope
        adjust = error / self.target * stepsize  # normalised error func
        g = si.ST() + adjust  # new gate voltage

        if g > self.upper_bound:  # upper bound
            print(f"Aborting feedback: correction voltage exceeds threshold, {g} > {self.upper_bound}. No change to ST.")
        elif g < self.lower_bound:  # lower bound
            print(f"Aborting feedback: correction voltage fails to meet threshold, {g} < {self.lower_bound}. No change to ST.")
        #elif np.abs(r-target) > 0.03e-10:  # take a small step if good
        #    print(f"small step {np.abs(r-target)}")
        #    gate(gate() + adjust/4)
        #    time.sleep(0.5)
        else:
            si.ST(g)
            time.sleep(0.5)

    def get_to_target(self, si: Device, lockin: SR860, progress=True, stepsize=10e-4):
        """Run feedback repeatably until we are within the desired tolerance"""
        #0if progress:
        #    print(f"Target = {self.target:.4e}, tol = {self.tol}, initial ST = {si.ST()}")
        while np.abs(lockin.R() - self.target) > self.tol:
            self.feedback(si, lockin, stepsize=stepsize)
            if progress:
                print(f"\rST = {si.ST():.4e}, lockin = {lockin.R():.4e}, delta = {np.abs(lockin.R()-self.target):.4e}", end="")
            time.sleep(0.1)
        if progress:
            print("")
            #print(f"\nFinal ST = {si.ST()}")

    def move_with_feedback(self, si: Device, lockin: SR860, gate: Gate, end: float, dx: float = 0.01, progress=True):
        """Move a specific gate, running get_to_target() repeatably to maintain the same peak"""
        start = gate()
        if end < start:  # backwards!
            dx *= -1

        if progress:
            print(f"Target = {self.target:.4e}, tol = {self.tol}, initial ST = {si.ST()}")
        for v in np.arange(start, end+dx, dx):
            gate(v)
            time.sleep(0.5)
            if progress:
                print(f"\r{gate.name} = {gate():.4e}, ST = {si.ST():.4e}, lockin = {lockin.R():.4e}, delta = {np.abs(lockin.R()-self.target):.4e}", end="")
            self.get_to_target(si, lockin, progress=progress)
        if progress:
            print(f"\nFinal ST = {si.ST()}")
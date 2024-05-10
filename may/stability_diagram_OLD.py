# -*- coding: utf-8 -*-
"""
Created on Tue May  7 10:58:15 2024

Measure (and plot) a charge stability diagram.

Use proportional feedback to mitigate the SET bias produced by cross talk.

Referenced initially from april/sweep_12.py

@author: J Zingel
"""

from quench.libraries import broom
broom.sweep()

import numpy as np
from tqdm import tqdm
import time
import matplotlib.pyplot as plt

from qcodes import Station, Instrument

from monty import Monty
import MDAC

# Import the neighbouring files. In may/
import quench.may.dots as dots
from quench.may.custom_devices import connect_to_gb, newSiDot


#%% Connect to instruments

# close any open instruments 
try:
    mdac = Instrument.find_instrument("mdac")
    mdac.close()
except KeyError:
    print('Attempting to remove instrument with name mdac. Does not exist')
    
try:
    lockin = Instrument.find_instrument("sr860_top")
    lockin.close()
except KeyError:
    print("Cannot remove instrument with name sr860_top. Does not exist")

scfg = Station(config_file='measurements/system.yaml')

mdac = MDAC.MDAC('mdac', 'ASRL11::INSTR')
lockin = scfg.load_instrument('sr860_top')

# Create our custom MDAC mappings
gb_control_si = connect_to_gb(mdac)
si = newSiDot(mdac)

#%% Start Experiment

experiment = {
    "desc": "Load electrons into the double dots and attempt to measure charge stability diagrams (and other associated plots) from them."
}


monty = Monty("double dot.initial", experiment)

# optionally load the experiment here now
#monty = monty.loadexperiment()


#%% Initilise gates

dots.output_checker_all(gb_control_si)
dots.get_all_voltages(mdac)


#%% Setup SET tuning

# Position the SET such that we can detect when the regime changes and offset the effect...
# Do this later


#%% 1D SET scan to see regime we are in

# 1D sweep. Just to see if the peaks are actually still there

pts = 400

gate_range = np.linspace(3.46, 3.58, pts)

X = np.zeros((pts))
Y = np.zeros((pts))
R = np.zeros((pts))
P = np.zeros((pts))

parameters = {
    "desc": "Quick 1D scan of the SET over ST",
    "ST":   f"range from {gate_range[0]}v -> {gate_range[-1]}v, over {pts}pts",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    }

monty.newrun("1D scan", parameters)

with tqdm(total=pts) as pbar:
    for (j, ST_voltage) in enumerate(gate_range):
        si.ST(ST_voltage)
        time.sleep(0.05)  # wait longer than the lockin integration time
        
        X[j] = lockin.X()
        Y[j] = lockin.Y()
        R[j] = lockin.R()
        P[j] = lockin.P()
        
        pbar.update(1)

monty.save({"X": X, "Y": Y, "R": R, "P": P})

fig = plt.figure()
plt.plot(gate_range, R)
plt.xlabel("ST gate voltage")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("Current (R)")
monty.savefig(plt, "1D")

#%% Plot point we choose for our ST

# voltage of marker
st = 3.526
si.ST(st)  # reset to this point for future measurements
 
inx = np.argmin(np.abs(gate_range - st))  # find corresponding point

fig = plt.figure()
plt.plot(gate_range, R)
plt.plot(gate_range[inx], R[inx], "x", label=f"ST = {st}V")

plt.xlabel("ST gate voltage")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("Current (R)")
plt.legend()

#monty.savefig(plt, "1D")


#%% Load electrons

dots.loaddots(si, high=1.0)

#%% Flush electrons

dots.flushdots(si, low=1.0, high=1.9)

#%% 1D scan of P1

pts = 800
gate_range = np.linspace(1.85, 1.9, pts)[::-1]  # reverse order

X = np.zeros((pts))
Y = np.zeros((pts))
R = np.zeros((pts))
P = np.zeros((pts))

parameters = {
    "desc": "1D sweep one dot (without proportional feedback techniques)",
    "lockin_amplitude": "Set to 10uV",
    "ST":   f"Fixed at {si.ST()}V",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    "SETB": f"Fixed at {si.SETB()}V",
    "J": f"Fixed at ? V",
    "P1": f"Ranged from {gate_range[0]}V <- {gate_range[-1]}V in {pts} points",
    "P2": f"Fixed at {si.P2()}V",
    }

monty.newrun("P1 scan", parameters)

# Move to the start and wait a sec (for lockin to catchup)
si.P1(gate_range[0])
time.sleep(1.0)

with tqdm(total=pts) as pbar:
    for (j, p1) in enumerate(gate_range):
        si.P1(p1)
        time.sleep(0.3)  # wait longer than the lockin integration time
        
        X[j] = lockin.X()
        Y[j] = lockin.Y()
        R[j] = lockin.R()
        P[j] = lockin.P()
        
        pbar.update(1)

monty.save({"X": X, "Y": Y, "R": R, "P": P})

fig = plt.figure()
plt.plot(gate_range, R)
plt.xlabel("P1 gate voltage")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("Current (R)")
monty.savefig(plt, "1D")

#%% 1D scan of P2

pts = 400
gate_range = np.linspace(1.68, 1.72, pts)

X = np.zeros((pts))
Y = np.zeros((pts))
R = np.zeros((pts))
P = np.zeros((pts))

parameters = {
    "desc": "1D sweep one dot P (without proportional feedback techniques)",
    "lockin_amplitude": "Set to 10uV",
    "ST":   f"Fixed at {si.ST()}V",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    "SETB": f"Fixed at {si.SETB()}V",
    "J": f"Fixed at ? V",
    "P2": f"Ranged from {gate_range[0]}V -> {gate_range[-1]}V in {pts} points",
    "P1": f"Fixed at {si.P1()}V",
    }

monty.newrun("P2 scan", parameters)

# Move to the start and wait a sec (for lockin to catchup)
si.P2(gate_range[0])
time.sleep(0.5)

with tqdm(total=pts) as pbar:
    for (j, p2) in enumerate(gate_range):
        si.P2(p2)
        time.sleep(0.05)  # wait longer than the lockin integration time
        
        X[j] = lockin.X()
        Y[j] = lockin.Y()
        R[j] = lockin.R()
        P[j] = lockin.P()
        
        pbar.update(1)

monty.save({"X": X, "Y": Y, "R": R, "P": P})

fig = plt.figure()
plt.plot(gate_range, R)
plt.xlabel("P2 gate voltage")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("Current (R)")
monty.savefig(plt, "1D")

#%% P1 vs P2

# Num of points to sweep over
P1_pts = 200
P2_pts = 200

P1_range = np.linspace(1.8, 1.95, P1_pts)
P2_range = np.linspace(1.8, 1.95, P2_pts)

X = np.zeros((P1_pts, P2_pts))
Y = np.zeros((P1_pts, P2_pts))
R = np.zeros((P1_pts, P2_pts))
P = np.zeros((P1_pts, P2_pts))

parameters = {
    "desc": "See if we can see any charge stability lines without proportional feedback techniques.",
    "lockin_amplitude": "Set to 10uV",
    "ST":   f"Fixed at {si.ST()}V",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    "SETB": f"Fixed at {si.SETB()}V",
    "J": f"Fixed at ? V",
    "P1": f"Ranged from {P1_range[0]}V -> {P1_range[-1]}V in {P1_pts} points",
    "P2": f"Ranged from {P2_range[0]}V -> {P2_range[-1]}V in {P2_pts} points",
    }

monty.newrun("p1 vs p2", parameters)


with tqdm(total=P1_pts*P2_pts) as pbar:
    for (j, p1) in enumerate(P1_range):
        si.P1(p1)
        time.sleep(0.05)
        
        for (i, p2) in enumerate(P2_range):
            si.P2(p2)
            time.sleep(0.1)  # wait longer than the lockin integration time
            
            X[j, i] = lockin.X()
            Y[j, i] = lockin.Y()
            R[j, i] = lockin.R()
            P[j, i] = lockin.P()
            
            pbar.update(1)
            
        # Save each sweep
        #monty.snapshot(data={"X": X, "Y": Y, "R": R, "P": P})

monty.save({"X": X, "Y": Y, "R": R, "P": P})

fig = plt.figure()
plt.pcolor(P1_range, P2_range, R)
plt.colorbar()
plt.title(monty.identifier + "." + monty.runname)
plt.xlabel("P1 gate voltage")
plt.ylabel("P2 gate voltage")
monty.savefig(plt, "matrix")

#%% P1-P2 vs J


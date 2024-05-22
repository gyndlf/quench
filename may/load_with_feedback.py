# -*- coding: utf-8 -*-
"""
Created on Wed May 22 11:22:34 2024

Combine the previous files to load electrons into the dot and use feedback while doing so

controller.py + proportional_feedback_tests.py

@author: jzingel
"""

from quench.libraries import broom
broom.sweep()

import numpy as np
import matplotlib.pyplot as plt
import time
from qcodes import Station, Instrument
from scipy.signal import find_peaks
from tqdm import tqdm

from monty import Monty
import feedback
import swiper
import MDAC

# Import the neighbouring files. In may/
import may.dots as dots
from may.custom_devices import connect_to_gb, newSiDot


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
    "desc": "Load electrons into the dot while using feedback"
}

monty = Monty("double dot.with feedback", experiment)

dots.get_all_voltages(mdac)


#%% Quick 1D SET sweep 

# Get our surroundings

low = 3.8
high = 3.95
pts = 300

parameters = {
    "desc": "Quick 1D scan of the SET over ST",
    "ST":   f"range from {low}v -> {high}v, over {pts} pts",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    }

monty.newrun("1D SET sweep", parameters)
result = swiper.sweep1d(lockin,
               si.ST, low, high, pts, 
               delay_time=0.1, monty=monty)  # overlap points so we average


monty.save(result)

#%% Choose a good value for our feedback point

g_range = np.linspace(low, high, pts)
deriv = np.abs(np.diff(result["R"]))

peaks, _ = find_peaks(deriv, distance=30)
#peak = np.argmax(deriv)

fig = plt.figure()
plt.plot(g_range[:-1], deriv)
plt.plot(g_range[peaks], deriv[peaks], "x")
#plt.plot(g_range[peak], deriv[peak], "x")
plt.xlabel("ST gate voltage")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("Current derivative")
plt.legend()

print(peaks)

#%% Find the best ST voltage to use

# choose the appropriate peak here
peak = peaks[3]

st_start = g_range[peak]
fix_lockin = result['R'][peak]  # current value to lock in at

print(f"Best peak at inx = {peak}")
print(f"Corresponds to ST={st_start} and lockin={fix_lockin}")

fig = plt.figure()
plt.plot(g_range, result["R"])
plt.plot(g_range[peak], result["R"][peak], "x", label=f"Lockin = {fix_lockin} A")

plt.xlabel("ST gate voltage")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("Current (R)")
plt.legend()


#%% Position ST to match our point

# Position the ST to match the target
si.ST(low)  # reset to bottom of the sweep 
time.sleep(1)
si.ST(st_start)
time.sleep(5)
lockin.R()

#%% Lock in on target

target = fix_lockin  
tol = 0.001e-10

#swiper.waitforfeedback(si.ST, lockin, target, tol=tol)
print(f"Target = {target}")
while np.abs(lockin.R()-target) > tol:
    feedback.feedback(si.ST, lockin, target, stepsize=0.001, slope="down")
    time.sleep(0.1)
    print(lockin.R())

print(f"Final ST = {si.ST()}")


#%% Load electrons

dots.loaddots(si, high=1.0)

#%% Flush electrons

dots.flushdots(si, low=1.0, high=1.9)


#%% 1D scan of P1

low = 1.85
high = 1.9
points = 400
gate = si.P1

parameters = {
    "desc": "1D sweep one dot (without proportional feedback techniques)",
    "lockin_amplitude": "Set to 10uV",
    "ST":   f"Fixed at {si.ST()}V",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    "SETB": f"Fixed at {si.SETB()}V",
    "J": f"Fixed at ? V",
    "P1": f"Ranged from {low}V <- {high}V in {pts} points",
    "P2": f"Fixed at {si.P2()}V",
    }

monty.newrun("P1 scan", parameters)


# don't use swiper to make modifying the feedback easier

gate_range = np.linspace(low, high, points)
X = np.zeros((points))
Y = np.zeros((points))
R = np.zeros((points))
P = np.zeros((points))

# Move to the start and wait a second for the lockin to catchup
gate(gate_range[0])
time.sleep(2.0)

with tqdm(total=points) as pbar:
    for (j, g) in enumerate(gate_range):
        gate(g)
        time.sleep(0.1)
        X[j] = lockin.X()
        Y[j] = lockin.Y()
        R[j] = lockin.R()
        P[j] = lockin.P()
        pbar.update(1)
        
        # apply feedback
        feedback.feedback(si.ST, lockin, target, stepsize=0.001, slope="down")
        


swiper.plotsweep1d(gate_range, R, gate.name, monty)
monty.save({"X": X, "Y": Y, "R": R, "P": P})

#%% P1 vs P2

# Num of points to sweep over

low = 1.8 
high = 1.96
pts = 200

parameters = {
    "desc": "See if we can see any charge stability lines without proportional feedback techniques.",
    "lockin_amplitude": "Set to 10uV",
    "ST":   f"Fixed at {si.ST()}V",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    "SETB": f"Fixed at {si.SETB()}V",
    "J": f"Fixed at ? V",
    "P1": f"Ranged from {low}V -> {high}V in {pts} points",
    "P2": f"Ranged from {low}V -> {high}V in {pts} points",
    }

monty.newrun("p1 vs p2", parameters)

result = swiper.sweep2d(lockin,
                        si.P1, low, high, pts,
                        si.P2, low, high, pts,
                        monty=monty)

monty.save(result)


#%% Sweep ST vs SLB/SRB 

low = 1.9
high = 1.96
pts = 8

stlow = 3.75
sthigh = 3.8
stpts = 10

parameters = {
    "desc": "Sweep the SET over SLB and SRB to find a region that has good Coulomb blocking",
    "ST":   f"Ranged from {stlow}V -> {sthigh}V in {stpts} points",
    "SLB":  f"Ranged from {low}V -> {high}V in {pts} points",
    "SRB":  f"Ranged from {low}V -> {high}V in {pts} points",
    "SETB": f"Fixed at {si.SETB()}V",
    "P1": f"Fixed at {si.P1()}",
    "P2": f"Fixed at {si.P2()}",
    }

monty.newrun("st vs slb srb", parameters)

result = swiper.sweep2d(lockin,
                        [si.SLB, si.SRB], low, high, pts,
                        si.ST, stlow, sthigh, stpts,
                        delay_time=0.3, monty=monty, alternate_directions=True)

monty.save(result)


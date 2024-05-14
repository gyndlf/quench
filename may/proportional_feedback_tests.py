# -*- coding: utf-8 -*-
"""
Created on Mon May 13 16:09:24 2024

Test that the proportional feedback is working as expected

@author: jzingel
"""

# Inherited from stability_diagram_OLD.py

from quench.libraries import broom
broom.sweep()

import numpy as np
import matplotlib.pyplot as plt
import time

from qcodes import Station, Instrument

from monty import Monty
import swiper
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
    "desc": "Test what happens with crosstalk between gates. How much is our proportional based feedback useful?."
}

monty = Monty("SET.proportional tests", experiment)

dots.get_all_voltages(mdac)

#%% Quick 1D sweep

low = 3.75
high = 4.0
pts = 400

parameters = {
    "desc": "Quick 1D scan of the SET over ST",
    "ST":   f"range from {low}v -> {high}v, over {pts} pts",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    }

monty.newrun("1D SET sweep", parameters)
result = swiper.sweep1d(lockin,
               si.ST, low, high, pts, 
               delay_time=0.1, monty=monty)


monty.save(result)


#%% Setup the drift

# Position the ST to match the target

si.ST(3.86)

#%%

target = 1.6e-10
tol = 0.04e-10

swiper.waitforfeedback(si.ST, lockin, target, tol=tol)


#%% Watch the drift

# Position ST to match the target

feedbacks = 30  # apply PID every x minutes
length = 60*8  # time to run for (minutes)

parameters = {
    "desc": "Watch how the SET changes over time and our effects of proportional based feedback",
    "feedback": "with feedback"
    }

monty.newrun("watch SET drift", parameters)


drifts = np.zeros(length)
for i in range(length):
    time.sleep(60)
    
    drifts[i] = lockin.R()
    
    # Apply feedback
    if i % feedbacks == 0:
        monty.snapshot(drifts)
        swiper.waitforfeedback(si.ST, lockin, target, tol=tol)
     
plt.plot(drifts)
plt.plot([0, length], [target-tol, target-tol], color="orange")
plt.plot([0, length], [target, target], color="green")
plt.plot([0, length], [target+tol, target+tol], color="orange")
plt.xlabel("Time (minutes)")
plt.ylabel("Lockin")
plt.title(monty.identifier + "." + monty.runname)   
monty.savefig(plt, "history") 
    
monty.save(drifts)

#%%

low = 1.9
high = 1.96
pts = 100

stlow = 3.75
sthigh = 3.8
stpts = 100

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


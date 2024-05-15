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
from scipy.signal import find_peaks
from tqdm import tqdm

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

#%%

peak = peaks[2]

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


#%% Setup the drift

# Position the ST to match the target

si.ST(st_start)
time.sleep(5)
lockin.R()

#%% Choose target

target = lockin.R()  # since we averaged before, can't trust it exactly
#tol = 0.04e-10
tol = 0.01e-10

swiper.waitforfeedback(si.ST, lockin, target, tol=tol)

#%% Watch the drift (no action)

# Position ST to match the target

feedbacks = 30  # apply PID every x minutes
length = 60*14  # time to run for (minutes)

parameters = {
    "desc": "Watch how the SET changes over time and our effects of proportional based feedback",
    "feedback": "no feedback"
    }

monty.newrun("watch SET drift", parameters)


drifts = np.zeros(length)
for i in range(length):
    time.sleep(60)
    
    drifts[i] = lockin.R()
    
    # Apply feedback
    if i % feedbacks == 0:
        monty.snapshot(drifts)
        #swiper.waitforfeedback(si.ST, lockin, target, tol=tol)

#target = drifts[0]
plt.plot(drifts)
plt.plot([0, length], [target-tol, target-tol], color="orange")
plt.plot([0, length], [target, target], color="green")
plt.plot([0, length], [target+tol, target+tol], color="orange")
plt.xlabel("Time (minutes)")
plt.ylabel("Lockin")
plt.title(monty.identifier + "." + monty.runname)   
monty.savefig(plt, "history") 
    
monty.save(drifts)

#%% Watch the drift (with action via P1)

# Position ST to match the target FIRST

length = 60*5   # time to run for (seconds)

# Setup P1 sweep parameters
low = 1.9
high = 1.96
pts = 100  # between low -> high. 1 point per second (so this controls sweep speed)

parameters = {
    "desc": "Attempt to fix current (via changing ST) when sweeping over P1",
    "feedback": "with feedback",
    "P1": f"Sweeping from {low} to {high} over {pts} points. 1 point per second",
    "tol": f"tolerance of {tol}"
    }

monty.newrun("fix ST with P1 sweep", parameters)

sweep = np.append(np.linspace(low, high, pts), np.linspace(high, low, pts))

si.P1(low)  # Reset to the start and wait for integration times
time.sleep(10)

drifts = np.zeros(length)
for i in tqdm(range(length)):
    si.P1(sweep[i % (2*pts)])  # sweep P1
    
    time.sleep(1)
    
    drifts[i] = lockin.R()

    swiper.waitforfeedback(si.ST, lockin, target, tol=tol, stepsize=0.001, slope="down")


#target = drifts[0]

fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

ax2.plot(sweep[np.arange(0, length) % (2*pts)], color="pink")

ax1.plot(drifts[1:])
ax1.plot([0, length], [target-tol, target-tol], color="orange")
ax1.plot([0, length], [target, target], color="green")
ax1.plot([0, length], [target+tol, target+tol], color="orange")

ax1.set_xlabel("Time (seconds)")
ax1.set_ylabel("Lockin")
ax2.set_ylabel("P1 (V)", color="pink")
plt.title(monty.identifier + "." + monty.runname)   
monty.savefig(plt, "history") 
    
monty.save(drifts)




# -*- coding: utf-8 -*-
"""
Created on Wed May 22 11:22:34 2024

New version of load_with_feedback.py to remove many of my hacks

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
from liveplot import LivePlot, LiveContourPlot
import feedback
import swiper
import MDAC
from fridge import Fridge

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
fridge = Fridge("BlueFors_LD")

#%% Start Experiment

experiment = {
    "desc": "Load electrons into the dot while using new feedback techniques."
}

#monty = Monty("sam.load e2", experiment)

monty = Monty("double dot.load e3", experiment)

#dots.get_all_voltages(mdac)


#%% Quick 1D SET sweep 

# Get our surroundings

low = 3.2
high = 3.45
pts = 500

parameters = {
    "desc": "Quick 1D scan of the SET over ST",
    "ST":   f"range from {low}v -> {high}v, over {pts} pts",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    }

monty.newrun("1D SET sweep", parameters)
result = swiper.sweep1d(lockin,
               si.ST, low, high, pts, 
               delay_time=0.3, monty=monty)  # overlap points so we average


monty.save(result)

#%% Choose a good value for our feedback point

g_range = np.linspace(low, high, pts)
deriv = np.abs(np.diff(result["R"]))
R = result["R"]

peaks, _ = find_peaks(deriv, height=1e-12, distance=10)
#peak = np.argmax(deriv)

fig = plt.figure()
plt.plot(g_range[:-1], deriv)
plt.plot(g_range[peaks], deriv[peaks], "x")
#plt.plot(g_range[peak], deriv[peak], "x")
plt.xlabel("ST gate voltage")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("Current derivative")
plt.legend()

fig = plt.figure()
plt.plot(g_range, R)
plt.plot(g_range[peaks], R[peaks], "x")
#plt.plot(g_range[peak], deriv[peak], "x")
plt.xlabel("ST gate voltage")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("Current current")
plt.legend()

print(peaks)

#%% Find the best ST voltage to use

# choose the appropriate peak here
peak = peaks[2]

st_start = g_range[peak]
fix_lockin = result['R'][peak]  # current value to lock in at

print(f"Best peak at inx = {peak}")
print(f"Corresponds to ST={st_start} and lockin={fix_lockin}")

fig = plt.figure()
plt.plot(g_range, result["R"])
plt.plot(g_range[peak], result["R"][peak], "x", label=f"Lockin = {fix_lockin} A")

# add where we are now
plt.plot(si.ST(), lockin.R(), "x", label="Actual")

# add our target point
#plt.plot(3.848668, target, "x")

plt.xlabel("ST gate voltage")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("Current (R)")
plt.legend()


#%% Position ST to match our point

# Position the ST to match the target
#si.ST(low)  # reset to bottom of the sweep 
#time.sleep(1)
si.ST(st_start)
time.sleep(1)
lockin.R()

#%% Lock in on target

#target = fix_lockin  
tol = 0.001e-10

#swiper.waitforfeedback(si.ST, lockin, target, tol=tol)

def gettotarget():  # inherit global variables (bad!!!!)
    print(f"Target = {target:.4e}, tol = {tol}, initial ST = {si.ST()}")
    while np.abs(lockin.R()-target) > tol:
        feedback(si.ST, lockin, target, stepsize=0.001, slope="up")
        print(f"\rST = {si.ST():.4e}, lockin = {lockin.R():.4e}, delta = {np.abs(lockin.R()-target):.4e}", end="")
        time.sleep(0.1)
    print(f"\nFinal ST = {si.ST()}")
   
#si.ST(st_start)
gettotarget()


#%% Fitted the polynominal

# Choose region to fit to (automatically choose based on target choice)
# assume `peak` is the correct peak and g_range is set well
# `deriv` is the current SET derivative

lowthresh = 0.8e-12  # require bigger curvature than this

R = result["R"]

for i in range(peak, pts):
    if deriv[i] < lowthresh:
        stmax = i
        print(f"Min (RHS) at {i} of {deriv[i]} and {R[i]}")
        break
    
for i in range(peak, 0, -1):
    if deriv[i] < lowthresh:
        stmin = i
        print(f"Min (LHS) at {i} of {deriv[i]} and {R[i]}")
        break


# Fit a polynominal to this region
# p: lockin -> ST voltage
order = 7  # polynominal order
coeffs = np.polyfit(R[stmin:stmax], g_range[stmin:stmax], order)
p = np.poly1d(coeffs)

fitted = p(R[stmin:stmax])


fig = plt.figure()
plt.plot(g_range, R)
plt.plot(g_range[peak], R[peak], "x", label="Target")  # our target point
plt.plot(g_range[stmin], R[stmin], "x", label="Lower bound")
plt.plot(g_range[stmax], R[stmax], "x", label="Upper bound")
plt.plot(fitted, R[stmin:stmax], "-.", label="Fitted")

plt.xlabel("ST gate voltage")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("Current")
plt.legend()


#%% Fitted feedback function

# feedback loop

def fittedfeedback():  # (inherit global variables. bad!!)
    """
    Apply proportional fitted feedback.
    
    Be aware there are no checks to make sure that we are still in a reasonable range of values...
    
    """
    # time.sleep(0.5)
    # if r == None:
    r = lockin.R()
    st = si.ST()
    
    delta_g = (p(r)-p(target))  # voltage difference
    g1 = st - delta_g
    
    delta_I1 = r-target
    
    # print (delta_g, g1, r-target, target)
    
    if g1 > 4.0:  # upper bound
        print(f"Aborting feedback: correction voltage exceeds threshold, {g1} > 4.0. No change to ST.")
    elif g1 < 3.5:  # lower bound
        print(f"Aborting feedback: correction voltage fails to meet threshold, {g1} < 3.5. No change to ST.")
    #elif np.abs(r-target) > 0.05e-10:
    #elif np.abs(delta_g) > 0.00005:  # how to pick a good value consistently?
        #print ('large shift')
   #     si.ST(st - delta_g/2)
   #     time.sleep(0.5)  # delay after changing ST
    else:
        # print(f"Adjusting {gate.name} voltage to {g} V")
        si.ST(st - delta_g)
        time.sleep(0.5)  # delay after changing ST
    return delta_I1


def feedback(gate, lockin, target: float, stepsize=0.001, slope="up"):
    """
    Apply proportional feedback blindly
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

    if g > 3.5:  # upper bound
        print(f"Aborting feedback: correction voltage exceeds threshold, {g} > 4.0. No change to ST.")
    elif g < 3.0:  # lower bound
        print(f"Aborting feedback: correction voltage fails to meet threshold, {g} < 3.5. No change to ST.")
    #elif np.abs(r-target) > 0.03e-10:  # take a small step if good
    #    print(f"small step {np.abs(r-target)}")
    #    gate(gate() + adjust/4)
    #    time.sleep(0.5)
    else:
        gate(g)
        time.sleep(0.5)


#fittedfeedback()

#%% Load electrons

#dots.loaddots(si, high=1.2)

thresh = 1.1

tic = time.time()
si.SETB(thresh)
time.sleep(0.5)
si.SETB(0)
print(f"Done. Took {time.time()-tic} seconds.")

#%% Flush electrons

#dots.flushdots(si, low=1.0, high=1.9)

low = 1.0
high = 1.75

tic = time.time()
si.P1(low)
si.P2(low)
print(f"Flushed out to {low}V, raising to {high}V")
time.sleep(0.5)
si.P1(high)
si.P2(high)
print(f"Done. Took {time.time()-tic} seconds.")


#%% 1D scan of P1

up = False

if up:
    low = 1.75
    high = 2.1
else:
    low = 2.1
    high = 1.75

stepsize = 15e-4
points = 100
gate = si.P1

parameters = {
    "desc": "1D sweep of P1 (with proportional feedback techniques). Stepsize = {stepsize}",
    "lockin_amplitude": "Set to 10uV",
    "ST":   f"Fixed at {si.ST()}V (target of {target} on lockin)",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    "SETB": f"Fixed at {si.SETB()}V",
    "J1": f"Fixed at {gb_control_si.VICL()}V",
    "P1": f"Ranged from {low}V -> {high}V in {points} points",
    "P2": f"Fixed at {si.P2()}V",
    "temp": f"Mixing chamber {fridge.temp()} K"
    }

monty.newrun("P1 scan", parameters)

gettotarget()
time.sleep(2)

# don't use swiper to make modifying the feedback easier

gate_range = np.linspace(low, high, points)
X = np.zeros((points))
Y = np.zeros((points))
R = np.zeros((points))
P = np.zeros((points))
ST_drift = np.zeros(points)
delta_I = np.zeros(points)

#fittedfeedback()

# Move to the start and wait a second for the lockin to catchup
# gate(gate_range[0])
# time.sleep(2.0)
# gettotarget()  # get within tolerance now

with tqdm(total=points) as pbar, LivePlot(gate_range, xlabel="P1 gate voltage (V)", ylabel="Current (A)") as lplot:
    for (j, g) in enumerate(gate_range):
        gate(g)
        
        time.sleep(0.5)
        ST_drift[j] = si.ST()
        X[j] = lockin.X()
        Y[j] = lockin.Y()
        R[j] = lockin.R()
        P[j] = lockin.P()
        pbar.update(1)
        lplot.update(R)
        
        feedback(si.ST, lockin, target, stepsize=stepsize, slope="up")
        #delta_I[j] = fittedfeedback()
        
        # time.sleep(0.3)


swiper.plotsweep1d(gate_range, R, gate.name, monty)
monty.save({"X": X, "Y": Y, "R": R, "P": P, "ST": ST_drift, 'ST_I': delta_I})

# Plot ST history over time
fig = plt.figure()
plt.plot(ST_drift)
# plt.plot(delta_I)
plt.xlabel("Steps when sweeping P1")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("ST voltage")
plt.legend()
monty.savefig(plt, "ST history")

# %%
# Plot ST history over time
fig = plt.figure()
# plt.plot(ST_drift)
plt.plot(delta_I)
# plt.xlabel("Steps when sweeping P1")
# plt.title(monty.identifier + "." + monty.runname)
# plt.ylabel("ST voltage")
# plt.legend()
# monty.savefig(plt, "ST history")

#%% Sweep detuning axis

low = 1.75
high = 2.2
points = 600
stepsize = 12e-4

# choose which gates are going up/down
gateup = si.P1
gatedown = si.P2

parameters = {
    "desc": "Sweep detuning axis (P1 - P2). Stepsize = {stepsize}",
    "lockin_amplitude": "Set to 10uV",
    "ST":   f"Fixed at {si.ST()}V (target of {target} on lockin)",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    "SETB": f"Fixed at {si.SETB()}V",
    "J1": f"Fixed at {gb_control_si.VICL()}V",
    gateup.name: f"Ranged from {low}V -> {high}V in {points} points",  # P1 or P2
    gatedown.name: f"Ranged from {high}V -> {low}V in {points} points",  # P1 or P2
    "temp": f"Mixing chamber {fridge.temp()} K",
    }

monty.newrun("detuning scan", parameters)

# gate voltat
gate_up_range = np.linspace(low, high, points)
gate_down_range = np.linspace(high, low, points)

X = np.zeros((points))
Y = np.zeros((points))
R = np.zeros((points))
P = np.zeros((points))
ST_drift = np.zeros(points)
delta_I = np.zeros(points)

#fittedfeedback()
gettotarget()
time.sleep(2)

# Move to the start and wait a second for the lockin to catchup
# gate(gate_range[0])
# time.sleep(2.0)
# gettotarget()  # get within tolerance now

with tqdm(total=points) as pbar, LivePlot(gate_up_range, xlabel="Detuning", ylabel="Current (A)") as lplot:
    for (j, g) in enumerate(gate_up_range):
        gateup(g)
        gatedown(gate_down_range[j])
        time.sleep(0.5)
        
        ST_drift[j] = si.ST()
        X[j] = lockin.X()
        Y[j] = lockin.Y()
        R[j] = lockin.R()
        P[j] = lockin.P()
        
        pbar.update(1)
        lplot.update(R)
        
        feedback(si.ST, lockin, target, stepsize=stepsize, slope="up")
        #delta_I[j] = fittedfeedback()
        # time.sleep(0.3)


#swiper.plotsweep1d(gate_range, R, gate.name, monty)
monty.save({"X": X, "Y": Y, "R": R, "P": P, "ST": ST_drift}) #, 'ST_I': delta_I})

# Plot detuning
fig = plt.figure()
plt.plot(gate_up_range, R)
plt.xlabel(f"{gateup.name} voltage (up)")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("Lockin (A)")
plt.legend()
monty.savefig(plt, "detuning")

# Plot ST history over time
fig = plt.figure()
plt.plot(ST_drift)
plt.xlabel("Detuning step number")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("ST voltage")
plt.legend()
monty.savefig(plt, "ST history")


#%% Charge stability diagram

# gate 1 stepped over slowly
gate1 = si.P2
low1 = 1.75
high1 = 1.81
points1 = 100

# gate 2 swept frequently
gate2 = si.P1
low2 = 1.75
high2 = 2.1
points2 = 600

parameters = {
    "desc": "Sweep both P1 and P2 with feedback present.",
    "lockin_amplitude": "Set to 10uV",
    "ST":   f"Fixed at {si.ST()}V (target of {target} on lockin)",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    "SETB": f"Fixed at {si.SETB()}V",
    "J1": f"Fixed at {gb_control_si.VICL()}V",
    gate1.name: f"Ranged from {low1}V -> {high1}V in {points1} points",
    gate2.name: f"Ranged from {low2}V -> {high2}V in {points2} points",
    "temp": f"Mixing chamber {fridge.temp()} K",
    }


monty.newrun("p1 vs p2", parameters)

G1_range = np.linspace(low1, high1, points1)
G2_range = np.linspace(low2, high2, points2)

X = np.zeros((points1, points2))
Y = np.zeros((points1, points2))
R = np.zeros((points1, points2))
P = np.zeros((points1, points2))
ST_drift = np.zeros(points1*points2)
delta_I = np.zeros(points1*points2)


with tqdm(total=points1*points2) as pbar, LiveContourPlot(G2_range, G1_range, xlabel=f"{gate2.name} voltage", ylabel=f"{gate1.name} voltage") as lplot:
    for (j, g1) in enumerate(G1_range):
        gate1(g1)
        time.sleep(0.3)
        #gettotarget()
        time.sleep(1)
        
        for (i, g2) in enumerate(G2_range):
            gate2(g2)
            time.sleep(0.3)
            
            ST_drift[j*points2+i] = si.ST()
            X[j, i] = lockin.X()
            Y[j, i] = lockin.Y()
            R[j, i] = lockin.R()
            P[j, i] = lockin.P()
            
            pbar.update(1)
            lplot.update(R)
            
            feedback(si.ST, lockin, target, stepsize=8e-4, slope="up")
            #delta_I[j*points2+i] = fittedfeedback()
            
        # Flip the direction of the next sweep
        monty.snapshot({"X": X, "Y": Y, "R": R, "P": P, "ST": ST_drift, "ST_T": delta_I})
        G2_range = G2_range[::-1]
        

swiper.plotsweep2d(G1_range, G2_range, R, gate1.name, gate2.name, monty)  # note wont separate directions
monty.save({"X": X, "Y": Y, "R": R, "P": P, "ST": ST_drift, "ST_T": delta_I})


# Plot ST history over time
fig = plt.figure()
plt.plot(ST_drift)
plt.xlabel("Steps when sweeping P1/P2")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("ST voltage")
plt.legend()
#monty.savefig(plt, "ST history")


# Split the 2D sweep into forwad and backward plots

plt.figure()
plt.pcolormesh(G2_range, G1_range[::2], R[::2, :], shading="nearest")  
plt.colorbar()
plt.ylabel(f"{gate1.name} voltage (V)")
plt.xlabel(f"{gate2.name} voltage (V)")
plt.title(monty.identifier + "." + monty.runname + "_forward")
monty.savefig(plt, "stability forward")

plt.figure()
plt.pcolormesh(G2_range, G1_range[1::2], R[1::2, ::-1], shading="nearest")  
plt.colorbar()
plt.ylabel(f"{gate1.name} voltage (V)")
plt.xlabel(f"{gate2.name} voltage (V)")
plt.title(monty.identifier + "." + monty.runname + "_back")
monty.savefig(plt, "stability backward")

#%% 
_R = R.copy()
_R[1::2, :] = _R[1::2, ::-1]  # reverse odd rows

plt.figure()
plt.pcolormesh(G2_range, G1_range, _R, shading="nearest")  
plt.colorbar()
plt.ylabel(f"{gate1.name} voltage (V)")
plt.xlabel(f"{gate2.name} voltage (V)")
plt.title(monty.identifier + "." + monty.runname + "_both")






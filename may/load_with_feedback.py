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
    "desc": "Load electrons into the dot while using feedback"
}

monty = Monty("double dot.fitted feedback", experiment)
#monty = Monty("double dot.with feedback", experiment)

dots.get_all_voltages(mdac)


#%% Quick 1D SET sweep 

# Get our surroundings

low = 3.85
high = 3.875
pts = 50

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

peaks, _ = find_peaks(deriv, distance=10)
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
si.ST(low)  # reset to bottom of the sweep 
time.sleep(1)
si.ST(st_start)
time.sleep(5)
lockin.R()

#%% Lock in on target

target = 1.55e-10 #fix_lockin  
tol = 0.0001e-10

#swiper.waitforfeedback(si.ST, lockin, target, tol=tol)

def gettotarget():  # inherit global variables (bad!!!!)
    print(f"Target = {target}")
    while np.abs(lockin.R()-target) > tol:
        feedback.feedback(si.ST, lockin, target, stepsize=0.001, slope="down")
        time.sleep(0.1)
        #print(lockin.R())
    
    print(f"Final ST = {si.ST()}")
   
#si.ST(st_start)
gettotarget()


#%% Fitted the polynominal

# Choose region to fit to (automatically choose based on target choice)
# assume `peak` is the correct peak and g_range is set well
# `deriv` is the current SET derivative

lowthresh = 1e-12  # require bigger curvature than this

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
order = 15  # polynominal order
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
        print(f"Aborting feedback: correction voltage exceeds threshold, {g} > 4.0. No change to ST.")
        return delta_I1
    elif g1 < 3.5:  # lower bound
        print(f"Aborting feedback: correction voltage fails to meet threshold, {g} < 3.5. No change to ST.")
        return delta_I1
    # elif np.abs(r-target) > 0.1*1e-10:
    #     print ('Here comes the tunneling')
    #     return delta_I1
    elif np.abs(delta_g) > 0.0002:
        print ('large shift')
        si.ST(st - delta_g/2)
        time.sleep(0.5)  # delay after changing ST
        return delta_I1
    else:
        # print(f"Adjusting {gate.name} voltage to {g} V")
        si.ST(st - delta_g)
        time.sleep(0.5)  # delay after changing ST
        return delta_I1

fittedfeedback()

#%% Load electrons

#dots.loaddots(si, high=1.2)

thresh = 0.9

tic = time.time()
si.SETB(thresh)
time.sleep(0.5)
si.SETB(0)
print(f"Done. Took {time.time()-tic} seconds.")

#%% Flush electrons

#dots.flushdots(si, low=1.0, high=1.9)

low = 1.0
high = 1.9

tic = time.time()
si.P1(low)
si.P2(low)
print(f"Flushed out to {low}V, raising to {high}V")
time.sleep(0.5)
si.P1(high)
si.P2(high)
print(f"Done. Took {time.time()-tic} seconds.")


#%% 1D scan of P1

low = 0.8
high = 2.4
points = 800
gate = si.P1

parameters = {
    "desc": "1D sweep of P1 (with fitted feedback techniques)",
    "lockin_amplitude": "Set to 10uV",
    "ST":   f"Fixed at {si.ST()}V (target of {target} on lockin)",
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
ST_drift = np.zeros(points)
delta_I = np.zeros(points)

fittedfeedback()

# Move to the start and wait a second for the lockin to catchup
# gate(gate_range[0])
# time.sleep(2.0)
# gettotarget()  # get within tolerance now

with tqdm(total=points) as pbar:
    for (j, g) in enumerate(gate_range):
        gate(g)
        
        time.sleep(0.5)
        ST_drift[j] = si.ST()
        X[j] = lockin.X()
        Y[j] = lockin.Y()
        R[j] = lockin.R()
        P[j] = lockin.P()
        pbar.update(1)
        
        delta_I[j] = fittedfeedback()
        # time.sleep(0.3)

        
        # apply feedback
        #feedback.feedback(si.ST, lockin, target, stepsize=0.004, slope="down")
        #time.sleep(0.1)
        #feedback.feedback(si.ST, lockin, target, stepsize=0.001, slope="down")
        #time.sleep(0.1)
        #feedback.feedback(si.ST, lockin, target, stepsize=0.001, slope="down")
        
        


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
#%% P1 vs P2

# Num of points to sweep over

low = 1.8
high = 1.88
pts = 20  # n x n

gate1 = si.P1
gate2 = si.P2

low1 = low
low2 = low
high1 = high
high2 = high
points1 = pts
points2 = pts

parameters = {
    "desc": "Sweep both P1 and P2 with feedback present.",
    "lockin_amplitude": "Set to 10uV",
    "ST":   f"Fixed at {si.ST()}V (measured changes due to feedback)",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    "SETB": f"Fixed at {si.SETB()}V",
    "J": f"Fixed at ? V",
    "P1": f"Ranged from {low}V -> {high}V in {pts} points",
    "P2": f"Ranged from {low}V -> {high}V in {pts} points",
    }

monty.newrun("p1 vs p2", parameters)

#result = swiper.sweep2d(lockin,
#                        si.P1, low, high, pts,
#                        si.P2, low, high, pts,
#                        monty=monty)

G1_range = np.linspace(low1, high1, points1)
G2_range = np.linspace(low2, high2, points2)
X = np.zeros((points1, points2))
Y = np.zeros((points1, points2))
R = np.zeros((points1, points2))
P = np.zeros((points1, points2))

ST_drift = np.zeros(points1*points2)

gate1(G1_range[0])
gate2(G2_range[0])
time.sleep(2.0)
gettotarget()  # get within tolerance now
time.sleep(0.1)

with tqdm(total=points1*points2) as pbar:
    for (j, g1) in enumerate(G1_range):
        gate1(g1)
        time.sleep(0.5)
        gettotarget()  # get within tolerance now
        time.sleep(0.1)
        
        for (i, g2) in enumerate(G2_range):
            gate2(g2)
            time.sleep(0.1)
            
            ST_drift[j*points1+i] = si.ST()
            X[j, i] = lockin.X()
            Y[j, i] = lockin.Y()
            R[j, i] = lockin.R()
            P[j, i] = lockin.P()
            
            pbar.update(1)
            
            # apply feedback
            feedback.feedback(si.ST, lockin, target, stepsize=0.004, slope="down")
            time.sleep(0.1)
            feedback.feedback(si.ST, lockin, target, stepsize=0.001, slope="down")
            time.sleep(0.1)
            feedback.feedback(si.ST, lockin, target, stepsize=0.001, slope="down")
        

swiper.plotsweep2d(G1_range, G2_range, R, gate1.name, gate2.name, monty)
monty.save({"X": X, "Y": Y, "R": R, "P": P, "ST": ST_drift})

# Plot ST history over time
fig = plt.figure()
plt.plot(ST_drift)
plt.xlabel("Steps when sweeping P1+P2")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("ST voltage")
plt.legend()
monty.savefig(plt, "ST history")

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


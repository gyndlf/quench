# -*- coding: utf-8 -*-
"""
Created on Fri May 10 15:50:31 2024

Connect and run the experiment

@author: jzingel
"""

# Inherited from stability_diagram_OLD.py

from quench.libraries import broom
broom.sweep()

import numpy as np
import matplotlib.pyplot as plt

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
    "desc": "Run tests after restarting all the equipment after power failure."
}


monty = Monty("double dot.restart", experiment)

# optionally load the experiment here now
#monty = monty.loadexperiment()


#%% Initilise gates

dots.output_checker_all(gb_control_si)
dots.get_all_voltages(mdac)



#%% 1D SET scan to see regime we are in

# 1D sweep. Just to see if the peaks are actually still there


low = 3.46
high = 3.58
pts = 400

parameters = {
    "desc": "Quick 1D scan of the SET over ST",
    "ST":   f"range from {low}v -> {high}v, over {pts} pts",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    }

monty.newrun("1D SET scan", parameters)
result = swiper.sweep1d(lockin,
               si.ST, low, high, pts, 
               delay_time=0.1, monty=monty)


monty.save(result)

#%% Plot point we choose for our ST

# voltage of marker
st = 3.526
si.ST(st)  # reset to this point for future measurements
 
g_range = np.linspace(low, high, pts)

inx = np.argmin(np.abs(g_range - st))  # find corresponding point

fig = plt.figure()
plt.plot(g_range, result["R"])
plt.plot(g_range[inx], result["R"][inx], "x", label=f"ST = {st}V")

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

low = 1.85
high = 1.9
pts = 400

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

result = swiper.sweep1d(lockin,
                        si.P1, low, high, pts,
                        monty=monty)

monty.save(result)

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


#%% P1-P2 vs J


# -*- coding: utf-8 -*-
"""
Created Sat Jun 01 10:59 pm 2024

Sweep detuning axis and 2D detuning.

Stub file. (Needs to be run from console with instruments loaded)

@author: jzingel
"""

# Inherited from may/load_e.py which itself inherited from somewhere else...
# Note that the 2D sweep matrix is saved in different dimensions to before. Now it matches reality initially.

# It is assumed that these variables have already be set somewhere else
raise(RuntimeError("Do not run this cell."))
lockin = SR860()
si = CMOSfake()
gb_control_si = GBfake()
fridge = Fridge()
monty = Monty()

target = 6e-10  # lockin target


# %% Sweep detuning axis

from tqdm import tqdm
import time
import numpy as np
from liveplot import LivePlot
from june.dc.proportionalfeedback import feedback, gettotarget
import matplotlib.pyplot as plt


low = 1.75
high = 2.1
points = 400
stepsize = 12e-4

# choose which gates are going up/down
forward = False
if forward:
    gateup = si.P1
    gatedown = si.P2
else:
    gateup = si.P2
    gatedown = si.P1

parameters = {
    "desc": "Sweep detuning axis (P1 - P2)",
    "lockin_amplitude": "Set to 10uV",
    "ST": f"Fixed at {si.ST()}V (target of {target} on lockin, stepsize = {stepsize})",
    "SLB": f"Fixed at {si.SLB()}V",
    "SRB": f"Fixed at {si.SRB()}V",
    "SETB": f"Fixed at {si.SETB()}V",
    "J1": f"Fixed at {gb_control_si.VICL()}V",
    gateup.name: f"Ranged from {low}V -> {high}V in {points} points",  # P1 or P2
    gatedown.name: f"Ranged from {high}V -> {low}V in {points} points",  # P1 or P2
    "temp": f"Mixing chamber {fridge.temp()} K",
}

monty.newrun("detuning scan", parameters)

# gate voltage
gate_up_range = np.linspace(low, high, points)
gate_down_range = np.linspace(high, low, points)

# Create detuning axis
mid = (high - low) / 2
detuning = np.linspace(mid - low, high - mid, points)
if not forward:  # reverse as the data is collected backwards
    detuning = detuning[::-1]

X = np.zeros((points))
Y = np.zeros((points))
R = np.zeros((points))
P = np.zeros((points))
ST_drift = np.zeros(points)
delta_I = np.zeros(points)

gettotarget(si.ST, lockin, target, slope="up")
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

# swiper.plotsweep1d(gate_range, R, gate.name, monty)
monty.save({"X": X, "Y": Y, "R": R, "P": P, "ST": ST_drift})

# Plot detuning
fig = plt.figure()
plt.plot(detuning, R)
plt.xlabel("Detuning (P1 - P2)")
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


#%% Sweep Detuning (P1-P2) vs J (VICL)

from liveplot import LiveContourPlot
import swiper


# Setup P1 / P2  detuning params
lowp = 1.75
highp = 2.1
pointsp = 200

# choose which gates are going up/down
forward = True
if forward:
    gateup = si.P1
    gatedown = si.P2
else:
    gateup = si.P2
    gatedown = si.P1

stepsize = 12e-4

# Setup J1 (VICL) (swept slowly)
lowj = 3.0
highj = 4.0
pointsj = 300
gatej = gb_control_si.VICL

parameters = {
    "desc": "Sweep detuning axis (P1 - P2) against J1 (VICL)",
    "lockin_amplitude": "Set to 10uV",
    "ST": f"Start at {si.ST()}V (target of {target} on lockin with stepsize = {stepsize})",
    "SLB": f"Fixed at {si.SLB()}V",
    "SRB": f"Fixed at {si.SRB()}V",
    "SETB": f"Fixed at {si.SETB()}V",
    gateup.name: f"Ranged from {lowp}V -> {highp}V in {pointsp} points",  # P1 or P2
    gatedown.name: f"Ranged from {highp}V -> {lowp}V in {pointsp} points",  # P1 or P2
    "J1": f"Ranged from {lowj}V -> {highj}V in {pointsj} points",
    "temp": f"Mixing chamber {fridge.temp()} K",
}

gettotarget()
time.sleep(2)

monty.newrun("detuning vs J", parameters)

# gate voltages
gate_up_range = np.linspace(lowp, highp, pointsp)
gate_down_range = np.linspace(highp, lowp, pointsp)
j_range = np.linspace(lowj, highj, pointsj)

# Create detuning axis
mid = (highp - lowp) / 2
detuning = np.linspace(mid - lowp, highp - mid, pointsp)
if not forward:  # reverse as the data is collected backwards (initially)
    detuning = detuning[::-1]

X = np.zeros((pointsj, pointsp))
Y = np.zeros((pointsj, pointsp))
R = np.zeros((pointsj, pointsp))
P = np.zeros((pointsj, pointsp))
ST_drift = np.zeros(pointsj * pointsp)

# TODO: When sweeping direction, instead of entering the data in the same way initially and reversing it later, enter it reversed.
# This means that the live plot corresponds to what we are actually measuring

with tqdm(total=pointsj * pointsp) as pbar, LiveContourPlot(detuning, j_range, xlabel=f"Detuning (P1-P2)",
                                                            ylabel="J gate voltage") as lplot:
    for (j, gj) in enumerate(j_range):
        gatej(gj)  # J1
        time.sleep(0.3)
        feedback(si.ST, lockin, target, stepsize=stepsize, slope="up")
        # gettotarget()  # perhaps be even more agressive on the start of each sweep?
        time.sleep(1)

        for (i, g) in enumerate(gate_up_range):
            gateup(g)
            gatedown(gate_down_range[i])
            time.sleep(0.3)

            ST_drift[j * pointsp + i] = si.ST()
            X[j, i] = lockin.X()
            Y[j, i] = lockin.Y()
            R[j, i] = lockin.R()
            P[j, i] = lockin.P()

            pbar.update(1)
            lplot.update(R)

            feedback(si.ST, lockin, target, stepsize=stepsize, slope="up")

        monty.snapshot({"X": X, "Y": Y, "R": R, "P": P, "ST": ST_drift})

        # Flip the direction of the next sweep
        gate_up_range = gate_up_range[::-1]
        gate_down_range = gate_down_range[::-1]

monty.save({"X": X, "Y": Y, "R": R, "P": P, "ST": ST_drift})

swiper.plotsweep2d(j_range, detuning, R, "J", "Detuning", monty)  # note wont separate directions

# Plot ST history over time
fig = plt.figure()
plt.plot(ST_drift)
plt.xlabel("Steps when sweeping detuning and J1")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("ST voltage")
plt.legend()
monty.savefig(plt, "ST history")

# Split the 2D sweep into forward and backward plots

plt.figure()
plt.pcolormesh(detuning, j_range[::2], R[::2, :], shading="nearest")
plt.colorbar()
plt.ylabel("J voltage (V)")
plt.xlabel(f"Detuning voltage(V)")
plt.title(monty.identifier + "." + monty.runname + "_forward")
monty.savefig(plt, "stability forward")

plt.figure()
plt.pcolormesh(detuning, j_range[1::2], R[1::2, ::-1], shading="nearest")
plt.colorbar()
plt.ylabel("J voltage (V)")
plt.xlabel(f"Detuning voltage (V)")
plt.title(monty.identifier + "." + monty.runname + "_back")
monty.savefig(plt, "stability backward")




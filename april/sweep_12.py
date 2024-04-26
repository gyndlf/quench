# -*- coding: utf-8 -*-
"""
Created on Fri Apr 26 10:53:31 2024

@author: Zingel
"""

# Sweep the SET using Python 3.12.2 and the new path structure

from quench.libraries import broom
broom.sweep()

import sys
import numpy as np
from tqdm import tqdm
import time
import matplotlib.pyplot as plt

import qcodes as qc
from qcodes import Station

from monty import Monty
import MDAC
import qcodes_measurements as qcm
from qcodes_measurements.device.states import ConnState


#%%

# Connect to instruments

# close any open instruments 
try:
    mdac = qc.Instrument.find_instrument("mdac")
    mdac.close()
except KeyError:
    print('Attempting to remove instrument with name mdac. Does not exist')
    
try:
    lockin = qc.Instrument.find_instrument("sr860_top")
    lockin.close()
except KeyError:
    print("Cannot remove instrument with name sr860_top. Does not exist")

scfg = Station(config_file='measurements/system.yaml')

mdac = MDAC.MDAC('mdac', 'ASRL11::INSTR')
lockin = scfg.load_instrument('sr860_top')


#%%

# Create Si CMOS device

def newSiDot():
    """Create a new Si device with named gates using qcodes_measurements"""
    BB1 = qcm.device.BB("Breakout_box_top")
    BB2 = qcm.device.BB("Breakout_box_bot")
    si = qcm.device.Device("Si28_quantum_dot")
    
    # Si gates CHANGE AS NECESSARY
    si.add_gate("test_gate", mdac.ch48, state=ConnState.SMC, default_mode="FREE")
    si.add_gate("LCB",          BB1.ch15.connect_dac(mdac.ch03), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("RCB",          BB2.ch09.connect_dac(mdac.ch08), state=ConnState.SMC, default_mode="FREE") # channel 35
    si.add_gate("RG",           BB2.ch17.connect_dac(mdac.ch11), state=ConnState.SMC, default_mode="FREE") # channel 41
    #si.add_gate("Res",          BB1.ch18.connect_dac(mdac.ch14), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("ResB",         BB1.ch17.connect_dac(mdac.ch14), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("P3",           BB1.ch19.connect_dac(mdac.ch16), state=ConnState.SMC, default_mode="FREE")
    #si.add_gate("J2",           BB1.ch20.connect_dac(mdac.ch20), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("P2",           BB1.ch13.connect_dac(mdac.ch19), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("P1",           BB1.ch04.connect_dac(mdac.ch20), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("SETB",         BB1.ch02.connect_dac(mdac.ch22), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("SRB",          BB2.ch04.connect_dac(mdac.ch26), state=ConnState.SMC, default_mode="FREE") # channel 29
    si.add_gate("SLB",          BB2.ch06.connect_dac(mdac.ch31), state=ConnState.SMC, default_mode="FREE") # channel 31
    si.add_gate("ST",           BB1.ch10.connect_dac(mdac.ch41), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("bias",         BB1.ch25.connect_dac(mdac.ch47), state=ConnState.SMC, default_mode="FREE") # fake BB gate
    #si.add_gate("Unused_Ohmic", BB1.ch24.connect_dac(mdac.ch44), state=ConnState.SMC, default_mode="FREE")
    si.add_ohmic("S",  BB1.ch09)
    si.add_ohmic("D",  BB1.ch01)
    si.add_ohmic("Res", BB1.ch18)
    return si


si = newSiDot()

#%%

# Sweep the discontinunity region

# Start new experiment

experiment = {
    "desc": "Scan the Coulomb blocking region. This is the region that we want to use to measure our qubit over. Vary which gates are used to sweep over."
}


monty = Monty("SET.coulomb blocking", experiment)

# optionally load the experiment here now

#%%

# 2D sweep.

ST_pts = 101  # num points to sweep over ST
SLB_pts = 101

ST_gate_range = np.linspace(3.4, 3.5, ST_pts)
SLB_gate_range = np.linspace(0.877, 0.888, SLB_pts)

X = np.zeros((SLB_pts, ST_pts))
Y = np.zeros((SLB_pts, ST_pts))
R = np.zeros((SLB_pts, ST_pts))
P = np.zeros((SLB_pts, ST_pts))

parameters = {
    "desc": "Sweep over the active range of ST/SLB/SRB. Ranges chosen from quick_square. Attempt to recreate part of double_dot_region_matrix_view.png",
    "ST":   f"range from {ST_gate_range[0]}v to {ST_gate_range[-1]}v, {ST_pts}pts",
    "SLB":  f"{SLB_gate_range[0]}v to {SLB_gate_range[-1]}v, {SLB_pts}pts",
    "SRB":  f"{SLB_gate_range[0]}v to {SLB_gate_range[-1]}v, {SLB_pts}pts (paried with SLB)",
    }

monty.newrun("initial sweep", parameters)

with tqdm(total=ST_pts*SLB_pts) as pbar:
    for (j, SLB_SRB_voltage) in enumerate(SLB_gate_range):
        si.SLB(SLB_SRB_voltage)
        si.SRB(SLB_SRB_voltage)
        time.sleep(0.05)
        
        for (i, ST_voltage) in enumerate(ST_gate_range):
            si.ST(ST_voltage)
            time.sleep(0.05)  # wait longer than the lockin integration time
            
            X[j, i] = lockin.X()
            Y[j, i] = lockin.Y()
            R[j, i] = lockin.R()
            P[j, i] = lockin.P()
            
            pbar.update(1)
            
        # Save each ST sweep
        monty.snapshot(data={"X": X, "Y": Y, "R": R, "P": P})

monty.save({"X": X, "Y": Y, "R": R, "P": P})

plt.pcolor(ST_gate_range, SLB_gate_range, R)
plt.colorbar()
plt.xlabel("ST gate voltage")
plt.ylabel("SLB/SRB gate voltage")
monty.savefig(plt, "matrix")





#%%

# 1D sweep.

ST_pts = 101  # num points to sweep over ST


ST_gate_range = np.linspace(3.4, 3.6, ST_pts)

X = np.zeros(ST_pts)
Y = np.zeros(ST_pts)
R = np.zeros(ST_pts)
P = np.zeros(ST_pts)

parameters = {
    "desc": "1D scan",
    "ST":   f"range from 3.4v to 3.6v, {ST_pts}pts",
    "SLB":  f"0.885v",
    "SRB":  f"0.885",
    }

#monty.newrun("1d sweep 0.885v", parameters)

si.SLB(0.885)
si.SRB(0.885)

with tqdm(total=ST_pts) as pbar:
    for (j, ST_voltage) in enumerate(ST_gate_range):
        si.ST(ST_voltage)
        time.sleep(0.05)  # wait longer than the lockin integration time
        
        X[j] = lockin.X()
        Y[j] = lockin.Y()
        R[j] = lockin.R()
        P[j] = lockin.P()
        
        pbar.update(1)
            
monty.save({"X": X, "Y": Y, "R": R, "P": P})

plt.plot(ST_gate_range, R)
#plt.colorbar()
plt.xlabel("ST gate voltage")
plt.ylabel("R current")
monty.savefig(plt, "line_plot")


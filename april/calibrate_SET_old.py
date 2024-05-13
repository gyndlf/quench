# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 11:28:00 2024

@author: jzingel
"""

# Sweep the Si CMOS SET to calibrate it

# Clean the system path because there is so much junk
import sys

sys.path = ['C:\\Users\\LD2007\\anaconda3\\envs\\py38\\python38.zip',
 'C:\\Users\\LD2007\\anaconda3\\envs\\py38\\DLLs',
 'C:\\Users\\LD2007\\anaconda3\\envs\\py38\\lib',
 'C:\\Users\\LD2007\\anaconda3\\envs\\py38',
 'C:\\Users\\LD2007\\AppData\\Roaming\\Python\\Python38\\site-packages',
 'C:\\Users\\LD2007\\anaconda3\\envs\\py38\\lib\\site-packages',
 'C:\\Users\\LD2007\\anaconda3\\envs\\py38\\lib\\site-packages\\win32',
 'C:\\Users\\LD2007\\anaconda3\\envs\\py38\\lib\\site-packages\\win32\\lib',
 'C:\\Users\\LD2007\\anaconda3\\envs\\py38\\lib\\site-packages\\Pythonwin',
 '/Users/LD2007/Documents/Si_CMOS_james/libraries']
print("Cleaned PATH")

import sys
import numpy as np
from tqdm import tqdm
import time
import matplotlib.pyplot as plt

import qcodes as qc
from qcodes import Station

# Import Qcodes measurements
#sys.path.append('/Users/LD2007/Documents/qcodes_measurements')


# Use custom libraries
LIBS = '/Users/LD2007/Documents/Si_CMOS_james/libraries'
if LIBS not in sys.path:
    sys.path.append(LIBS)
    
# Import custom MDAC driver
import MDAC

# Import data saver
from monty import Monty

# Import QNL measurement helpers
from qcodes_measurements import qcodes_measurements as qcm
from qcodes_measurements.qcodes_measurements.device.states import ConnState

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

scfg = Station(config_file='measurements/system1.yaml')

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

# Now set and/or measure and/or sweep
#
# Use code like the following to set values on the MDAC
# 
# si.SLB(0.93)
# si.SRB(0.93)
#
# And code like the following to read values from the lock-in
#
# X = lockin_top.X()
# Y = lockin_top.Y()
# R = lockin_top.R()
# P = lockin_top.P()
 
si.SLB(0.93)
si.SRB(0.93)

N = 101  # num points to sweep over

ST_gate_range = np.linspace(3.4, 3.6, N)

X = np.zeros(N)
Y = np.zeros(N)
R = np.zeros(N)
P = np.zeros(N)

for (i, ST_voltage) in tqdm(enumerate(ST_gate_range)):
    si.ST(ST_voltage)
    time.sleep(0.1)  # wait for the MDAC to update
    
    X[i] = lockin.X()
    Y[i] = lockin.Y()
    R[i] = lockin.R()
    P[i] = lockin.P()


#%%

# 2D sweep.

ST_pts = 501  # num points to sweep over ST
SLB_pts = 501

ST_gate_range = np.linspace(3.525, 3.6, ST_pts)
SLB_gate_range = np.linspace(0.86, 0.88, SLB_pts)

X = np.zeros((SLB_pts, ST_pts))
Y = np.zeros((SLB_pts, ST_pts))
R = np.zeros((SLB_pts, ST_pts))
P = np.zeros((SLB_pts, ST_pts))

experiment = {
    "desc":         "Sweeping a region of where some discontinunities appeared",
    "ST":           f"range from 3.525v to 3.6v, {ST_pts}pts",
    "SLB and SRB":  f"0.86v to 0.88v, {SLB_pts}pts"
    }

monty = Monty("SET_discontinuity_region", experiment)

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
plt.xlabel("ST gate voltage")
plt.ylabel("SLB/SRB gate voltage")

    
#%%
    
# Plot what actually happened

plt.figure()

plt.plot(ST_gate_range, R)

plt.xlabel("ST gate voltage")
plt.ylabel("Current")
plt.show()































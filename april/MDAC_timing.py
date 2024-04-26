# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 15:12:01 2024.

@author: Zingel
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
LIBS = "C:\\Users\\LD2007\\Documents\\Si_CMOS_james\\libraries"
if LIBS not in sys.path:
    sys.path.append(LIBS)
    
# Import custom MDAC driver
import MDAC

# Import data saver
from monty import Monty

# Import QNL measurement helpers
from qcodes_measurements import qcodes_measurements as qcm
from qcodes_measurements.qcodes_measurements.device.states import ConnState

# Connect to instruments

# close any open instruments 
try:
    mdac = qc.Instrument.find_instrument("mdac")
    mdac.close()
except KeyError:
    print('Cannot remove instrument with name mdac. Does not exist')
    
try:
    lockin = qc.Instrument.find_instrument("sr860_top")
    lockin.close()
except KeyError:
    print("Cannot remove instrument with name sr860_top. Does not exist")

scfg = Station(config_file='measurements/system1.yaml')

mdac = MDAC.MDAC('mdac', 'ASRL11::INSTR')
lockin = scfg.load_instrument('sr860_top')


# Create Si CMOS device

def newSiDot():
    """Create a new Si device with named gates using qcodes_measurements."""
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

base = 3.0

def move(delta):
    """Adjust ST voltage by delta."""
    si.ST(base)
    si.ST(base + delta)


#%%

%timeit move(0.1)
3.94 s ± 6.7 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

%timeit move(0.01)
439 ms ± 6.81 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

%timeit move(0.001)
32.4 ms ± 690 µs per loop (mean ± std. dev. of 7 runs, 1 loop each)

%timeit move(0.0001)
32.4 ms ± 174 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

%timeit move(0.00001)
32.4 ms ± 310 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)





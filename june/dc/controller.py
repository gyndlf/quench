# -*- coding: utf-8 -*-
"""
Created on Tue Jun 04 14:16 2024

Set up the instruments and connect to them

@author: jzingel
"""

import broom
broom.sweep()

import numpy as np
import matplotlib.pyplot as plt
import time
from qcodes import Station, Instrument

from monty import Monty
import MDAC
from fridge import Fridge

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


#%% Start experiment

experiment = {
    "desc": "Run some detuning sweeps."
}

#monty = Monty("sam.load e2", experiment)
monty = Monty("double dot.detuning", experiment)
#monty = Monty("double dot.load e3", experiment)


#dots.get_all_voltages(mdac)

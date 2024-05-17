# -*- coding: utf-8 -*-
"""
Created on Fri May 17 10:37:16 2024

Watch the natural drift of the fridge. From this we can determine how much temperature has an effect

@author: jzingel
"""

from quench.libraries import broom

broom.sweep()

import numpy as np
import matplotlib.pyplot as plt
import time
from tqdm import tqdm

from qcodes import Station, Instrument

from monty import Monty
from fridge import Fridge
import MDAC

# Import the neighbouring files. In may/
import quench.may.dots as dots
from quench.may.custom_devices import connect_to_gb, newSiDot

# %% Connect to instruments

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

# %% Start Experiment

experiment = {
    "desc": "Watch the natural drift of the SET over time."
}

monty = Monty("SET.natural drift", experiment)

# optionally load the experiment here now
# monty = monty.loadexperiment()


#%% Watch the drift

length = 10  # minutes

parameters = {
    "desc": "Watch the SET drift over the weekend",
    "gates" : dots.getvoltages(mdac),
    "duration": f"{length} minutes",
    "tempsensor": "MC"
}

monty.newrun("SET drift", parameters)

R = np.zeros(length)
temps = np.zeros(length)

for i in tqdm(range(length)):
    R[i] = lockin.R()
    temps[i] = fridge.get_temperatures()["MC"]
    time.sleep(60)

    if i % 30 == 0:  # save every 1/2 hour
        monty.snapshot({"R": R, "temps": temps})


fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

ax1.plot(R, color="green")
ax2.plot(temps, color="blue")

ax1.set_xlabel("Time (minutes)")
ax1.set_ylabel("Lockin (A)", color="green")
ax2.set_ylabel("MC Temp (K)", color="blue")
plt.title(monty.identifier + "." + monty.runname)
monty.savefig(plt, "history")

monty.save({"R": R, "temps": temps})

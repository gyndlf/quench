# -*- coding: utf-8 -*-
"""
Created on Sat May 25 20:00:00 2024

Plot the progress of a SNAPSHOT while it is still being run

@author: jzingel
"""

from monty import Monty
import matplotlib.pyplot as plt
import lzma
import pickle
import numpy as np


#%% Load data

monty = Monty("double_dot.load_2e")

data = monty.loaddata("_SNAPSHOT")

#%% Raw load

path = "p1_vs_p2.4_SNAPSHOT.xz"

with lzma.open(path, "r") as fz:
    data = pickle.load(fz)
    print(f"Loaded data with run name {data['runname']}")


#%% Build x / y arrays

X = np.linspace(1.2, 2.2, 200)
Y = np.linspace(1.2, 2.2, 400)
Z = data["data"]["R"]

# Replace 0s with nan
Z[Z==0] = np.nan

plt.figure()
plt.pcolormesh(X, Y[1::2], Z[1::2, ::-1], shading="nearest")
plt.colorbar()
plt.show()

plt.figure()
plt.pcolormesh(X, Y[::2], Z[::2, :], shading="nearest")
plt.colorbar()
plt.show()
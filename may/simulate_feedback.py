# -*- coding: utf-8 -*-
"""
Created on Fri May 10 15:50:31 2024

Simulate feedback from some artificial noisy data.

@author: jzingel
"""

from feedback import Feedback
import numpy as np
import matplotlib.pyplot as plt


# Generate data with some underlying movement to it
x = np.linspace(1, 10, 100)

# what the lockin measures over time [0, 10] sec
# offset with potential bias to the lockin via ST graph
y = lambda x: np.sin(x**2) * np.cos(x) * 5 + (np.random.rand()-0.5)*4

# create the coulomb blocking slope
coulomb = lambda st: (5-st)**2*0.2  # valid for st in [-5, 5]
vs = np.linspace(-5, 5, 100)

# run and apply feedback
measured = np.zeros(100)
feed = 0
for (i, t) in enumerate(x):
    measured[i] = coulomb(y(t) + feed)
    # apply feedback if necessary

    feed = -y(t)*2

plt.plot(measured)
plt.show()
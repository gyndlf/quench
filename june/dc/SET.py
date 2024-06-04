# -*- coding: utf-8 -*-
"""
Created Sat Jun 01 10:39 pm 2024

Common methods used for sweeping the SET and choosing a good coulomb region

Stub file. (Needs to be run from console with instruments loaded)

@author: jzingel
"""

from monty import Monty
from qcodes.instrument_drivers.stanford_research.SR860 import SR860

# It is assumed these variables have already been set somewhere that makes sense
raise(RuntimeError("Do not run this cell."))
monty = Monty.__class__
lockin = SR860.__class__

#%% Standard ST sweep

import swiper

low = 3.2
high = 3.45
pts = 500

parameters = {
    "desc": "Quick 1D scan of the SET over ST",
    "ST":   f"range from {low}v -> {high}v, over {pts} pts",
    "SLB":  f"Fixed at {si.SLB()}V",
    "SRB":  f"Fixed at {si.SRB()}V",
    }

monty.newrun("1D SET sweep", parameters)
result = swiper.sweep1d(lockin,
               si.ST, low, high, pts,
               delay_time=0.3, monty=monty)  # optionally choose small delay time to overlap points so we average

monty.save(result)


#%% Find a good coulomb blocking region

from scipy.signal import find_peaks

g_range = np.linspace(low, high, pts)
R = result["R"]
deriv = np.abs(np.diff(R))

peaks, _ = find_peaks(deriv, height=1e-12, distance=10)

# Plot current derivative over voltage
fig = plt.figure()
plt.plot(g_range[:-1], deriv)
plt.plot(g_range[peaks], deriv[peaks], "x")
plt.xlabel("ST gate voltage")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("Current derivative")
plt.legend()

# Plot original sweep with peaks annotated
fig = plt.figure()
plt.plot(g_range, R)
plt.plot(g_range[peaks], R[peaks], "x")
plt.xlabel("ST gate voltage")
plt.title(monty.identifier + "." + monty.runname)
plt.ylabel("Current current")
plt.legend()

# Print information about each peak
print("Choose 'target' current (R) from the following")
for (i, peak) in enumerate(peaks):
    print(f"Peak #{i} -> ST={g_range[peak]} : R={R[peak]}")

# -*- coding: utf-8 -*-
"""
Created on Fri May 10 14:31:54 2024

Quickly perform a 2D sweep between the specified gates

@author: Zingel
"""

#from quench.libraries import broom
#broom.sweep()

from qcodes_measurements.device.gate import Gate
from monty import Monty

from qcodes.instrument_drivers.stanford_research.SR860 import SR860

import numpy as np
from tqdm import tqdm
import time
import matplotlib.pyplot as plt


# Based upon may.stability_diagram.py

def plotsweep1d(X: np.ndarray, Y: np.ndarray, gate_name: str, monty: Monty=None):
    """Plot a 1D sweep"""
    plt.figure()
    plt.plot(X, Y)
    plt.xlabel(f"{gate_name} gate voltage (V)")
    plt.ylabel("Current (A)")
    if monty is not None:
        plt.title(monty.identifier + "." + monty.runname)
        monty.savefig(plt, "1D")
    else:
        print("WARNING: Plotting but no monty object specified. Some things may break")

    
    
def plotsweep2d(X1: np.ndarray, X2: np.ndarray, Y: np.ndarray, 
                gate1_name: str, gate2_name: str, monty: Monty = None):
    """Plot a 2D sweep"""
    plt.figure()
    plt.pcolor(X1, X2, Y)
    plt.colorbar()
    plt.xlabel(f"{gate1_name} gate voltage (V)")
    plt.ylabel(f"{gate2_name} gate voltage (V)")
    if monty is not None:
        plt.title(monty.identifier + "." + monty.runname)
        monty.savefig(plt, "2D")
    else:
        print("WARNING: Plotting but no monty object specified. Some things may break")
    

def sweep1d(lockin: SR860,
            gate: Gate, low: float, high: float, points: int,
            delay_time=0.1, plot=True, monty=None) -> dict:
    """
    Perform a 1D sweep of the specified gate.
    
    plot= if we should plot additionally
    monty= the Monty datasaver object (needed if plotting)
    """
    print(f"Sweeping {gate} from {low}V to {high}V in {points} points.")
    gate_range = np.linspace(low, high, points)
    X = np.zeros((points))
    Y = np.zeros((points))
    R = np.zeros((points))
    P = np.zeros((points))
    
    # Move to the start and wait a second for the lockin to catchup
    gate(gate_range[0])
    time.sleep(2.0)
    
    with tqdm(total=points) as pbar:
        for (j, g) in enumerate(gate_range):
            gate(g)
            #print(f"Set = {g}")
            time.sleep(delay_time)
            X[j] = lockin.X()
            Y[j] = lockin.Y()
            R[j] = lockin.R()
            P[j] = lockin.P()
            pbar.update(1)
    
    if plot:
        plotsweep1d(gate_range, R, gate.name, monty)
    return {"X": X, "Y": Y, "R": R, "P": P}


def sweep2d(lockin: SR860, 
            gate1: Gate, low1: float, high1: float, points1: int,
            gate2: Gate, low2: float, high2: float, points2: int,
            callback=None, delay_time=0.1, plot=True, monty=None):
    """
    Perform a 2D sweep between the specified gates.
    
    callback({X,Y,R,P}) is called optionally at the end of one line sweep
    plot= if we should plot additionally
    monty= the Monty datasaver object (needed if plotting)
    """
    print(f"Sweeping {gate1} from {low1}V to {high1}V in {points1} points,")
    print(f"Sweeping {gate2} from {low2}V to {high2}V in {points2} points")
    G1_range = np.linspace(low1, high1, points1)
    G2_range = np.linspace(low2, high2, points2)
    X = np.zeros((points1, points2))
    Y = np.zeros((points1, points2))
    R = np.zeros((points1, points2))
    P = np.zeros((points1, points2))
    
    # Move to the start and wait a second for the lockin to catchup
    gate1(G1_range[0])
    gate2(G2_range[0])
    time.sleep(2.0)
    
    with tqdm(total=points1*points2) as pbar:
        for (j, g1) in enumerate(G1_range):
            gate1(g1)
            time.sleep(delay_time)
            
            for (i, g2) in enumerate(G2_range):
                gate2(g2)
                time.sleep(delay_time)
                
                X[j, i] = lockin.X()
                Y[j, i] = lockin.Y()
                R[j, i] = lockin.R()
                P[j, i] = lockin.P()
                
                pbar.update(1)
                
            # Save each sweep
            if callback is not None:
                callback({"X": X, "Y": Y, "R": R, "P": P})
    
    if plot:
        plotsweep2d(G1_range, G2_range, R, gate1.name, gate2.name, monty)
    return {"X": X, "Y": Y, "R": R, "P": P}
                
                
    

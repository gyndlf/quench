# -*- coding: utf-8 -*-
"""
Created on Fri May 10 14:31:54 2024

Quickly perform a 2D sweep between the specified gates

@author: jzingel
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
    """
    Plot a 2D sweep.
    Assumes that X1 and X2 have the same shape (when meshed) as Y
    """
    plt.figure()
    # This may look backwards but it is the right order since I define my matrices weird
    plt.pcolormesh(X2, X1, Y, shading="nearest")  
    plt.colorbar()
    plt.ylabel(f"{gate1_name} gate voltage (V)")
    plt.xlabel(f"{gate2_name} gate voltage (V)")
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


def sweep1dfeedback(lockin: SR860,
            gate: Gate, low: float, high: float, points: int,
            fbgate: Gate, target: float, tol=1e-11,
            delay_time=0.1, plot=True, monty=None) -> dict:
    """
    Perform a 1D sweep of the specified gate with feedback (PID)
    
    plot= if we should plot additionally
    monty= the Monty datasaver object (needed if plotting)
    
    calibration=float is the lockin current expected (will shift due to the sweep)
    tol=0.1 range we move to get within before measuring another point
    
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
            
            waitforfeedback(fbgate, lockin, target, tol)
            
            pbar.update(1)
    
    if plot:
        plotsweep1d(gate_range, R, gate.name, monty)
    return {"X": X, "Y": Y, "R": R, "P": P}


def waitforfeedback(gate: Gate, lockin: SR860, target: float, tol:float=1e-12, stepsize=0.001, slope="down"):
    """
    Proportionally change the gate voltage based on how far away we are until we are within threshold
    Wait until this occurs.
    
    Slope = "up" or "down". Indicates the direction of the Coulomb potential that we're locked onto and directs which direction the feedback should operate in.
    """
    
    if slope == "up":
        sgn = 1
    elif slope == "down":
        sgn = -1
    else:
        raise(f"Unknown slope '{slope}'. Must be either 'up' or 'down'")
    
    waiting = np.abs(lockin.R() - target) > tol
    while waiting:
        r = lockin.R()
        
        error = (target - r) * sgn
        adjust = error*stepsize/target # normalised error func
    
        if np.abs(error) < tol:
            break  # early exiting
        
        #print(f"Difference of {error} adjusting by {adjust}")
        g = gate() + adjust  # new gate voltage
        
        if g > 4.0:  # upper bound
            print(f"Aborting feedback: correction voltage exceeds threshold, {g} > 4.0. No change to ST.")
            break
        elif g < 3.5:  # lower bound
            print(f"Aborting feedback: correction voltage fails to meet threshold, {g} < 3.5. No change to ST.")
            break
        else:
            #print(f"Adjusting {gate.name} voltage to {g} V")
            gate(g)
            time.sleep(0.15)  # delay after changing ST
            
def feedback(gate: Gate, lockin: SR860, target: float, stepsize=0.001, slope="down"):
    """
    Apply proportional based feedback always.
    This will result in some jumping around near the target but should hopefully not be too much.

    Parameters
    ----------
    target : float
        lockin.R value to match
    stepsize : TYPE, optional
        How large a step should be taken in the direction of the error. The default is 0.001.
    slope : TYPE, optional
        Indicates the direction of the Coulomb potential that we're locked onto and directs which direction the feedback should operate in. Either "up" or "down". The default is "down".
    """
    if slope == "up":
        sgn = 1
    elif slope == "down":
        sgn = -1
    else:
        raise(f"Unknown slope '{slope}'. Must be either 'up' or 'down'")
    
    r = lockin.R()
    error = (target - r) * sgn
    adjust = error/target*stepsize  # normalised error func
    g = gate() + adjust  # new gate voltage
    
    if g > 4.0:  # upper bound
        print(f"Aborting feedback: correction voltage exceeds threshold, {g} > 4.0. No change to ST.")
    elif g < 3.5:  # lower bound
        print(f"Aborting feedback: correction voltage fails to meet threshold, {g} < 3.5. No change to ST.")
    else:
        gate(g)


def sweep2d(lockin: SR860, 
            gate1: Gate | list[Gate], low1: float, high1: float, points1: int,
            gate2: Gate, low2: float, high2: float, points2: int,
            callback=None, delay_time=0.1, plot=True, monty=None, alternate_directions=False):
    """
    Perform a 2D sweep between the specified gates.
    
    callback({X,Y,R,P}) is called optionally at the end of one line sweep
    plot= if we should plot additionally
    monty= the Monty datasaver object (needed if plotting)
    alternate_directions=False if the sweep should alternate in a snake like map over the voltages (unimplemneted)
    
    gate1 can optionly be a group of gates to move at once. If so give these as a list
    """
    if isinstance(gate1, list):
        print(f"Sweeping {[g.name for g in gate1]} from {low1}V to {high1}V in {points1} points,")
    else:
        print(f"Sweeping {gate1} from {low1}V to {high1}V in {points1} points,")
    print(f"Sweeping {gate2} from {low2}V to {high2}V in {points2} points")
    if alternate_directions:
        print("WARNING THIS IS FAILING: Alternating directions after each 1D sweep (zig zag pathing)")
    G1_range = np.linspace(low1, high1, points1)
    G2_range = np.linspace(low2, high2, points2)
    X = np.zeros((points1, points2))
    Y = np.zeros((points1, points2))
    R = np.zeros((points1, points2))
    P = np.zeros((points1, points2))
    
    # Move to the start and wait a second for the lockin to catchup
    if isinstance(gate1, list):
        for gate in gate1:
            gate(G1_range[0])
    else:
        gate1(G1_range[0])
    gate2(G2_range[0])
    time.sleep(2.0)
    
    with tqdm(total=points1*points2) as pbar:
        for (j, g1) in enumerate(G1_range):
            if isinstance(gate1, list):
                for gate in gate1:
                    gate(g1)
            else:
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
            
            if alternate_directions:  # sweep in a zig-zag path
                G2_range = G2_range[::-1]  # some how this doesn't work???? 
                time.sleep(0.1)
                
            # Save each sweep
            if callback is not None:
                callback({"X": X, "Y": Y, "R": R, "P": P})
                
    if alternate_directions:  # fix saving as every second line is the wrong direction
        X[1::2, :] = X[1::2, ::-1]  # grab every second row and flip it
        Y[1::2, :] = Y[1::2, ::-1]
        R[1::2, :] = R[1::2, ::-1]
        P[1::2, :] = P[1::2, ::-1]
    
    if plot:
        plotsweep2d(G1_range, G2_range, R, "Paired gates" if isinstance(gate1, list) else gate1.name, gate2.name, monty)
    return {"X": X, "Y": Y, "R": R, "P": P}
                
                
    

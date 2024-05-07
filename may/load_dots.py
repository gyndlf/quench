# -*- coding: utf-8 -*-
"""
Created on Tue May  7 10:57:46 2024

Load electrons into the double dot.

Use this file by importing it into your function or running it in the console.

@author: J Zingel
"""

import time

# Having a high voltage means that electrons are able to flow.
# Low voltages means that the gates are closed.
# Raised = high voltage = open gate / transport
# Lowered = low voltage = closed gate / transport

def flushdots(si, low=1.0, high=1.7):
    """Pulse the P1 and P2 gates to remove all electrons from the dots"""
    tic = time.time()
    si.P1(low)
    si.P2(low)
    print(f"Flushed out to {low}V, raising to {high}V")
    time.sleep(0.5)
    si.P1(high)
    si.P2(high)
    print(f"Done. Took {time.time()-tic} seconds.")
    

def loaddots(si, high=1.0):
    """Load the electrons into the dots"""
    tic = time.time()
    si.SETB(high)
    time.sleep(0.5)
    si.SETB(0)
    print(f"Done. Took {time.time()-tic} seconds.")

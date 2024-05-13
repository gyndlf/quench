# -*- coding: utf-8 -*-
"""
Created on Tue May  7 10:57:46 2024

Load electrons into the double dot.

Use this file by importing it into your function or running it in the console.

@author: jzingel
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


# The following are some helper methods for using with the MDAC

def output_checker(gate):
    '''Checks the output of any gate or pin connected to the MDAC.'''
    print(' NAME:      ', gate.name, '\n',
    'CHANNEL:   ', gate.source.name, '\n',
    'ground:    ', gate.source.gnd(),'\n',
    'microd:    ', gate.source.microd(),'\n',
    'smc:       ', gate.source.smc(),'\n',
    'dac_output:', gate.source.dac_output(),'\n',
    'bus:       ', gate.source.bus(),'\n',
    'voltage:   ', gate.source.voltage())


def output_checker_all(gb_control_si):
    """Get the current status of all the gates according to Gooseberry"""
    smc_gates = [gb_control_si.RST_N,
          gb_control_si.MOSI,
          gb_control_si.MISO,
          gb_control_si.SCLK,
          gb_control_si.SS_N,
          gb_control_si.APBCLK,
          gb_control_si.DTEST_1,
          gb_control_si.DTEST_2,
          gb_control_si.ATEST,
          gb_control_si.TMODE, 
          gb_control_si.VICL,
          gb_control_si.VLFG,
          gb_control_si.VHFG]

    microd_gates = [gb_control_si.VDD1P8, 
          gb_control_si.VDD1P0, 
          gb_control_si.VSS1P8, 
          gb_control_si.VSS1P0,
          gb_control_si.VDD1P8_ANA,
          gb_control_si.BGN1P0, 
          gb_control_si.BGN1P8, 
          gb_control_si.BGP1P0,
          gb_control_si.BGP1P8]
    
    for gate in smc_gates:
        print('### SMC GATES ###')
        output_checker(gate)
    for gate in microd_gates:
        print('### MICROD GATES ###')
        output_checker(gate)
        
        
def get_all_voltages(mdac):
    """Get all current voltages set by the MDAC"""
    print("LCB:  ", mdac.ch03.voltage(), 'V')
    print("RCB:  ", mdac.ch08.voltage(), 'V')
    print("RG:   ", mdac.ch11.voltage(), 'V')
    print("ResB: ", mdac.ch14.voltage(), 'V')
    print("P3:   ", mdac.ch16.voltage(), 'V')
    print("P2:   ", mdac.ch19.voltage(), 'V')
    print("P1:   ", mdac.ch20.voltage(), 'V')
    print("SETB: ", mdac.ch22.voltage(), 'V')
    print("SRB:  ", mdac.ch26.voltage(), 'V')
    print("SLB:  ", mdac.ch31.voltage(), 'V')
    print("ST:   ", mdac.ch41.voltage(), 'V')
    print("bias: ", mdac.ch47.voltage(), 'V')
    print("VSS1P8:     ", mdac.ch02.voltage(), 'V')
    print("VSS1P0:     ", mdac.ch36.voltage(), 'V')
    print("VDD1P8:     ", mdac.ch34.voltage(), 'V')
    print("VDD1P0:     ", mdac.ch32.voltage(), 'V')
    print("VDD1P8_ANA: ", mdac.ch29.voltage(), 'V')
    print("BGN1P0:     ", mdac.ch24.voltage(), 'V')
    print("BGN1P8:     ", mdac.ch45.voltage(), 'V')
    print("BGP1P0:     ", mdac.ch46.voltage(), 'V')
    print("BGP1P8:     ", mdac.ch39.voltage(), 'V')
    print("RST:        ", mdac.ch15.voltage(), 'V')
    print("MOSI:       ", mdac.ch04.voltage(), 'V')
    print("SCLK:       ", mdac.ch13.voltage(), 'V')
    print("SS_N:       ", mdac.ch09.voltage(), 'V')
    print("APBCLK:     ", mdac.ch06.voltage(), 'V')
    print("VICL:       ", mdac.ch05.voltage(), 'V')
    print("VLFG:       ", mdac.ch07.voltage(), 'V')
    print("VHFG:       ", mdac.ch10.voltage(), 'V')
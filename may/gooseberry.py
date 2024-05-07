# -*- coding: utf-8 -*-
"""
Created on Tue May  7 10:31:54 2024

Connect to Gooseberry.

This controls the J1 and J2 interaction gates on the CMOS. It is somehow in series (parallel?) with the MDAC in this regard.

@author: J Zingel
"""

from quench.libraries import broom
broom.sweep()

import qcodes as qc
from qcodes import Station

from monty import Monty
import MDAC
import qcodes_measurements as qcm
from qcodes_measurements.device.states import ConnState, DigitalDevice, GateMode, DigitalMode, SPIController

from gb_spyder import Gooseberry


#%% MDAC Helper functions

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
    

#%% Gooseberry Definitions


def connect_to_gb(mdac):
    """Connects to GB and returns the instrument (legacy of gb_control_si)"""
    
    print('Loading GB driver and connecting')
    
    # Ignore station configuration since we don't save to it anymore
    #try:
    #    scfg.remove_component("Gooseberry")
    #except KeyError:
    #    pass
    
    gb_raw = DigitalDevice("Gooseberry")
    gb_raw.v_high(1.8)
    gb_raw.v_low(0)
    
    # # Power supply - converted to gate
    #gb_raw.add_gate("VDD1P0",  mdac.ch01, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    gb_raw.add_gate("VSS1P8",   mdac.ch02, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb_raw.add_gate("VDD1P8",  mdac.ch27, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb_raw.add_gate("VDD1P0",  mdac.ch28, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb_raw.add_gate("VSS1P0",  mdac.ch30, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    gb_raw.add_gate("VDD1P0",   mdac.ch32, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb_raw.add_gate("VSS1P8",  mdac.ch33, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    gb_raw.add_gate("VDD1P8",   mdac.ch34, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb_raw.add_gate("VSS1P0",  mdac.ch35, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    gb_raw.add_gate("VSS1P0",   mdac.ch36, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb.add_gate("VSS1P8_CL_B", mdac.ch38, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb.add_gate("VDD1P0_CL_E", mdac.ch41, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    
    gb_raw.add_gate("VDD1P8_ANA", mdac.ch29, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb_raw.add_gate("VDD1P8_ANA_B", mdac.ch38, max_step=2, state=ConnState.FLOAT, default_mode=GateMode.FREE)
    
    # Back Gates
    gb_raw.add_gate("BGN1P0", mdac.ch24, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    gb_raw.add_gate("BGP1P8", mdac.ch45, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    gb_raw.add_gate("BGN1P8", mdac.ch39, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    gb_raw.add_gate("BGP1P0", mdac.ch46, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    
    # SPI and Control Channels
    gb_raw.add_digital_gate("RST_N",    mdac.ch15, io_mode=DigitalMode.PROBE_OUT) # RF back 4
    gb_raw.add_digital_gate("MOSI",     mdac.ch04, io_mode=DigitalMode.PROBE_OUT) # RF back 5 
    gb_raw.add_digital_gate("MISO",     mdac.ch12, io_mode=DigitalMode.IN)        # RF back 1 check
    gb_raw.add_digital_gate("SCLK",     mdac.ch13, io_mode=DigitalMode.PROBE_OUT) # RF front 5
    gb_raw.add_digital_gate("SS_N",     mdac.ch09, io_mode=DigitalMode.PROBE_OUT) # RF back 3
    gb_raw.add_digital_gate("APBCLK",   mdac.ch06, io_mode=DigitalMode.PROBE_OUT) # RF back 6
    
    
    gb_raw.add_digital_gate("DTEST_1", mdac.ch18, io_mode=DigitalMode.IN) # RF center 3 
    gb_raw.add_digital_gate("DTEST_2", mdac.ch17, io_mode=DigitalMode.IN) # RF center 4 
    gb_raw.add_digital_gate("ATEST",   mdac.ch23, io_mode=DigitalMode.IN) # RF center 1
    gb_raw.add_digital_gate("TMODE",   mdac.ch21, io_mode=DigitalMode.IN) # RF center 2
    
    # Analog Gates
    # gb_raw.add_gate("VICL", mdac.ch05, rate=0.5, state=ConnState.SMC, default_mode=GateMode.FREE) # RF back 2
    # gb_raw.add_gate("VLFG", mdac.ch07, rate=0.5, state=ConnState.SMC, default_mode=GateMode.FREE) # RF front 7
    # gb_raw.add_gate("VHFG", mdac.ch10, rate=0.5, state=ConnState.SMC, default_mode=GateMode.FREE) # RF front 8
    gb_raw.add_gate("VICL", mdac.ch05, rate=0.5, state=ConnState.PROBE, default_mode=GateMode.FREE) # RF back 2
    gb_raw.add_gate("VLFG", mdac.ch07, rate=0.5, state=ConnState.PROBE, default_mode=GateMode.FREE) # RF front 7
    gb_raw.add_gate("VHFG", mdac.ch10, rate=0.5, state=ConnState.PROBE, default_mode=GateMode.FREE) # RF front 8
    
    spic = SPIController(gb_raw, "GB_SPI", gb_raw.MOSI, gb_raw.MISO, gb_raw.SCLK, gb_raw.SS_N, clk_rate=100)
    gb_raw.add_submodule("SPI", spic)
    
    # No longer using qcodes measurements
    #add_device_to_scfg(scfg, gb_raw)
    
    # Don't need complex importing system (just use return values!)
    #import importlib
    #import gb_spyder as gb_mod
    #gb_mod = importlib.reload(gb_mod)
    #Gooseberry = gb_mod.Gooseberry
    
    return Gooseberry(gb_raw)
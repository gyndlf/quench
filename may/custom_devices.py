# -*- coding: utf-8 -*-
"""
Created on Tue May  7 10:31:54 2024

Create custom devices that are really just remappings of the MDAC and Gooseberry ports.

Use this file by importing it into your function or running it in the console.

@author: jzingel
"""

from qcodes_measurements.device import DigitalDevice, DigitalMode, SPIController, Device, BB
from qcodes_measurements.device.states import ConnState, GateMode

# Get Gooseberry qcodes driver
from gb_spyder import Gooseberry


def newSiDot(mdac):
    """Create a new Si device with named gates using qcodes_measurements"""
    BB1 = BB("Breakout_box_top")
    BB2 = BB("Breakout_box_bot")
    si = Device("Si28_quantum_dot")
    
    # Si gates CHANGE AS NECESSARY
    si.add_gate("test_gate", mdac.ch48, state=ConnState.SMC, default_mode="FREE")
    si.add_gate("LCB",          BB1.ch15.connect_dac(mdac.ch03), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("RCB",          BB2.ch09.connect_dac(mdac.ch08), state=ConnState.SMC, default_mode="FREE") # channel 35
    si.add_gate("RG",           BB2.ch17.connect_dac(mdac.ch11), state=ConnState.SMC, default_mode="FREE") # channel 41
    #si.add_gate("Res",          BB1.ch18.connect_dac(mdac.ch14), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("ResB",         BB1.ch17.connect_dac(mdac.ch14), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("P3",           BB1.ch19.connect_dac(mdac.ch16), state=ConnState.SMC, default_mode="FREE")
    #si.add_gate("J2",           BB1.ch20.connect_dac(mdac.ch20), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("P2",           BB1.ch13.connect_dac(mdac.ch19), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("P1",           BB1.ch04.connect_dac(mdac.ch20), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("SETB",         BB1.ch02.connect_dac(mdac.ch22), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("SRB",          BB2.ch04.connect_dac(mdac.ch26), state=ConnState.SMC, default_mode="FREE") # channel 29
    si.add_gate("SLB",          BB2.ch06.connect_dac(mdac.ch31), state=ConnState.SMC, default_mode="FREE") # channel 31
    si.add_gate("ST",           BB1.ch10.connect_dac(mdac.ch41), state=ConnState.SMC, default_mode="FREE")
    si.add_gate("bias",         BB1.ch25.connect_dac(mdac.ch47), state=ConnState.SMC, default_mode="FREE") # fake BB gate
    #si.add_gate("Unused_Ohmic", BB1.ch24.connect_dac(mdac.ch44), state=ConnState.SMC, default_mode="FREE")
    si.add_ohmic("S",  BB1.ch09)
    si.add_ohmic("D",  BB1.ch01)
    si.add_ohmic("Res", BB1.ch18)
    return si


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



def link_j_on_gb(mdac, gb_control_si):
    """Link J1 and J2 on gooseberry to share the same voltages"""
    print('Ramping J1 down to 0V')
    mdac.ch05.ramp(0, 0.05)
    mdac.ch05.block()
    
    print('Coupling J1, J2 together')
    gb_control_si.disable_all_gates()
    gb_control_si.enable_multiple_gates([18, 20])
    
    print('Ramping J1, J2 to loading values')
    mdac.ch05.ramp(3.5, 0.05)
    mdac.ch05.block()
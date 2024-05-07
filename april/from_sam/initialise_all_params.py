# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 13:05:55 2024

@author: Sam Bartee

Initialises all Qcodes and GB parameters needed for operation.
"""
#%% 

# Import fundamental modules

import time
import sys
import numpy as np
import scipy, scipy.constants
import matplotlib.pyplot as plt
import logging
from IPython.display import Image
from tqdm import tqdm
import os

# Import Qcodes
import sys
sys.path.append('/Users/LD2007/anaconda3/envs/qcodes/lib/site-packages')

import qcodes as qc
from qcodes import ChannelList, Parameter, Station, Measurement
from qcodes.dataset.plotting import plot_by_id
from qcodes.dataset.data_set import load_by_id, load_by_counter
from qcodes import load_or_create_experiment, load_by_id

# Import Qcodes measurements
sys.path.append('/Users/LD2007/Documents/qcodes_measurements')

import qcodes_measurements as qcm
from qcodes_measurements import logging

import qcodes_measurements.plot as qcm_plot
#from qcodes_measurements.qcodes_measurements.plot.plot_tools import *
from qcodes_measurements.device import *
from qcodes_measurements.device import GateWrapper, DigitalDevice, Register

# Import custom scripts/drivers
sys.path.append('/Users/LD2007/Documents/Si_CMOS')

from quick_sweeps import quick_iv
#from useful_functions import *

# MDAC
import MDAC

#RF Switch
import qcodes.instrument_drivers.Minicircuits.USB_SPDT as switch

# Fast2d sweep code
#import fast2d

# Gooseberry
from gb_spyder import Gooseberry

#%% Create some useful functions

def output_changer(gate, microd = 'open', smc = 'open', dac_output = 'open', ground = 'open', bus = 'open', microd_connection = False, smc_connection = False, float_gate = False, ground_gate = False, do_print=True):
    '''Changes the output of any connection to the MDAC, user specified.'''
    if microd_connection:
        gate.source.smc('open') 
        gate.source.bus('open')
        gate.source.dac_output('close')
        gate.source.gnd('open')
        gate.source.microd('close')
    if smc_connection:
        gate.source.smc('close') 
        gate.source.bus('open')
        gate.source.dac_output('close')
        gate.source.gnd('open')
        gate.source.microd('open')
    if float_gate:
        gate.source.smc('open') 
        gate.source.bus('open')
        gate.source.dac_output('open')
        gate.source.gnd('open')
        gate.source.microd('open')
    if ground_gate:
        gate.source.smc('open') 
        gate.source.bus('open')
        gate.source.dac_output('open')
        gate.source.gnd('close')
        gate.source.microd('open')
    else:
        gate.source.smc(smc) 
        gate.source.bus(bus)
        gate.source.dac_output(dac_output)
        gate.source.gnd(ground)
        gate.source.microd(microd)
    if do_print:
        print(' NAME:      ', gate.name, '\n',
        'CHANNEL:   ', gate.source.name, '\n',
        'ground:    ', gate.source.gnd(),'\n',
        'microd:    ', gate.source.microd(),'\n',
        'smc:       ', gate.source.smc(),'\n',
        'dac_output:', gate.source.dac_output(),'\n',
        'bus:       ', gate.source.bus(),'\n',
        'voltage:   ', gate.source.voltage())

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

def get_all_voltages():
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
 
def save_voltages():
    filepath = os.path.join(str(m.path), 'voltages.txt')
    with open(filepath, 'w') as f:
        f.write(
    "LCB:  "+str(mdac.ch03.voltage())+'V\n'
    "RCB:  "+str(mdac.ch08.voltage())+ 'V\n'
    "RG:   "+str(mdac.ch11.voltage())+ 'V\n'
    "ResB: "+str(mdac.ch14.voltage())+ 'V\n'
    "P3:   "+str(mdac.ch16.voltage())+ 'V\n'
    "P2:   "+str(mdac.ch19.voltage())+ 'V\n'
    "P1:   "+str(mdac.ch20.voltage())+ 'V\n'
    "SETB: "+str(mdac.ch22.voltage())+ 'V\n'
    "SRB:  "+str(mdac.ch26.voltage())+ 'V\n'
    "SLB:  "+str(mdac.ch31.voltage())+ 'V\n'
    "ST:   "+str(mdac.ch41.voltage())+ 'V\n'
    "bias: "+str(mdac.ch47.voltage())+ 'V\n'
    "VSS1P8:     "+str(mdac.ch02.voltage())+ 'V\n'
    "VSS1P0:     "+str(mdac.ch36.voltage())+ 'V\n'
    "VDD1P8:     "+str(mdac.ch34.voltage())+ 'V\n'
    "VDD1P0:     "+str(mdac.ch32.voltage())+ 'V\n'
    "VDD1P8_ANA: "+str(mdac.ch29.voltage())+ 'V\n'
    "BGN1P0:     "+str(mdac.ch24.voltage())+ 'V\n'
    "BGN1P8:     "+str(mdac.ch45.voltage())+ 'V\n'
    "BGP1P0:     "+str(mdac.ch46.voltage())+ 'V\n'
    "BGP1P8:     "+str(mdac.ch39.voltage())+ 'V\n'
    "RST:        "+str(mdac.ch15.voltage())+ 'V\n'
    "MOSI:       "+str(mdac.ch04.voltage())+ 'V\n'
    "SCLK:       "+str(mdac.ch13.voltage())+ 'V\n'
    "SS_N:       "+str(mdac.ch09.voltage())+ 'V\n'
    "APBCLK:     "+str(mdac.ch06.voltage())+ 'V\n'
    "VICL:       "+str(mdac.ch05.voltage())+ 'V\n'
    "VLFG:       "+str(mdac.ch07.voltage())+ 'V\n'
    "VHFG:       "+str(mdac.ch10.voltage())+ 'V\n')   
 
def output_checker_all():
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

#%%

def connect_APBCLK_to_mdac():
    print('Disconnecting OPX')
    rfswitch.all(2)
    print('Connecting MDAC')
    output_changer(gb_control_si.APBCLK, microd='open', smc='close', dac_output='close', \
                   ground='open', bus='open')
        
def connect_APBCLK_to_OPX():
    print('Disconnecting MDAC')
    output_changer(gb_control_si.APBCLK, microd='open', smc='open', dac_output='open', \
                   ground='open', bus='open')
    print('Connecting OPX')
    rfswitch.all(1)
   
def en_charge_lock(): # connect to VICL
    gb_control_si.registers["CTL1"]["CHRG_SEL"] = 0x3
    gb_control_si.write_registers(gb_control_si.registers["CTL1"])

def disable_charge_lock(): # disconnect from VICL
    gb_control_si.registers["CTL1"]["CHRG_SEL"] = 0x2
    gb_control_si.write_registers(gb_control_si.registers["CTL1"])

def connect_to_gb():
    
    global gb_control_si
    
    # ConnState = qcm.device.states.ConnState
    # GateMode = qcm.device.states.GateMode
    # DigitalDevice = qcm.device.DigitalDevice
    # DigitalMode = qcm.device.DigitalMode
    
    print('Loading GB driver and connecting')
    
    # Load GB and components, connect to device
    try:
        scfg.remove_component("Gooseberry")
    except KeyError:
        pass
    
    gb_raw = DigitalDevice("Gooseberry")
    gb_raw.v_high(1.8)
    gb_raw.v_low(0)
    
    # # Power supply - converted to gate
    #gb_raw.add_gate("VDD1P0",             mdac.ch01, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    gb_raw.add_gate("VSS1P8",             mdac.ch02, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb_raw.add_gate("VDD1P8",             mdac.ch27, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb_raw.add_gate("VDD1P0",             mdac.ch28, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb_raw.add_gate("VSS1P0",             mdac.ch30, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    gb_raw.add_gate("VDD1P0",           mdac.ch32, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb_raw.add_gate("VSS1P8",             mdac.ch33, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    gb_raw.add_gate("VDD1P8",             mdac.ch34, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb_raw.add_gate("VSS1P0",             mdac.ch35, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    gb_raw.add_gate("VSS1P0",           mdac.ch36, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb.add_gate("VSS1P8_CL_B",           mdac.ch38, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb.add_gate("VDD1P0_CL_E",           mdac.ch41, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    
    gb_raw.add_gate("VDD1P8_ANA",         mdac.ch29, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    #gb_raw.add_gate("VDD1P8_ANA_B",       mdac.ch38, max_step=2, state=ConnState.FLOAT, default_mode=GateMode.FREE)
    
    # Back Gates
    gb_raw.add_gate("BGN1P0", mdac.ch24, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    gb_raw.add_gate("BGP1P8", mdac.ch45, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    gb_raw.add_gate("BGN1P8", mdac.ch39, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    gb_raw.add_gate("BGP1P0", mdac.ch46, max_step=2, state=ConnState.DAC, default_mode=GateMode.FREE)
    
    # SPI and Control Channels
    gb_raw.add_digital_gate("RST_N",      mdac.ch15, io_mode=DigitalMode.PROBE_OUT) # RF back 4
    gb_raw.add_digital_gate("MOSI",       mdac.ch04, io_mode=DigitalMode.PROBE_OUT) # RF back 5 
    gb_raw.add_digital_gate("MISO",       mdac.ch12, io_mode=DigitalMode.IN)        # RF back 1 check
    gb_raw.add_digital_gate("SCLK",       mdac.ch13, io_mode=DigitalMode.PROBE_OUT) # RF front 5
    gb_raw.add_digital_gate("SS_N",       mdac.ch09, io_mode=DigitalMode.PROBE_OUT) # RF back 3
    gb_raw.add_digital_gate("APBCLK",     mdac.ch06, io_mode=DigitalMode.PROBE_OUT) # RF back 6
    
    
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
    
    add_device_to_scfg(scfg, gb_raw)
    
    #import importlib
    #import gb_spyder as gb_mod
    #gb_mod = importlib.reload(gb_mod)
    #Gooseberry = gb_mod.Gooseberry
    
    gb_control_si = Gooseberry(gb_raw)


#%% Start Qcodes database

# Start experiment
exp_name = 'OC21_cooldown'
sample_name = 'OC21'

#exp = load_or_create_experiment(exp_name, sample_name)
#print('Experiment loaded. Last counter no:', exp.last_counter)

def add_device_to_scfg(scfg, device, mon_only=False):
    if not mon_only:
        qc.Station.default.add_component(device, device.name)

    monitor_params = []
    for gate in device.gates:
        monitor_params.append(gate.voltage)
        gate.state.label = f"{gate.voltage.label}_state"
        monitor_params.append(gate.state)
        
    if hasattr(device, "digital_gates"):
        for gate in device.digital_gates:
            monitor_params.append(gate.voltage)
            gate.state.label = f"{gate.voltage.label}_state"
            monitor_params.append(gate.state)

    for ohmic in device.ohmics:
        ohmic.state.label = f"{ohmic.voltage.label[:-5]}_state"
        monitor_params.append(ohmic.state)

    # qc.Monitor(*qc.Monitor.running._parameters, *monitor_params)

    print(f"Initialized {device.name}")
    
#%% Measure/record fridge temps

import requests
from functools import partial
from qcodes import Instrument

class FridgeTemps(Instrument):
    def __init__(self, fridge, url):
        super().__init__(fridge)
        self.url = url
        
        params = requests.get(url)
        if params.status_code != 200:
            raise RuntimeError("Unable to query fridge")
        params = set(params.json().keys())
        params.remove("Time")
        params = tuple(params)
        self.params = params
        
        for param in params:
            self.add_parameter(f"{param}_temp",
                               unit="K",
                               label=f"{param}",
                               get_cmd=partial(self.get_param, param),
                               snapshot_get=False)
        
    def get_param(self, param):
        temps = requests.get(self.url)
        if temps.status_code != 200:
            raise RuntimeError("Unable to query fridge")
        temps = temps.json()
        return temps[param]

#%% Connect to tools

# close instruments 
try:
    mdac = qc.Instrument.find_instrument("mdac")
    mdac.close()
except KeyError:
    print('Attempting to remove instrument with name mdac. Does not exist')

scfg = Station(config_file='measurements/system1.yaml')
mdac = MDAC.MDAC('mdac', 'ASRL11::INSTR')

#rfswitch = switch.USB_SPDT('rf4')

# from qcodes.instrument_drivers.oxford.MercuryiPS_VISA import MercuryiPS
# magnet = MercuryiPS('magnet', 'TCPIP0::192.168.0.106::7020::SOCKET')

#%% Init si device

ConnState = qcm.device.states.ConnState
GateMode = qcm.device.states.GateMode
DigitalDevice = qcm.device.DigitalDevice
DigitalMode = qcm.device.DigitalMode

# Si gates CHANGE AS NECESSARY

BB1 = qcm.device.BB("Breakout_box_top")
BB2 = qcm.device.BB("Breakout_box_bot")
si = qcm.device.Device("Si28_quantum_dot")

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

add_device_to_scfg(scfg, si)

#%% Connect to GB

print("Connecting to GB...")
connect_to_gb()

#%% In case of power failure

# The MDAC connections will reset. Uncomment these to make MDAC connections good

# GB - MDAC microd connections
output_changer(gb_control_si.VDD1P8, microd = 'close', smc = 'open', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.VDD1P0, microd = 'close', smc = 'open', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.VSS1P8, microd = 'close', smc = 'open', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.VSS1P0, microd = 'close', smc = 'open', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.VDD1P8_ANA, microd = 'close', smc = 'open', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.BGP1P8, microd = 'close', smc = 'open', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.BGP1P0, microd = 'close', smc = 'open', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.BGN1P8, microd = 'close', smc = 'open', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.BGN1P0, microd = 'close', smc = 'open', \
                dac_output = 'close', bus = 'open', ground = 'open')
    
# GB - MDAC SMC connections
output_changer(gb_control_si.RST_N, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.MOSI, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.SCLK, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.SS_N, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.APBCLK, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.VICL, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.VLFG, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(gb_control_si.VHFG, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
    
# GB test channels - MDAC SMC connections
output_changer(gb_control_si.MISO, microd = 'open', smc = 'close', \
                dac_output = 'open', bus = 'open', ground = 'open')
output_changer(gb_control_si.DTEST_1, microd = 'open', smc = 'close', \
                dac_output = 'open', bus = 'open', ground = 'open')
output_changer(gb_control_si.DTEST_2, microd = 'open', smc = 'close', \
                dac_output = 'open', bus = 'open', ground = 'open')
output_changer(gb_control_si.ATEST, microd = 'open', smc = 'close', \
                dac_output = 'open', bus = 'open', ground = 'open')
output_changer(gb_control_si.TMODE, microd = 'open', smc = 'close', \
                dac_output = 'open', bus = 'open', ground = 'open')
    
# Si channels
output_changer(si.LCB, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(si.RCB, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(si.RG, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(si.ResB, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(si.P3, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(si.P2, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(si.P1, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(si.SETB, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(si.SRB, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(si.SLB, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(si.ST, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
output_changer(si.bias, microd = 'open', smc = 'close', \
                dac_output = 'close', bus = 'open', ground = 'open')
    
#%% Power on GB

'''GB is bonded to gates J1 and J2. Need to connect APBCLK to MDAC (via RF 
switch, if not already connected), ramp down VICL to 0V, disable all gates 
(GB), power down, power up, reset, connect VICL to appropriate cells,
ramp gate up.'''

'''
IF CHARGE-LOCKED, TRY TO MAKE SURE VICL AND SI GATE VALUE ARE THE SAME BEFORE
DISABLING CHARGE LOCKING TO AVOID DAMAGING J1 AND/OR J2!
'''

'''
MONITOR MXC TEMPERATURE WHILE DOING THIS STEP. IF TEMPERATURE RISES RAPIDLY
AND ABOVE 30MK, SHUT DOWN IMMEDIATELY. SOMETHING IS SHORTED AND DUMPING 
POWER.
'''

'''
IF YOU WANT TO PERFORM CHARGE LOCKING, CONTACT ME FOR FURTHER INSTRUCTIONS.
'''

connect_APBCLK_to_mdac()
time.sleep(2) 
en_charge_lock()

print('Ramping P gates up, J down to preserve electron count...')
# si.P1(2.1)
# si.P2(2.1)
mdac.ch05.ramp(0.0, 0.1)
mdac.ch05.block()
time.sleep(5)

print('Disabling GB gates...')
gb_control_si.disable_all_gates()

print('Restarting GB...')
gb_control_si.power_down()
time.sleep(1)
gb_control_si.power_up()
time.sleep(1)
gb_control_si.reset()

print('Ramping J1...')
# gb_control_si.enable_gate(20)  # close GB gate to J1
gb_control_si.enable_multiple_gates([18, 20])

time.sleep(1)
#mdac.ch05.ramp(3.5, 0.1) # VICL, has a 2.5:1 divider
#mdac.ch05.block()
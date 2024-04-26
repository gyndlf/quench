# -*- coding: utf-8 -*-
"""
Created on Fri Feb  3 10:23:28 2023

@author: LD2007

Custom restart that doesn't initialise GB, only connects to MDAC for Si gates.'
"""
# Restart no GB

from startup import *
import qcodes_measurements
# import restart_gb
import restart_no_gb

#%%
# Change P1 and/or P2 voltages

si.P1(1.839) # Lower P1 shifts detuning right
si.P2(1.931) # Lower P2 shifts detuning left


#%%

si.SRB(1.0)
si.SLB(1.0)
si.ST(3.4)

# Change J1 value 
# Can only be done if GB is NOT chargelocked

# mdac.ch05.ramp(3.4, 0.05)
# mdac.ch05.ramp(3.32, 0.05) # goes through a 2.5:1 divider
# mdac.ch05.ramp(3.25, 0.05)
# mdac.ch05.block()
#%%

mdac.ch41.smc('close')
mdac.ch31.smc('close')
mdac.ch26.smc('close')
mdac.ch03.smc('close')
mdac.ch08.smc('close')
mdac.ch11.smc('close')
mdac.ch14.smc('close')
mdac.ch16.smc('close')
mdac.ch19.smc('close')
mdac.ch20.smc('close')
mdac.ch22.smc('close')



#%%
# Connect J1 to MDAC and OPX+ for RT control

# connect_APBCLK_to_mdac()
# time.sleep(2)
# en_charge_lock()

#%%
# Use GB to control J1
# J1 is chargelocked, and APBCLK of GB is connected to OPX trigger for triggering

# disable_charge_lock()
# time.sleep(2)
# connect_APBCLK_to_OPX()

#%%
# get all current voltages
# does not tell status of GB

# get_all_voltages()
si.P1(1.94)
si.P2(1.76)

#%% 
# Load four electrons into device
# J1 must be connected to the MDAC for this to work properly

# print('Ramping gates (Except J1, J2) to loading values')
si.SRB(0.92)
si.SLB(0.92)
si.ST(4.5) 
si.bias(0.01)
si.RG(2.0)
si.P1(1.7) # previous 1.7
si.P2(1.7)
si.P3(1.8) # previous 1.8
si.RCB(0.15)
si.LCB(0.15)
# mdac.ch05.ramp(0, 0.05)
# mdac.ch05.block()
si.ResB(1.8)

print('Ramping J1 down to 0V')
mdac.ch05.ramp(0, 0.05)
mdac.ch05.block()

# print('Coupling J1, J2 together')
gb_control_si.disable_all_gates()
gb_control_si.enable_multiple_gates([18,20])

# print('Ramping J1, J2 to loading values')
mdac.ch05.ramp(2.85, 0.05)
mdac.ch05.block()

# # print('Ramping P1 and P2 to 2.1V to preserve electron count')
# # # P1 and P2 high to (hopefully) keep electrons in
# # # si.P1(1.7) # loads two electrons in
# # # si.P2(1.7)
si.P1(1.8) # previous 1.8
si.P2(1.8)

print('Ramping VICL to 0V')
# # ramp J1, J2 to 0V and then back again
mdac.ch05.ramp(0, 0.05)
mdac.ch05.block()

# print('Disabling GB outCL gates')

gb_control_si.disable_all_gates()

print('Enabling J1 only')
gb_control_si.enable_gate(20)

# time.sleep(2)

# # # relocation
print('Ramping P1 and P2 back down to previous values')
si.P1(1.845) # 1.8415
si.P2(1.925) # 1.925

# print('Ramping J1 back to original value')
mdac.ch05.ramp(3.33, 0.05)
mdac.ch05.block()

# print('Electrons loaded! Tuning into isolation mode...')
# # # isolating
si.ResB(0)
si.P3(0)




print("Done!")

#%%

# gb_control_si.power_up()
# time.sleep(1)
# gb_control_si.reset()

# gb_control_si.power_down()

#%%

connect_to_gb()

#%%
def connect_to_gb():
    
    global gb_control_si
    
    ConnState = qcodes_measurements.device.states.ConnState
    GateMode = qcodes_measurements.device.states.GateMode
    DigitalDevice = qcodes_measurements.device.DigitalDevice
    DigitalMode = qcodes_measurements.device.DigitalMode
    
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
    
    import importlib
    import gb_spyder as gb_mod
    gb_mod = importlib.reload(gb_mod)
    Gooseberry = gb_mod.Gooseberry
    
    gb_control_si = Gooseberry(gb_raw)

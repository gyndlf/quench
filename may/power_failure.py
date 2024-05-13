# -*- coding: utf-8 -*-
"""
Created on Mon May 13 10:19:51 2024

@author: LD2007
"""


# Inherited from stability_diagram_OLD.py

from quench.libraries import broom
broom.sweep()

from qcodes import Instrument
import MDAC

# Import the neighbouring files. In may/
from quench.may.custom_devices import connect_to_gb, newSiDot


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


try:
    mdac = Instrument.find_instrument("mdac")
    mdac.close()
except KeyError:
    print('Attempting to remove instrument with name mdac. Does not exist')

mdac = MDAC.MDAC('mdac', 'ASRL11::INSTR')

# Create our custom MDAC mappings
gb_control_si = connect_to_gb(mdac)
si = newSiDot(mdac)

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
    

    
#%%


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

import time
#connect_APBCLK_to_mdac()
#time.sleep(2) 
#en_charge_lock()

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
gb_control_si.enable_gate(20)  # close GB gate to J1
# gb_control_si.enable_multiple_gates([18, 20])

time.sleep(1)
mdac.ch05.ramp(3.5, 0.1) # VICL, has a 2.5:1 divider
mdac.ch05.block()
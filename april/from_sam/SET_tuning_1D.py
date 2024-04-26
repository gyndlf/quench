# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 14:46:17 2024

@author: LD2007

SET 1D Tuning
"""
lockin_top = scfg.load_instrument('sr860_top')

#%%

'''SET 1D sweep:
Sweeps ST.'''

# TO DO:
# Sweep ST between ~3V - 4.5V (MAXIMUM)
# Step SLB, SRB between ~0.7V - ~1.2V


si.SLB(0.93)
si.SRB(0.93)

gate_range = np.linspace(3.4, 3.6, 201)
data = np.full(len(gate_range), np.nan)
title = "ST voltage vs current (lockin). "
 
meas = Measurement()
meas.register_parameter(lockin_top.X)
meas.register_parameter(lockin_top.Y)
meas.register_parameter(lockin_top.R)
meas.register_parameter(lockin_top.P)
meas.register_parameter(si.ST)
# meas.register_parameter(si.SRB)
# meas.register_parameter(si.SLB)

with meas.run() as datasaver:
    for set_v in tqdm(gate_range):
        si.ST(set_v)
        # si.SRB.set(set_v)
        # si.SLB.set(set_v)
        time.sleep(0.1)
        
        X = lockin_top.X()
        Y = lockin_top.Y()
        R = lockin_top.R()
        P = lockin_top.P()
        
        datasaver.add_result((si.ST, set_v),
                             (lockin_top.R, R),
                             (lockin_top.X, X),
                             (lockin_top.Y, Y),
                             (lockin_top.P, P))
        
    dataid = datasaver.run_id 

run_id = dataid
data = load_by_id(run_id)
print(data)

ST_voltage = data.get_parameter_data('Si28_quantum_dot_ST')['Si28_quantum_dot_ST']['Si28_quantum_dot_ST']
lockin_current = data.get_parameter_data('sr860_top_R')['sr860_top_R']['sr860_top_R']

plt.figure()
plt.plot(ST_voltage, lockin_current)
plt.xlabel('ST voltage (V)')
plt.ylabel('Lockin current (A)')
plt.title('Run: {}'.format(run_id))

#%%

ST_gate_range = np.linspace(3, 4.4, 100)
SRB_gate_range = np.linspace(0.8, 1.2, 100)

meas = Measurement()
meas.register_parameter(lockin_top.X)
meas.register_parameter(lockin_top.Y)
meas.register_parameter(lockin_top.R)
meas.register_parameter(lockin_top.P)
meas.register_parameter(si.ST)
meas.register_parameter(si.SRB)

with meas.run() as datasaver:
    for set_v in tqdm(SRB_gate_range):
        si.SRB(set_v)
        # si.SRB.set(set_v)
        # si.SLB.set(set_v)
        
        for sweep_v in ST_gate_range:
        
            time.sleep(0.1)
            
            X = lockin_top.X()
            Y = lockin_top.Y()
            R = lockin_top.R()
            P = lockin_top.P()
            
            datasaver.add_result((si.ST, sweep_v),
                                 (si.SRB, set_v)
                                 (lockin_top.R, R),
                                 (lockin_top.X, X),
                                 (lockin_top.Y, Y),
                                 (lockin_top.P, P))
        
    dataid = datasaver.run_id 
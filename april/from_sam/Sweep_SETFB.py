# -*- coding: utf-8 -*-
"""
Sweep the SET feedback set point, whilst measuring a charge anticrossing.
The anticrossing is used to find the set point with maximum sensitivity.

1/4/2021

Will Gilbert - UNSW
"""
#%%
from qm.QuantumMachinesManager import QuantumMachinesManager

from qm.qua import *
from Configuration import *
from AWG_config import *
from qm import SimulationConfig
import numpy as np
import matplotlib.pyplot as plt
import time
import datetime

start_time=time.time()

Nshots = 1
npts_vRead = 50
npts_setPt = 50

vRead_list=np.linspace(-0.000/unit_amp,0.00005/unit_amp,npts_vRead).tolist()
# vRead_list=np.linspace(-0.05/unit_amp,0.05/unit_amp,npts_vRead).tolist()
# vRead_list=np.linspace(0.1/unit_amp,0.25/unit_amp,npts_vRead).tolist()
# setPt_list=np.linspace(0.017,0.03,npts_setPt).tolist()
# setPt_list=np.linspace(0.005,0.05,npts_setPt).tolist()
setPt_list=np.linspace(-0.0188,-0.0184,npts_setPt).tolist()
# setPt_list=np.linspace(-0.182,-0.176,npts_setPt).tolist()

Nshots_total = Nshots * npts_vRead * npts_setPt
sequence_time = tShot # Estimate using only longest wait time
time_estimate = sequence_time * Nshots_total
print("Estimated time = " + str(datetime.timedelta(seconds=int(time_estimate))))

#%%
with program() as findRO:
    shotn = declare(int)
    vRead_qua = declare(fixed)
    set_pt_qua = declare(fixed)
    setVars.init_qua_vars()
    readVars.init_qua_vars()
    
    with for_each_(set_pt_qua,setPt_list):
        with for_(shotn,1,shotn<=Nshots,shotn+1):
            with for_each_(vRead_qua, vRead_list):
                # reset_phase('SRF')
                # Init
                readRef(readVars)
#                 initMixed()
                
#                 wait(2500,'J1')
#                 align()
#                 # Read
                readAndRamp(readVars, readpt=[-vRead_qua,0,vRead_qua])
                setVars.feedback(readVars, set_pt=set_pt_qua)
                wait(250000, 'SRF') # 1000us wait
                align()

                resetChannels()
                
    ramp_to_zero('SDC')
    resetChannels()
    
    with stream_processing():
        setVars.save_streams()
        readVars.save_streams()
        
# run program
m = MyStore(my_dictator, __file__)
QMm = QuantumMachinesManager(host=host_IP, port=port_num, store=m)
Qm1 = QMm.open_qm(config)

job = Qm1.execute(findRO)
res=job.result_handles
res.wait_for_all_values()

# SRF_READ_I = res.SDC_READ_I.fetch_all()['value']
# SRF_REF_I = res.SDC_REF_I.fetch_all()['value']
# SRF_DIFF_I = SRF_READ_I - SRF_REF_I
# STATES = res.STATES.fetch_all()['value']

readVars.fetch_streams(res)


# plt.figure()
# plt.hist(SRF_DIFF_I,100)
# plt.ylabel('Counts')
# plt.xlabel('DIFF voltage')
# plt.show()
# plt.figure()
# plt.hist(SRF_REF_I,100)
# plt.ylabel('Counts')
# plt.xlabel('Ref voltage')
# plt.show()

end_time=time.time()
print("Time elapsed: " + str(datetime.timedelta(seconds=int(end_time-start_time))))

# %%
bounds=[min(vRead_list)*unit_amp,max(vRead_list)*unit_amp,min(setPt_list),max(setPt_list)]

# SRF_REF_I_avg=np.mean(np.reshape(SRF_REF_I,(npts_setPt,Nshots,npts_vRead)),1)
# plt.figure()
# plt.set_cmap('turbo')
# plt.imshow(SRF_REF_I_avg,aspect='auto',extent=bounds,interpolation='none',origin='lower')
# plt.colorbar()
# plt.title('Read Reference')
# plt.xlabel('Read level detuning')
# plt.ylabel('SET set point')
# plt.show()

SRF_REF_avg=np.mean(np.reshape(readVars.SDC_REF,(npts_setPt,Nshots,npts_vRead)),1)
plt.figure()
plt.set_cmap('turbo')
plt.imshow(SRF_REF_avg,aspect='auto',extent=bounds,interpolation='none',origin='lower')
plt.colorbar()
plt.title('Read Reference')
plt.xlabel('Read level detuning')
plt.ylabel('SET set point')
plt.show()


# SRF_DIFF_I_avg=np.mean(np.reshape(SRF_DIFF_I,(npts_setPt,Nshots,npts_vRead)),1)
# plt.figure()
# plt.imshow(SRF_DIFF_I_avg,aspect='auto',extent=bounds,interpolation='none',origin='lower')
# plt.colorbar()
# plt.title('Difference')
# plt.xlabel('Read level detuning')
# plt.ylabel('SET set point')
# # plt.clim(-0.01,0.1)
# plt.show()

# STATES_avg=np.mean(np.reshape(STATES,(npts_setPt,Nshots,npts_vRead)),1)
# plt.figure()
# plt.imshow(STATES_avg,aspect='auto',extent=bounds,interpolation='none',origin='lower')
# plt.colorbar()
# plt.title('States')
# plt.xlabel('Read level detuning')
# plt.ylabel('SET set point')
# # plt.clim(-0.01,0.1)
# plt.show()
# #%%

# plt.figure()
# # plt.plot(STATES_avg[10,:])
# plt.plot(SRF_DIFF_I_avg[10,:])
# plt.title('States')
# plt.xlabel('Read level detuning')
# plt.ylabel('Readout current')
# # plt.clim(-0.01,0.1)
# plt.show()


#%% Plot SETFB
font = {'family' : 'normal',
        'weight' : 'bold',
        'size'   : 6}

plt.rc('font', **font)
setVars.fetch_streams(res)

plt.figure()
plt.hist(setVars.CORR)

plt.show()

plt.figure()
plt.plot(setVars.CORR)

plt.show()
# -*- coding: utf-8 -*-
"""
SET feedback protocol

Will Gilbert
22/4/21
"""

from qm.qua import *
from deviceConfig import *
import numpy as np
import matplotlib.pyplot as plt

# SETFB_DCsetpt = -0.070 # Lower gain / higher bandwidth setup
# SETFB_DCsetpt = -0.131 # 10us integration
# SETFB_DCsetpt = -0.0203 # 20us integration
# SETFB_DCsetpt = -0.890 # 40us integration
# SETFB_DCsetpt = -0.31 # 60us integration
# SETFB_DCsetpt = -0.31 # 80us integration
SETFB_DCsetpt = -0.1045 # 100us integration
SETFB_DCalpha = 0.21e1
SETFB_DCbeta = 0.0e-4
# SETFB_RFsetpt = 0.021 
# SETFB_RFalpha = 10e-4 / unit_amp
# SETFB_RFbeta = 0.0e-4

class SETFB(object):
    def __init__(self):
        self.SETFB_error = None
        self.SETFB_accum = None
        self.SETFB_corr = None
        self.SETFB_stream = None
        #self.alpha = 0e-4
        self.CORR_all = []
        
    def init_qua_vars(self):
        self.SETFB_error = declare(fixed, value=0)
        self.SETFB_accum = declare(fixed, value=0)
        self.SETFB_corr = declare(fixed, value=0)
#         self.SETFB_alpha = declare(fixed, value=SETFB_DCalpha)
        self.SETFB_stream = declare_stream()
        
    def feedback(self, readVars, set_pt=SETFB_DCsetpt):
        # SET Feedback
        assign(self.SETFB_error, (set_pt - readVars.SDCref))
        assign(self.SETFB_accum, self.SETFB_accum + self.SETFB_error)
        assign(self.SETFB_corr, SETFB_DCalpha * self.SETFB_error + SETFB_DCbeta * self.SETFB_accum)
        play('unit_ramp'*amp(self.SETFB_corr),'SDC')
        #play('unit_ramp'*amp(0.001),'SDC')
        save(self.SETFB_corr,self.SETFB_stream)
        
    def save_streams(self):
        self.SETFB_stream.save_all("SETFB_CORR")
        
    def fetch_streams(self, res):
        self.CORR = res.get('SETFB_CORR').fetch_all()['value']
        
        self.CORR_all = self.CORR_all + np.array(self.CORR).tolist()
        
    def plot(self):
        # minutes = np.array(readVars.TIMES_all) * 1e-9 / 60
        
        plt.figure()
        plt.plot(self.CORR_all)
        plt.xlabel('Shot #')
        plt.ylabel('Correction step')
        plt.show()
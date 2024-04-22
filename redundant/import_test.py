# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 10:23:52 2024

@author: LD2007
"""

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

#%%

# Import Qcodes
#sys.path.append('/Users/LD2007/anaconda3/envs/qcodes/lib/site-packages')

import qcodes as qc
from qcodes import ChannelList, Parameter, Station, Measurement
from qcodes.dataset.plotting import plot_by_id
from qcodes.dataset.data_set import load_by_id, load_by_counter
from qcodes import load_or_create_experiment, load_by_id


#%%
# Import Qcodes measurements

# Modify the path to access files
sys.path.append('/Users/LD2007/Documents/qcodes_measurements')

import qcodes_measurements as qcm
from qcodes_measurements import logging

import qcodes_measurements.plot as qcm_plot
#from qcodes_measurements.qcodes_measurements.plot.plot_tools import *
from qcodes_measurements.device import *
from qcodes_measurements.device import GateWrapper, DigitalDevice, Register

#%%

# Import custom libraries of scripts/drivers
sys.path.append('/Users/LD2007/Documents/Si_CMOS_james/libraries')

#from quick_sweeps import quick_iv
#from useful_functions import *

# MDAC
import MDAC

#RF Switch
import qcodes.instrument_drivers.Minicircuits.USB_SPDT as switch

# Fast2d sweep code
#import fast2d

# Gooseberry
from gb_spyder import Gooseberry
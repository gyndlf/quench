# -*- coding: utf-8 -*-
"""
Created on Fri Apr 26 12:30:24 2024

Rewrite the notebooks into a simple python file to perform a quick scan with SHFQC

@author: Zingel
"""

from quench.libraries import broom
broom.sweep()

#%%

from laboneq.dsl.device.device_setup import DeviceSetup
from laboneq.dsl.session import Session

#%%

# Connect to SHFQC

with open("measurements/shfqc.yaml", "r") as f:
    yaml = f.read()

# Define and Load our Device Setup
device_setup = DeviceSetup.from_descriptor(
    yaml_text=yaml, #descriptor_shfsg_shfqa_shfqc_hdawg_pqsc,
    server_host="localhost",  # ip address of the LabOne dataserver used to communicate with the instruments
    server_port="8004",  # port number of the dataserver - default is 8004
    setup_name="my_setup",  # setup name
)

#lsg_keys = device_setup.logical_signal_groups.keys()

# create and connect to a session
session = Session(device_setup=device_setup)
session.connect(do_emulation=False)

#%%


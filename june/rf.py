# -*- coding: utf-8 -*-
"""
Created on Tue Jun 04 14:34 2024

Run RF measurements

@author: jzingel
"""


from laboneq.simple import *


# Load configuration from the yaml file
with open("descriptor.yaml", "r") as f:
    descriptor = f.read()


# Define and Load our Device Setup
device_setup = DeviceSetup.from_descriptor(
    yaml_text=descriptor, #descriptor_shfsg_shfqa_shfqc_hdawg_pqsc,
    server_host="localhost",  # ip address of the LabOne dataserver used to communicate with the instruments
    server_port="8004",  # port number of the dataserver - default is 8004
    setup_name="my_setup",  # setup name
)

def lsg(qubit_str, line_str):
    return device_setup.logical_signal_groups[qubit_str].logical_signals[line_str]

lsg_keys = device_setup.logical_signal_groups.keys()

# perform experiments in emulation mode only? - if True, also generate dummy data for fitting
emulate = True

# create and connect to a session
session = Session(device_setup=device_setup)
session.connect(do_emulation=emulate)


#%% Setup parameters

num_qudits = len(lsg_keys)

ro_pulse_duration = 1e-6

qudits_params = {
    "qudits": lsg_keys,
    "ro_num_states": num_qudits * [2],
    "ro_cent_f": 0,
    "ro_df": num_qudits * [10e6],
    "ro_pin_range":   0,
    "ro_pout_range":  0,
    "ro_pulse_data": {},
    "ro_pulse_delay": 0,
    "ro_int_t": ro_pulse_duration,
    "ro_int_delay": 0e-9,

    "ro_int_weights": {},
    "thresholds":{},
    "ro_snr": num_qudits * [0],
    "ro_fidelity": num_qudits * [0],
    "ro_fidelity_ef": num_qudits * [0],
    "ro_x_talk_matrix": {},
    "wait_after_int": 5e-6,

    "dr_cent_f": num_qudits * [7e9],  # <= 3 different LO f, because ch1 and ch2 share the same LO, and same for ch3 and ch4, ch5 and ch6
    "dr_df": num_qudits * [10e6],
    "dr_df_ef": num_qudits * [10e6],
    "dr_p_range":   num_qudits * [0],
    "dr_pulse_data": num_qudits * [0.5],
    "dr_pulse_data_ef": num_qudits * [0.5],
    "dr_pi_pulse": {},
    "dr_pi_pulse_ef": {},
    "dr_pi/2_pulse": {},
    "dr_pi/2_pulse_ef": {},
    "T1": num_qudits * [0],
    "T2": num_qudits * [0],
    "T2_echo": num_qudits * [0],
    "T2_Ramsey": num_qudits * [0],
    "T2_CPMG": num_qudits * [0],
    "T1_ef": num_qudits * [0],
    "T2_echo_ef": num_qudits * [0],
    "T2_Ramsey_ef": num_qudits * [0],
    "T2_CPMG_ef": num_qudits * [0],
    "1q_gate_fidelity": num_qudits * [0],
    "2q_gate_fidelity": num_qudits * [0],
    "dr_x_talk_matrix": {},
}

states_str = ["g", "e", "f", "h"]




#%% Intro
# Follow getting started guide from https://docs.zhinst.com/labone_q_user_manual/getting_started/hello_world/
# Simulate RF and IQ signals

#%config IPCompleter.greedy=True

from laboneq.simple import *

descriptor="""
instrument_list:
  HDAWG:
  - address: DEV8000
    uid: device_hdawg
connections:
  device_hdawg:
    - rf_signal: q0/flux_line
      ports: [SIGOUTS/0]
    - iq_signal: q0/drive_line
      ports: [SIGOUTS/2, SIGOUTS/3]
"""

device_setup = DeviceSetup.from_descriptor(
    descriptor,
    server_host="111.22.33.44",
    server_port="8004",
    setup_name="ZI_HDAWG",
)

#%%

# Create experiment object with one signal line
exp = Experiment(
    uid="minimal_experiment",
    signals=[
        ExperimentSignal("simple_pulse"),
        ],
)

# simple constant pulse of 1us to play in the experiment
my_first_pulse = pulse_library.const(length=1e-6, amplitude=0.8)

# wrap exp.play with section/acquire
with exp.acquire_loop_rt(count=1, uid="shots"):
    with exp.section(uid="pulse"):
            exp.play(signal="simple_pulse", pulse=my_first_pulse,)


# Now we have a "logical" signal line created, we need to map it to one of the device physical outputs

# shortcut to the logical signal group q0
lsg = device_setup.logical_signal_groups["q0"].logical_signals

## define signal map
map_signals = {
    "simple_pulse" : lsg["flux_line"]
}

## apply map to the experiment
exp.set_signal_map(map_signals)

#%%
# now create a session and run the experiment

session = Session(device_setup=device_setup)
session.connect(do_emulation=True)

session.run(exp)

#%%

# Generate an IQ signal instead reusing the same experiment

lsg["drive_line"].calibration = SignalCalibration(
    oscillator=Oscillator(
        uid="drive_q0_osc",
        frequency=500e6,  ## 500 MHz
    )
)

map_signals = {
    "simple_pulse" : lsg["drive_line"]
}

## apply the signal map
exp.set_signal_map(map_signals)

session.run(exp)

#%%

# Run both at once

exp2 = Experiment(
    uid="simple_q0",
    signals=[
        ExperimentSignal("flux"),
        ExperimentSignal("drive"),
    ]
)

with exp2.acquire_loop_rt(uid="shots", count=1):
    # Run each section
    with exp2.section(uid="bias"):
        exp2.play(signal="flux",  pulse=my_first_pulse)
    with exp2.section(uid="excitation"):
        exp2.play(signal="drive", pulse=my_first_pulse)


# Link logical signals to hardware signals
map_signals = {
    "flux":  lsg["flux_line"],
    "drive":  lsg["drive_line"],
}

exp2.set_signal_map(map_signals)
session.run(exp2)

#%%
# View session result

compiled_exp = session.compiled_experiment
show_pulse_sheet("simple_q0", compiled_exp)
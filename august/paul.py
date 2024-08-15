# -*- coding: utf-8 -*-
"""
All methods to load, run and plot Pauli spin blockade sweeps.

Based upon psb_sequence.ipynb and psb_sequence

Created on Thu Aug 15 15:57 2024

@author: james
"""

# Standard imports
import numpy as np
import time
import warnings
from tqdm.notebook import tqdm
import matplotlib.pyplot as plt

# Quantum imports
from zhinst.toolkit import Session, CommandTable, Sequence, Waveforms, SHFQAChannelMode
from qcodes import Instrument, Station

# Custom imports
from monty import Monty
import MDAC
from may.dots import getvoltages
from may.custom_devices import connect_to_gb, newSiDot
from liveplot import LivePlot
from fridge import Fridge
import swiper

"""
The dynamic variables used throughout should be initilised in jupyter and passed to each function

`chan` contains quick references to all of the drive lines. Change quickly for debugging purposes
chan = {
    "measure": device.qachannels[0],  # measure and acquire lines
    "ST": device.sgchannels[0],
    "P1": device.sgchannels[1],  # drive P1 line
    "P2": device.sgchannels[2],  # drive P2 line
    "J": device.sgchannels[3],  # drive J line
}

`cts` contains the current command tables as uploaded to the instrument
cts = {
    c: CommandTable(chan[c].awg.commandtable.load_validation_schema())
    for c in drive_chans
}

`params` contains all constants used for the experiment
params = {
    "amplitude_volts": {
        "mixed_pulse": MIXED_AMP,
        "measure_pulse_start": MES_AMP_START,
        "measure_pulse_end": MES_AMP_END,
        "ramp_rate": ramp_rate,
    },
    "dc_steps": {
        "start": p1_steps[0],
        "end": p1_steps[-1],
    },
    "readout": {
        "freq": readout_freq,
        "gain": readout_gain,
        "time": read_len
    },
    "timings_sec": {
        "mixed_initilise": init_len,
        "read": read_len,
        "settle": wait_and_settle,
        "trigger": trigger_time,
        "buffer": buffer,
        "sampling_divider": samplingDivider,
    },
    "feedback": {
        "target": FB_TARGET,
        "stepsize": FB_STEPSIZE,
        "slope": FB_SLOPE
    },
    "powers": {
        "acq_in": input_pwr,
        "acq_out": output_pwr,
        "drive": dr_pwr,
    },
    "averaging": {
        "seqc_averages": seq_averages,
        "num_detuning": NUM_DETUNING,
        "num_j": NUM_J,
    },
    "gates": getvoltages(mdac),
    "temp": f"Mixing chamber {fridge.temp()} K",
}
"""


def validate(params):
    """Make sure that the parameters are valid"""
    # check we can fit all the points into memory
    MAX_MEASUREMENTS = 2**19
    if params["averaging"]["seqc_averages"] > MAX_MEASUREMENTS:
        raise OverflowError("Requested too many points to be measured. (Use around 500,000 points)")


def timeToSamples(time, samplingRateDivider):
    """Returns the number of samples divisible by 16 given a time (in seconds) and sampling rate divider"""
    samples_raw = time * (1/(2**samplingRateDivider))/0.5e-9
    #samples_modulo = int(samples_raw) % 16
    #samples = int(samples_raw) - int(samples_modulo)
    return 16*np.floor(samples_raw/16)
    #return samples


def voltToDbm(volt, dbmrange):
    """Convert from voltage to dBm (power)"""
    # Ok yes this can be better, deal with it
    if dbmrange != 0:
        raise Exception("This function only works with a dBm range of 0.")

    if volt > 0.34 or volt < -0.34:
        raise ValueError(f"Given voltage ({volt} V) is greater than max output of SHFQC (0.34 V)")

    if volt < 0:
        amplitude = 1 / 300 * (np.sqrt(3e5 * -volt + 529) - 23)
        return -amplitude
    else:
        amplitude = 1 / 300 * (np.sqrt(3e5 * volt + 529) - 23)
        return amplitude


def autodb(res):
    """Change a.u. to dB power. Used in the data result."""
    return 10*np.log10(np.abs(res)**2/50*1000)

def setupchannels(device, chan, drive_chans, params):
    """Set up the SHFQC device for PSB."""
    with device.set_transaction():
        # setup drive channels
        for c in drive_chans:
            chan[c].output.range(params["powers"]["drive"])  # in dBm
            chan[c].output.rflfpath(0)  # use LF not RF (1 for RF)

            # set the center synth frequency (oscillator frequency)
            synth = chan[c].synthesizer()
            device.synthesizers[synth].centerfreq(0)  # in Hz
            chan[c].output.on(1)  # enable output

            chan[c].awg.outputamplitude(1.0)  # overall amplitude scaling factor (don't really need to change)
            chan[c].oscs[0].freq(0)  # oscillator 1 frequency (Hz) disable for DC
            chan[c].oscs[1].freq(0)  # oscillator 2 frequency (Hz)
            chan[c].awg.modulation.enable(1)  # start digital modulation

            chan[c].marker.source(
                0)  # setup the AWG trigger 1 (is this an input trigger option? doesn't seem necessary)
            # see manual page p235 for all trigger options
            chan[c].awg.auxtriggers[0].channel(8)  # 8=use internal trigger, 1024=use software trigger

        # setup measure channel

        chan["measure"].output.rflfpath(0)  # use LF mode not RF (for signals under 600Mhz)
        chan["measure"].input.rflfpath(0)
        chan["measure"].oscs[0].freq(params["readout"]["freq"])  # CW frequency (in LF mode)
        chan["measure"].oscs[0].gain(params["readout"]["gain"])  # If we set this to 1, then output overloads

        # configure these based on how the sweeper works internally
        # See https://docs.zhinst.com/zhinst-utils/en/latest/_modules/zhinst/utils/shf_sweeper.html#ShfSweeper
        chan["measure"].spectroscopy.delay(0)  # integration delay in units of second
        chan["measure"].spectroscopy.length(
            100e-6 * 2e9)  # timeToSamples(read_len, 0))  # integration time length in units of number of samples (usually integration_time*sampling_rate)
        # setup when the spectroscopy is triggered
        chan["measure"].spectroscopy.trigger.channel(
            "chan0seqtrig0")  # make sure to use the trigger coming from the sequencer code
        # setup result parameters
        chan["measure"].spectroscopy.result.averages(
            params["averaging"]["seqc_averages"])  # number of averages (always average in software not hardware)
        chan["measure"].spectroscopy.result.length(2)  # number of results
        chan["measure"].spectroscopy.result.enable(0)  # disable result logger
        chan["measure"].spectroscopy.result.mode('cyclic')  # sequential readout for averaging
        chan["measure"].spectroscopy.envelope.enable(0)  # changes into continuous mode

        chan["measure"].configure_channel(
            center_frequency=0,  # in units of Hz  # minimum of 600MHz for RF mode
            input_range=params["powers"]["acq_in"],  # in units of dBm
            output_range=params["powers"]["acq_out"],  # in units of dBm
            mode=SHFQAChannelMode.SPECTROSCOPY,  # SHFQAChannelMode.READOUT or SHFQAChannelMode.SPECTROSCOPY
        )

        chan["measure"].input.on(1)
        chan["measure"].output.on(1)

        chan["measure"].generator.auxtriggers[1].channel(
            "inttrig")  # i believe this is overwritten by the following line
        chan["measure"].generator.configure_sequencer_triggering(
            aux_trigger=8,
            # alternatively use 8=internal trigger, or "software_trigger0" to use the software triggering system
            play_pulse_delay=0
        )

        device.system.internaltrigger.repetitions(
            params["averaging"]["seqc_averages"])  # make sure that this matches how many pulses we are sending
        device.system.internaltrigger.holdoff(
            params["timings_sec"]["trigger"])  # init_len + 2*wait_and_settle + 100e-6*2)  # how long to wait between retriggers (increments of 100ns)


def synchchannels(device, chan):
    """
    Sync the given channels, un-syncing the rest.
    Assumes that the internal trigger should always be synced.
    """
    for i in range(6):
        device.sgchannels[i].synchronization.enable(0)
    time.sleep(1)
    for c in chan.keys():
        chan[c].synchronization.enable(1)
    device.system.internaltrigger.synchronization.enable(1)

###### SEQUENCES ######
def setupsequencers(chan, params):
    samplingDivider = params["timings_sec"]["samplingDivider"]
    wait_and_settle = params["timings_sec"]["settle"]
    read_len = params["timings_sec"]["read"]
    init_len = params["timings_sec"]["mixed_initilise"]
    buffer = params["timings_sec"]["buffer"]

    # Signal generator channels
    seqc_program_p1 = f"""
    // Assign a single channel waveform to wave table entry 0

    // Reset the oscillator phase
    resetOscPhase();

    repeat({params["averaging"]["seqc_averages"]}) {{

        // Trigger the scope

        waitDigTrigger(1);

        setTrigger(1);
        setTrigger(0);

        executeTableEntry(0);                                                               // mixed state init.

        playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});    // wait and settle
        playZero({timeToSamples(read_len, samplingDivider)},  {samplingDivider});           // read reference

        executeTableEntry(1);                                                               // read

        playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});    // wait and settle
    }}
    """

    seqc_program_p2 = f"""
    // Assign a single channel waveform to wave table entry 0

    // Reset the oscillator phase
    resetOscPhase();

    repeat({params["averaging"]["seqc_averages"]}) {{

        // Trigger the scope

        waitDigTrigger(1);

        setTrigger(1);
        setTrigger(0);

        executeTableEntry(0);                                                               // mixed state init.

        playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});    // wait and settle
        playZero({timeToSamples(read_len, samplingDivider)},  {samplingDivider});           // read reference

        executeTableEntry(1);                                                               // read

        playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});    // wait and settle
    }}
    """

    seqc_program_j = f"""
    // Assign a single channel waveform to wave table entry 0
    wave w_j = ones({timeToSamples(init_len, samplingDivider)});
    assignWaveIndex(1,2, w_j, 0);

    // Reset the oscillator phase
    resetOscPhase();

    repeat({params["averaging"]["seqc_averages"]}) {{

        // Trigger the scope

        waitDigTrigger(1);

        setTrigger(1);
        setTrigger(0);

        playZero({timeToSamples(init_len, samplingDivider)},  {samplingDivider});           // mixed state init.
        playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});    // wait and settle

        executeTableEntry(1);                                                               // read reference

        // playZero({timeToSamples(read_len, samplingDivider)},  {samplingDivider});           // read
        playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});    // wait and settle
        playZero(32);    // wait and settle
    }}
    """

    seqc_program_st = f"""
    // Assign a single channel waveform to wave table entry 0
    wave w_st = ones({timeToSamples(wait_and_settle, 9)});
    assignWaveIndex(1,2, w_st, 0);

    repeat({params["averaging"]["seqc_averages"]}) {{
        waitDigTrigger(1);

        playZero({timeToSamples(init_len, samplingDivider)},  {samplingDivider});
        playZero({timeToSamples(wait_and_settle - 10 * buffer, samplingDivider)},  {samplingDivider});
        //playZero({timeToSamples(buffer, samplingDivider)},  {samplingDivider});

        executeTableEntry(0);
    }}
    """

    # Quantum Analyser Channel
    seqc_program_prior_read = f"""
    repeat({params["averaging"]["seqc_averages"]}) {{
        waitDigTrigger(1);

        setTrigger(1);
        setTrigger(0);
    }}
    """

    readout_prog_code = f"""
    setTrigger(0); // Set low as this starts the spectroscopy readout....

    repeat({params["averaging"]["seqc_averages"]}) {{
        waitDigTrigger(1);

        playZero(224); // lineup with SG trigger (224 samples = lines up with SG trigger);

        playZero({timeToSamples(init_len, samplingDivider)},  {samplingDivider});
        playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});
        playZero({timeToSamples(buffer, samplingDivider)},  {samplingDivider});

        setTrigger(1);  // trigger the output. As this matches "chan0seqtrig0" the spectroscopy is started
        setTrigger(0);

        playZero({timeToSamples(read_len, samplingDivider)},  {samplingDivider});
        playZero({timeToSamples(buffer, samplingDivider)},  {samplingDivider});

        setTrigger(1);  // trigger the output. As this matches "chan0seqtrig0" the spectroscopy is started
        setTrigger(0);

        playZero({timeToSamples(buffer, samplingDivider)},  {samplingDivider});
        playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});
        }}
    """

    # Create waveform pulses
    ramp_rate = params["amplitude_volts"]["ramp_rate"]
    # Create mixed state
    samples = timeToSamples(init_len, samplingDivider)
    #mixed_p = np.linspace(voltToDbm(0.34 - 0.34 * samples * ramp_rate, 0), voltToDbm(0.34, 0), samples) # ramps
    mixed_p = np.linspace(voltToDbm(0.34, 0), voltToDbm(0.34, 0), samples)  # no ramping
    # Read pulse driver
    samples = timeToSamples(read_len, samplingDivider)
    read_p = np.linspace(voltToDbm(0.34 - 0.34 * samples * ramp_rate, 0), voltToDbm(0.34, 0), samples)

    # Upload to sequencers
    # P1
    seq = Sequence()
    seq.code = seqc_program_p1
    seq.waveforms = Waveforms()
    seq.waveforms[0] = mixed_p
    seq.waveforms[1] = read_p
    chan["P1"].awg.load_sequencer_program(seq)
    chan["P1"].awg.write_to_waveform_memory(seq.waveforms)
    print(f"_________ {chan["P1"]} _________")
    print(seq.code)

    # P2
    seq = Sequence()
    seq.code = seqc_program_p2
    seq.waveforms = Waveforms()
    seq.waveforms[0] = mixed_p
    seq.waveforms[1] = read_p
    chan["P2"].awg.load_sequencer_program(seq)
    chan["P2"].awg.write_to_waveform_memory(seq.waveforms)
    print(f"_________ {chan["P2"]} _________")
    print(seq.code)

    # J
    chan["J"].awg.load_sequencer_program(seqc_program_j)
    print(f"_________ {chan["J"]} _________")
    print(seqc_program_j)

    # ST
    chan["ST"].awg.load_sequencer_program(seqc_program_st)
    print(f"_________ {chan["ST"]} _________")
    print(seqc_program_st)

def cmdtable(ct, amplitude, length, wave_index, ct_index, samplingDivider):
    """Load a default command table with a sin/cos wave (used throughout the documentation)"""
    ct.table[ct_index].waveform.index = wave_index
    ct.table[ct_index].amplitude00.value = amplitude  # all in dBm
    ct.table[ct_index].amplitude01.value = -amplitude
    ct.table[ct_index].amplitude10.value = amplitude
    ct.table[ct_index].amplitude11.value = amplitude
    ct.table[ct_index].waveform.length = length  # in samples
    ct.table[ct_index].waveform.samplingRateDivider = samplingDivider  # inherit global

def setupcommandtables(cts, chan, params):
    """Set up the command tables. Give current command tables"""
    for c in ["P1", "P2"]:
        cmdtable(cts[c],
                 amplitude=voltToDbm(params["amplitude_volts"]["mixed_pulse"][c], params["powers"]["drive"]),
                 length=timeToSamples(params["timings_sec"]["mixed_initilise"], params["timings_sec"]["samplingDivider"]),
                 wave_index=0,
                 ct_index=0,
                 samplingDivider=params["timings_sec"]["samplingDivider"]
                 )

    # Upload the command tables
    for c in cts.keys():
        chan[c].awg.commandtable.upload_to_device(cts[c])


###### RUN ######

def waitForInternalTrigger(device, progress=True, leave=True):
    """
    Waits for the internal trigger to finish running and shows the current progress.
    Progress = if show tqdm progress meter
    Leave = if keep progress bar afterwards
    """
    if progress:
        pbar = tqdm(total=100, leave=leave, desc="Internal trigger")
    while device.system.internaltrigger.progress() != 1.0:
        p = int(device.system.internaltrigger.progress()*100)
        if progress:
            pbar.update(p-pbar.n)
        time.sleep(0.001)
    if progress:
        pbar.update(100-pbar.n)
        pbar.close()

###### FEEDBACK ######

def calculatefeedback(cts, last_point, params):
    """Calculate the appropriate feedback adjustment to ST."""
    # use last datapoint
    unit_amp = 0.34
    error = params["feedback"]["target"]- autodb(last_point)
    st_err = error * params["feedback"]["stepsize"] * params["feedback"]["slope"]
    st_err = -1 if st_err < -1 else (1 if st_err > 1 else st_err)
    st_corr = st_err*unit_amp

    # update command table
    cmdtable(cts["ST"],
             amplitude= voltToDbm(st_corr, params["powers"]["drive"]),
             length=timeToSamples(params["timings_sec"]["trigger"]-2e-3, 9),  # TODO: Remove constant
             wave_index=0,
             ct_index=0,
             samplingDivider=params["timings_sec"]["samplingDivider"],
            )
    return st_corr


def movemeasurement(cts, chan, p1, p2, j, params):
    """Modify the command tables of P1/P2/J to measure the next appropriate datapoint."""
    samplingDivider = params["timings_sec"]["samplingDivider"]
    read_len = params["timings_sec"]["read"]
    buffer = params["timings_sec"]["buffer"]

    cmdtable(cts["P1"],
             amplitude=voltToDbm(p1, chan["P1"].output.range()),
             length=timeToSamples(buffer + read_len + buffer, samplingDivider),
             wave_index=1,
             ct_index=1,
             samplingDivider=params["timings_sec"]["samplingDivider"]
            )
    cmdtable(cts["P2"],
             amplitude=voltToDbm(p2, chan["P2"].output.range()),
             length=timeToSamples(buffer + read_len + buffer, samplingDivider),
             wave_index=1,
             ct_index=1,
             samplingDivider=params["timings_sec"]["samplingDivider"]
            )
    cmdtable(cts["J"],
             amplitude= voltToDbm(j, chan["J"].output.range()),
             length=timeToSamples(buffer + read_len + buffer + read_len, samplingDivider),     # THIS LINE IS WRONG, FIX
             wave_index=0,
             ct_index=1,
             samplingDivider=params["timings_sec"]["samplingDivider"]
            )

###### EXPERIMENTS ######

def runfeedback():
    """Run feedback measurement where we only measure"""
    device.system.internaltrigger.enable(0)

    result_node = chan["measure"].spectroscopy.result.data.wave
    result_node.subscribe()

    chan["measure"].spectroscopy.result.enable(1)  # start logger
    chan["measure"].generator.enable_sequencer(single=True)
    device.system.internaltrigger.enable(1)

    time.sleep(0.2)  # delay for networking issues

    # wait for the measurement to complete
    waitForInternalTrigger()

    m_state = chan["measure"].generator.sequencer.status()
    if m_state != 4:
        warnings.warn(f"Sequencers in unknown state. Perhaps they are not synchronised? {bin(m_state)}")
        time.sleep(0.5)

    # wait for completion
    while chan["measure"].spectroscopy.result.enable() != 0:
        print(chan["measure"].spectroscopy.result.enable())
        chan["measure"].spectroscopy.result.enable.wait_for_state_change(0, timeout=10)

    # get results
    results = get_results(result_node, timeout=5)
    result_node.unsubscribe()

    # verify results
    acq = chan["measure"].spectroscopy.result.acquired()
    if len(results) > acq:
        print(chan["measure"].generator.ready())
        raise TimeoutError(f"Not all datapoints measured in the time provided. {acq} of {len(results)}.")

    return results


def run_psb_experiment(device, chan):
    """Run one PSB experiment. Returns the reference and measurement points."""
    device.system.internaltrigger.enable(0)

    result_node = chan["measure"].spectroscopy.result.data.wave
    result_node.subscribe()

    chan["measure"].spectroscopy.result.enable(1)  # start logger

    # start sequencers
    chan["measure"].generator.enable_sequencer(single=True)
    chan["J"].awg.enable_sequencer(single=True)  # dont want to repeat
    chan["P1"].awg.enable_sequencer(single=True)
    chan["P2"].awg.enable_sequencer(single=True)
    chan["ST"].awg.enable_sequencer(single=True)

    # start triggering sequence (which starts each sequencer)
    device.system.internaltrigger.enable(1)
    time.sleep(0.2)

    # wait for the measurement to complete
    waitForInternalTrigger(progress=True, leave=False)
    # device.system.internaltrigger. .wait_for_state_change(1.0, timeout=100)  # wait for completion

    # check sequencers have finished their sequences
    # Status of the Sequencer on the instrument.
    # - Bit 0: Sequencer is running;
    # - Bit 1: reserved;
    # - Bit 2: Sequencer is waiting for a trigger to arrive;
    # - Bit 3: Sequencer has detected an error;
    # - Bit 4: sequencer is waiting for synchronization with other channels
    m_state = chan["measure"].generator.sequencer.status()
    st_state = chan["P1"].awg.sequencer.status()
    if m_state != 4 and st_state != 4:
        warnings.warn(
            f"Sequencers in unknown state. Perhaps they are not synchronised? {bin(m_state)}, {bin(st_state)}")
        # time.sleep(0.5)

    # wait for completion
    while chan["measure"].spectroscopy.result.enable() != 0:
        chan["measure"].spectroscopy.result.enable.wait_for_state_change(0, timeout=100)

    # get results
    results = get_results(result_node, timeout=5)
    result_node.unsubscribe()

    # verify results
    acq = chan["measure"].spectroscopy.result.acquired()
    if len(results) > acq:
        print(chan["measure"].generator.ready())
        print([chan[c].awg.ready() for c in drive_chans])
        raise TimeoutError(f"Not all datapoints measured in the time provided. {acq} of {len(results)}.")

    # return np.mean(results.reshape((seq_averages, 2)), axis=0)
    return results
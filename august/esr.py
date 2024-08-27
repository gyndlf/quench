# -*- coding: utf-8 -*-
"""
All methods to load and run frequency sweeps over ESR

Created on Thu Aug 15 15:57 2024

@author: james
"""

# Standard imports
import numpy as np
import time
import logging
from tqdm.notebook import tqdm
from zhinst.toolkit import Session, CommandTable, Sequence, Waveforms, SHFQAChannelMode
from shfqc import SHFQC


"""
The dynamic variables used throughout should be initialised in jupyter and passed to each function

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
    "mw": {
        "freq": 7e9,  # (Hz)
        "psgfreq": 13.9e9,
        "gain": 0.95,  # If we set this to 1, then output overloads
        "span": 1e6,  # frequency span for chirp signal, if enabled
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
    return 16*int(np.floor(samples_raw/16))
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

def autodeg(res):
    """Change a.u. result to phase angle in degrees."""
    return np.unwrap(np.angle(res))  # FIXME: Add axis=?


# NEED TO CHANGE THIS. ESR CHANNEL NEEDS TO BE IN RF MODE WITH A ~6GHZ CENTER FREQ

def setupchannels(shfqc: SHFQC, params, hyper=False):
    """Set up the SHFQC device for PSB. hyper = If to setup for detuning sweeps in SHFQC."""
    with shfqc.device.set_transaction():
        # setup drive channels
        for c in shfqc.drive_channels:
            if c == "MW_I":
                shfqc[c].output.range(params["powers"]["drive"])  # in dBm
                shfqc[c].output.rflfpath(1)  # use LF not RF (1 for RF)

                # set the center synth frequency (oscillator frequency)
                synth = shfqc[c].synthesizer()
                shfqc.device.synthesizers[synth].centerfreq(params["mw"]["freqs"]["center"])  # in Hz
                shfqc[c].oscs[0].freq(0)  # oscillator 1 frequency (Hz) disable for DC
                shfqc[c].oscs[1].freq(0)  # oscillator 2 frequency (Hz)
            elif c ==  "MW_Q":
                shfqc[c].output.range(params["powers"]["drive"])  # in dBm
                shfqc[c].output.rflfpath(1)  # use LF not RF (1 for RF)

                # set the center synth frequency (oscillator frequency)
                synth = shfqc[c].synthesizer()
                shfqc.device.synthesizers[synth].centerfreq(params["mw"]["freqs"]["center"])  # in Hz
                shfqc[c].oscs[0].freq(0)  # oscillator 1 frequency (Hz) disable for DC
                shfqc[c].oscs[1].freq(0)  # oscillator 2 frequency (Hz)
            elif c ==  "MW":
                shfqc[c].output.range(params["powers"]["drive"])  # in dBm
                shfqc[c].output.rflfpath(1)  # use LF not RF (1 for RF)

                # set the center synth frequency (oscillator frequency)
                synth = shfqc[c].synthesizer()
                shfqc.device.synthesizers[synth].centerfreq(params["mw"]["freqs"]["center"])  # in Hz
                shfqc[c].oscs[0].freq(0)  # oscillator 1 frequency (Hz) disable for DC
                shfqc[c].oscs[1].freq(0)  # oscillator 2 frequency (Hz)

            else:  # special setup for MW channel
                shfqc[c].output.range(params["powers"]["mw_drive"])
                shfqc[c].output.rflfpath(0)  # use RF

                 # set the center synth frequency (oscillator frequency)
                synth = shfqc[c].synthesizer()
                shfqc.device.synthesizers[synth].centerfreq(0)  # in Hz
                shfqc[c].oscs[0].freq(0)#params["mw"]["freqs"]["start"])  # oscillator 1 frequency (Hz) disable for DC
                shfqc[c].oscs[1].freq(0)#params["mw"]["freqs"]["start"])  # oscillator 2 frequency (Hz)
            
            shfqc[c].awg.outputamplitude(1.0)  # overall amplitude scaling factor (don't really need to change)
            shfqc[c].output.on(1)  # enable output
            shfqc[c].awg.modulation.enable(1)  # start digital modulation
            shfqc[c].marker.source(
                0)  # setup the AWG trigger 1 (is this an input trigger option? doesn't seem necessary)
            # see manual page p235 for all trigger options
            shfqc[c].awg.auxtriggers[0].channel(8)  # 8=use internal trigger, 1024=use software trigger

        # setup measure channel

        shfqc["measure"].output.rflfpath(0)  # use LF mode not RF (for signals under 600Mhz)
        shfqc["measure"].input.rflfpath(0)
        shfqc["measure"].oscs[0].freq(params["readout"]["freq"])  # CW frequency (in LF mode)
        shfqc["measure"].oscs[0].gain(params["readout"]["gain"])  # If we set this to 1, then output overloads

        # configure these based on how the sweeper works internally
        # See https://docs.zhinst.com/zhinst-utils/en/latest/_modules/zhinst/utils/shf_sweeper.html#ShfSweeper
        shfqc["measure"].spectroscopy.delay(0)  # integration delay in units of second
        shfqc["measure"].spectroscopy.length(
            100e-6 * 2e9)  # timeToSamples(read_len, 0))  # integration time length in units of number of samples (usually integration_time*sampling_rate)
        # setup when the spectroscopy is triggered
        shfqc["measure"].spectroscopy.trigger.channel(
            "chan0seqtrig0")  # make sure to use the trigger coming from the sequencer code
        # setup result parameters
        shfqc["measure"].spectroscopy.result.averages(
            params["averaging"]["seqc_averages"])  # number of averages (always average in software not hardware)
        if hyper:  # do detuning steps in seqc
            shfqc["measure"].spectroscopy.result.length(2*params["averaging"]["num_detuning"])  # number of results to acquire
        else:  # do detuning steps in python
            shfqc["measure"].spectroscopy.result.length(2)  # number of results
        shfqc["measure"].spectroscopy.result.mode('cyclic')  # sequential readout for averaging
        shfqc["measure"].spectroscopy.result.enable(0)  # disable result logger
        shfqc["measure"].spectroscopy.envelope.enable(0)  # changes into continuous mode

        shfqc["measure"].configure_channel(
            center_frequency=0,  # in units of Hz  # minimum of 600MHz for RF mode
            input_range=params["powers"]["acq_in"],  # in units of dBm
            output_range=params["powers"]["acq_out"],  # in units of dBm
            mode=SHFQAChannelMode.SPECTROSCOPY,  # SHFQAChannelMode.READOUT or SHFQAChannelMode.SPECTROSCOPY
        )

        shfqc["measure"].input.on(1)
        shfqc["measure"].output.on(1)

        shfqc["measure"].generator.auxtriggers[1].channel(
            "inttrig")  # i believe this is overwritten by the following line
        shfqc["measure"].generator.configure_sequencer_triggering(
            aux_trigger=8,
            # alternatively use 8=internal trigger, or "software_trigger0" to use the software triggering system
            play_pulse_delay=0
        )

        if hyper:
            shfqc.device.system.internaltrigger.repetitions(
            params["averaging"]["seqc_averages"]*params["averaging"]["num_detuning"])  # make sure that this matches how many pulses we are sending
        else:
            shfqc.device.system.internaltrigger.repetitions(
                params["averaging"]["seqc_averages"])  # make sure that this matches how many pulses we are sending
        shfqc.device.system.internaltrigger.holdoff(
            params["timings_sec"]["trigger"])  # init_len + 2*wait_and_settle + 100e-6*2)  # how long to wait between retriggers (increments of 100ns)


def synchchannels(shfqc: SHFQC, channels):
    """
    Sync the given channels, un-syncing the rest.
    Assumes that the internal trigger should always be synced.
    """
    for i in range(6):  # desync all channels
        shfqc.device.sgchannels[i].synchronization.enable(0)
    shfqc.device.qachannels[0].synchronization.enable(0)
    time.sleep(1)
    for c in channels:
        shfqc[c].synchronization.enable(1)
    shfqc.device.system.internaltrigger.synchronization.enable(1)

def configure_psg(shfqc: SHFQC, params):
    psg.power(params["powers"]["psg_drive"])
    psg.frequency(params["mw"]["psgfreq"])
    # add more, such as enabling output etc.


###### SEQUENCES ######
def setupsequencers(shfqc: SHFQC, params, print_programs=True):
    samplingDivider = params["timings_sec"]["sampling_divider"]
    wait_and_settle = params["timings_sec"]["settle"]
    read_len = params["timings_sec"]["read"]
    init_len = params["timings_sec"]["mixed_initilise"]
    buffer = params["timings_sec"]["buffer"]
    mw_len = params["timings_sec"]["mw_pulse"]
    
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
        playZero({timeToSamples(mw_len, samplingDivider)},  {samplingDivider});             // chirp
        playZero({timeToSamples(buffer, samplingDivider)},  {samplingDivider});             // buffer

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
        playZero({timeToSamples(mw_len, samplingDivider)},  {samplingDivider});             // chirp
        playZero({timeToSamples(buffer, samplingDivider)},  {samplingDivider});             // buffer

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

        playZero({timeToSamples(mw_len, samplingDivider)},  {samplingDivider});             // chirp
        playZero({timeToSamples(buffer, samplingDivider)},  {samplingDivider});             // buffer

        // playZero({timeToSamples(read_len, samplingDivider)},  {samplingDivider});            // read
        playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});    // wait and settle
        playZero(32);    // wait and settle
    }}
    """

    # seqc_program_st = f"""
    # // Assign a single channel waveform to wave table entry 0
    # wave w_st = ones({timeToSamples(wait_and_settle, 9)});
    # assignWaveIndex(1,2, w_st, 0);

    # repeat({params["averaging"]["seqc_averages"]}) {{
    #     waitDigTrigger(1);

    #     playZero({timeToSamples(init_len, samplingDivider)},  {samplingDivider});
    #     playZero({timeToSamples(wait_and_settle - 10 * buffer, samplingDivider)},  {samplingDivider});
    #     //playZero({timeToSamples(buffer, samplingDivider)},  {samplingDivider});

    #     executeTableEntry(0);
    # }}
    # """

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
        playZero({timeToSamples(mw_len, samplingDivider)},  {samplingDivider});             // chirp
        playZero({timeToSamples(buffer, samplingDivider)},  {samplingDivider});
        playZero({timeToSamples(buffer, samplingDivider)},  {samplingDivider});             // buffer

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
    shfqc["P1"].awg.load_sequencer_program(seq)
    shfqc["P1"].awg.write_to_waveform_memory(seq.waveforms)
    if print_programs:
        print(f"_________ {shfqc['P1']} _________")
        print(seq.code)

    # P2
    seq = Sequence()
    seq.code = seqc_program_p2
    seq.waveforms = Waveforms()
    seq.waveforms[0] = mixed_p
    seq.waveforms[1] = read_p
    shfqc["P2"].awg.load_sequencer_program(seq)
    shfqc["P2"].awg.write_to_waveform_memory(seq.waveforms)
    if print_programs:
        print(f"_________ {shfqc['P2']} _________")
        print(seq.code)

    # J
    shfqc["J"].awg.load_sequencer_program(seqc_program_j)
    if print_programs:
        print(f"_________ {shfqc['J']} _________")
        print(seqc_program_j)

    # ST
    # shfqc["ST"].awg.load_sequencer_program(seqc_program_st)
    # if print_programs:
    #     print(f"_________ {shfqc['ST']} _________")
    #     print(seqc_program_st)

    # QA
    shfqc["measure"].generator.load_sequencer_program(readout_prog_code)


def setup_hyper_sequencers(shfqc: SHFQC, params, print_programs=False):
    """
    Create and upload sequencer code to run detuning steps.
    Utilise command tables 1-N for each step to take in detuning for P1/P2. After creation of the mixed state on command table 0.
    """
    samplingDivider = params["timings_sec"]["sampling_divider"]
    wait_and_settle = params["timings_sec"]["settle"]
    read_len = params["timings_sec"]["read"]
    init_len = params["timings_sec"]["mixed_initilise"]
    buffer = params["timings_sec"]["buffer"]
    num_detuning = params["averaging"]["num_detuning"]
    mw_len = params["timings_sec"]["mw_pulse"]

    # Signal generator channels
    seqc_program_p = f"""
    // Reset the oscillator phase
    resetOscPhase();

    repeat({params["averaging"]["seqc_averages"]}) {{
        for(var ct = 1; ct < {num_detuning+1}; ct++) {{                                               // repeat for each step in detuning

            // Trigger the scope
            waitDigTrigger(1);

            setTrigger(1);
            setTrigger(0);

            executeTableEntry(0);                                                               // mixed state init.

            playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});    // wait and settle
            playZero({timeToSamples(read_len, samplingDivider)},  {samplingDivider});           // read reference
            playZero({timeToSamples(mw_len, samplingDivider)},  {samplingDivider});             // chirp

            executeTableEntry(ct);                                                              // read

            playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});    // wait and settle
        }}
    }}
    """

    seqc_program_j = f"""
    // Assign a single channel waveform to wave table entry 0
    wave w_j = ones({timeToSamples(init_len, samplingDivider)});
    assignWaveIndex(1,2, w_j, 0);

    // Reset the oscillator phase
    resetOscPhase();

    repeat({params["averaging"]["seqc_averages"]}) {{
        for(var ct = 1; ct < {num_detuning+1}; ct++) {{                                               // repeat for each step in detuning

            // Trigger the scope
            waitDigTrigger(1);

            setTrigger(1);
            setTrigger(0);

            playZero({timeToSamples(init_len, samplingDivider)},  {samplingDivider});           // mixed state init.
            playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});    // wait and settle

            executeTableEntry(1);                                                               // read reference
            
            playZero({timeToSamples(mw_len, samplingDivider)},  {samplingDivider});             // chirp

            // playZero({timeToSamples(read_len, samplingDivider)},  {samplingDivider});        // read
            playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});    // wait and settle
            playZero(32);                                                                       // wait and settle
        }}
    }}
    """

    readout_prog_code = f"""
    setTrigger(0); // Set low as this starts the spectroscopy readout....

    repeat({params["averaging"]["seqc_averages"]}) {{
        for(var ct = 1; ct < {num_detuning+1}; ct++) {{                                               // repeat for each step in detuning
            waitDigTrigger(1);

            playZero(224); // lineup with SG trigger (224 samples = lines up with SG trigger);

            playZero({timeToSamples(init_len, samplingDivider)},  {samplingDivider});
            playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});
            playZero({timeToSamples(buffer, samplingDivider)},  {samplingDivider});

            setTrigger(1);  // trigger the output. As this matches "chan0seqtrig0" the spectroscopy is started
            setTrigger(0);

            playZero({timeToSamples(read_len, samplingDivider)},  {samplingDivider});
            playZero({timeToSamples(mw_len, samplingDivider)},  {samplingDivider});             // chirp
            playZero({timeToSamples(buffer, samplingDivider)},  {samplingDivider});

            setTrigger(1);  // trigger the output. As this matches "chan0seqtrig0" the spectroscopy is started
            setTrigger(0);

            playZero({timeToSamples(buffer, samplingDivider)},  {samplingDivider});
            playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});
        }}
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
    seq.code = seqc_program_p
    seq.waveforms = Waveforms()
    seq.waveforms[0] = mixed_p
    seq.waveforms[1] = read_p
    shfqc["P1"].awg.load_sequencer_program(seq)
    shfqc["P1"].awg.write_to_waveform_memory(seq.waveforms)
    if print_programs:
        print(f"_________ {shfqc['P1']} _________")
        print(seq.code)

    # P2
    seq = Sequence()
    seq.code = seqc_program_p
    seq.waveforms = Waveforms()
    seq.waveforms[0] = mixed_p
    seq.waveforms[1] = read_p
    shfqc["P2"].awg.load_sequencer_program(seq)
    shfqc["P2"].awg.write_to_waveform_memory(seq.waveforms)
    if print_programs:
        print(f"_________ {shfqc['P2']} _________")
        print(seq.code)

    # J
    shfqc["J"].awg.load_sequencer_program(seqc_program_j)
    if print_programs:
        print(f"_________ {shfqc['J']} _________")
        print(seqc_program_j)

    # QA
    shfqc["measure"].generator.load_sequencer_program(readout_prog_code)
    if print_programs:
        print(f"_________ {shfqc['measure']} _________")
        print(readout_prog_code)


def setup_dummy_sequencers(shfqc: SHFQC, params, print_programs=False):

    samplingDivider = params["timings_sec"]["sampling_divider"]

    mw_len = params["timings_sec"]["mw_pulse"]
    
    mw_amp = params["mw"]["gain"]
    mw_phase = 3.1415/2 # hardcoded, don't need it changed but need it in sequence
    # mw_start_freq = params["mw"]["freqs"]["start"]
    # mw_stop_freq = params["mw"]["freqs"]["start"] + params["mw"]["span"]

    seqc_program_mw_dummy = f"""
    // Assign a single channel waveform to wave table entry 0
    wave w_mw = ones({timeToSamples(mw_len, params["mw"]["sampling_divider"])});
    assignWaveIndex(1,2, w_mw, 0);

    // Reset the oscillator phase
    resetOscPhase();

    repeat({params["averaging"]["seqc_averages"]}) {{

        // Trigger the scope

        waitDigTrigger(1);

        setTrigger(1);
        setTrigger(0);

        executeTableEntry(1);                                                               // chirp

    }}
    """

    seq = Sequence()
    seq.code = seqc_program_mw_dummy
    # shfqc["MW_I"].awg.load_sequencer_program(seq)
    # shfqc["MW_Q"].awg.load_sequencer_program(seq)
    shfqc["MW"].awg.load_sequencer_program(seq)
    # if print_programs:
    #     print(f"_________ {shfqc['MW']} _________")
    #     print(seq.code)

    # Make sure to reupload command tables as they are cleared whenever a sequence is loaded



def cmdtable(ct, amplitude, length, wave_index, ct_index, samplingDivider):
    """
    Load a default command table with a sin/cos wave (used throughout the documentation)
    Operates in-place.
    """
    ct.table[ct_index].waveform.index = wave_index
    ct.table[ct_index].amplitude00.value = amplitude  # all in dBm
    ct.table[ct_index].amplitude01.value = -amplitude
    ct.table[ct_index].amplitude10.value = amplitude
    ct.table[ct_index].amplitude11.value = amplitude
    ct.table[ct_index].waveform.length = length  # in samples
    ct.table[ct_index].waveform.samplingRateDivider = samplingDivider  # inherit global


def upload_command_tables(shfqc: SHFQC):
    """Upload the command tables to the device"""
    # Upload the command tables
    for c in shfqc.cmd_tables.keys():
        shfqc[c].awg.commandtable.upload_to_device(shfqc.cmd_tables[c])


def setup_command_tables(shfqc: SHFQC, params):
    """Set up the command tables. Give current command tables"""
    for c in ["P1", "P2"]:
        cmdtable(shfqc.cmd_tables[c],
                 amplitude=voltToDbm(params["amplitude_volts"]["mixed_pulse"][c], params["powers"]["drive"]),
                 length=timeToSamples(params["timings_sec"]["mixed_initilise"], params["timings_sec"]["sampling_divider"]),
                 wave_index=0,
                 ct_index=0,
                 samplingDivider=params["timings_sec"]["sampling_divider"]
                 )
    upload_command_tables(shfqc)


def setup_hyper_command_tables(shfqc: SHFQC, params):
    """
    Set up the command tables for a whole detuning sweep on device.
    Index 0 => Corresponds to creation of the mixed state pulse
    """
    read_pulse_time = 2*params["timings_sec"]["buffer"] + params["timings_sec"]["read"]
    samplingDivider=params["timings_sec"]["sampling_divider"]
    # Setup mixed pulse
    for c in ["P1", "P2"]:
        cmdtable(shfqc.cmd_tables[c],
                 amplitude=voltToDbm(params["amplitude_volts"]["mixed_pulse"][c], params["powers"]["drive"]),
                 length=timeToSamples(params["timings_sec"]["mixed_initilise"], params["timings_sec"]["sampling_divider"]),
                 wave_index=0,
                 ct_index=0,
                 samplingDivider=params["timings_sec"]["sampling_divider"]
                 )

    # Setup detuning pulsing
    p1_steps = np.linspace(params["amplitude_volts"]["measure_pulse_start"]["P1"], params["amplitude_volts"]["measure_pulse_end"]["P1"], params["averaging"]["num_detuning"])
    p2_steps = np.linspace(params["amplitude_volts"]["measure_pulse_start"]["P2"], params["amplitude_volts"]["measure_pulse_end"]["P2"], params["averaging"]["num_detuning"])
    ct_indexs = np.arange(1, params["averaging"]["num_detuning"]+1)
    for (ct, p1, p2) in zip(ct_indexs, p1_steps, p2_steps):
        cmdtable(shfqc.cmd_tables["P1"],
                amplitude=voltToDbm(p1, shfqc["P1"].output.range()),
                length=timeToSamples(read_pulse_time, samplingDivider),
                wave_index=1,
                ct_index=int(ct),
                samplingDivider=params["timings_sec"]["sampling_divider"]
                )
        cmdtable(shfqc.cmd_tables["P2"],
                amplitude=voltToDbm(p2, shfqc["P2"].output.range()),
                length=timeToSamples(read_pulse_time, samplingDivider),
                wave_index=1,
                ct_index=int(ct),
                samplingDivider=params["timings_sec"]["sampling_divider"]
                )

    # Constant J pulse for the experiment. Upload in move_j_measurement
    upload_command_tables(shfqc)


###### RUN ######

def wait_for_internal_trigger(shfqc: SHFQC, progress=True, leave=True):
    """
    Waits for the internal trigger to finish running and shows the current progress.
    Progress = if show tqdm progress meter
    Leave = if keep progress bar afterwards
    """
    if progress:
        pbar = tqdm(total=100, leave=leave, desc="Internal trigger")
    while shfqc.device.system.internaltrigger.progress() != 1.0:
        p = int(shfqc.device.system.internaltrigger.progress()*100)
        if progress:
            pbar.update(p-pbar.n)
        time.sleep(0.001)
    if progress:
        pbar.update(100-pbar.n)
        pbar.close()


def get_results(shfqc: SHFQC, result_node, timeout):
    """Subscribe to the given node and retrieve the results."""
    wave_data_captured = {}
    wave_data_captured[result_node] = False
    start_time = time.time()
    captured_data = {}
    while not all(wave_data_captured.values()):
        if start_time + timeout < time.time():
            print(captured_data)
            raise TimeoutError('Timeout before all samples collected.')
        test = shfqc.session.poll()
        for node, value in test.items():
            node = shfqc.session.raw_path_to_node(node)
            for v in value:
                if node not in captured_data:
                    captured_data[node] = [v['vector']]
                else:
                    captured_data[node].append(v['vector'])
            if len(captured_data[node]) >= 1:  # readout 1 point
                wave_data_captured[node] = True
                # total_num_data = sum([len(element) for element in captured_data[node]])
    data = captured_data[result_node][0]
    return data


def check_sequencers_finished(shfqc: SHFQC, sequencers):
    """
    Check if the sequencers have finished their programs.
    sequencers = ["measure", "ST"] etc are the sequencers to check
    """
    # Status of the Sequencer on the instrument.
    # - Bit 0: Sequencer is running;
    # - Bit 1: reserved;
    # - Bit 2: Sequencer is waiting for a trigger to arrive;
    # - Bit 3: Sequencer has detected an error;
    # - Bit 4: sequencer is waiting for synchronization with other channels

    for c in sequencers:
        if c == shfqc.qa_channel_name:
            state = shfqc[c].generator.sequencer.status()
        else:
            state = shfqc[c].awg.sequencer.status()
        if state != 4:
            logging.warn(f"Sequencer {c} in unknown state. Perhaps they are not synchronised? State = {bin(state)}")


def check_all_results_acquired(shfqc: SHFQC, len_results):
    """Check that all the desired results have been acquired. (Otherwise spectroscopy setup is incorrect!)"""
    acq = shfqc["measure"].spectroscopy.result.acquired()
    if len_results > acq:
        print("QA CHANNEL READY? -", shfqc["measure"].generator.ready())
        print("SG CHANNELS READY? -", [shfqc[c].awg.ready() for c in shfqc.sg_channel_names])
        raise TimeoutError(f"Not all datapoints measured in the time provided. {acq} of {len_results}.")


###### FEEDBACK ######

def calculate_feedback(shfqc: SHFQC, last_point, params):
    """Calculate the appropriate feedback adjustment to ST."""
    # use last datapoint
    unit_amp = 0.34
    error = params["feedback"]["target"]- autodb(last_point)
    st_err = error * params["feedback"]["stepsize"] * params["feedback"]["slope"]
    st_err = -1 if st_err < -1 else (1 if st_err > 1 else st_err)
    st_corr = st_err*unit_amp

    # update command table
    cmdtable(shfqc.cmd_tables["ST"],
             amplitude= voltToDbm(st_corr, params["powers"]["drive"]),
             length=timeToSamples(params["timings_sec"]["trigger"]-2e-3, 9),  # TODO: Remove constant
             wave_index=0,
             ct_index=0,
             samplingDivider=params["timings_sec"]["sampling_divider"],
            )
    return st_corr


def move_j_measurement(shfqc: SHFQC, j, params):
    """Modify the j command table to measure the next appropriate data point."""
    samplingDivider = params["timings_sec"]["sampling_divider"]
    read_len = params["timings_sec"]["read"]
    buffer = params["timings_sec"]["buffer"]
    mw_len = params["timings_sec"]["mw_pulse"]
    cmdtable(shfqc.cmd_tables["J"],
             amplitude= voltToDbm(j, shfqc["J"].output.range()),
             length=timeToSamples(buffer + read_len + mw_len, samplingDivider),  # TODO: THIS LINE IS WRONG
             wave_index=0,
             ct_index=1,
             samplingDivider=params["timings_sec"]["sampling_divider"]
            )


def change_mw_freq(shfqc: SHFQC, params):
    """Change the ESR chirp frequency by uploading a new sequence."""
    samplingDivider = params["timings_sec"]["sampling_divider"]
    wait_and_settle = params["timings_sec"]["settle"]
    read_len = params["timings_sec"]["read"]
    init_len = params["timings_sec"]["mixed_initilise"]
    buffer = params["timings_sec"]["buffer"]
    mw_len = params["timings_sec"]["mw_pulse"]
    
    mw_amp = params["mw"]["gain"]
    mw_phase = 0 # hardcoded, don't need it changed but need it in sequence
    # mw_start_freq = freq
    # mw_stop_freq = freq + params["mw"]["span"]

    seqc_program_mw = f"""
    // Assign a single channel waveform to wave table entry 0
    wave w_mw = ones({timeToSamples(mw_len, params["mw"]["sampling_divider"])});
    assignWaveIndex(1,2, w_mw, 0);

    // Reset the oscillator phase
    resetOscPhase();

    repeat({params["averaging"]["seqc_averages"]}) {{

        // Trigger the scope

        waitDigTrigger(1);

        setTrigger(1);
        setTrigger(0);

        playZero({timeToSamples(init_len, samplingDivider)},  {samplingDivider});           // mixed state init.
        playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});    // wait and settle
        playZero({timeToSamples(read_len, samplingDivider)},  {samplingDivider});           // read reference

        executeTableEntry(1);                                                               // chirp

        // playZero({timeToSamples(read_len, samplingDivider)},  {samplingDivider});           // read
        playZero({timeToSamples(wait_and_settle, samplingDivider)},  {samplingDivider});    // wait and settle
        playZero(32);    // wait and settle
    }}
    """
    # shfqc["MW_I"].awg.load_sequencer_program(seqc_program_mw)
    # shfqc["MW_Q"].awg.load_sequencer_program(seqc_program_mw)
    shfqc["MW"].awg.load_sequencer_program(seqc_program_mw)
    # Make sure to reupload command tables as they are cleared whenever a sequence is loaded



def movemeasurement(shfqc: SHFQC, p1, p2, j, mw, params):
    """Modify the command tables of P1/P2/J to measure the next appropriate datapoint. mw in au not dB"""
    samplingDivider = params["timings_sec"]["sampling_divider"]
    read_len = params["timings_sec"]["read"]
    buffer = params["timings_sec"]["buffer"]

    cmdtable(shfqc.cmd_tables["P1"],
             amplitude=voltToDbm(p1, shfqc["P1"].output.range()),
             length=timeToSamples(buffer + read_len + buffer, samplingDivider),
             wave_index=1,
             ct_index=1,
             samplingDivider=params["timings_sec"]["sampling_divider"]
            )
    cmdtable(shfqc.cmd_tables["P2"],
             amplitude=voltToDbm(p2, shfqc["P2"].output.range()),
             length=timeToSamples(buffer + read_len + buffer, samplingDivider),
             wave_index=1,
             ct_index=1,
             samplingDivider=params["timings_sec"]["sampling_divider"]
            )
    cmdtable(shfqc.cmd_tables["MW"],
             amplitude=mw,
             length=timeToSamples(params["timings_sec"]["mw_pulse"], params["mw"]["sampling_divider"]),
             wave_index=0,
             ct_index=1,
             samplingDivider=params["mw"]["sampling_divider"]
    # cmdtable(shfqc.cmd_tables["MW_I"],
    #          amplitude=mw,
    #          length=timeToSamples(params["timings_sec"]["mw_pulse"], params["mw"]["sampling_divider"]),
    #          wave_index=0,
    #          ct_index=1,
    #          samplingDivider=params["mw"]["sampling_divider"]
    #         )
    # cmdtable(shfqc.cmd_tables["MW_Q"],
    #          amplitude=mw,
    #          length=timeToSamples(params["timings_sec"]["mw_pulse"], params["mw"]["sampling_divider"]),
    #          wave_index=0,
    #          ct_index=1,
    #          samplingDivider=params["mw"]["sampling_divider"]
            )
    move_j_measurement(shfqc, j, params)

def upload_dummy_sequence(shfqc: SHFQC, mw, params):
    """Modify the command tables of P1/P2/J to measure the next appropriate datapoint. mw in au not dB"""
    samplingDivider = params["timings_sec"]["sampling_divider"]

    cmdtable(shfqc.cmd_tables["MW"],
             amplitude=mw,
             length=timeToSamples(params["timings_sec"]["mw_pulse"], params["mw"]["sampling_divider"]),
             wave_index=0,
             ct_index=1,
             samplingDivider=params["mw"]["sampling_divider"]
            )
    # cmdtable(shfqc.cmd_tables["MW_Q"],
    #          amplitude=mw,
    #          length=timeToSamples(params["timings_sec"]["mw_pulse"], params["mw"]["sampling_divider"]),
    #          wave_index=0,
    #          ct_index=1,
    #          samplingDivider=params["mw"]["sampling_divider"]
    #         )

###### EXPERIMENTS ######

def run_empty_experiment(shfqc: SHFQC):
    """Run measurement where we only measure and don't drive anything."""
    shfqc.device.system.internaltrigger.enable(0)

    result_node = shfqc["measure"].spectroscopy.result.data.wave
    result_node.subscribe()

    shfqc["measure"].spectroscopy.result.enable(1)  # start logger
    shfqc["measure"].generator.enable_sequencer(single=True)
    shfqc.device.system.internaltrigger.enable(1)

    time.sleep(0.2)  # delay for networking issues

    # wait for the measurement to complete
    wait_for_internal_trigger(shfqc)
    check_sequencers_finished(shfqc, ["measure"])


    # wait for completion
    while shfqc["measure"].spectroscopy.result.enable() != 0:
        #print(shfqc["measure"].spectroscopy.result.enable())
        shfqc["measure"].spectroscopy.result.enable.wait_for_state_change(0, timeout=10)

    # get results
    results = get_results(shfqc, result_node, timeout=5)
    result_node.unsubscribe()

    # verify results
    check_all_results_acquired(shfqc, len(results))

    return results


def run_esr_experiment(shfqc: SHFQC):
    """Run one ESR freqq sweep experiment. Returns the reference and measurement points."""
    shfqc.device.system.internaltrigger.enable(0)

    result_node = shfqc["measure"].spectroscopy.result.data.wave
    result_node.subscribe()

    shfqc["measure"].spectroscopy.result.enable(1)  # start logger

    # start sequencers
    shfqc["measure"].generator.enable_sequencer(single=True)
    shfqc["J"].awg.enable_sequencer(single=True)  # dont want to repeat
    shfqc["P1"].awg.enable_sequencer(single=True)
    shfqc["P2"].awg.enable_sequencer(single=True)
    shfqc["MW"].awg.enable_sequencer(single=True)
    # shfqc["MW_I"].awg.enable_sequencer(single=True)
    # shfqc["MW_Q"].awg.enable_sequencer(single=True)

    # start triggering sequence (which starts each sequencer)
    shfqc.device.system.internaltrigger.enable(1)
    time.sleep(0.2)

    # wait for the measurement to complete
    wait_for_internal_trigger(shfqc, progress=True, leave=False)
    # device.system.internaltrigger. .wait_for_state_change(1.0, timeout=100)  # wait for completion

    # Don't check if sequencers have finished as they say they haven't finished... but they really have
    #check_sequencers_finished(shfqc, ["measure", "P1", "P2"])

    # wait for completion
    while shfqc["measure"].spectroscopy.result.enable() != 0:
        shfqc["measure"].spectroscopy.result.enable.wait_for_state_change(0, timeout=100)

    # get results
    results = get_results(shfqc, result_node, timeout=5)
    result_node.unsubscribe()

    # verify results
    #check_all_results_acquired(shfqc, len(results))

    # return np.mean(results.reshape((seq_averages, 2)), axis=0)
    return results

def run_dummy_sequence(shfqc: SHFQC):
    """Run one ESR freqq sweep experiment. Returns the reference and measurement points."""
    shfqc.device.system.internaltrigger.enable(0)
    time.sleep(1)

    # result_node = shfqc["measure"].spectroscopy.result.data.wave
    # result_node.subscribe()

    # shfqc["measure"].spectroscopy.result.enable(1)  # start logger

    # # start sequencers
    # shfqc["measure"].generator.enable_sequencer(single=True)
    # shfqc["J"].awg.enable_sequencer(single=True)  # dont want to repeat
    # shfqc["P1"].awg.enable_sequencer(single=True)
    # shfqc["P2"].awg.enable_sequencer(single=True)
    # shfqc["ST"].awg.enable_sequencer(single=True)
    # shfqc["MW_I"].awg.enable_sequencer(single=True)
    shfqc["MW"].awg.enable_sequencer(single=True)
    time.sleep(1)

    # start triggering sequence (which starts each sequencer)
    shfqc.device.system.internaltrigger.enable(1)
    time.sleep(0.2)

    # wait for the measurement to complete
    wait_for_internal_trigger(shfqc, progress=True, leave=False)
    # device.system.internaltrigger. .wait_for_state_change(1.0, timeout=100)  # wait for completion

    # Don't check if sequencers have finished as they say they haven't finished... but they really have
    #check_sequencers_finished(shfqc, ["measure", "P1", "P2"])

    # wait for completion
    # while shfqc["measure"].spectroscopy.result.enable() != 0:
    #     shfqc["measure"].spectroscopy.result.enable.wait_for_state_change(0, timeout=100)

    # # get results
    # results = get_results(shfqc, result_node, timeout=5)
    # result_node.unsubscribe()

    # # verify results
    # #check_all_results_acquired(shfqc, len(results))

    # # return np.mean(results.reshape((seq_averages, 2)), axis=0)
    # return results


def run_hyper_psb_experiment(shfqc: SHFQC):
    """Run one loop of detuning for PSB experiment. Return collection of reference and measurement points."""
    shfqc.device.system.internaltrigger.enable(0)

    result_node = shfqc["measure"].spectroscopy.result.data.wave
    result_node.subscribe()

    shfqc["measure"].spectroscopy.result.enable(1)  # start logger

    # start sequencers
    shfqc["measure"].generator.enable_sequencer(single=True)
    shfqc["J"].awg.enable_sequencer(single=True)  # dont want to repeat
    shfqc["P1"].awg.enable_sequencer(single=True)
    shfqc["P2"].awg.enable_sequencer(single=True)
    shfqc["ST"].awg.enable_sequencer(single=True)

    # start triggering sequence (which starts each sequencer)
    shfqc.device.system.internaltrigger.enable(1)
    time.sleep(0.2)

    # wait for the measurement to complete
    wait_for_internal_trigger(shfqc, progress=True, leave=False)

    check_sequencers_finished(shfqc, ["measure", "P1", "P2"])  # we have time to check this

    # wait for completion
    while shfqc["measure"].spectroscopy.result.enable() != 0:
        shfqc["measure"].spectroscopy.result.enable.wait_for_state_change(0, timeout=100)

    # get results
    print("Downloading results...")
    results = get_results(shfqc, result_node, timeout=20)
    result_node.unsubscribe()

    # verify results
    check_all_results_acquired(shfqc, len(results))

    return results
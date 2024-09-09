# -*- coding: utf-8 -*-
"""
Convert between different units. Fixes numerous issues previously present in the code....

Created on Fri Sep 6 11:50 2024

@author: james
"""

import numpy as np


def timeToSamples(time, samplingRateDivider):
    """Returns the number of samples divisible by 16 given a time (in seconds) and sampling rate divider"""
    samples_raw = time * (1/(2**samplingRateDivider))/0.5e-9
    #samples_modulo = int(samples_raw) % 16
    #samples = int(samples_raw) - int(samples_modulo)
    #return samples
    return 16*int(np.floor(samples_raw/16))  # my faster method


def volt_to_arbitrary(volt, dbm_range):
    """Convert from voltage to an arbitrary scaling factor depending on the output range."""
    vmax = np.sqrt(2 * 10**(dbm_range/10) * 1e-3 * 50)  # See SHFQC manual page 52 (4.1)
    if np.abs(volt) > vmax:
        raise ValueError(f"Cannot convert voltage {volt} to arbitrary value with setting {dbm_range} dBm. Max voltage is +-{vmax}")
    arb = volt / vmax
    return arb


def max_volt(dbm_range):
    """Find the maximum voltage we can output at a given power"""
    return np.sqrt(2 * 10**(dbm_range/10) * 1e-3 * 50)  # See SHFQC manual page 52 (4.1)



def voltToDbm(volt, dbmrange):
    """Convert from voltage to dBm (power)"""
    # Ok yes this can be better, deal with it
    raise Exception("this is wrong. use new formulas")
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
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 21 16:38 2024

Functions to plot the plots used in my thesis.

@author: james
"""

from monty import Monty, loadraw
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import os


default_ftype = ".pdf"
default_color = "orange"
default_color_2 = "green"
default_cmap = mpl.colormaps["viridis"]

ST = "SET Plunger (V)"
DETUNING = "$P_1 - P_2$ (V)"

## Common functions ##

def autodb(res):
    """Change a.u. to dB power. Used in the data result."""
    return 10*np.log10(np.abs(res)**2/50*1000)


def autodeg(res):
    """Change a.u. result to phase angle in degrees."""
    return np.unwrap(np.angle(res))


def save_plot(fname, ftype=None):
    ftype = ftype if ftype is not None else default_ftype
    path = os.path.join('figures', fname + ftype)
    print(f"Saved to {path}")
    plt.savefig(path, bbox_inches='tight')


def plot_amp_phase(X, amp, phase, xlabel="P1 voltage", fname="fname"):
    """Plot both amplitude and phase of a result."""
    fig, (ax0, ax1) = plt.subplots(nrows=2, sharex=True)
    ax0.plot(X, amp, ".", color=default_color)
    ax1.plot(X, phase, ".", color=default_color_2)
    ax0.set_ylabel("Amplitude (dBm)")
    ax1.set_ylabel("Phase (deg)")
    ax1.set_xlabel(xlabel)
    fig.align_ylabels([ax0, ax1])
    plt.tight_layout()
    fig.patch.set_alpha(0.0)  # transparent axes
    save_plot(fname)


def oned_plot(X, Y, xlabel="x label", ylabel="y label", fname="fname"):
    """Plot a simple 1D plot"""
    fig, ax = plt.subplots()
    ax.plot(X, Y, color=default_color)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    # ax.grid()
    plt.tight_layout()
    fig.patch.set_alpha(0.0)  # transparent axes
    save_plot(fname)


def oned_two_plots(X, Y1, Y2, xlabel="x label", y1label="y1 label", y2label="y2 label", fname="fname"):
    fig, (ax0, ax1) = plt.subplots(nrows=2, sharex=True)
    ax0.plot(X, Y1, "-", color=default_color)
    ax0.set_ylabel(y1label)
    ax1.plot(X, Y2, "-", color=default_color_2)
    ax1.set_ylabel(y2label)
    ax1.set_xlabel(xlabel)
    plt.tight_layout()
    fig.patch.set_alpha(0.0)  # transparent axes
    save_plot(fname)


def twod_plot(X, Y, Z, xlabel="x label", ylabel="y label", zlabel="z label", fname="fname"):
    """Plot a simple 2D plot"""
    fig, ax = plt.subplots()
    # This may look backwards but it is the right order since I define my matrices weird
    im = ax.pcolormesh(X, Y, Z, shading="nearest", cmap=default_cmap)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    # ax.set_zlabel(zlabel)

    fig.colorbar(im, ax=ax, label=zlabel)
    plt.tight_layout()
    fig.patch.set_alpha(0.0)  # transparent axes
    save_plot(fname, ftype=".png")


## Actual functions
def coulomb_blockade():
    monty = Monty("summary.dc_detuning")
    result = monty.loadrun("SET_ST_sweep.1")
    X = np.linspace(3.3, 3.7, 201)
    Y = result["R"] * 1e9  # convert to nA
    oned_plot(X, Y, xlabel=ST, ylabel="Current (nA)", fname="coulombs")

    monty = Monty("dc.power_recovery")
    result = monty.loadrun("1D_SET_sweep.7")
    X = np.linspace(3.2, 3.3, 101)
    Y = result["R"] * 1e9
    oned_plot(X, Y, xlabel=ST, ylabel="Current (nA)", fname="3_peaks")

    monty = Monty("dc.power_recovery")
    result = monty.loadrun("1D_SET_sweep.7")
    range = slice(35, 70)
    X = np.linspace(3.2, 3.3, 101)[range]
    Y = result["R"][range] * 1e9
    oned_plot(X, Y, xlabel=ST, ylabel="Current (nA)", fname="1_peaks")


def naive_detuning_1d():
    result = loadraw("double_dot/initial/P1_scan.7.xz")["data"]
    X = np.linspace(1.85, 1.9, 400)
    Y = result["R"] * 1e12
    oned_plot(X, Y, xlabel=DETUNING, ylabel="Current (pA)", fname="naive_detuning")

    monty = Monty("sam.load_e2")
    result = monty.loaddata("P1_scan.7")
    X = np.linspace(2.1, 1.75, 600)
    Y = result["R"] * 1e12
    oned_plot(X, Y, xlabel=DETUNING, ylabel="Current (pA)", fname="without_feedback")


def detuning_1d():
    monty = Monty("dc.power_recovery")
    result = monty.loadrun("detuning_scan.82")
    X = np.linspace((1.625 - 2.1) / np.sqrt(2), (2.1 - 1.625) / np.sqrt(2), 1001)
    Y1 = result["R"] * 1e12
    Y2 = result["ST"]
    cutoff = 100  # focus on the important region
    X = X[cutoff:]
    Y1 = Y1[cutoff:]
    Y2 = Y2[cutoff:]
    oned_two_plots(X, Y1, Y2, DETUNING, "Current (pA)", ST, "4_electrons")

    monty = Monty("double_dot.detuning")
    result = monty.loaddata("detuning_scan.7")
    X = np.linspace((1.75 - 2.1) / np.sqrt(2), (2.1 - 1.75) / np.sqrt(2), 400)
    Y1 = result["R"] * 1e12
    Y2 = result["ST"]
    oned_two_plots(X, Y1, Y2, DETUNING, "Current (pA)", ST, "3_electrons")


def isolated_mode_2d():
    monty = Monty("double_dot.load_e3")
    result = monty.loaddata("p1_vs_p2.2")
    R = result["R"][::2, :] * 1e12
    X = np.linspace(1.75, 2.1, 200)
    Y = np.linspace(1.75, 2.1, 100)
    twod_plot(X, Y, R, "$P_1$ (V)", "$P_2$ (V)", "Current (pA)", "double_isolated")

    monty = Monty("double_dot.detuning")
    result = monty.loaddata("detuning_vs_J.2")
    R = result["R"][::2, :] * 1e12
    Y = np.linspace(3.0, 4.0, 150)[::-1]
    X = np.linspace(-0.75, 0.75, 200)
    twod_plot(X, Y, R, "$P_1 - P_2$ (V)", "$J$ (V)", "Current (pA)", "isolated_dots")

    monty = Monty("summary.dc_detuning")
    result = monty.loaddata("detuning_vs_J.2")
    R = result["R"][::2, :] * 1e12
    Y = np.linspace(2.9, 3.8, 101)[::-2]
    dd = (2.1-1.625)/np.sqrt(2)
    X = np.linspace(-dd, dd, 401)
    twod_plot(X, Y, R, "$P_1 - P_2$ (V)", "$J$ (V)", "Current (pA)", "4_isolated_dots")

    monty = Monty("summary.dc_detuning")
    result = monty.loaddata("detuning_vs_J.10")
    R = result["R"][::2, :] * 1e12
    Y = np.linspace(3.3, 3.6, 201)[::2]
    dd = 0.1
    X = np.linspace(-dd, dd, 501)
    twod_plot(X, Y, R, "$P_1 - P_2$ (V)", "$J$ (V)", "Current (pA)", "2_isolated_dots")


def pauli_spin_blockade():
    monty = Monty("rf.psb_best")
    result = monty.loadrun("hyper_j.20")
    data = result["data"]
    ref = data[:, ::2][0]
    mes = data[:, 1::2][0]

    ref_amp = autodb(ref)
    ref_phase = autodeg(ref)
    mes_amp = autodb(mes)
    mes_phase = autodeg(mes)  # add axis for unwrap?

    # X axis (p1_steps)
    X = np.linspace(0, -0.006, 1001) * 1e3
    d_phase = mes_phase - ref_phase
    d_amp = mes_amp - ref_amp
    plot_amp_phase(X, d_amp, d_phase, "$P_1 - P_2$ (mV)", "1d_pauli")


def coulomb_in_rf():
    monty = Monty("rf.set_testing")
    result = monty.loadrun("rf_ST_sweep.9")
    data = result["data"]
    amp = autodb(data)
    phase = autodeg(data)
    X = np.linspace(0, -0.4, 401) * 1e3
    plot_amp_phase(X, amp, phase, "SET Plunger (mV)", "rf_coulomb")


def impedance_network():
    monty = Monty("rf.set_testing")
    data = monty.loadrun("spectroscopy")["data"]
    amp = autodb(data)
    phase = autodeg(data)
    X = np.linspace(300, 500, 401)
    plot_amp_phase(X, amp, phase, "Impedance frequency (MHz)", "impedance_network")


def coulomb_diamonds():
    monty = Monty("summary.dc_detuning")
    result = monty.loaddata("coulomb_diamond.23")
    R = result["R"][::2, :] * 1e12
    Y = np.linspace(-0.01, 0.01, 201)[::2] * 1e3
    X = np.linspace(3.6, 3.7, 501)
    twod_plot(X, Y, R, "Plunger gate (V)", "Bias (mV)", "Current (pA)", "diamond")


def fake():
    x,y = (400, 400)
    R = np.linspace(0, 0.02, x*y).reshape((y,x))
    J = np.linspace(3.35, 3.77, y)
    det = np.linspace(0, -0.006, x)
    twod_plot(det, J, R, DETUNING, "J (V)", "Amplitude (dBm)", "psb_fake")


def ramping():
    # Print the ramping rates
    monty = Monty("rf.decay")
    result = monty.loadrun("p1_decay.119")
    data = result["data"]
    gX = np.linspace(0, 0.0008, 30)[:30-10-5] * 1e3
    gamp = autodb(data)[5:30-10]

    monty = Monty("rf.decay")
    result = monty.loadrun("p1_decay.93")
    data = result["data"]
    wX = np.linspace(0, 0.002, 30)[:30-10-5] * 1e3
    wamp = autodb(data)[5:30-10]

    # sync data to align
    gamp -= gamp[0]
    wamp -= wamp[0]
    print(monty.parameters)

    fig, ax = plt.subplots()
    ax.plot(gX, gamp, ".", color=default_color, label="Ramp = 0.13 mV/s")
    ax.plot(wX, wamp, ".", label="Ramp = 0 V/s")
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("RF signal (a.b. units)")
    plt.legend()
    plt.tight_layout()
    fig.patch.set_alpha(0.0)  # transparent axes
    save_plot("ramping")


def coulomb_rf_power_sweep():
    # Plot the power sweep version of coulomb blockade
    monty = Monty("rf.set_testing")
    result = monty.loadrun("pwr_set_sweep.15")
    data = result["data"]

    print(monty.parameters)
    print(data.keys())

    X = np.linspace(-0.5, 0.5, 401)

    fig, (ax0, ax1) = plt.subplots(nrows=2, sharex=True)

    colors = default_cmap(np.linspace(0, 1, 8))

    for (i, k) in enumerate(data.keys()):
        if k != "-30":
            amp = autodb(data[k]) - int(k)
            phase = autodeg(data[k])
            ax0.plot(X, amp, "-", color=colors[i], label=k)
            ax1.plot(X, phase, "-", color=colors[i])

    #ax0.legend(loc='center left', bbox_to_anchor=(1.04, 0.0),
              #ncol=1, fancybox=True, shadow=False)
    fig.legend(loc='outside center right', bbox_to_anchor=(1.08, 0.5), title="Power (dBm)")

    ax0.set_ylabel("Amplitude (dBm)")
    ax1.set_ylabel("Phase (deg)")
    ax1.set_xlabel(ST)
    fig.align_ylabels([ax0, ax1])
    #plt.tight_layout()
    fig.patch.set_alpha(0.0)  # transparent axes
    save_plot("rf_coulomb_pwr_sweep")

## Run everything ##


def main():
    coulomb_blockade()
    naive_detuning_1d()
    detuning_1d()
    isolated_mode_2d()
    pauli_spin_blockade()
    coulomb_diamonds()
    coulomb_in_rf()
    impedance_network()
    fake()
    ramping()
    coulomb_rf_power_sweep()


if __name__ == "__main__":
    main()

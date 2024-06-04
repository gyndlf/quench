# -*- coding: utf-8 -*-
"""
Created on Tue Jun 04 14:30 2024

Plotting functions from notebook

@author: jzingel
"""

import numpy as np
import matplotlib.pyplot as plt


def plot_sweeper(f, result, unwrap=True, deg=True):
    """Plot results from Sweeper"""
    f = f / 1e9
    power = 10 * np.log10(np.abs(result) ** 2 / 50 * 1000)
    phase = np.unwrap(np.angle(result, deg=deg)) if unwrap is True else np.angle(result, deg=deg)
    phase_unit = 'deg' if deg is True else 'rad'

    fig, (ax0, ax1) = plt.subplots(nrows=2, sharex=True)
    ax0.plot(f, power, '.-', color='steelblue', label='power')
    ax0.legend(loc='upper left')
    ax0.set_ylabel('Power (dBm)')
    ax1.plot(f, phase, '.-', color='orange', label='phase')
    ax1.legend(loc='upper left')
    ax1.set_xlabel('Frequency (GHz)')
    fig.align_ylabels([ax0, ax1])
    ax0.grid()
    ax1.grid()
    ax1.set_ylabel(f'Phase ({phase_unit})')
    plt.tight_layout()
    plt.show()


def plot_n(x, y, z, do_plot=1):
    """Plot multiple results"""
    if do_plot == 1:
        power = 10 * np.log10(np.abs(z) ** 2 / 50 * 1000)
        phase = np.angle(z, deg=True)

        fig, (ax0, ax1) = plt.subplots(nrows=2, sharex=True)
        for i in range(len(power)):
            ax0.plot(x / 1e9, power[i], '.-', color=colors[i], label=f'gain = {y[i]}')
            ax1.plot(x / 1e9, phase[i], '.-', color=colors[i], label=f'gain = {y[i]}')
        ax0.set_ylabel('Power (dBm)')
        ax1.set_ylabel('Phase (deg)')
        ax1.set_xlabel('Frequency (GHz)')
        ax0.legend(loc='upper left')
        ax1.legend(loc='upper left')
        ax0.grid()
        ax1.grid()
        fig.tight_layout()
        fig.align_ylabels([ax0, ax1])


def plot_2d(x, y, z, do_plot=1):
    """2D plot"""
    if do_plot == 1:
        x = x / 1e9
        x0 = np.zeros(len(x) + 1)
        x0[:-1] = x - (x[1] - x[0]) / 2
        x0[-1] = x[-1] + (x[1] - x[0]) / 2
        y0 = np.zeros(len(y) + 1)
        y0[:-1] = y - (y[1] - y[0]) / 2
        y0[-1] = y[-1] + (y[1] - y[0]) / 2

        z_abs = 10 * np.log10(np.abs(z) ** 2 / 50 * 1000)
        z_angle = np.angle(z, deg=True)
        X, Y = np.meshgrid(x0, y0)

        fig, (ax0, ax1) = plt.subplots(nrows=2, sharex=True)
        c0 = ax0.pcolormesh(X, Y, z_abs)
        ax0.set_yticks(y)
        ax0.set_ylabel('Gain')
        ax0.set_title('Power (dBm)')
        fig.colorbar(c0, ax=ax0)

        c1 = ax1.pcolormesh(X, Y, z_angle)
        ax1.set_yticks(y)
        ax1.set_xlabel('Offset frequency (GHz)')
        ax1.set_ylabel('Gain')
        ax1.set_title('Phase (degree)')
        fig.colorbar(c1, ax=ax1)

        fig.tight_layout()
        plt.show()


# -*- coding: utf-8 -*-
"""
Created Sat Jun 1 12:00:00 2024

Parent object for live plotters

@author: jzingel
"""

import matplotlib.pyplot as plt
import os
import numpy as np


class LiveBase:
    def __init__(self):
        """Set up the engine."""
        # don't use inbuilt pycharm/spyder plotting window which cannot show animations
        self.prev_backend = plt.get_backend()
        if os.name == "posix":
            plt.switch_backend("TkAgg")  # mac or linux
        else:
            plt.switch_backend("Qt5Agg")

    def __enter__(self):
        """
        Yield the plot engine object to use
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Close the current plot window
        """
        # TODO: Add message describing the error?
        plt.close()
        plt.switch_backend(self.prev_backend)  # use IDE plots

    def update(self, Y: np.ndarray):
        """
        Update the plot data with new incoming data
        """
        pass

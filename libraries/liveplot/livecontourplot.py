# -*- coding: utf-8 -*-
"""
Created Tue May 28 22:00:00 2024

Plot 2D live as it is being generated. Assumes that the X and Y ranges are fixed while Z may vary.

For reference of the animation process see: https://matplotlib.org/stable/users/explain/animations/blitting.html

@author: jzingel
"""

import matplotlib.pyplot as plt
import numpy as np
import os


class LiveContourPlot:
    def __init__(self, X: np.ndarray, Y: np.ndarray, xlabel="x", ylabel="y",
                 colorbar=True, figsize=(8,6), replace_zero_with_nan=True):
        """
        Set up the live 2D plotting engine
        """
        # don't use inbuilt pycharm/spyder plotting window which cannot show animations
        self.prev_backend = plt.get_backend()
        if os.name == "posix":
            plt.switch_backend("TkAgg")  # mac or linux
        else:
            plt.switch_backend("Qt5Agg")

        self.X = X
        self.Y = Y
        self.Z_shape = (Y.shape[0], X.shape[0])
        self.show_colorbar = colorbar
        self.replace_zero = replace_zero_with_nan

        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title("Realtime data")

        # get started
        self.qmesh = self.ax.pcolormesh(X, Y, np.zeros(self.Z_shape), animated=True)

        if self.show_colorbar:  # see https://matplotlib.org/stable/users/explain/axes/colorbar_placement.html
            self.cbar = self.fig.colorbar(self.qmesh, ax=self.ax) # ax=self.ax)
            self.cbar.ax.set_visible(False)

        plt.show(block=False)
        plt.pause(0.1)  # flush changes

        # now blit the image
        self.bg = self.fig.canvas.copy_from_bbox(self.fig.bbox)
        self.ax.draw_artist(self.qmesh)
        self.fig.canvas.blit(self.fig.bbox)  # show the result on the screen

        if self.show_colorbar:
            self.cbar.ax.set_visible(True)

    def __enter__(self):
        """
        Yeild the live plot object to use
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Close the current plot window
        """
        plt.close()
        plt.switch_backend(self.prev_backend)

    def update(self, Z: np.ndarray):
        """
        Update the plot with new incoming data
        """
        if Z.shape != self.Z_shape:
            raise ValueError(f"Z shape of {Z.shape} does not match X shape of {self.X.shape} and Y shape {self.Y.shape}")
        if self.replace_zero:
            Z[Z == 0] = np.nan

        self.fig.canvas.restore_region(self.bg)  # restore to blit
        self.qmesh.set_array(Z)

        self.qmesh.autoscale()  # adjust colors to scale
        self.qmesh.changed()

        # draw what updated
        self.ax.draw_artist(self.ax.patch)
        self.ax.draw_artist(self.qmesh)
        if self.show_colorbar:
            self.cbar.ax.draw_artist(self.cbar.ax)  # draw colorbar

        if os.name != "posix":
            self.fig.canvas.update()
        self.fig.canvas.blit(self.fig.bbox)
        self.fig.canvas.flush_events()  # flush the changes to the gui


if __name__ == "__main__":
    import time

    x = np.linspace(0, 10, 30)
    y = np.linspace(5, 15, 10)
    z = np.zeros((len(y), len(x)))
    with LiveContourPlot(x, y, colorbar=False) as lplot:
        for i in range(len(y)):
            for j in range(len(x)):
                z[i,j] = np.random.rand() + 0.1 + len(y)*i + j
                lplot.update(z)
                time.sleep(0.01)

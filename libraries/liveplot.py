# -*- coding: utf-8 -*-
"""
Created May 26, 2024

Plot 1D live as it is being generated

For reference of the animation process see: https://matplotlib.org/stable/users/explain/animations/blitting.html

@author: jzingel
"""


import matplotlib.pyplot as plt
import time
import numpy as np


class LivePlot:
    def __init__(self, X: np.ndarray, xlabel="x", ylabel="y"):
        """
        Set up the live 1D plotting engine.
        """
        self.prev_backend = plt.get_backend()
        plt.switch_backend("TkAgg")  # don't use inbuilt pycharm/spyder plotting window which cannot show animations

        self.fig, self.ax = plt.subplots()
        self.X = X

        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)

        # animated=True tells matplotlib to only draw the artist when we explicitly request it
        (self.ln,) = self.ax.plot(X, np.zeros(X.shape), animated=True)
        plt.show(block=False)
        plt.pause(0.1)  # flush changes
        self.bg = self.fig.canvas.copy_from_bbox(self.fig.bbox)
        self.ax.draw_artist(self.ln)
        self.fig.canvas.blit(self.fig.bbox)  # show the result on the screen

    def __enter__(self):
        """
        Yield the plot engine object to use
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Close the current plot window
        """
        plt.close()
        plt.switch_backend(self.prev_backend)  # use IDE plots

    def update(self, Y: np.ndarray):
        """
        Update the plot data with new incoming data
        """
        if Y.shape != self.X.shape:
            raise ValueError(f"Y shape of {Y.shape} does not match X shape of {self.X.shape}")

        # Update limits of the y-axis
        self.ax.relim()
        self.ax.autoscale_view()

        # reset the background back in the canvas state, screen unchanged
        self.fig.canvas.restore_region(self.bg)
        # update the artist, neither the canvas state nor the screen have changed
        self.ln.set_ydata(Y)
        # re-render the artist, updating the canvas state, but not the screen
        self.ax.draw_artist(self.ln)
        # copy the image to the GUI state, but screen might not be changed yet
        self.fig.canvas.blit(self.fig.bbox)
        # flush any pending GUI events, re-painting the screen if needed
        self.fig.canvas.flush_events()


if __name__ == "__main__":
    x = np.linspace(0, 10, 100)
    y = np.zeros(100)
    with LivePlot(x) as lplot:
        for t in range(100):
            y[t] = np.random.rand()
            lplot.update(y)
            time.sleep(0.1)

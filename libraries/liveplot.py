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
import os


class LivePlot:
    def __init__(self, X: np.ndarray, xlabel="x", ylabel="y", ignore_trailing_zeros=True):
        """
        Set up the live 1D plotting engine.
        """
        # don't use inbuilt pycharm/spyder plotting window which cannot show animations
        self.prev_backend = plt.get_backend()
        if os.name == "posix":  
            plt.switch_backend("TkAgg")  # mac or linux
        else:
            plt.switch_backend("Qt5Agg")

        self.fig, self.ax = plt.subplots(figsize=(8,6))
        self.X = X
        self.ignorezeros = ignore_trailing_zeros

        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)

        # animated=True tells matplotlib to only draw the artist when we explicitly request it
        # prepare the blit
        (self.ln,) = self.ax.plot(X, np.zeros(X.shape), animated=True)
        self.ax.get_yaxis().set_visible(False)
        self.ax.get_xaxis().set_visible(False)
        self.ax.set_title("Realtime data")
        plt.show(block=False)
        plt.pause(0.1)  # flush changes
        self.bg = self.fig.canvas.copy_from_bbox(self.fig.bbox)
        self.ax.draw_artist(self.ln)
        self.fig.canvas.blit(self.fig.bbox)  # show the result on the screen
        self.ax.get_yaxis().set_visible(True)
        self.ax.get_xaxis().set_visible(True)

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
            
        if self.ignorezeros:
            zeros = np.where(Y==0)[0]
            if zeros.shape[0] > 0:
                maxi = zeros[0]
            else:
                maxi = Y.shape[0]
            
            X = self.X[:maxi]
            Y = Y[:maxi]
        else:
            X = self.X

        self.fig.canvas.restore_region(self.bg)
        
        self.ln.set_ydata(Y)
        self.ln.set_xdata(X)
        
        
        # Update limits of the y-axis
        self.ax.relim()
        self.ax.autoscale_view()

        # draw the parts that changed
        self.ax.draw_artist(self.ax.patch)
        self.ax.draw_artist(self.ax.yaxis)
        self.ax.draw_artist(self.ax.xaxis)
        self.ax.draw_artist(self.ln)
        for spine in self.ax.spines.values():
            self.ax.draw_artist(spine)

        if os.name != "posix":
            self.fig.canvas.update()
        
        # copy the image to the GUI state, but screen might not be changed yet
        self.fig.canvas.blit(self.fig.bbox)
        
        # flush any pending GUI events, re-painting the screen if needed
        self.fig.canvas.flush_events()
        
        


if __name__ == "__main__":
    x = np.linspace(0, 10, 100)
    y = np.zeros(100)
    with LivePlot(x) as lplot:
        for t in range(100):
            y[t] = np.random.rand() + 0.1 + t/10
            lplot.update(y)
            time.sleep(0.1)

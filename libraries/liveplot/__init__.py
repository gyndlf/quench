# -*- coding: utf-8 -*-
"""
Created on Tue May 28 22:00:00 2024.

Matplotlib wrapper to plot incoming data in an external plot with minimal overhead.
Great for long experiments with data that trickles in slowly.

Use LivePlot for 1D data and LiveContourPlot for 2D data

@author: jzingel
"""

from .liveplot import LivePlot
from .livecontourplot import LiveContourPlot

__version__ = 1.0
__all__ = [LivePlot, LiveContourPlot]

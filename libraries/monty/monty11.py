# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 14:04:24 2024

Data saver using pickle and LZMA

@author: jzingel
"""

import lzma
import pickle
import os
from datetime import datetime


DATA_DIR = "C:\\Users\\LD2007\\Documents\\Si_CMOS_james\\measurements\\data"
VERSION = 1.1

# TODO
# - Upgrade to a folder based design
# - Save multiple experiment data with same experiments (run numbers)
# - Save associated figures in experiment dir


# To migrate to v1.2 use something like the following
#
# >> m = Monty11("SET_long_2d_sweep_zoomed").load()
# Loading from SET_long_2d_sweep_zoomed.xz
# Saved at 2024-04-14 20:52:19.828636
#
# >> monty.newrun("anticrossing zoomed", m.experiment)
# Started new run anticrossing_zoomed
# 
# >> monty.save(m.data)


class Monty:
    def __init__(self, fname, experiment={}, data={}):
        self.fname = fname
        self.experiment = experiment
        self.data = data
        self.time = datetime.min
        
    def __repr__(self):
        rep = self.time + "\n"
        for v in self.experiment.keys():
            rep += v + " = " + self.experiment[v] + "\n"
        return rep
    
    def _save(self, path, issnapshot=False):
        """Internal saving method"""
        with lzma.open(path, "w") as fz:
            pickle.dump({
                "fname": self.fname+"_SNAPSHOT" if issnapshot else self.fname,
                "experiment": self.experiment,
                "data": self.data,
                "version": VERSION,
                "time": str(datetime.now())
                }, fz, 4)
        # DO NOT USE PROTOCOL 5. There is a bug with large numpy arrays
        # See https://github.com/lucianopaz/compress_pickle/issues/23
        
    def save(self, data={}):
        """Save the experiment data. Will not overwrite existing files"""
        if data != {}:
            self.data = data
        assert self.fname != None
        # Check if an existing file exists
        path = os.path.join(DATA_DIR, self.fname + ".xz")
        repeat = 0
        while os.path.exists(path):
            repeat += 1
            path = os.path.join(DATA_DIR, self.fname + str(repeat) + ".xz")
        self.fname += str(repeat)
        print(f"Saving to {self.fname}.xz")
        self._save(path)
            
    def snapshot(self, data={}):
        """Save a snapshot of the current data. Will overwrite existing
        files so use with care"""
        if data != {}:
            self.data = data
        assert self.fname != None
        path = os.path.join(DATA_DIR, self.fname + "_SNAPSHOT.xz")
        #print(f"Saving snapshot to {self.fname}_SNAPSHOT.xz")
        self._save(path, issnapshot=True)
    
    def load(self, fname=None):
        if fname != None:
            self.fname = fname
        assert self.fname != None
        print(f"Loading from {self.fname}.xz")
        path = os.path.join(DATA_DIR, self.fname + ".xz")
        with lzma.open(path, "r") as fz:
            saved = pickle.load(fz)
            
            if saved["version"] != VERSION:
                print("WARNING: Saved object does not match current Monty version")
            
            self.fname = saved["fname"]
            self.experiment = saved["experiment"]
            self.data = saved["data"]
            self.time = saved["time"]
        print(f"Saved at {self.time}")
        return self
    
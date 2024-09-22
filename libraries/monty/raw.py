# -*- coding: utf-8 -*-
"""
Created on Sun Sep 22 09:30 2024

Just load a raw data file. Don't process it or anything.

@author: james
"""

import lzma
import pickle
import os


if os.name == "posix":  # mac or linux
    DATA_DIR = "/Users/james/Documents/Backups/honours-quench-data"
else:  # Windows (Probably LD fridge)
    DATA_DIR = "C:\\Users\\LD2007\\Documents\\Si_CMOS_james\\data"


def loadraw(fname: str):
    """Load a raw .xz file, bypassing monty"""
    path = os.path.join(DATA_DIR, fname)
    print(f"Loading {path}")
    with lzma.open(path, "r") as fz:
        data = pickle.load(fz)
    return data

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
import yaml
import logging


if os.name == "posix":  # mac or linux
    print("Warning running on posix... what are you doing??")
    DATA_DIR = "/mnt/c/Users/LD2007/Documents/Si_CMOS_james/measurements/data"
else:  # Windows (Probably LD fridge)
    DATA_DIR = "C:\\Users\\LD2007\\Documents\\Si_CMOS_james\\data"
VERSION = 1.3

# run names cannot be the following as they would collide with internal identifiers
RESERVED_KEYWORDS = ["version", "identifier", "experiment", "runs"]

# Configure yaml to dump unknown objects as `repr(object)`
yaml.SafeDumper.yaml_representers[None] = lambda self, data: \
    yaml.representer.SafeRepresenter.represent_str(
        self,
        repr(data),
    )


class Monty:
    """Library for saving and loading data quickly."""
    
    def __init__(self, identifier: str, experiment={}):
        """Create new experiment."""
        # Experiment values
        self.identifier = identifier.replace(" ", "_")  # experiment directory
        self.root = os.path.join(DATA_DIR, self.identifier.replace(".", "/"))  # Root path of experiment
        os.makedirs(self.root, exist_ok=True)  # create dir if not exists

        self.experiment = experiment  # general experiment description
        self.data = {}
        self.runs = {}  # indexed by runname
        self.run_map = []  # indexed by runid to return run name

        # Run values (only parameters; don't keep the raw data here)
        self.isrunrunning = False
        self.figures = []  # fnames of figures
        self.datafiles = []  # fnames of compressed data files
        self.runid = 0
        self.runname = ""
        self.start_time = datetime.min  # stand in
        self.parameters = {}  # run parameters (values sweeping, etc)
        
        # Attempt to load the experiment if it already exists
        if os.path.exists(os.path.join(DATA_DIR, identifier.replace(".", "/").replace(" ", "_"), "experiment.yaml")):
            print("Loading existing experiment (ignoring given experiment parameters)")
            self.loadexperiment()
        else:
            print(f"Started new experiment {self.identifier}")

    @property
    def plot_title(self):
        """Returns the current experiment and run name as a title."""
        return self.identifier + "." + self.runname

    def __repr__(self):
        """Display a current representation of monty."""
        rep = self.identifier + "\n"
        rep += str(self.experiment) + "\n"
        rep += "Is running = " + str(self.isrunrunning) + "\n"
        if self.isrunrunning:
            rep += f"Current run = {self.runname} ({self.runid})\n"
            rep += f"Began run {self.start_time}\n"
        if len(self.runs) > 0:
            rep += "Runs = " + str(self.runs.keys()) + "\n"
        return rep

    def _save_data(self, path, fname):
        """Save numpy data internally method."""
        with lzma.open(path, "w") as fz:
            pickle.dump({
                "runname": self.runname,
                "data": self.data,
                "version": VERSION,
                "info": self.parameters
                }, fz, 4)
        # DO NOT USE PROTOCOL 5. There is a bug with large numpy arrays
        # See https://github.com/lucianopaz/compress_pickle/issues/23

    def _save_experiment(self):
        """Save the experiment as a yaml file."""
        path = os.path.join(self.root, "experiment.yaml")
        with open(path, 'w') as yf:
            yf.write(f"# << This file is machine generated. Last updated {datetime.now().isoformat()}. Do not edit directly. >>\n")
            yf.write(yaml.safe_dump({
                    "identifier": self.identifier,
                    "experiment": self.experiment,
                    "version": VERSION,
                    "runs": self.run_map,
                }))
            yf.write("\n")
            for run in self.runs.keys():
                yf.write(yaml.safe_dump({
                    run: self.runs[run]
                }))
                yf.write("\n")

    def _find_unused_filename(self, path: str, extension: str):
        """Return a filename that is currently not being used. Extension is the filetype."""
        newpath = path
        repeat = 0
        while os.path.exists(newpath + "." + extension):  # Check if an existing file exists
            repeat += 1
            newpath = path + "." + str(repeat)
        return newpath + "." + extension, repeat

    def save(self, data=None):
        """Save the experiment. Will not overwrite existing files."""
        if data is not None:
            self.data = data
        self.finishrun()
        print(f"Saving to {self.runname}.xz")
        path, repeat = self._find_unused_filename(os.path.join(self.root, self.runname), "xz")
        self.datafiles.append(self.runname + (("." + str(repeat)) if repeat > 0 else "") + ".xz")
        self._save_data(path, self.runname)
        print("Saving to experiment.yaml")
        self._save_experiment()

    def snapshot(self, data=None):
        """
        Save a snapshot of the current data.
        
        Will overwrite existing files so use with care. Needs a current run to be active.
        """
        if not self.isrunrunning:
            print("WARNING: Tried to snapshot data without a current run being active. Silently failing...")
            return
        if data is not None:
            self.data = data
        path = os.path.join(self.root, self.runname + "_SNAPSHOT.xz")  # we overwrite the old snapshot if it exists
        if self.runname + "_SNAPSHOT.xz" not in self.datafiles:
            self.datafiles.append(self.runname + "_SNAPSHOT.xz")  # we overwrite the file so only add it once
        self._save_data(path, self.runname + "_SNAPSHOT")
        self._save_experiment()

    def savefig(self, plt, desc: str, dpi=1000):
        """Save the given plot as a png."""
        fname = self.runname + "_" + desc.replace(" ", "_")
        path, repeat = self._find_unused_filename(os.path.join(self.root, fname), "png")
        self.figures.append(fname + (("." + str(repeat)) if repeat > 0 else "") + ".png")
        plt.savefig(path, bbox_inches="tight", dpi=dpi)
        self._save_experiment()

    def newrun(self, name: str, parameters: dict):
        """Create a new run for the experiment."""
        name = name.replace(" ", "_")
        if self.isrunrunning:
            print("WARNING: Finishing existing run to start a new one")
            self.finishrun()

        name_adj = name  # adjust with numbers for repeating runs
        i = 1
        while name_adj in self.runs.keys() or name_adj in RESERVED_KEYWORDS:
            name_adj = name + "." + str(i)
            i += 1
            
        self.isrunrunning = True
        self.runid += 1
        self.runname = name_adj
        self.start_time = datetime.now()
        self.parameters = parameters
        self.figures = []
        self.datafiles = []
        print(f"Started new run {self.runname}")
        self._save_experiment()

    def finishrun(self):
        """Add the finished run to the list of runs."""
        self.isrunrunning = False
        if self.runname in self.runs.keys():
            print(f"WARNING: Overwriting run {self.runname}")
        self.runs[self.runname] = {
            "runid": self.runid,
            "time_start": str(self.start_time),
            "time_end": str(datetime.now()),
            "parameters": self.parameters,
            "figures": self.figures,
            "datafiles": self.datafiles,
        }
        if self.runname not in self.run_map:  # dont add duplicates when rerunning runs
            self.run_map.append(self.runname)
        print(f"Run finished and took {str(datetime.now() - self.start_time)}.")

    def loadrun(self, runname: str):
        """Load specific run of data."""
        runname = runname.replace(" ", "_")
        if runname not in self.runs.keys():
            raise ValueError(f"ERROR: Unknown run '{runname}'.")
        path = os.path.join(self.root, runname + ".xz")
        if not os.path.exists(path):
            raise OSError(f"ERROR: File doesn't exist '{path}'")
        print(f"Loading '{path}'")
        with lzma.open(path, "r") as fz:
            data = pickle.load(fz)
            if data["version"] != VERSION:
                print("WARNING: Saved object does not match current Monty version")
            if data["runname"] != runname:
                print(f'{data["runname"]}')
                print(f"WARNING: File runname ({data['runname']}) does not match requested run name {runname}")
            self.data = data["data"]
        # Configure internal variables to point to loaded data
        self.runname = data["runname"]
        try:
            self.parameters = self.runs[self.runname]
        except KeyError:
            logging.warn("Loaded run is not found in experiment parameter list.")
        return self.data

    def loadexperiment(self, identifier: str = None):
        """Load experiment from disk."""
        if identifier is None:
            identifier = self.identifier
        
        path = os.path.join(DATA_DIR, identifier.replace(".", "/").replace(" ", "_"), "experiment.yaml")
        if not os.path.exists(path):
            raise OSError(f"ERROR: Could not find experiment '{path}'")

        with open(path, "r") as yf:
            try:
                experiment = yaml.safe_load(yf)
            except yaml.YAMLError as err:
                raise OSError(f"ERROR: Could not load experiment: '{err}'")

        # set values from experiment
        if experiment["version"] != VERSION:
            print(f"WARNING: Experiment version {experiment['version']} does not match current monty version {VERSION}")
        self.identifier = experiment["identifier"]
        self.experiment = experiment["experiment"]
        self.run_map = experiment["runs"]
        
        runid = 0
        self.runs = {}
        for key in experiment.keys():
            if key not in RESERVED_KEYWORDS:
                self.runs[key] = experiment[key]
                if self.runs[key]["runid"] > runid:
                    runid = self.runs[key]["runid"]
        self.runid = runid
        print("Note that no experimental data has been loaded.")
        print(f"Next run will have id {self.runid}")
        return self
    
    def loaddata(self, fname: str):
        """Load a raw data file. Usually this is a SNAPSHOT file that didn't save properly"""
        if not fname.endswith(".xz"):
            fname += ".xz"
        path = os.path.join(self.root, fname)
        if not os.path.exists(path):
            raise OSError(f"ERROR: File doesn't exist '{path}'")
        print(f"Loading '{path}'")
        with lzma.open(path, "r") as fz:
            data = pickle.load(fz)
            if data["version"] != VERSION:
                print("WARNING: Saved object does not match current Monty version")
            self.data = data["data"]
            self.parameters = data["info"]
            self.runname = data["runname"]
            print(f"Loaded data with run name {data['runname']}")
        return self.data


        


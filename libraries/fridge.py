# -*- coding: utf-8 -*-
"""
Created on Fri May 17 10:37:16 2024

Record fridge temperatures and pressures using the API

@author: jzingel
"""

import requests
from functools import partial
from qcodes import Instrument

# To find these API endpoints just open up the network analyser on the thermometry site
API_URL = "https://qphys1114.research.ext.sydney.edu.au/therm_flask/"


class Fridge():
    """Connect to the Thermometry API and get the fridge temperatures and pressures"""
    def __init__(self, name: str):
        self.name = name
        self.url = API_URL + name
        print(f"Using base URL {self.url}")

    def get_temperatures(self) -> dict:
        """Return the current fridge temperatures"""
        r = requests.get(self.url + "/data/?current")
        if r.status_code != 200:
            print(f"Error {r.status_code}: Failed to query fridge.")
            return {}
        return r.json()

    def get_pressures(self) -> dict:
        """Return the current fridge pressures"""
        r = requests.get(self.url + "/MaxiGauge/?current")
        if r.status_code != 200:
            print(f"Error {r.status_code}: Failed to query fridge.")
            return {}
        return r.json()


if __name__ == "__main__":
    f = Fridge("BlueFors_LD")
    print(f.get_pressures())
    print(f.get_temperatures())

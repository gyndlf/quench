# -*- coding: utf-8 -*-
"""
Created on Wed 19 Jun 2024

Clean up the python path and allow import from the libraries dir easily.

@author: jzingel
"""

import sys

paths = ['/Users/LD2007/Documents/Si_CMOS_james/quench/libraries',
         '/Users/LD2007/Documents/Si_CMOS_james/quench']

for path in paths:
    if path not in sys.path:
        sys.path.append(path)
print("Added 'quench/' and 'quench/libraries' for easy importing.")
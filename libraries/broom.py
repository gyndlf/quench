# -*- coding: utf-8 -*-
"""
Created on Fri Apr 26 10:48:41 2024

Clean up the python path and allow import from the libraries dir easily.

@author: jzingel
"""

def sweep(env="py312"):
    # Clean the system path because there is so much junk
    import sys

    sys.path = [
        f'C:\\Users\\LD2007\\anaconda3\\envs\\{env}\\python38.zip',
        f'C:\\Users\\LD2007\\anaconda3\\envs\\{env}\\DLLs',
        f'C:\\Users\\LD2007\\anaconda3\\envs\\{env}\\lib',
        f'C:\\Users\\LD2007\\anaconda3\\envs\\{env}',
        #'C:\\Users\\LD2007\\AppData\\Roaming\\Python\\Python38\\site-packages',
        f'C:\\Users\\LD2007\\anaconda3\\envs\\{env}\\lib\\site-packages',
        f'C:\\Users\\LD2007\\anaconda3\\envs\\{env}\\lib\\site-packages\\win32',
        f'C:\\Users\\LD2007\\anaconda3\\envs\\{env}\\lib\\site-packages\\win32\\lib',
        f'C:\\Users\\LD2007\\anaconda3\\envs\\{env}\\lib\\site-packages\\Pythonwin',
        '/Users/LD2007/Documents/Si_CMOS_james/quench/libraries',
        '/Users/LD2007/Documents/Si_CMOS_james/quench',
        ]
    
    print("Cleaned PYTHONPATH and added quench/ and quench/libraries for easy importing.")

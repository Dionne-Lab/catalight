# -*- coding: utf-8 -*-
"""
Created on Thu Oct 14 17:30:17 2021

This script simply creates and returns a running instance of PeaksimpleConnector()
Note: if this connection is closed, Peaksimple also must be restarted

@author: Briley Bourgeois
"""

import sys, os
import clr  # python.NET is imported with the name clr (Common Language Runtime)

dir_path = os.path.dirname(os.path.realpath(__file__))
assemblydir = os.path.join(dir_path, 'PeaksimpleClient', 'PeaksimpleConnector.dll')

clr.AddReference(assemblydir) # Add the assembly to python.NET

# Now that the Assembly has been added to python.NET, 
# it can be imported like a normal module
import Peaksimple  # Import the assembly namespace, which has a different name

Connector = Peaksimple.PeaksimpleConnector()  # This class has all the functions

ctrl_file = 'C:/Program Files/Added Programs/PeakSimple version 4.89Win10/DEFAULT2.CON'

def initialize_connector():
    Connector.Connect() # Connect to running instance of peaksimple using class method
    return Connector


# -*- coding: utf-8 -*-
"""
Created on Thu Oct 14 17:30:17 2021

@author: brile
"""

import clr  # Weirdly this is python.NET
import sys

assemblydir = ('C:/Program Files/Added Programs/PeakSimple_Control/'
               'PeakSimple_Control_Demo/PeaksimpleClient/PeaksimpleConnector')

sys.path.append(assemblydir)  # Make sure the assembly is in path
clr.AddReference(assemblydir) # Add the assembly to python.NET
import Peaksimple  # Import the assembly namespace, which has a different name

Connector = Peaksimple.PeaksimpleConnector()  # This class has all the functions

Channel = int(1)
ctrl_file = 'C:\\Program Files\\Added Programs\\PeakSimple version 4.89Win10\\DEFAULT2.CON'
ctrl_file = 'Vial1.CON'
#"C:\Program Files\Added Programs\PeakSimple version 4.89Win10\333calibration.ASC"
Connector.Connect()
Connector.LoadControlFile(ctrl_file)

with open(ctrl_file) as f:
    contents = f.read()
    
print(contents)


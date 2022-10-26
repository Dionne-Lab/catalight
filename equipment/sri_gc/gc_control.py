# -*- coding: utf-8 -*-
"""
Created on Thu Oct 14 17:30:17 2021

This script simply creates and returns a running instance of PeaksimpleConnector()
Note: if this connection is closed, Peaksimple also must be restarted
TODO: integrate TCD
@author: Briley Bourgeois

AXD - changed default control file to CO2 (2022-03-28)

2022-05-31
Changed it back to C2H2 and added line to print what control file is loading
Added Channel 2 file updating (for TCD)

"""

import os
import re
import time
import clr  # python.NET is imported with the name clr (Common Language Runtime)

dir_path = os.path.dirname(os.path.realpath(__file__))
assemblydir = os.path.join(dir_path, 'PeaksimpleClient', 'PeaksimpleConnector.dll')

# if the assembly can't be found, find the .dll file, right click, properties,
# check "unblock", click apply
clr.AddReference(assemblydir)  # Add the assembly to python.NET
import Peaksimple  # Import the assembly namespace, which has a different name
# Now that the Assembly has been added to python.NET,
# it can be imported like a normal module
# the default won't run from the repo for some reason
default_ctrl_file = ("C:\\Peak489Win10\\CONTROL_FILE\\"
                     "HayN_C2H2_Hydrogenation\\C2H2_Hydro_HayN_TCD_off.CON")

class GC_Connector():
    def __init__(self, ctrl_file=default_ctrl_file):
        print('Connecting to Peaksimple...')
        self.peaksimple = Peaksimple.PeaksimpleConnector()  # This class has all the functions
        self.connect()
        self.ctrl_file = ctrl_file
        print('Loading', ctrl_file)
        self.load_ctrl_file()
        self.sample_set_size = 4 # default value, can change in main .py script per experiment
        self._sample_rate = 0  # Sample rate is read only
        self.read_ctrl_file()  # Reads loaded ctrl file and upates sample rate
        print('Connected!')

    sample_rate = property(lambda self: self._sample_rate)

    def update_ctrl_file(self, data_file_path):
        '''Writes over the currently loaded ctrl file to update the save path'''
        # TODO add channel 2 to this
        with open(self.ctrl_file, 'r+') as ctrl_file:
            new_ctrl_file = []
            for line in ctrl_file:  # read values after '=' line by line
                if re.search('<DATA FILE PATH>=', line):
                    line = ('<DATA FILE PATH>=' + data_file_path + '\n')
                elif re.search('<CHANNEL 1 POSTRUN CYCLE>=', line):
                    line = ('<CHANNEL 1 POSTRUN CYCLE>=1\n')
                elif re.search('<CHANNEL 1 POSTRUN REPEAT>=', line):
                    line = ('<CHANNEL 1 POSTRUN REPEAT>='
                            + str(self.sample_set_size) + '\n')
                    
                elif re.search('<CHANNEL 1 FILE>=', line):
                    line = ('<CHANNEL 1 FILE>=FID\n')
                elif re.search('<CHANNEL 1 POSTRUN SAVE DATA>=', line):
                    line = ('<CHANNEL 1 POSTRUN SAVE DATA>=1\n')
                elif re.search('<CHANNEL 1 POSTRUN SAVE RESULTS>=', line):
                    line = ('<CHANNEL 1 POSTRUN SAVE RESULTS>=1\n')
                elif re.search('<CHANNEL 1 POSTRUN AUTOINCREMENT>=', line):
                    line = ('<CHANNEL 1 POSTRUN AUTOINCREMENT>=1\n')
                elif re.search('<CHANNEL 1 POSTRUN SAVE IMAGE>=', line):
                    line = ('<CHANNEL 1 POSTRUN SAVE IMAGE>=1\n')
                    
                elif re.search('<CHANNEL 2 FILE>=', line):
                    line = ('<CHANNEL 2 FILE>=TCD\n')
                elif re.search('<CHANNEL 2 POSTRUN SAVE DATA>=', line):
                    line = ('<CHANNEL 2 POSTRUN SAVE DATA>=1\n')
                elif re.search('<CHANNEL 2 POSTRUN SAVE RESULTS>=', line):
                    line = ('<CHANNEL 2 POSTRUN SAVE RESULTS>=1\n')
                elif re.search('<CHANNEL 2 POSTRUN AUTOINCREMENT>=', line):
                    line = ('<CHANNEL 2 POSTRUN AUTOINCREMENT>=1\n')
                elif re.search('<CHANNEL 2 POSTRUN SAVE IMAGE>=', line):
                    line = ('<CHANNEL 2 POSTRUN SAVE IMAGE>=1\n')

                new_ctrl_file += line
            ctrl_file.seek(0)
            ctrl_file.writelines(new_ctrl_file)

        print(self.ctrl_file)
        self.load_ctrl_file()
    
    def load_ctrl_file(self):
        '''Loads a new ctrl file to the GC based on .ctrl_file atr'''
        print('Loading Control File...')
        for attempt in range(0, 3):
            try:
                self.peaksimple.LoadControlFile(self.ctrl_file)
                print('Successful!')
                break
            except Peaksimple.ConnectionWriteFailedException:
                print('Write error. Retrying...')
                time.sleep(1)
                continue
        time.sleep(5)  # I think peaksimple is cranky when rushed
    
    def connect(self):
        '''Tries to connect to peak simple 5 times'''
        for attempt in range(0, 5):
            try:
                self.peaksimple.Connect()
                print('Connected!')
                break
            except Peaksimple.ConnectionFailedException:
                print('Connection error. Retrying...')
                time.sleep(1)
                continue
            print('Cannot Connect :(')
    
    def read_ctrl_file(self):
        '''
        Reads loaded control file and updates sample rate attribute

        Returns
        -------
        None.

        '''
        with open(self.ctrl_file, 'r+') as ctrl_file:
            for line in ctrl_file:  # read values after '=' line by line

                if re.search('<CHANNEL 1 TIME>=', line):
                    run_time = int(line.split('=')[-1].strip(' \n'))

                elif re.search('<CHANNEL 1 POSTRUN CYCLE TIME>=', line):
                    post_time = int(line.split('=')[-1].strip(' \n'))

            self._sample_rate = (run_time+post_time)/1000


if __name__ == "__main__":
    print(dir_path)
    gc1 = GC_Connector()
    data_path = 'C:\\Peak489Win10\\GCDATA\\20220118_CodeTest'
    # gc1.sample_set_size = 2
    # gc1.update_ctrl_file(data_path)
    # gc1.peaksimple.SetRunning(1, True)
    # time.sleep(10)
    # for n in range(0, 21):
    #     print(gc1.peaksimple.IsRunning(1))
    #     # IsRunning returns false inbetween runs
    #     time.sleep(60)
    # print('Finished')

# -*- coding: utf-8 -*-
"""
Created on Thu Oct 14 17:30:17 2021

This script simply creates and returns a running instance of PeaksimpleConnector()
Note: if this connection is closed, Peaksimple also must be restarted
TODO: integrate TCD
@author: Briley Bourgeois
"""

import sys, os, re, time
import clr  # python.NET is imported with the name clr (Common Language Runtime)

dir_path = os.path.dirname(os.path.realpath(__file__))
assemblydir = os.path.join(dir_path, 'PeaksimpleClient', 'PeaksimpleConnector.dll')

clr.AddReference(assemblydir) # Add the assembly to python.NET

# Now that the Assembly has been added to python.NET, 
# it can be imported like a normal module
import Peaksimple  # Import the assembly namespace, which has a different name
# the default won't run from the repo for some reason
default_ctrl_file = ("C:\\Peak489Win10\\CONTROL_FILE\\"
                     "HayN_C2H2_Hydrogenation\C2H2_Hydro_HayN_TCD_off.CON")
print(default_ctrl_file)

class GC_Connector():
    def __init__(self, ctrl_file=default_ctrl_file):
        self.peaksimple = Peaksimple.PeaksimpleConnector()  # This class has all the functions
        self.peaksimple.Connect()
        time.sleep(20) # I think peaksimple is cranky when rushed
        self.ctrl_file = ctrl_file
        self.peaksimple.LoadControlFile(self.ctrl_file)
        time.sleep(60)
        self.sample_set_size = 4
        
        # Sample rate is read only
        self._sample_rate = 0
        self.read_ctrl_file()
    
    sample_rate = property(lambda self: self._sample_rate)
        
    def update_ctrl_file(self, data_file_path):
        # TODO add channel 2 to this
        with open(self.ctrl_file, 'r+') as ctrl_file:
            new_ctrl_file = []
            for line in ctrl_file:  # read values after '=' line by line
                if re.search('<DATA FILE PATH>=', line):
                    line = ('<DATA FILE PATH>=' + data_file_path + '\n')
                elif re.search('<CHANNEL 1 POSTRUN CYCLE>=', line):
                    line = ('<CHANNEL 1 POSTRUN CYCLE>=' + '1\n')
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
                
                new_ctrl_file += line
            ctrl_file.seek(0)
            ctrl_file.writelines(new_ctrl_file)
            
        print(self.ctrl_file)
        
        self.peaksimple.LoadControlFile(self.ctrl_file)
        time.sleep(60) # I think peaksimple is cranky when rushed
        
    def read_ctrl_file(self):
        '''
        Reads loaded control file and updates run time

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
    gc1.sample_set_size = 2
    gc1.update_ctrl_file(data_path)
    gc1.peaksimple.SetRunning(1, True)
    time.sleep(10)
    for n in range(0,21):
        print(gc1.peaksimple.IsRunning(1))
        # IsRunning returns false inbetween runs
        time.sleep(60)
    print('Finished')
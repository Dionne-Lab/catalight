# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 14:32:19 2022

@author: brile
"""
import os
import time
from datetime import date

from alicat_MFC.gas_control import Gas_System
from sri_gc.gc_control import GC_Connector

## User Inputs:
main_dir = 'C:\Peak489Win10\GCDATA'
gas_list = ['C2H4', 'C2H2', 'H2', 'Ar']
sample_set_size = 1
delay_times = [5, 15, 25, 35, 45, 55] # In minutes
flows = [5, 25, 50]
comp_list_on = ([0,0.05,0,0.95])
comp_list_off = ([0,0,0,1])


## Main Script
expt_dir = os.path.join(main_dir,
                        (date.today().strftime('%Y%m%d') + '_gc_delay_test'))
os.makedirs(expt_dir, exist_ok=True)

gc = GC_Connector()
gc.sample_set_size = sample_set_size
gas_control = Gas_System()
gas_control.set_gasses(gas_list)

for tot_flow in flows:
    flow_dir = os.path.join(expt_dir, (str(tot_flow)+'_sccm'))
    for delay in delay_times:
        filename = (str(delay)+'_min_delay')
        filepath = os.path.join(flow_dir, filename)
        os.makedirs(filepath, exist_ok=True)
        gc.update_ctrl_file(filepath) # Changes save path
        gas_control.set_flows(comp_list_on, tot_flow) # Flow Target Gas

        for second in range(int(delay*60)):
            time.sleep(1) # 1 second at a time so script can be stopped

        # Turn on gc and pause a minute to be safe
        gc.peaksimple.SetRunning(1, True)
        time.sleep(60)

        gas_control.set_flows(comp_list_off, 50) # Clear out line

        # Wait until gc collection is done
        for second in range(int((gc.sample_rate-1)*60)):
            time.sleep(1) # 1 second at a time so script can be stopped
gas_control.disconnect()

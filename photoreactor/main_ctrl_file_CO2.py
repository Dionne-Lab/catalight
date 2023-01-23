# -*- coding: utf-8 -*-
"""
Created on Fri Jan  7 16:59:01 2022
Study control file: test main script before the development of a fully integrated GUI

@author: brile, AXD edits with no python knowledge

"""
import os
import time

import matplotlib.pyplot as plt
import numpy as np
from equipment.alicat_MFC.gas_control import Gas_System
from equipment.diode_laser.diode_control import Diode_Laser
from equipment.harrick_watlow.heater_control import Heater
from equipment.sri_gc.gc_control import GC_Connector
from experiment_control import Experiment


def initialize_equipment():
    gc_connector = GC_Connector("C:\\Peak489Win10\CONTROL_FILE\\HayN_CO2_Hydrogenation\\"
                                "CO2_Hydro_p417min-backflush_7minFon_17mintotal_TCDon.CON") #can specify what control file to use here, otherwise will load default
    laser_controller = Diode_Laser()
    gas_controller = Gas_System()
    heater = Heater()
    return (gc_connector, laser_controller, gas_controller, heater)

def calculate_time(expt_list):
    start_time = time.time()
    run_time = []
    for expt in expt_list:
        run_time.append(expt.plot_sweep()[-1])
        print(run_time)
        if max(expt.power) > 0:
            laser_on = time.localtime(start_time + 60*sum(run_time[:-1]))
            laser_off = time.localtime(start_time + 60*sum(run_time))
            time_on = time.strftime('%b-%d at %I:%M%p', laser_on)
            time_off = time.strftime('%b-%d at %I:%M%p', laser_off)
            print('laser on from %s to %s' % (time_on, time_off))

    end_time = time.localtime(start_time + 60*sum(run_time))
    end_time = time.strftime('%b-%d at %I:%M%p', end_time)
    print('experiment will end on %s' % (end_time))

def shut_down(eqpt_list):
    print('Shutting Down Equipment')
    gc_connector, laser_controller, gas_controller, heater = eqpt_list
    laser_controller.shut_down()
    heater.shut_down()
    gas_controller.shut_down()

def run_study(expt_list, eqpt_list):
    for expt in expt_list:
        print('Starting ' + expt.expt_type + expt.expt_name)
        try:
            expt.run_experiment()
            print('Finished ' + expt.expt_type + expt.expt_name)
        except:
            shut_down(eqpt_list)
            raise

if __name__ == "__main__": #edit this part and below which will only execute when running this script
    eqpt_list = initialize_equipment()
    plt.close('all')
    sample_name = '20220713_Al2O3_control'
    main_fol = os.path.join('C:\Peak489Win10\GCDATA', sample_name)
    p_sweep_path = os.path.join("C:\Peak489Win10\GCDATA\pressure_tests", sample_name)
    os.makedirs(main_fol, exist_ok=True)
    os.makedirs(p_sweep_path, exist_ok=True)
    
    # #example code block for setting experimental conditions 
    # reduction = Experiment(eqpt_list) # edit variable name on left ("reduction") to rename experiment
    # reduction.sample_set_size = 12 # number of GC runs to run per experimental condition
    # reduction.expt_type = 'temp_sweep' # experiment type for what condition you're varying
    # reduction.temp = [273+250] # array of temperatures in Kelvin (can be single value)
    # reduction.gas_type = ['C2H2', 'Ar', 'H2'] #Names of gases corresponding to MFC A, B, and C, respectively
    # reduction.gas_comp = [[0, 1-0.05, 0.05]] #Gas composition as mole fraction
    # reduction.tot_flow = [50] #Total gas flow rate in sccm
    # reduction.sample_name = sample_name #set main data folder with this name
    # reduction.create_dirs(main_fol, 'blah') #change "blah" to folder name you want to create to contain your data
    # #to run this block of code only, highlight and press F9

    # expt1 = Experiment(eqpt_list)
    # expt1.expt_type = 'temp_sweep'
    # expt1.sample_set_size = 4
    # expt1.temp = list(np.arange(300, 701, 25))
    # expt1.gas_type = ['N2', 'CO2', 'H2']
    # expt1.gas_comp = [[0.5, 0.25, 0.25]]
    # expt1.tot_flow = [10]
    # expt1.sample_name = sample_name
    # expt1.power = [0]
    # expt1.create_dirs(os.path.join(main_fol, 'expt5_CO2_fulltempsweep_N2'))

    # expt1 = Experiment(eqpt_list)
    # expt1.expt_type = 'temp_sweep'
    # expt1.sample_set_size = 20
    # expt1.temp = [700]
    # expt1.gas_type = ['N2', 'CO2', 'H2']
    # expt1.gas_comp = [[0.5, 0.25, 0.25]]
    # expt1.tot_flow = [10]
    # expt1.sample_name = sample_name
    # expt1.power = [0]
    # expt1.create_dirs(os.path.join(main_fol, 'expt6_hightempCO2_postC2H2'))

    expt2 = Experiment(eqpt_list)
    expt2.expt_type = 'power_sweep'
    expt2.sample_set_size = 4
    expt2.temp = [300]
    expt2.power = list(np.arange(0, 1001, 100))
    expt2.gas_type = ['N2', 'CO2', 'H2']
    expt2.gas_comp = [[0.00, 0.5, 0.5]]
    expt2.tot_flow = [10]
    expt2.sample_name = sample_name
    expt2.create_dirs(os.path.join(main_fol, 'expt8_roomtempCO2_powersweep'))

    # expt3 = Experiment(eqpt_list)
    # expt3.expt_type = 'power_sweep'
    # expt3.sample_set_size = 20
    # expt3.temp = [200+273]
    # expt3.power = [900]
    # expt3.gas_type = ['N2', 'CO2', 'H2']
    # expt3.gas_comp = [[0.00, 0.5, 0.5]]
    # expt3.tot_flow = [10]
    # expt3.sample_name = sample_name
    # expt3.create_dirs(os.path.join(main_fol, 'run9_200C_450nm_900mW_stability'))
    
    # expt4 = Experiment(eqpt_list)
    # expt4.expt_type = 'comp_sweep'
    # expt4.sample_set_size = 4
    # expt4.temp = [698]
    # P_H2 = 0.09*np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    # P_CO2 = 0.09*np.ones(len(P_H2))
    # P_N2 = 1-P_CO2-P_H2
    # expt4.gas_type = ['N2', 'CO2', 'H2']
    # expt4.gas_comp = np.stack([P_N2, P_CO2, P_H2], axis=1).tolist()
    # expt4.tot_flow = [10]
    # expt4.sample_name = sample_name
    # expt4.create_dirs(os.path.join(main_fol, 'run9_698K_gascompsweep'))
    
    # expt5 = Experiment(eqpt_list)
    # expt5.expt_type = 'temp_sweep'
    # expt5.sample_set_size = 4
    # expt5.temp = list(np.arange(575, 701, 25))
    # expt5.gas_type = ['N2', 'CO2', 'H2']
    # expt5.gas_comp = [[0.00, .125, .875]]
    # expt5.tot_flow = [10]
    # expt5.sample_name = sample_name
    # expt5.power = [0]
    # expt5.create_dirs(os.path.join(main_fol, 'test13_575-700K_7H2_1CO2_520nm_0mW'))
   
    # expt3 = Experiment(eqpt_list)
    # expt3.expt_type = 'flow_sweep'
    # expt3.sample_set_size = 10
    # expt3.temp = [698]
    # expt3.gas_type = ['N2', 'CO2', 'H2']
    # expt3.gas_comp = [[0.00, 0.5, 0.5]]
    # expt3.tot_flow = list(np.arange(.1, 1.01, .1))
    # expt3.sample_name = sample_name
    # expt3.power = [0]
    # expt3.create_dirs(os.path.join(main_fol, 'run11_698K_flowsweep'))
    
    # expt4 = Experiment(eqpt_list)
    # expt4.expt_type = 'comp_sweep'
    # expt4.temp = [373]
    # P_h2 = 0.01*np.array([0.5, 1, 2, 5, 10, 15, 20])
    # P_c2h2 = 0.01*np.ones(len(P_h2))
    # P_Ar = 1-P_c2h2-P_h2
    # expt4.gas_comp = np.stack([P_c2h2, P_Ar, P_h2], axis=1).tolist()
    # expt4.tot_flow = [10]
    # expt4.sample_name = sample_name
    # expt4.create_dirs(os.path.join(main_fol, 'postreduction'))
   
    # expt5 = Experiment(eqpt_list)
    # expt5.expt_type = 'temp_sweep'
    # expt5.sample_set_size = 4
    # expt5.temp = list(np.arange(300, 481, 20))
    # expt5.gas_type = ['C2H2', 'Ar', 'H2']
    # expt5.gas_comp = [[0.1, 1-0.6, 0.5]]
    # expt5.tot_flow = [10]
    # expt5.power = [0]
    # expt5.sample_name = sample_name
    # expt5.create_dirs(os.path.join(main_fol, 'expt3_fulltempsweep_C2H2'))
    
    # eqpt_list[0].sample_set_size = 4
    # expt3 = Experiment(eqpt_list)
    # expt3.expt_type = 'temp_sweep'
    # expt3.temp = list(np.arange(300, 481, 20))
    # expt3.gas_type = ['C2H2', 'Ar', 'H2']
    # expt3.gas_comp = [[0.1, 1-0.6, 0.5]]
    # expt3.tot_flow = [10]
    # expt3.sample_name = sample_name
    # expt3.create_dirs(os.path.join(main_fol, 'postreduction'))
    # print('finished expt3')

    # eqpt_list[0].sample_set_size = 4
    # expt4 = Experiment(eqpt_list)
    # expt4.expt_type = 'power_sweep'
    # expt4.temp = [300]
    # expt4.power = list(np.arange(50, 300, 75))
    # expt4.gas_type = ['C2H2', 'Ar', 'H2']
    # expt4.gas_comp = [[0.1, 1-0.6, 0.5]]
    # expt4.tot_flow = [10]
    # expt4.sample_name = sample_name
    # expt4.create_dirs(os.path.join(main_fol, 'postreduction'))
    # print('finished expt4')

    # stability_test = Experiment(eqpt_list)
    # stability_test.sample_set_size = 6*42
    # stability_test.expt_type = 'temp_sweep'
    # stability_test.temp = [400]
    # stability_test.gas_type = ['C2H2', 'Ar', 'H2']
    # stability_test.gas_comp = [[0.01, 1-0.06, 0.05]]
    # stability_test.tot_flow = [10]
    # stability_test.sample_name = sample_name
    # stability_test.create_dirs(main_fol)
    
    #always run these two lines
    run_study([expt2], eqpt_list) #type in the square brackets which experiments to run (in order), based on what you named them above
    shut_down(eqpt_list)
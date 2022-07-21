# -*- coding: utf-8 -*-
"""
Created on Fri Jan  7 16:59:01 2022
Study control file: test main script before the development of a fully integrated GUI

@author: brile
"""
import equipment.sri_gc.gc_control
from equipment.sri_gc.gc_control import GC_Connector
from equipment.diode_laser.diode_control import Diode_Laser
from equipment.harrick_watlow.heater_control import Heater
from equipment.alicat_MFC.gas_control import Gas_System
from experiment_control import Experiment
import numpy as np
import matplotlib.pyplot as plt
import os
import time

def initialize_equipment():
    gc_connector = GC_Connector(r"C:\Peak489Win10\CONTROL_FILE\HayN_C2H2_Hydrogenation\C2H2_Hydro_HayN_TCD_off.CON")
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
        
        try:
            expt.run_experiment()
            
        except:
            shut_down(eqpt_list)
            raise

if __name__ == "__main__":
    eqpt_list = initialize_equipment()
    plt.close('all')
    sample_name = '20220602_Ag5Pd95_6wt%_3.45mg_sasol900_300C_3hr'
    main_fol = os.path.join('C:\Peak489Win10\GCDATA', sample_name)
    # os.makedirs(main_fol, exist_ok=True)
   
    # os.makedirs(p_sweep_path, exist_ok=True)
    # p_sweep_path = os.path.join("C:\Peak489Win10\GCDATA\pressure_tests", sample_name)
    # os.makedirs(p_sweep_path, exist_ok=True)
    # eqpt_list[2].test_pressure(p_sweep_path)
    
    # expt1 = Experiment(eqpt_list)
    # expt1.expt_type = 'temp_sweep'
    # expt1.temp = list(np.arange(300, 401, 10))
    # expt1.gas_type = ['C2H2', 'Ar', 'H2']
    # expt1.gas_comp = [[0.01, 1-0.06, 0.05]]
    # expt1.tot_flow = [50]
    # expt1.sample_name = sample_name
    # expt1.create_dirs(os.path.join(main_fol, 'prereduction'))

    # expt2 = Experiment(eqpt_list)
    # expt2.expt_type = 'power_sweep'
    # expt2.temp = [300]
    # expt2.power = list(np.arange(0, 301, 50))
    # expt2.gas_type = ['C2H2', 'Ar', 'H2']
    # expt2.gas_comp = [[0.01, 1-0.06, 0.05]]
    # expt2.tot_flow = [50]
    # expt2.sample_name = sample_name
    # expt2.create_dirs(os.path.join(main_fol, 'prereduction'))
    
    # reduction = Experiment(eqpt_list)
    # reduction.sample_set_size = 12*21
    # reduction.expt_type = 'stability_test'
    # reduction.temp = [295]
    # reduction.gas_type = ['C2H2', 'Ar', 'H2']
    # reduction.gas_comp = [[0, 1, 0]]
    # reduction.tot_flow = [50]
    # reduction.sample_name = sample_name
    # reduction.create_dirs(main_fol)
   
    # expt3 = Experiment(eqpt_list)
    # expt3.expt_type = 'temp_sweep'
    # expt3.temp = list(np.arange(300, 401, 10))
    # expt3.gas_type = ['C2H2', 'Ar', 'H2']
    # expt3.gas_comp = [[0.1, 1-0.6, 0.5]]
    # expt3.tot_flow = [50]
    # expt3.sample_name = sample_name
    # expt3.create_dirs(os.path.join(main_fol, 'postreduction'))

    # expt4 = Experiment(eqpt_list)
    # expt4.expt_type = 'power_sweep'
    # expt4.temp = [300]
    # expt4.power = list(np.arange(0, 301, 50))
    # expt4.gas_type = ['C2H2', 'Ar', 'H2']
    # expt4.gas_comp = [[0.1, 1-0.6, 0.5]]
    # expt4.tot_flow = [50]
    # expt4.sample_name = sample_name
    # expt4.create_dirs(os.path.join(main_fol, 'postreduction'))

    # stability_test = Experiment(eqpt_list)
    # stability_test.sample_set_size = 6*42
    # stability_test.expt_type = 'stability_test'
    # stability_test.temp = [373]
    # stability_test.gas_type = ['C2H2', 'Ar', 'H2']
    # stability_test.gas_comp = [[0.01, 1-0.06, 0.05]]
    # stability_test.tot_flow = [50]
    # stability_test.sample_name = sample_name
    # stability_test.create_dirs(main_fol)
    
    # expt5 = Experiment(eqpt_list)
    # expt5.expt_type = 'temp_sweep'
    # expt5.temp = list(np.arange(300, 401, 10))
    # expt5.gas_type = ['C2H2', 'Ar', 'H2']
    # expt5.gas_comp = [[0.01, 1-0.06, 0.05]]
    # expt5.tot_flow = [50]
    # expt5.sample_name = sample_name
    # expt5.create_dirs(os.path.join(main_fol, 'postreduction'))

    # expt6 = Experiment(eqpt_list)
    # expt6.expt_type = 'power_sweep'
    # expt6.temp = [300]
    # expt6.power = list(np.arange(0, 301, 50))
    # expt6.gas_type = ['C2H2', 'Ar', 'H2']
    # expt6.gas_comp = [[0.01, 1-0.06, 0.05]]
    # expt6.tot_flow = [50]
    # expt6.sample_name = sample_name
    # expt6.create_dirs(os.path.join(main_fol, 'postreduction'))
    
    # expt7 = Experiment(eqpt_list)
    # expt7.expt_type = 'flow_sweep'
    # expt7.temp = [340]
    # expt7.gas_type = ['C2H2', 'Ar', 'H2']
    # expt7.gas_comp = [[0.01, 1-0.03, 0.02]]
    # expt7.tot_flow = list(np.arange(10, 60, 10))
    # expt7.sample_name = sample_name
    # expt7.create_dirs(os.path.join(main_fol, 'postreduction'))
    
    # expt8 = Experiment(eqpt_list)
    # expt8.expt_type = 'comp_sweep'
    # expt8.temp = [340]
    # P_h2 = 0.01*np.array([0.5, 1, 2, 5, 10, 15, 20, 30, 40])
    # P_c2h2 = 0.01*np.ones(len(P_h2))
    # P_Ar = 1-P_c2h2-P_h2
    # expt8.gas_comp = np.stack([P_c2h2, P_Ar, P_h2], axis=1).tolist()
    # expt8.tot_flow = [50]
    # expt8.sample_name = sample_name
    # expt8.create_dirs(os.path.join(main_fol, 'postreduction'))
    
    # expt_list = [expt3, expt4, expt7]
    # calculate_time(expt_list)
    # run_study(expt_list, eqpt_list)
    shut_down(eqpt_list)
# -*- coding: utf-8 -*-
"""
Created on Fri Jan  7 16:59:01 2022
Study control file: test main script before the development of a fully integrated GUI

@author: brile
"""
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
    gc_connector = GC_Connector()
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

if __name__ == "__main__":
    eqpt_list = initialize_equipment()
    plt.close('all')
    main_fol = (r'C:\Peak489Win10\GCDATA\20220201_Ag95Pd5_2wt%_25.2mg_shaken')
    os.makedirs(main_fol, exist_ok=True)
    
    p_sweep_path = r"C:\Peak489Win10\GCDATA\pressure_tests\20220201_Ag95Pd5_2wt%_25.2mg_stirred_try2"
    eqpt_list[2].test_pressure(p_sweep_path)

    eqpt_list[0].sample_set_size = 4
    Expt2 = Experiment(eqpt_list)
    Expt2.expt_type = 'temp_sweep'
    Expt2.temp = list(np.arange(300, 401, 10))
    Expt2.gas_type = ['C2H2', 'Ar', 'H2']
    Expt2.gas_comp = [[0.1, 1-0.6, 0.5]]
    Expt2.tot_flow = [10]
    Expt2.sample_name = '20220201_Ag95Pd5_2wt%_25.2mg_shaken'
    Expt2.create_dirs(main_fol)
    print('finished Expt2')

    eqpt_list[0].sample_set_size = 4
    Expt3 = Experiment(eqpt_list)
    Expt3.expt_type = 'power_sweep'
    Expt3.temp = [300]
    Expt3.power = list(np.arange(50, 300, 75))
    Expt3.gas_type = ['C2H2', 'Ar', 'H2']
    Expt3.gas_comp = [[0.1, 1-0.6, 0.5]]
    Expt3.tot_flow = [10]
    Expt3.sample_name = '20220201_Ag95Pd5_2wt%_25.2mg_shaken'
    Expt3.create_dirs(main_fol)
    print('finished Expt3')

    expt_list = [Expt2, Expt3]
    calculate_time(expt_list)
    run_study(expt_list, eqpt_list)
    shut_down(eqpt_list)

    # Expt1 = Experiment(eqpt_list)
    # Expt1.expt_type = 'stability_test'
    # Expt1.temp = [320+273]
    # Expt1.gas_type = ['C2H2', 'Ar', 'H2']
    # Expt1.gas_comp = [[0.0, 1-0.05, 0.05]]
    # Expt1.tot_flow = [50]
    # Expt1.sample_name = '20220201_Ag95Pd5_2wt%_25.2mg_shaken'
    # Expt1.create_dirs(main_fol)
    # time = 2 * 60  # hrs * minutes/hr
    # eqpt_list[0].sample_set_size = time/eqpt_list[0].sample_rate
    # print('finished Expt1')

    # eqpt_list[0].sample_set_size = 4
    # Expt2 = Experiment(eqpt_list)
    # Expt2.expt_type = 'temp_sweep'
    # Expt2.temp = list(np.arange(300, 401, 10))
    # Expt2.gas_type = ['C2H2', 'Ar', 'H2']
    # Expt2.gas_comp = [[0.01, 1-0.06, 0.05]]
    # Expt2.tot_flow = [10]
    # Expt2.sample_name = '20220201_Ag95Pd5_2wt%_25.2mg_shaken'
    # Expt2.create_dirs(main_fol)
    # print('finished Expt2')

    # eqpt_list[0].sample_set_size = 4
    # Expt3 = Experiment(eqpt_list)
    # Expt3.expt_type = 'temp_sweep'
    # Expt3.temp = list(np.arange(300, 401, 10))
    # Expt3.gas_type = ['C2H2', 'Ar', 'H2']
    # Expt3.gas_comp = [[0.1, 1-0.6, 0.5]]
    # Expt3.tot_flow = [10]
    # Expt3.sample_name = '20220201_Ag95Pd5_2wt%_25.2mg_shaken'
    # Expt3.create_dirs(main_fol)
    # print('finished Expt3')

    # eqpt_list[0].sample_set_size = 4
    # Expt2 = Experiment(eqpt_list)
    # Expt2.expt_type = 'power_sweep'
    # Expt2.temp = [300]
    # Expt2.power = list(np.arange(50, 300, 75))
    # Expt2.gas_type = ['C2H2', 'Ar', 'H2']
    # Expt2.gas_comp = [[0.01, 1-0.06, 0.05]]
    # Expt2.tot_flow = [10]
    # Expt2.sample_name = '20220201_Ag95Pd5_2wt%_25.2mg_shaken'
    # Expt2.create_dirs(main_fol)
    # print('finished Expt2')

    # Expt3 = Experiment(eqpt_list)
    # Expt3.expt_type = 'flow_sweep'
    # Expt3.temp = [373]
    # Expt3.gas_type = ['C2H2', 'Ar', 'H2']
    # Expt3.gas_comp = [[0.01, 1-0.06, 0.05]]
    # Expt3.tot_flow = list(np.arange(10, 60, 10))
    # Expt3.sample_name = '20220201_Ag95Pd5_2wt%_25.2mg_shaken'
    # Expt3.create_dirs(main_fol)
    # print('finished expt3')

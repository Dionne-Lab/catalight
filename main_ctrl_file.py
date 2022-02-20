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


def initialize_equipment():
    gc_connector = GC_Connector()
    laser_controller = Diode_Laser()
    gas_controller = Gas_System()
    heater = Heater()
    return (gc_connector, laser_controller, gas_controller, heater)


if __name__ == "__main__":
    eqpt_list = initialize_equipment()
    gas_controller = eqpt_list[2]
    gas_controller.print_details()

    plt.close('all')
    main_fol = (r'C:\Peak489Win10\GCDATA\20220201_Ag95Pd5_2wt%_25.2mg_shaken')
    os.makedirs(main_fol, exist_ok=True)
    
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
    # Expt1.run_experiment()
    # print('finished Expt1')
    
    eqpt_list[0].sample_set_size = 4
    Expt2 = Experiment(eqpt_list)
    Expt2.expt_type = 'temp_sweep'
    Expt2.temp = list(np.arange(300, 401, 10))
    Expt2.gas_type = ['C2H2', 'Ar', 'H2']
    Expt2.gas_comp = [[0.01, 1-0.06, 0.05]]
    Expt2.tot_flow = [10]
    Expt2.sample_name = '20220201_Ag95Pd5_2wt%_25.2mg_shaken'
    Expt2.plot_sweep()
    Expt2.create_dirs(main_fol)
    Expt2.run_experiment()
    print('finished Expt2')
    
    eqpt_list[0].sample_set_size = 4
    Expt3 = Experiment(eqpt_list)
    Expt3.expt_type = 'temp_sweep'
    Expt3.temp = list(np.arange(300, 401, 10))
    Expt3.gas_type = ['C2H2', 'Ar', 'H2']
    Expt3.gas_comp = [[0.1, 1-0.6, 0.5]]
    Expt3.tot_flow = [10]
    Expt3.sample_name = '20220201_Ag95Pd5_2wt%_25.2mg_shaken'
    Expt3.plot_sweep()
    Expt3.create_dirs(main_fol)
    Expt3.run_experiment()
    print('finished Expt3')
    
    # Shutdown Process
    gas_controller.shut_down()
    eqpt_list[3].turn_off()
    
    # Expt3 = Experiment(eqpt_list)
    # Expt3.expt_type = 'flow_sweep'
    # Expt3.temp = [373]
    # Expt3.gas_type = ['C2H2', 'Ar', 'H2']
    # Expt3.gas_comp = [[0.01, 1-0.06, 0.05]]
    # Expt3.tot_flow = list(np.arange(10, 60, 10))
    # Expt3.sample_name = '20220201_Ag95Pd5_2wt%_25.2mg_shaken'
    # Expt3.plot_sweep()
    # Expt3.create_dirs(main_fol)
    # Expt3.run_experiment()
    # print('finished expt3')


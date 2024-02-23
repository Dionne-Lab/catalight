"""
Created on Fri Jan  7 16:59:01 2022
Study control file: test main script before the development of a fully integrated GUI

@author: brile
"""
import os
import time

import matplotlib.pyplot as plt
import numpy as np

from catalight.equipment.gas_control.alicat import Gas_System
from catalight.equipment.light_sources.diode_control import Diode_Laser
from catalight.equipment.light_sources.nkt_system import NKT_System
from catalight.equipment.heating.watlow import Heater
from catalight.equipment.gc_control.sri_gc import GC_Connector
from catalight.equipment.experiment_control import Experiment


def initialize_equipment():
    gc_connector = GC_Connector(r"C:\Users\dionn\GC\Control_Files\HayN_C2H2_Hydrogenation\20221106_C2H2_Hydro_HayN_TCD_off.CON")
    #laser_controller = Diode_Laser()
    laser_controller = NKT_System()
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
            laser_on = time.localtime(start_time + 60 * sum(run_time[:-1]))
            laser_off = time.localtime(start_time + 60 * sum(run_time))
            time_on = time.strftime('%b-%d at %I:%M%p', laser_on)
            time_off = time.strftime('%b-%d at %I:%M%p', laser_off)
            print('laser on from %s to %s' % (time_on, time_off))

    end_time = time.localtime(start_time + 60 * sum(run_time))
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

        except Exception as e:
            print('error')
            print(e)
            shut_down(eqpt_list)
            raise


if __name__ == "__main__":
    eqpt_list = initialize_equipment()
    plt.close('all')
    sample_name = '20230504_Au95Pd5_4wt%_5mg'
    main_fol = os.path.join(r'C:\Users\dionn\GC\GC_Data\20240131', sample_name)
    os.makedirs(main_fol, exist_ok=True)

    # eqpt_list[2].set_gasses(['Ar','Air','Air','Air'])
    # p_sweep_path = os.path.join(main_fol, 'prereduction')
    # os.makedirs(p_sweep_path, exist_ok=True)
    # flows = [1, 2, 4, 8, 16, 32, 50]
    # eqpt_list[2].test_pressure(p_sweep_path, flows)

    # # Run a pre-experiment reduction
    # reduction = Experiment(eqpt_list)
    # reduction.expt_type = 'stability_test'
    # reduction.gas_type = ['Ar', 'C2H2', 'H2', 'Ar']
    # reduction.temp = [300+273]
    # reduction.gas_comp = [[0, 0, 0.05, 0.95]]
    # reduction.tot_flow = [50]
    # reduction.sample_rate = 30
    # reduction.sample_set_size = 4
    # reduction.t_steady_state = 30
    # reduction.sample_name = sample_name
    # reduction.create_dirs(main_fol)

    # stability_test = Experiment(eqpt_list)
    # stability_test.expt_type = 'stability_test'
    # stability_test.gas_type = ['Ar', 'C2H2', 'H2', 'Ar']
    # stability_test.temp = [380]
    # stability_test.gas_comp = [[1-0.06, 0.01, 0.05, 0]]
    # stability_test.tot_flow = [50]
    # stability_test.sample_rate = 30
    # test_time = 8 * 24 * 60  # 8 days converted to minutes
    # stability_test.sample_set_size = test_time / stability_test.sample_rate
    # stability_test.t_steady_state = 30
    # stability_test.sample_name = sample_name
    # stability_test.create_dirs(main_fol)

    ratios = np.array([0.5, 1, 1.5, 2, 3, 4, 5, 10, 20])
    P_c2h2 = 0.01 * np.ones(len(ratios))
    P_c2h4 = 0.2 * np.ones(len(ratios))
    P_h2 =  P_c2h2 * ratios
    P_Ar = 1 - P_c2h2 - P_h2 - P_c2h4
    gas_comp_list = np.stack([P_c2h4, P_c2h2, P_h2, P_Ar], axis=1).tolist()
    gas_comp_list = np.round(gas_comp_list, 6)
    
    P_sweep_thermal = Experiment(eqpt_list)
    P_sweep_thermal.expt_type = 'comp_sweep'
    P_sweep_thermal.gas_type = ['C2H4', 'C2H2', 'H2', 'Ar']
    P_sweep_thermal.temp = [380]
    P_sweep_thermal.power = [0]
    P_sweep_thermal.wavelength = [480]
    P_sweep_thermal.bandwidth = [50]
    P_sweep_thermal.gas_comp = gas_comp_list
    P_sweep_thermal.tot_flow = [50]
    P_sweep_thermal.sample_rate = 30
    P_sweep_thermal.sample_set_size = 3
    P_sweep_thermal.t_steady_state = 45
    P_sweep_thermal.sample_name = sample_name
    P_sweep_thermal.create_dirs(main_fol)
    
    # P_sweep_photo = Experiment(eqpt_list)
    # P_sweep_photo.expt_type = 'comp_sweep'
    # P_sweep_photo.gas_type = ['Ar', 'C2H2', 'H2', 'Ar']
    # P_sweep_photo.temp = [360]
    # P_sweep_photo.power = [60]
    # P_sweep_photo.wavelength = [530]
    # P_sweep_photo.bandwidth = [50]
    # P_sweep_photo.gas_comp = gas_comp_list
    # P_sweep_photo.tot_flow = [50]
    # P_sweep_photo.sample_rate = 30
    # P_sweep_photo.sample_set_size = 3
    # P_sweep_photo.t_steady_state = 30
    # P_sweep_photo.sample_name = sample_name
    # P_sweep_photo.create_dirs(main_fol)
    
    barrier_thermal = Experiment(eqpt_list)
    barrier_thermal.expt_type = 'temp_sweep'
    barrier_thermal.temp = list(np.arange(340, 380+1, 10))
    barrier_thermal.wavelength = [530]
    barrier_thermal.power = [0]
    barrier_thermal.bandwidth = [50]
    barrier_thermal.gas_type = ['C2H4', 'C2H2', 'H2', 'Ar']
    barrier_thermal.gas_comp = [[0.2, 0.01, 0.2, 1-0.41]]
    barrier_thermal.tot_flow = [50]
    barrier_thermal.sample_rate = 30
    barrier_thermal.sample_set_size = 4
    barrier_thermal.t_steady_state = 45
    barrier_thermal.sample_name = sample_name
    barrier_thermal.create_dirs(main_fol)
    
    # barrier_photo = Experiment(eqpt_list)
    # barrier_photo.expt_type = 'temp_sweep'
    # barrier_photo.temp = list(np.arange(340, 380+1, 10))
    # barrier_photo.wavelength = [530]
    # barrier_photo.power = [60]
    # barrier_photo.bandwidth = [50]
    # barrier_photo.gas_type = ['Ar', 'C2H2', 'H2', 'N2']
    # barrier_photo.gas_comp = [[1-0.12, 0.02, 0.1, 0]]
    # barrier_photo.tot_flow = [10]
    # barrier_photo.sample_rate = 30
    # barrier_photo.sample_set_size = 4
    # barrier_photo.t_steady_state = 30
    # barrier_photo.sample_name = sample_name
    # barrier_photo.create_dirs(main_fol)

    # expt_list = [P_sweep_photo, P_sweep_thermal, barrier_photo, barrier_thermal]
    expt_list = [P_sweep_thermal, barrier_thermal]
    # calculate_time(expt_list)
    run_study(expt_list, eqpt_list)
    shut_down(eqpt_list)

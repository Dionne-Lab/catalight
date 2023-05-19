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
from catalight.equipment.light_sources.nkt_system import NKT_System
from catalight.equipment.heating.watlow import Heater
from catalight.equipment.gc_control.sri_gc import GC_Connector
from catalight.equipment.experiment_control import Experiment


def initialize_equipment():
    gc_connector = GC_Connector(r"C:\Peak489Win10\CONTROL_FILE\HayN_C2H2_Hydrogenation\C2H2_Hydro_HayN_TCD_off.CON")
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

        except:
            shut_down(eqpt_list)
            raise


if __name__ == "__main__":
    #eqpt_list = initialize_equipment()
    eqpt_list = None
    plt.close('all')
    sample_name = 'dummy_sample'
    main_fol = os.path.join('C:\Peak489Win10\GCDATA', sample_name)
    main_fol = os.path.join(r"C:\Users\brile\Documents\Temp Files", sample_name)
    os.makedirs(main_fol, exist_ok=True)
    expt_list = []
    for wavelength in range(450, 800+1, 50):
        for power in range(0, 100+1, 25):
            expt = Experiment(eqpt_list)
            expt.temp = list(np.arange(300, 340+1, 10))
            expt.wavelength = [wavelength]
            expt.power = [power]
            expt.bandwidth = [50]
            expt.gas_type = ['C2H2', 'Ar', 'H2']
            expt.gas_comp = [[0.01, 1-0.06, 0.05]]
            expt.tot_flow = [50]
            expt.sample_name = sample_name
            expt_list.append(expt)
            expt.create_dirs(main_fol)



    # calculate_time(expt_list)
    # run_study(expt_list, eqpt_list)
    # shut_down(eqpt_list)

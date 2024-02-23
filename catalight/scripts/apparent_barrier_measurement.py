"""
This script is set up to run an apparent activation energy experiment.

The user should edit for the exact values to sweep over that they require.
The loop sweeps over central wavelength and laser power, then runs a
temperature sweep over for each of those conditions.
"""
import os
import time

import numpy as np

from catalight.equipment.gas_control.alicat import Gas_System
from catalight.equipment.light_sources.nkt_system import NKT_System
from catalight.equipment.heating.watlow import Heater
from catalight.equipment.gc_control.sri_gc import GC_Connector
from catalight.equipment.experiment_control import Experiment


def initialize_equipment():
    ctrl_file = (r"C:\Users\dionn\GC\Control_Files\HayN_C2H2_Hydrogenation"
                 r"\20221106_C2H2_Hydro_HayN_TCD_off.CON")
    gc_connector = GC_Connector(ctrl_file)
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
            shut_down(eqpt_list)
            raise (e)


if __name__ == "__main__":
    eqpt_list = initialize_equipment()  # Initialize equipment
    # Create folder to save data into
    sample_name = '20230504_Au95Pd5_4wt_4mg'
    main_fol = os.path.join(r"C:\Users\dionn\GC\GC_Data\20231225", sample_name)
    os.makedirs(main_fol, exist_ok=True)

    # Run a pre-experiment reduction
    reduction = Experiment(eqpt_list)
    reduction.expt_type = 'stability_test'
    reduction.gas_type = ['Ar', 'C2H2', 'H2', 'Ar']
    reduction.temp = [300+273]
    reduction.gas_comp = [[0, 0, 0.05, 0.95]]
    reduction.tot_flow = [50]
    reduction.sample_rate = 30
    reduction.sample_set_size = 4
    reduction.t_steady_state = 30
    reduction.sample_name = sample_name
    reduction.create_dirs(main_fol)
    try:
        reduction.run_experiment()
    except Exception as e:
        shut_down(eqpt_list)
        raise (e)

    # Main experiment
    for wavelength in range(480, 680+1, 50):
        for power in range(0, 60+1, 20):
            expt = Experiment(eqpt_list)
            expt.expt_type = 'temp_sweep'
            expt.temp = list(np.arange(340, 380+1, 10))
            expt.wavelength = [wavelength]
            expt.power = [power]
            expt.bandwidth = [50]
            expt.gas_type = ['Ar', 'C2H2', 'H2', 'N2']
            expt.gas_comp = [[1-0.06, 0.01, 0.05, 0]]
            expt.tot_flow = [50]
            expt.sample_rate = 30
            expt.sample_set_size = 4
            expt.t_steady_state = 30
            expt.sample_name = sample_name
            expt.create_dirs(main_fol)
            try:
                expt.run_experiment()
            except Exception as e:
                shut_down(eqpt_list)
                raise (e)
    shut_down(eqpt_list)

# -*- coding: utf-8 -*-
"""
Created on Fri Jan  7 16:59:01 2022
Study control file: test main script before the development of a fully integrated GUI

@author: brile
"""
from equipment.sri_gc.gc_control import GC_Connector
from equipment.diode_laser.diode_control import Diode_Laser
from alicat import FlowController
from experiment_control import Experiment
import numpy as np
import matplotlib.pyplot as plt
import os

def initialize_equipment():
    gc_connector = GC_Connector()
    MFC_A = FlowController(port='COM8')
    MFC_B = FlowController(port='COM9')
    MFC_C = FlowController(port='COM6')
    MFC_D = FlowController(port='COM7')
    laser_controller = Diode_Laser()

    return (gc_connector, MFC_A, MFC_B, MFC_C, MFC_D, laser_controller)


if __name__ == "__main__":
    eqpt_list = initialize_equipment()
    plt.close('all')
    main_fol = (r"C:\\Peak489Win10\\GCDATA\\"
                "20220118_CodeTest")
    os.makedirs(main_fol, exist_ok=True)
    Expt1 = Experiment(eqpt_list)
    Expt1.expt_type = 'temp_sweep'
    Expt1.temp = list(np.arange(30, 150, 10)+273)
    Expt1.gas_comp = [0.5, 47, 2.5]
    Expt1.sample_name = '20220118_fakesample'
    Expt1.plot_sweep()
    print('finished expt1')
    Expt1.create_dirs(main_fol)
    Expt2 = Experiment(eqpt_list)
    Expt2.expt_type = 'power_sweep'
    Expt2.power = np.arange(30, 150, 10)
    Expt2.plot_sweep()
    print('finished expt 2')
    Expt2.create_dirs(main_fol)

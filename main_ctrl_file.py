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
    laser_controller = Diode_Laser()
    MFC_A = FlowController(port='COM8')
    MFC_B = FlowController(port='COM9')
    MFC_C = FlowController(port='COM6')
    MFC_D = FlowController(port='COM7')
    # Heater will be added hear in future

    return (gc_connector, laser_controller, MFC_A, MFC_B, MFC_C, MFC_D)


if __name__ == "__main__":
    eqpt_list = initialize_equipment()
    plt.close('all')
    main_fol = (r"C:\\Peak489Win10\\GCDATA\\"
                "20220118_CodeTest")
    os.makedirs(main_fol, exist_ok=True)
    Expt3 = Experiment()
    Expt3.expt_type = 'flow_sweep'
    Expt3.temp = [273]
    Expt3.gas_type = ['N2', 'Ar', 'N2']
    Expt3.gas_comp = [[0.01, 1-0.06, 0.05]]
    Expt3.tot_flow = list(np.arange(10, 60, 10))
    Expt3.sample_name = '20211221_fakesample'
    Expt3.plot_sweep()
    print('finished expt3')

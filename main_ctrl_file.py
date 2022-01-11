# -*- coding: utf-8 -*-
"""
Created on Fri Jan  7 16:59:01 2022
Study control file: test main script before the development of a fully integrated GUI

@author: brile
"""
from equipment.sri_gc import PeakSimple_Control
from equipment.diode_laser import Diode_Laser
from alicat import FlowController

def initialize_equipment():
    connector = PeakSimple_Control.initialize_connector()
    MFC_A = FlowController(port='COM8')
    MFC_B = FlowController(port='COM9')
    MFC_C = FlowController(port='COM6')
    MFC_D = FlowController(port='COM7')
    laser_controller = Diode_Laser
    
    return Connector

if __name__ == "__main__":
    Connector = initialize_equipment()
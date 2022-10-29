# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 15:32:48 2022

@author: DLAB
"""
from alicat import FlowController, FlowMeter


for port_name in ['COM6', 'COM7', 'COM8', 'COM9', 'COM10', 'COM11']:
    for address_name in ['A', 'B', 'C', 'D', 'E']:
        if FlowController.is_connected(port_name, address=address_name):
            print(port_name + ' ' + address_name + ' is flow controller')
            break
        elif FlowMeter.is_connected(port_name, address=address_name):
            print(port_name + ' ' + address_name + ' is flow meter')
            break
        
# for port_name in ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM11']:
#     for address_name in ['A', 'B', 'C', 'D', 'E']:
#         if FlowController.is_connected(port_name, address=address_name):
#             print(port_name + ' ' + address_name + ' is flow controller')
#         elif FlowMeter.is_connected(port_name, address=address_name):
#             print(port_name + ' ' + address_name + ' is flow meter')
      
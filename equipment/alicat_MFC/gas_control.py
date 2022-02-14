# -*- coding: utf-8 -*-
"""
Created on Sun Feb 13 20:56:51 2022

@author: brile
"""

from alicat import FlowController, FlowMeter
import pandas as pd

factory_gasses = ['C2H2', 'Air', 'Ar', 'i-C4H10', 'n-C4H10', 'CO2', 'CO',
                  'D2', 'C2H6', 'C2H4', 'He', 'H2', 'Kr', 'CH4', 'Ne',
                  'N2', 'N2O', 'O2', 'C3H8', 'SF6', 'Xe']

class Gas_System:
    def __init__(self):
        self.mfc_A = FlowController(port='COM8', address='A')
        self.mfc_B = FlowController(port='COM9', address='B')
        self.mfc_C = FlowController(port='COM6', address='C')
        self.mfc_D = FlowMeter(port='COM7', address='D')

    def set_gasses(self, gas_list):
        self.mfc_A.set_gas(gas_list[0])
        self.mfc_B.set_gas(gas_list[1])
        self.mfc_C.set_gas(gas_list[2])
        self.mfc_D.set_gas(gas_list[1])

    def set_flows(self, comp_list, tot_flow):
        self.mfc_A.set_flow_rate(float(comp_list[0]*tot_flow))
        self.mfc_B.set_flow_rate(float(comp_list[1]*tot_flow))
        self.mfc_C.set_flow_rate(float(comp_list[2]*tot_flow))

    def set_gasD(self, gas_list, comp_list):
        self.mfc_D.create_mix(mix_no=236, name='output',
                              gases=dict(zip(gas_list, comp_list)))

    def print_flows(self):

        print('MFC A = ' + str(self._MFC_A.get()['setpoint'])
              + self._MFC_A.get()['gas'])
        print('MFC B = ' + str(self._MFC_B.get()['setpoint'])
              + self._MFC_B.get()['gas'])
        print('MFC C = ' + str(self._MFC_C.get()['setpoint'])
              + self._MFC_C.get()['gas'])
        print('MFC D = ' + str(self._MFC_D.get()['mass_flow'])
              + self._MFC_D.get()['gas'])

    def print_details(self):
        print(self.mfc_A.get())
        print(self.mfc_B.get())
        print(self.mfc_C.get())
        print(self.mfc_D.get())

    def shut_down(self):
        '''Sets MFC B to 1 sccm and others to 0'''
        self.mfc_A.set_flow_rate(0.0)
        self.mfc_B.set_flow_rate(1.0)
        self.mfc_C.set_flow_rate(0.0)

    def set_calibration_gas(self, mfc, calDF, fill_gas='Ar'):
        '''Sets a custom gas mixture for the mfc of choice, typically for
        calibration gas. This function uses the standard calDF format utilized
        elsewhere in this code. Please consult the alicat gas composer website
        for the official list of possible gasses'''
        percents = calDF['ppm']/10000
        percents.index = percents.index.map(lambda x: x.split('_')[0])
        percents = percents[~percents.index.duplicated()]
        percents[fill_gas] = 100 - percents.sum()
        percents = percents.sort_values(ascending=False)
        new_idx = pd.DataFrame([False]*len(percents), index=percents.index)
        for chemical in percents.index:
            new_idx.loc[chemical] = chemical in factory_gasses
        percents = percents[new_idx[0]]
        mfc.create_mix(mix_no=237, name='CalGas', gases=percents[0:5].to_dict())

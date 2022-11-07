# -*- coding: utf-8 -*-
"""
Created on Sun Feb 13 20:56:51 2022

@author: brile
20221026 -- added mfcD as 4th flow controller. changed old mfcD to mfcE for flow meter
AXD - edit lines 43-46
"""

from alicat import FlowController, FlowMeter
import pandas as pd
import numpy as np
import time
import os

factory_gasses = ['C2H2', 'Air', 'Ar', 'i-C4H10', 'n-C4H10', 'CO2', 'CO',
                  'D2', 'C2H6', 'C2H4', 'He', 'H2', 'Kr', 'CH4', 'Ne',
                  'N2', 'N2O', 'O2', 'C3H8', 'SF6', 'Xe']

class Gas_System:
    def __init__(self):
        self.mfc_A = FlowController(port='COM6', address='A')
        self.mfc_B = FlowController(port='COM9', address='B')
        self.mfc_C = FlowController(port='COM8', address='C')
        self.mfc_D = FlowController(port='COM10', address='D')
        self.mfc_E = FlowMeter(port='COM11', address='E')

    def set_gasses(self, gas_list):
        self.mfc_A.set_gas(gas_list[0])
        self.mfc_B.set_gas(gas_list[1])
        self.mfc_C.set_gas(gas_list[2])
        self.mfc_D.set_gas(gas_list[3])

    def set_flows(self, comp_list, tot_flow):
        '''
        sets the flow rate of all mfc based on a desired total flow
        and the desired gas composition
        TODO: add limit for tot_flow for each MFC
        Parameters
        ----------
        comp_list : list of gas fraction for mfc [a, b, c]. should add to one
        tot_flow : total flow to send

        Raises
        ------
        AttributeError
            if gas comp doesn't sum to one

        Returns
        -------
        None.

        '''
        if (sum(comp_list) != 1) and (sum(comp_list) != 0):                
            raise AttributeError('Gas comp. must be list of list == 1')
        self.mfc_A.set_flow_rate(float(comp_list[0]*tot_flow))
        self.mfc_B.set_flow_rate(float(comp_list[1]*tot_flow))
        self.mfc_C.set_flow_rate(float(comp_list[2]*tot_flow))
        self.mfc_D.set_flow_rate(float(comp_list[3]*tot_flow))

    def set_gasD(self, gas_list, comp_list):
        # convert to percents, make dict, drop zero values
        percents = np.array(comp_list, dtype=float)*100
        gas_dict = dict(zip(gas_list, percents))
        gas_dict = {x:y for x,y in gas_dict.items() if y != 0}

        # Uses create_mix method to write to gas slot 236,
        # first custom gas slot on MFC
        if len(gas_dict)>1: # if more than 1 gas, creates mix
            self.mfc_E.create_mix(mix_no=236, name='output',
                                  gases=gas_dict)
            self.mfc_E.set_gas(236)
        else:  # If only one gas, sets that as output
            self.mfc_E.set_gas(list(gas_dict)[0])


    def print_flows(self):
        '''prints mass flow rates and gas type for each MFC to console'''
        print('MFC A = ' + str(self.mfc_A.get()['mass_flow'])
              + self.mfc_A.get()['gas'])
        print('MFC B = ' + str(self.mfc_B.get()['mass_flow'])
              + self.mfc_B.get()['gas'])
        print('MFC C = ' + str(self.mfc_C.get()['mass_flow'])
              + self.mfc_C.get()['gas'])
        print('MFC D = ' + str(self.mfc_D.get()['mass_flow'])
              + self.mfc_D.get()['gas'])
        print('MFC E = ' + str(self.mfc_E.get()['mass_flow'])
              + self.mfc_E.get()['gas'])

    def print_details(self):
        '''
        Runs mfc.get() for each mfc, printing full status details
        Returns
        -------
        None.

        '''
        print(self.mfc_A.get())
        print(self.mfc_B.get())
        print(self.mfc_C.get())
        print(self.mfc_D.get())
        print(self.mfc_E.get())

    def read_flows(self):
        '''

        Returns
        -------
        Nested Dictionary
        '''

        flow_dict = {'mfc_A': self.mfc_A.get(),
                     'mfc_B': self.mfc_B.get(),
                     'mfc_C': self.mfc_C.get(),
                     'mfc_D': self.mfc_D.get(),
                     'mfc_E': self.mfc_E.get()}
        return(flow_dict)

    def shut_down(self):
        '''Sets MFC with Ar or N2 running to 1 sccm and others to 0'''
        mfc_list = [self.mfc_A, self.mfc_B, self.mfc_C, self.mfc_D]
        for mfc in mfc_list:
            if mfc.get()['gas'] in ['Ar', 'N2']:
                mfc.set_flow_rate(1.0)
            else:
                mfc.set_flow_rate(0.0)

    def disconnect(self):
        '''Sets MFC with Ar/N2 to 1sccm, others to 0, and closes connections'''
        self.shut_down()
        self.mfc_A.close()
        self.mfc_B.close()
        self.mfc_C.close()
        self.mfc_D.close()
        self.mfc_E.close()
        del self

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

    def test_pressure(self, path):
        print('Testing Pressure Build-up...')
        output = pd.DataFrame(columns=['time', 'setpoint', 'flow rate', 'pressure'])
        mfc_list = [self.mfc_A, self.mfc_B, self.mfc_C, self.mfc_D]
        sample_num = 0
        for mfc in mfc_list:
            if mfc.get()['gas'] in ['Ar', 'N2']:
                test_mfc = mfc
            else:
                mfc.set_flow_rate(0.0)
        self.mfc_E.set_gas(test_mfc.get()['gas'])
        print('Starting Conditions:')
        self.print_flows()
        start_time = time.time()
        for setpoint in range(5, 51, 5):
            test_mfc.set_flow_rate(setpoint)
            for sample in range(0,5):
                pressure = test_mfc.get()['pressure']
                flow_rate = self.mfc_E.get()['mass_flow']
                reading = [(time.time()-start_time)/60,
                           setpoint, flow_rate, pressure]
                print('time: %4.1f (min) setpoint: %4.2f (sccm) '
                      'flow rate: %4.2f (sccm) pressure: %4.2f (psia)' % tuple(reading))
                output.loc[sample_num] = reading
                time.sleep(60)
                sample_num += 1

        ax1 = output.plot(x='time', y='pressure', ylabel='Pressure (psia)', style='--ok')
        ax2 = ax1.twinx()
        ax2.spines['right'].set_position(('axes', 1.0))
        output.plot(ax=ax2, x='time',
                    y=['setpoint', 'flow rate'], ylabel='Flow Rate (sccm)')
        fig = ax1.get_figure()
        fig.savefig(os.path.join(path, 'flow_test.svg'), format='svg')
        output.to_csv(os.path.join(path, 'flow_test.csv'))

if __name__ == "__main__":
    gas_controller = Gas_System()
    comp_list = [0, 1, 0, 0]
    tot_flow = 1
    gas_controller.set_flows(comp_list, tot_flow)
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  8 14:06:48 2022

@author: brile
"""

from pywatlow.watlow import Watlow
import numpy as np
import pandas as pd
import time
import os

def convert_temp(old_unit, new_unit, temp):
    '''Converts temp in old_unit to temp in new_unit'''
    conversion = {'c_to_f': temp * 1.8 + 32.0,
                  'f_to_c': (temp - 32.0) / 1.8,
                  'k_to_f': (temp-273) * 1.8 + 32.0,
                  'f_to_k': (temp - 32.0) / 1.8 + 273,
                  'c_to_k': temp + 273,
                  'k_to_c': temp - 273}
    return conversion[old_unit.lower()+'_to_'+new_unit.lower()]

max_temp = 450  # Max temp in C; 450C reduces lifetime 900C is real max
#TODO integrate max temp
class Heater:
    '''
    Connects with and controls watlow heater. allows ramping, reading set point
    and current temperature, and running test on heater, printing output
    '''

    def __init__(self):
        """Connects to watlow, prints current state"""
        self.controller = Watlow(port='COM5', address=1)
        print('Heater Initializing...')
        print('Current temperature = ' + str(self.read_temp()) + ' C')
        print('Current setpoint = ' + str(self.read_setpoint()) + ' C')
        self.ramp_rate = 15  # C/min
        # TODO put check on heat rate

    def read_temp(self, temp_units='C'):
        '''returns current controller temp in defined units (default = C)'''
        temp = self.controller.read()['data']
        if temp_units.upper() != 'F':
            temp = convert_temp('F', temp_units, temp)
        return round(temp, 3)

    def read_setpoint(self, temp_units='C'):
        '''returns current controller setpoint in defined units (default=C)'''
        setpoint = self.controller.readSetpoint()['data']
        if temp_units.upper() != 'F':
            setpoint = convert_temp('F', temp_units, setpoint)
        return round(setpoint, 3)

    def shut_down(self):
        '''Sets heater to 0 F'''
        self.controller.write(0)
        
    def disconnect(self):
        '''set heat off and closes connection'''
        self.shut_down()
        self.controller.close()

    def ramp(self, T2, T1=None, temp_units='C'):
        '''
        ramps the heater from T1 to T2
        at ramp rate defined by object

        Parameters
        ----------
        T2: target setpoint
        T1: starting setpoint, last setpoint by default
        temp_units: C, K, or F
        '''
        if T1 is None:
            T1 = self.read_setpoint(temp_units)

        # Switch units to C
        if temp_units.upper() == 'F':
            T2, T1 = [convert_temp('F', 'C', temp) for temp in [T2, T1]]
        elif  temp_units.upper() == 'K':
            T2, T1 = [convert_temp('K', 'C', temp) for temp in [T2, T1]]
        elif  temp_units.upper() != 'C':
            raise ValueError('Temp Unit not recognized')

        if T2 > max_temp:
            print('Desired setpoint is above maximum safe working temp!!!')
            print('Resetting T2 to heater max instead...')
            T2 = max_temp
        refresh_rate = 20  # 1/min
        ramp_time = (T2-T1)/self.ramp_rate  # min
        setpoints = np.linspace(T1, T2, abs(int(ramp_time*refresh_rate)))

        for temp in setpoints:
            temp = convert_temp('C', 'F', temp)  # Change units to F
            self.controller.write(temp)  # write to controller
            time.sleep(60/refresh_rate)  # wait

        print('Soak Temp = ' + str(self.read_temp()))

    def test_heater_performance(self, T2, T1=None, temp_units='C'):
        '''
        ramps the heater from T1 to T2
        at ramp rate defined by object

        Parameters
        ----------
        T2: target setpoint
        T1: starting setpoint, last setpoint by default
        temp_units: C, K, or F
        '''
        if T1 is None:
            T1 = self.read_setpoint(temp_units)

        # Switch units to C
        if temp_units.upper() == 'F':
            T2, T1 = [convert_temp('F', 'C', temp) for temp in [T2, T1]]
        elif  temp_units.upper() == 'K':
            T2, T1 = [convert_temp('K', 'C', temp) for temp in [T2, T1]]
        elif  temp_units.upper() != 'C':
            raise ValueError('Temp Unit not recognized')

        refresh_rate = 20  # 1/min
        ramp_time = (T2-T1)/self.ramp_rate  # min
        setpoints = np.linspace(T1, T2, abs(int(ramp_time*refresh_rate)))
        read_out = []
        for temp in setpoints:
            temp = convert_temp('C', 'F', temp)  # Change units to F
            read_out.append([time.time(),
                             self.read_setpoint(),
                             self.read_temp()])
            self.controller.write(temp)  # write to controller
            time.sleep(60/refresh_rate)  # wait

        read_out = pd.DataFrame(read_out,
                                columns=['time', 'set point', 'temperature'])
        read_out['time'] = (read_out['time']-read_out['time'][0])/60
        ax = read_out.plot(x='time')
        ax.set_xlabel('time [min]')
        ax.set_ylabel('Temperature [$\degree$C]')
        ax.set_title('Ramp rate = ' + str(self.ramp_rate))
        return (read_out, ax.get_figure(), ax)

if __name__ == "__main__":
    save_path = r"C:\temp control\20210214_heater_test"
    heater = Heater()
    heater.ramp(20)
    # time.sleep(300)
    # for rate in np.arange(5, 31, 5):
    #     heater.ramp_rate = rate
    #     read_out, fig, ax = heater.test_heater_performance(140, T1=30)
    #     heater.shut_down()
    #     while heater.read_temp() > 30:
    #         time.sleep(60)
    #     read_out.to_csv(os.path.join(save_path, str(rate)+'_heater_read_out.csv'))
    #     fig.savefig(os.path.join(save_path,
    #                              str(rate)+'_heater_test.svg'), format="svg")

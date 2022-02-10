# -*- coding: utf-8 -*-
"""
Created on Tue Feb  8 14:06:48 2022

@author: brile
"""

from pywatlow.watlow import Watlow
import numpy as np
import time

def f_to_c(f):
    """Convert Fahrenheit to Celsius."""
    return (f - 32.0) / 1.8


def c_to_f(c):
    """Convert Celsius to Fahrenheit."""
    return c * 1.8 + 32.0

class Heater:
    '''
    An object that contains all of the information necessary to run a
    particular experiment.

    Attributes
    ----------
        expt_list : pandas data frame

    '''

    def __init__(self):
        """

        Parameters
        ----------
        eqpt_list : optional
            DESCRIPTION. The default is 'None'.

        Returns
        -------
        None.

        """
        self.controller = Watlow(port='COM5', address=1)
        print('Heater Initializing...')
        print(self.controller.read())
        print(self.controller.readSetpoint())
        self.ramp_rate = 15  # C/min

    def ramp(self, T1, T2):
        '''
        ramps the heater from T1 to T2 (no F please)
        at ramp rate defined by object

        Parameters
        ----------
        T1 : starting setpoint
        T2 : target setpoint
            DESCRIPTION. The default is 'None'.
        '''
        T2 = c_to_f(T2)
        T1 = c_to_f(T1)
        refresh_rate = 20  # 1/min
        ramp_time = (T2-T1)/self.ramp_rate  # min
        setpoints = np.linspace(T1, T2, int(ramp_time*refresh_rate))
        for temp in setpoints:
            self.controller.write(temp)
            time.sleep(60/refresh_rate)


if __name__ == "__main__":

    heater = Heater()
    heater.ramp(0,90)
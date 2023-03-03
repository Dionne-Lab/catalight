"""
Contains the Heater class which connect to Watlow heating system.

Also contains convert_temp helper function used within class.

Created on Tue Feb  8 14:06:48 2022.
@author: Briley Bourgeois
"""

import os
import time

import numpy as np
import pandas as pd
from pywatlow.watlow import Watlow


def convert_temp(old_unit, new_unit, temp):
    """
    Converts temp in old_unit to temp in new_unit

    Parameters
    ----------
    old_unit : str
        Units to switch from (C, K, or F)
    new_unit : str
        Units to switch to (C, K, or F)
    temp : float or int
        Temperature in current units.

    Returns
    -------
    float
        Current temperature in new units.

    """
    # On call converts entry to key, value performs math on current temp.
    conversion = {'c_to_f': temp * 1.8 + 32.0,
                  'f_to_c': (temp - 32.0) / 1.8,
                  'k_to_f': (temp - 273) * 1.8 + 32.0,
                  'f_to_k': (temp - 32.0) / 1.8 + 273,
                  'c_to_k': temp + 273,
                  'k_to_c': temp - 273}
    return conversion[old_unit.lower() + '_to_' + new_unit.lower()]


class Heater:
    """
    Connect with and controls Watlow Heater.

    Allows ramping, reading set point and current temperature, and running test
    on heater, printing output
    """

    max_temp = 450
    """int or float: Max temp in C; 450C reduces lifetime 900C is real max.
    To change, use Heater.max_temp = new_value"""

    def __init__(self):
        """Connect to watlow, print current state."""
        self.controller = Watlow(port='COM5', address=1)
        self.is_busy = False  #: Used to block access from other threads
        print('Heater Initializing...')
        print('Current temperature = ' + str(self.read_temp()) + ' C')
        print('Current setpoint = ' + str(self.read_setpoint()) + ' C')
        self.ramp_rate = 15  #: C/min used for ramp method
        # TODO put check on heat rate

    def read_temp(self, temp_units='C'):
        """
        Read current controller temp in defined units (default = C).

        Parameters
        ----------
        temp_units : str, optional
            (C, K, or F) units to return temp in. The default is 'C'.

        Returns
        -------
        float
            Current temperature in requested units.

        """
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True
        temp = self.controller.read()['data']
        self.is_busy = False
        if temp_units.upper() != 'F':
            temp = convert_temp('F', temp_units, temp)
        return round(temp, 3)

    def read_setpoint(self, temp_units='C'):
        """
        Read current controller setpoint in defined units (default = C).

        Parameters
        ----------
        temp_units : str, optional
            (C, K, or F) units to return temp in. The default is 'C'.

        Returns
        -------
        float
            Current setpoint in requested units, rounded to 3 digits.

        """
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True
        setpoint = self.controller.readSetpoint()['data']
        self.is_busy = False
        if temp_units.upper() != 'F':
            setpoint = convert_temp('F', temp_units, setpoint)
        return round(setpoint, 3)

    def shut_down(self):
        """Set heater to 0 F."""
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True
        self.controller.write(0)
        self.is_busy = False

    def disconnect(self):
        """Run shut_down() and then close connection."""
        self.shut_down()
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True
        self.controller.close()
        self.is_busy = False

    def ramp(self, T2, T1=None, temp_units='C', record=False):
        """
        Ramp the heater from T1 to T2 at ramp rate defined by instance attr.

        If record=True, records the time, setpoint, and temp. Plots outcome.

        Parameters
        ----------
        T2 : float
            Target setpoint
        T1 : float
            Starting setpoint Uses the last setpoint if None. None is default.
        temp_units : str
            C, K, or F. The default is 'C'.
        record : bool
            If True, will record setpoints during ramp, plot outcome,
            and return readout dataframe and plot. Mainly used for testing
            heater performance.

        Returns
        -------
        pandas.DataFrame, when record=True
            pandas.DataFrame with columns ['time', 'set point', 'temperature']
            recorded during the experiment.
        matplotlib.pyplot.figure, when record=True
            figure handle for ramp rate plot
        matplotlib.pyplot.axis, when record=True
            axis handle for ramp rate plot
        """
        if T1 is None:
            T1 = self.read_setpoint(temp_units)

        # Switch units to C
        if temp_units.upper() == 'F':
            T2, T1 = [convert_temp('F', 'C', temp) for temp in [T2, T1]]
        elif temp_units.upper() == 'K':
            T2, T1 = [convert_temp('K', 'C', temp) for temp in [T2, T1]]
        elif temp_units.upper() != 'C':
            raise ValueError('Temp Unit not recognized')

        if T2 > Heater.max_temp:
            print('Desired setpoint is above maximum safe working temp!!!')
            print('Resetting T2 to heater max instead...')
            T2 = Heater.max_temp

        refresh_rate = 20  # 1/min
        ramp_time = (T2 - T1) / self.ramp_rate  # min
        setpoints = np.linspace(T1, T2, abs(int(ramp_time * refresh_rate)))
        read_out = []
        for temp in setpoints:
            temp = convert_temp('C', 'F', temp)  # Change units to F
            if record:
                read_out.append([time.time(),
                                 self.read_setpoint(),
                                 self.read_temp()])
            while self.is_busy:
                time.sleep(0)
            self.is_busy = True
            self.controller.write(temp)  # write to controller
            self.is_busy = False
            time.sleep(60 / refresh_rate)  # wait

        print('Soak Temp = ' + str(self.read_temp()))

        if record:  # Record and return output
            read_out = pd.DataFrame(read_out, columns=['time', 'set point',
                                                       'temperature'])
            read_out['time'] = (read_out['time'] - read_out['time'][0]) / 60
            ax = read_out.plot(x='time')
            ax.set_xlabel('time [min]')
            ax.set_ylabel('Temperature [$\degree$C]')
            ax.set_title('Ramp rate = ' + str(self.ramp_rate))
            return (read_out, ax.get_figure(), ax)
        else:
            return

    def test_heater_performance(self, savepath, rates, T_max, T_min=30):
        """
        Loops through provided ramp rates, ramps heater, save outcomes.

        Sets heater to 20C, gives 5 min to steady out. Loops through ramp rates
        while recording the outcome (Heater.ramp(record=True)). Saves results.
        Always lets heater cool to < 30C between runs.

        Parameters
        ----------
        savepath : str
            Full path to directory in which to save data.
        rates : list[int or float]
            (deg C/min) List of heater ramp rates to test e.g. [5, 10, 15, 20]
        T_max : int or float
            (deg C) Maximum temperature setpoint to use for testing
        T_min : int or float, optional
            (deg C) Starting setpoint to use for testing. The default is 30.

        Returns
        -------
        None.

        """
        heater.ramp(20)  # Start from 'off'
        time.sleep(300)  # Allow steady state for 5 min
        for rate in rates:
            # Set new rate, ramp, turn off
            heater.ramp_rate = rate
            read_out, fig, ax = heater.ramp(T_max, T_min, record=True)
            heater.shut_down()

            # Allow temperature to return to < 30 C
            while heater.read_temp() > 30:
                time.sleep(60)

            # Save results
            read_out.to_csv(os.path.join(savepath,
                                         str(rate) + '_heater_read_out.csv'))
            fig.savefig(os.path.join(savepath, str(rate) + '_heater_test.svg'),
                        format="svg")


if __name__ == "__main__":
    # Example Usage
    heater = Heater()
    heater.ramp(20)
    print(heater.read_setpoint())
    print(heater.read_temp())

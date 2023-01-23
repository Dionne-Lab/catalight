# -*- coding: utf-8 -*-
"""
Created on Tue Feb 22 23:15:23 2022

@author: DLAB
"""
import numpy as np
import pandas as pd
from diode_laser.diode_control import Diode_Laser
from power_meter.power_meter_ctrl import NewportMeter

diode = Diode_Laser()
power_meter = NewportMeter()
power_meter.change_wavelength(450)

data = pd.DataFrame(columns=['Power', 'error'])
print('Running Calibration...')

for current in range(150, 800, 35):
    diode.set_current(current)
    error = 100
    power_readings = np.array([-1000])  # Set unreal number
    while error > 10:
        power_readings = np.append(power_readings, power_meter.read()[1])
        if len(power_readings)>20:
            power_readings = np.delete(power_readings, 0)
            std = np.std(power_readings)
            avg = np.average(power_readings)
            error = std/avg*100

    print('Power Reading = %.2f +/- %.2f' % (avg, std))    
    data.loc[current] = [avg, std]
x_data, y_data, y_err = (data.index, data['Power'], data['error'])
ax1 = data.plot(y=['Power'], ylabel='Power (mW)', xlabel='Current (mA)', yerr=y_err)
try:
    p, V = np.polyfit(x_data, y_data, 1, cov=True, w=1/y_err)
    m, b, err_m, err_b = (*p, np.sqrt(V[0][0]), np.sqrt(V[1][1]))
    label = '\n'.join(["m: %4.2f +/- %4.2f" % (m, err_m),
                       "b: %4.2f +/- %4.2f" % (b, err_b)])
except(np.linalg.LinAlgError):
    p = np.polyfit(x_data, y_data, 1)
    m, b = (p[0], p[1])
    label = '\n'.join(["m: %4.2f" % m,
                       "b: %4.2f" % b])
x_fit = np.linspace(0, max(x_data), 100)
ax1.plot(x_fit, (p[0]*x_fit+p[1]), '--r')
diode.update_calibration(p[0], p[1])
diode.shut_down()
fig = ax1.get_figure()
fig.savefig('diode_laser/calibration_plot.svg', format="svg")
print(label)
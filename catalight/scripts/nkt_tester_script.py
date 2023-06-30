import time
import pickle
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt

from catalight.equipment.power_meter import newport
from nkt_tools import (extreme, varia)


def save_all(name, df, fig):
    """
    Save data as csv and fig as png, pickle, svg.

    Parameters
    ----------
    name : str
        Name of save file to be prepended with the date.
    df : pandas.DataFrame
        Dataframe to save as csv
    fig : matplotlib.pyplot.Figure
        Figure to save as svg, png, and pickle
    """
    date = dt.date.today().strftime('%Y%m%d')
    savepath = date + name
    df.to_csv(savepath + '.csv')
    fig.savefig(savepath + '.svg')
    fig.savefig(savepath + '.png')
    pickle.dump(fig, open(savepath + '.pickle', 'wb'))


def nd_test(bandpass, meter, nd_setpoints):
    print('Beginning ND setpoint test')
    # Test ND setpoint vs monitor/power meter readings
    # ---------------------------------------------------
    starting_nd = bandpass.nd_setpoint
    monitor_readings = []
    meter_readings = []
    for nd in nd_setpoints:
        bandpass.nd_setpoint = nd
        time.sleep(2)
        monitor_readings.append(bandpass.monitor_input)
        timestamp, reading = meter.read()
        meter_readings.append(reading)

    data = np.array([nd_setpoints, monitor_readings, meter_readings]).T
    nd_test = pd.DataFrame(data, columns=['ND Setpoint',
                                        'Monitor Reading',
                                        'Meter Reading'])
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.plot(nd_test['ND Setpoint'], nd_test['Monitor Reading'],
             "ko", linewidth=2)
    ax2.plot(nd_test['ND Setpoint'], nd_test['Meter Reading'],
             "r^", linewidth=2)
    ax1.set_xlabel('ND Setpoint [%]', fontsize=18)
    ax1.set_ylabel('Power Reading [%]', fontsize=18)
    ax2.set_ylabel('Power Reading [mW]', fontsize=18, color='r')
    ax2.set_ybound(lower=0)
    fig.tight_layout()
    time.sleep(2)
    bandpass.nd_setpoint = starting_nd
    return fig, nd_test


def power_test(bandpass, meter, laser, power_setpoints):
    print('Beginning Power setpoint test')
    # Test Power setpoint vs monitor/power meter readings
    # ---------------------------------------------------
    starting_power = laser.current_power()
    monitor_readings = []
    meter_readings = []
    for power in power_setpoints:
        laser.set_power(power)
        time.sleep(10)
        monitor_readings.append(bandpass.monitor_input)
        timestamp, reading = meter.read()
        meter_readings.append(reading)

    data = np.array([power_setpoints, monitor_readings, meter_readings]).T
    power_test = pd.DataFrame(data, columns=['Power Setpoint',
                                             'Monitor Reading',
                                             'Meter Reading'])
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.plot(power_test['Power Setpoint'], power_test['Monitor Reading'],
              "ko", linewidth=2)
    ax2.plot(power_test['Power Setpoint'], power_test['Meter Reading'],
              "r^", linewidth=2)
    ax1.set_xlabel('Power Setpoint [%]', fontsize=18)
    ax1.set_ylabel('Power Reading [%]', fontsize=18)
    ax2.set_ylabel('Power Reading [mW]', fontsize=18, color='r')
    ax2.set_ybound(lower=0)
    fig.tight_layout()
    laser.set_power(starting_power)
    time.sleep(2)

    return fig, power_test


def wavelength_test(bandpass, meter, center_wavelengths, bandwidth=50):
    print('Beginning wavelength setpoint test')
    # Test Wavelength setpoint vs monitor/power meter readings
    # --------------------------------------------------------
    monitor_readings = []
    meter_readings = []
    for center in center_wavelengths:
        bandpass.long_setpoint = center + bandwidth/2
        bandpass.short_setpoint = center - bandwidth/2
        meter.change_wavelength(center)
        time.sleep(2)
        monitor_readings.append(bandpass.monitor_input)
        timestamp, reading = meter.read()
        meter_readings.append(reading)

    data = np.array([center_wavelengths, monitor_readings, meter_readings]).T
    wavelength_test = pd.DataFrame(data, columns=['Center Wavelength',
                                                  'Monitor Reading',
                                                  'Meter Reading'])
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.plot(wavelength_test['Center Wavelength'],
             wavelength_test['Monitor Reading'], "ko", linewidth=2)
    ax2.plot(wavelength_test['Center Wavelength'],
             wavelength_test['Meter Reading'], "r^", linewidth=2)
    ax1.set_xlabel('Center Wavelength [nm]', fontsize=18)
    ax1.set_ylabel('Power Reading [%]', fontsize=18)
    ax2.set_ylabel('Power Reading [mW]', fontsize=18, color='r')
    ax2.set_ybound(lower=0)
    fig.tight_layout()

    return fig, wavelength_test


def main():
    date = dt.date.today().strftime('%Y%m%d')
    print('Starting Experiment on ', date)
    print('Initializing Equipment...')

    laser = extreme.Extreme()
    bandpass = varia.Varia()
    meter = newport.NewportMeter()
    laser.set_watchdog_interval(0)
    laser.test_read_funcs()

    bandpass.long_setpoint = 650
    bandpass.short_setpoint = 550
    laser.set_emission(False)
    laser.set_power(50)
    meter.change_wavelength(500)
    print("Initial Reading ", meter.read()[1])
    laser.set_emission(True)
    print("Initial Reading ", meter.read()[1])
    laser.test_read_funcs()

    nd_setpoints = np.arange(0, 100+1, 10)
    fig, nd_result = nd_test(bandpass, meter, nd_setpoints)
    save_all('_nd_test', nd_result, fig)

    power_setpoints = np.arange(20, 50+1, 5)
    fig, power_result = power_test(bandpass, meter, laser, power_setpoints)
    save_all('_power_test', power_result, fig)

    center_wavelengths = np.arange(475, 800+1, 25)
    fig, wavelength_result = wavelength_test(bandpass, meter,
                                             center_wavelengths)
    save_all('_wavelength_test', wavelength_result, fig)

    laser.set_emission(False)
    laser.test_read_funcs()

    # Plot all results on one graph
    test_dfs = [wavelength_result, nd_result, power_result]
    fig, ax = plt.subplots()
    for df in test_dfs:
        ax.plot(df['Monitor Reading'], df['Meter Reading'],
                'o', label=df.columns[0])

    ax.set_xlabel('Monitor Reading [%]', fontsize=18)
    ax.set_ylabel('Meter Reading [mW]', fontsize=18)
    ax.legend(loc='best')
    fig.savefig(date + '_monitor_vs_meter.svg')
    fig.savefig(date + '_monitor_vs_meter.png')
    pickle.dump(fig, open(date + '_monitor_vs_meter.pickle', 'wb'))

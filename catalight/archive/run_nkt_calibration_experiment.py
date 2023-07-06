import time
import pickle
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt

from catalight.equipment.power_meter import newport
from catalight.equipment.light_sources import nkt_system

import catalight.equipment.light_sources.nkt_cal_analysis as cal_analysis


def save_all(name, df, fig):
    """
    Save data as csv and fig as png, pickle, svg.

    Parameters
    ----------
    name : str
        Name of save file to be prepended with the date.
    df : pandas.DataFrame
        Dataframe to save as csv
    fig : matplotlib.pyplot.figure
        Figure to save as svg, png, and pickle
    """
    savepath = date + name
    df.to_csv(savepath + '.csv')
    fig.savefig(savepath + '.svg')
    fig.savefig(savepath + '.png')
    pickle.dump(fig, open(savepath + '.pickle', 'wb'))


def run_calibration(laser, bandpass, meter):
    data = []
    powers = np.arange(20, 100+1, 20)
    for power in powers:
        laser.set_power(power)
        time.sleep(120)
        wavelengths, avg_power = sweep_wavelengths(meter, bandpass)
        data.append(avg_power)

    calibration = pd.DataFrame(data, columns=wavelengths, index=powers).T

    fig, ax = plt.subplots()
    calibration.plot(ax=ax)
    ax.set_xlabel('Wavelength [nm]', fontsize=18)
    ax.set_ylabel('Avg. Power [mW/nm]', fontsize=18)
    fig.tight_layout()
    save_all('_calibration', calibration, fig)
    return calibration


def sweep_wavelengths(meter, bandpass, tolerance=10):
    bandwidth = 10
    start = int(400 + bandwidth/2)
    end = int(800 - bandwidth/2)
    bandpass.short_setpoint = start
    bandpass.long_setpoint = start+bandwidth
    time.sleep(10)
    wavelengths = []
    avg_power = []

    for center in range(start, end, 1):
        meter.change_wavelength(int(center))
        bandpass.short_setpoint = center - bandwidth/2
        bandpass.long_setpoint = center + bandwidth/2
        time.sleep(0.5)
        error = 100
        power_readings = np.array([-1000])  # Set unreal number
        while error > tolerance:
            power_readings = np.append(power_readings, meter.read()[1])
            print('Current Readout = %.2f mW' % power_readings[-1], end='\r')
            # If error is high and theres more than 20 readings, remove first
            if len(power_readings) > 20:
                power_readings = np.delete(power_readings, 0)
                std = np.std(power_readings)
                avg = np.average(power_readings)
                error = std / avg * 100

        print('Wavelength = %3.0f nm -- Power Reading = %.2f +/- %.2f mW'
              % (center, avg, std))

        avg_power.append(avg/bandwidth)
        wavelengths.append(center)

    return wavelengths, avg_power


def growing_window_test(start, end, step, bandpass):
    if abs(start - end) > 100:
        print('Range > 100')
        return
    if start > end:  # Growing Left
        step = -abs(step)
        varia.long_setpoint = start
        varia.short_setpoint = start+step
    else:  # Growing Right
        varia.short_setpoint = start
        varia.long_setpoint = start+step
    tolerance = 10
    time.sleep(10)
    meter_readings = []
    wavelengths = []

    for setpoint in range(start+step, end, step):
        if setpoint > start:  # Growing Right
            varia.long_setpoint = setpoint
        elif setpoint < start:  # Growing Left
            varia.short_setpoint = setpoint

        meter.change_wavelength(int((varia.short_setpoint + varia.long_setpoint)/2))
        time.sleep(0.5)
        error = 100
        power_readings = np.array([-1000])  # Set unreal number
        while error > tolerance:
            power_readings = np.append(power_readings, meter.read()[1])
            print('Current Readout = %.2f mW' % power_readings[-1], end='\r')
            # If error is high and theres more than 20 readings, remove first
            if len(power_readings) > 20:
                power_readings = np.delete(power_readings, 0)
                std = np.std(power_readings)
                avg = np.average(power_readings)
                error = std / avg * 100

        print('Short Wavelength = %3.0f nm -- Long Wavelength = %3.0f nm -- Power Reading = %.2f +/- %.2f mW'
              % (varia.short_setpoint, varia.long_setpoint, avg, std))
        meter_readings.append(avg)
        wavelengths.append(setpoint)

    data = np.array([wavelengths, meter_readings]).T
    results = pd.DataFrame(data, columns=['Wavelength', 'Meter Reading'])
    return results


def get_random_with_precision(min_val, max_val, precision):
    random_num = np.random.uniform(min_val, max_val)
    scaled_num = round(random_num, precision)
    return scaled_num


def make_measurement(meter, tolerance=2.5):
    error = 100
    power_readings = np.array([-1000])  # Set unreal number
    while error > tolerance:
        power_readings = np.append(power_readings, meter.read()[1])
        print('Current Readout = %.2f mW' % power_readings[-1], end='\r')
        # If error is high and theres more than 20 readings, remove first
        if len(power_readings) > 20:
            power_readings = np.delete(power_readings, 0)
            std = np.std(power_readings)
            avg = np.average(power_readings)
            error = std / avg * 100
    return avg


def randomized_test(calibration, num_measurements, laser, powermeter):
    data = []

    while len(data) < num_measurements:
        bandwidth = get_random_with_precision(10, 50, 1)
        center = get_random_with_precision(400+bandwidth/2, 800-bandwidth/2, 1)
        requested_power = random.uniform(1, bandwidth*2)
        setpoint = nkt_system.determine_setpoint(calibration, requested_power,
                                                 center, bandwidth)
        if setpoint != 0:
            powermeter.change_wavelength(int(center))
            laser.set_bandpass(center, bandwidth)
            laser.set_power(requested_power)
            time.sleep(60)
            measured_power = make_measurement(powermeter)
            data.append([center, bandwidth, requested_power, measured_power])
            print('Measuring at: ', [center, bandwidth, requested_power, measured_power])
        else:
            print('skipping point', [center, bandwidth, requested_power])

    df = pd.DataFrame(data, columns=['center', 'bandwidth',
                                     'requested_power', 'measured_power'])
    return df


def verify_calibration():
    path = (r"G:\Shared drives\Ensemble Photoreactor"
            r"\Reactor Baseline Experiments\nkt_calibration\nkt_calibration.pkl")
    calibration = pd.read_pickle(path)
    results = generate_data(calibration, 50, laser, meter)
    fig, ax = plt.subplots()
    results.plot(ax=ax, x='requested_power', style='o')
    fig, ax = plt.subplots()
    results.plot(ax=ax, x='requested_power', y='measured_power', style='o')
    ax.plot(np.linspace(0, results['requested_power'].max(), 4),
            np.linspace(0, results['requested_power'].max(), 4), '--')
    results.to_csv('calibration_verification.csv')
    fig.savefig('calibration_verification.svg')
    fig.savefig('calibration_verification.png')
    plt.show()

date = dt.date.today().strftime('%Y%m%d')
meter = newport.NewportMeter()
nkt = nkt_system.NKT_System()
laser = nkt._laser
bandpass = nkt._varia

laser.test_read_funcs()
laser.set_watchdog_interval(0)
laser.set_emission(True)

print('Start Time = ', time.ctime())
cal_data = run_calibration(laser, bandpass, meter)
print('End Time = ', time.ctime())
cal_data = cal_analysis.determine_correction_factor(cal_data, plot_results=True,
                                                    savedata=True)
calibration = cal_analysis.build_calibration(cal_data)

growing_window_test()
randomized_test()

cal_analysis.benchmark(calibration, savedata=True)

laser.set_emission(False)
laser.test_read_funcs()

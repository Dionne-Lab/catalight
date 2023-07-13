"""
Experimental portion of nkt calibration process.

The main function of this script will coordinate an NKT system and compatible
powermeter through a calibration experiment. Typically, this should be called
by the nkt_system's run_calibration() method. Will save calibration data and
a 'growing window test' to csv files to be analyzed by the
'nkt_analyze_calibration' script.
"""
import time
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from catalight.cl_tools import printProgressBar


def sweep_wavelengths(meter, bandpass, tolerance=10):
    """
    Sweep through the NKT wavelength range, recording output power.

    Sweeps from 405 nm to 795 nm in steps of 1 nm. Uses a bandwidth of 10 nm,
    and returns the average power (power/bandwidth) for each wavelength tested.
    This essentially creates the power spectrum for the laser emission at the
    current laser power setpoint.

    Parameters
    ----------
    meter : catalight.equipment.power_meter.newport.NewportMeter
        Compatible power meter for making power measurments
    bandpass : nkt_tools.varia.Varia
        Bandpass object for laser system
    tolerance : `int` or `float`, optional
        Acceptable deviation in % between measurments, by default 10

    Returns
    -------
    tuple(list, list)
        (wavelengths, avg_power); the wavelength test and recorded avg. powers
        with mW/nm units calculated by dividing by bandwidth
    """
    bandwidth = 10
    start = int(400 + bandwidth/2)
    end = int(800 - bandwidth/2)
    bandpass.short_setpoint = start
    bandpass.long_setpoint = start+bandwidth
    time.sleep(1)
    wavelengths = []
    avg_power = []

    for center in range(start, end, 1):
        meter.change_wavelength(int(center))
        bandpass.short_setpoint = center - bandwidth/2
        bandpass.long_setpoint = center + bandwidth/2
        time.sleep(0.25)
        avg, std, error = make_measurement(meter, tolerance)

        printProgressBar(center-start, end-start, length=50, printEnd='')
        print('\tWavelength = %3.0f nm -- Power Reading = %.2f +/- %.2f mW'
              % (center, avg, std), end='\r')

        avg_power.append(avg/bandwidth)
        wavelengths.append(center)
    print()

    return (wavelengths, avg_power)


def make_measurement(meter, tolerance=2.5, num_measurements=20):
    """
    Sample power meter until last num_measurements fall within tolerance.

    Parameters
    ----------
    meter : catalight.equipment.power_meter.newport.NewportMeter
        Some type of power meter supported by catalight
    tolerance : `float`, optional
        acceptable standard deviation in percent, by default 2.5
    num_measurements : `int`, optional
        the number of measurements to average, by default 20

    Returns
    -------
    tuple(float, float, float)
        (avg, std, error) average power reading/standard deviation in mW and
        standard deviation in % as "error"
    """
    error = 100
    power_readings = np.array([])
    while (error > tolerance) or (len(power_readings) < num_measurements):
        power_readings = np.append(power_readings, meter.read(averaging_time=0.1)[1])
        print('Current Readout = %.2f mW' % power_readings[-1], end='\r')
        # If error is high and theres more than 20 readings, remove first
        if len(power_readings) > 20:
            power_readings = np.delete(power_readings, 0)
            std = np.std(power_readings)
            avg = np.average(power_readings)
            error = std / avg * 100
    return (avg, std, error)


def growing_window_test(start, end, step, bandpass):
    """
    Expands the bandwidth of the laser and records power at each step.

    The first measurement is taken at [start, start + step]. The function will
    detect whether the window should grow towards longer or shorter wavelengths
    start - end must be <= 100 nm

    Parameters
    ----------
    start : int or float
        Starting wavelength for sweep
    end : int or float
        Ending wavelength for sweep
    step : int or float
        Step size between start/end points.
    bandpass : nkt_tools.varia.Varia
        Computer controlled bandpass filter for laser

    Returns
    -------
    pandas.DataFrame
        A dataframe with columns ['Wavelength', 'Meter Reading']
    """
    if abs(start - end) > 100:  # Maximum bandwidth of varia
        print('Growing window test aborted: Range > 100')
        return
    if start > end:  # Growing Left
        step = -abs(step)
        bandpass.long_setpoint = start
        bandpass.short_setpoint = start+step
    else:  # Growing Right
        bandpass.short_setpoint = start
        bandpass.long_setpoint = start+step
    tolerance = 2
    time.sleep(2)
    meter_readings = []
    cutin = []
    cutout = []

    for setpoint in range(start+step, end+1, step):
        if setpoint > start:  # Growing Right
            bandpass.long_setpoint = setpoint
        elif setpoint < start:  # Growing Left
            bandpass.short_setpoint = setpoint

        meter.change_wavelength(int((bandpass.short_setpoint
                                     + bandpass.long_setpoint)/2))
        time.sleep(0.5)
        avg, std, error = make_measurement(meter, tolerance)

        print('Short Wavelength = %3.0f nm | '
              'Long Wavelength = %3.0f nm | '
              'Power Reading = %.2f +/- %.2f mW'
              % (bandpass.short_setpoint, bandpass.long_setpoint, avg, std))
        meter_readings.append(avg)
        cutin.append(bandpass.short_setpoint)
        cutout.append(bandpass.long_setpoint)

    data = np.array([cutin, cutout, meter_readings]).T
    results = pd.DataFrame(data, columns=['Cut-in', 'Cut-out', 'Meter Reading'])
    return results


def run_calibration(laser, bandpass, meter):
    """
    Execute calibration experiment.

    Loops through power setpoints from 20 - 100% in steps of 20. Calls
    sweep_wavelengths() each time. Creates and returns plotted data.

    Parameters
    ----------
    laser : nkt_tools.extreme.Extreme
        NKT laser to calibrate
    bandpass : nkt_tools.varia.Varia
        Connected bandpass filter
    meter : catalight.equipment.power_meter.newport.NewportMeter
        Compatible power meter to use for calibration measurements.

    Returns
    -------
    tuple(pandas.DataFrame, matplotlib.figure.Figure)
        (calibration data, figure) A tuple containing the calibration
        experiment data in a dataframe and a figure of the plotted raw results.
    """
    data = []
    powers = np.arange(20, 100+1, 20)
    for power in powers:
        laser.set_power(power)
        time.sleep(120)
        print('Starting %4.1f%% Power Sweep' % power)
        wavelengths, avg_power = sweep_wavelengths(meter, bandpass, tolerance=2)
        data.append(avg_power)

    calibration = pd.DataFrame(data, columns=wavelengths, index=powers).T

    fig, ax = plt.subplots()
    calibration.plot(ax=ax)
    ax.set_xlabel('Wavelength [nm]', fontsize=18)
    ax.set_ylabel('Avg. Power [mW/nm]', fontsize=18)
    fig.tight_layout()
    return (calibration, fig)


def main(laser, bandpass, meter):
    """
    Execute laser calibration and growing window test.

    Call run_calibration() and growing_window_test(). Save all results and
    plots of raw data.

    Parameters
    ----------
    laser : nkt_tools.extreme.Extreme
        NKT laser to calibrate
    bandpass : nkt_tools.varia.Varia
        Connected bandpass filter
    meter : catalight.equipment.power_meter.newport.NewportMeter
        Compatible power meter to use for calibration measurements.
    """

    laser.test_read_funcs()
    laser.set_watchdog_interval(0)
    laser.set_emission(True)

    # Collect calibration data, plot, and save
    print('Beginning collection of calibration data')
    print('Start Time = ', time.ctime())
    cal_data, cal_fig = run_calibration(laser, bandpass, meter)
    cal_data.to_csv('nkt_calibration_data.csv')
    cal_fig.savefig('nkt_calibration_data.svg')
    cal_fig.savefig('nkt_calibration_data.png')
    pickle.dump(cal_fig, open('nkt_calibration_data.pkl', 'wb'))
    print('End Time = ', time.ctime())

    # Collect growing window benchmark data
    print('Running growing window benchmark')
    growing_window_data = growing_window_test()
    growing_window_data.to_csv('nkt_growing_window_test.csv')
    print('Finished benchmark measurements')
    print('Finished collecting calibration data')


if __name__ == '__main__':
    pass

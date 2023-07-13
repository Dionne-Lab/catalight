"""
Random sampling experiment to test last run calibration performance.

The main function of this script will coordinate an NKT system and compatible
powermeter through a randomized verification experimtn in which the last run
calibration is used to predict the power output of random laser conditions.
Typically, this should be called by the nkt_system's run_calibration() method.
"""

import os
import time
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from catalight.equipment.light_sources import nkt_system
from catalight.equipment.power_meter import newport
from catalight.equipment.light_sources.nkt_collect_calibration \
    import make_measurement


def get_random_with_precision(min_val, max_val, precision):
    """
    Get a random value between min/max with "precision" points after decimal.

    Uses numpy.random.uniform() then round()

    Parameters
    ----------
    min_val : int or float
        minimum value to possibly return
    max_val : int or float
        maximum value to possibly return
    precision : int
        Number of digits past decimal (i.e. precision=2 => 2.19)

    Returns
    -------
    float
        random number between max/min with "precision" point past decimal.
    """
    random_num = np.random.uniform(min_val, max_val)
    scaled_num = round(random_num, precision)
    return scaled_num


def generate_data(calibration, num_measurements, laser_system, powermeter):
    """
    Request randomized conditions for laser system and record power output.

    This function will request a random bandwidth, power setpoint (mW), and
    central wavelength and record the output power of the given laser system.
    The requested number of measurements are made. The powermeter wavelength
    setpoint is changed to the central value between measurments and fringe
    measurments (100% or 12% power setpoint) are skipped. The calibration is
    supplied to determine the setpoint needed so the code can skip extreme
    cases. The proper calibration should be loaded into the laser_system object
    before passing it to this function.

    Parameters
    ----------
    calibration : pandas.DataFrame
        calibration fits for nkt_laser system
    num_measurements : int
        Number of random conditions to request for verfication
    laser_system : catalight.equipment.light_sources.nkt_system.NKT_System
        NKT System to run verification on
    powermeter : catalight.equipment.power_meter.newport.NewportMeter
        Compatible power meter object

    Returns
    -------
    pandas.DataFrame
        Randomized power measurements with columns ['center', 'bandwidth',
        'requested_power', 'measured_power']
    """
    data = []

    while len(data) < num_measurements:
        # Randomly determine relevant laser settings
        bandwidth = get_random_with_precision(10, 50, 1)
        center = get_random_with_precision(400+bandwidth/2, 800-bandwidth/2, 1)
        requested_power = random.uniform(1, bandwidth*2)
        # Check the setpoint needed for given conditions
        setpoint = nkt_system.determine_setpoint(calibration, requested_power,
                                                 center, bandwidth)
        # If required setpoint is min/max of laser, skip it.
        if setpoint not in [12, 100]:
            powermeter.change_wavelength(int(center))
            laser_system.set_bandpass(center, bandwidth)
            laser_system.set_power(requested_power)
            time.sleep(60)
            measured_power, std, error = make_measurement(powermeter)
            data.append([center, bandwidth, requested_power, measured_power])
            print_vals = (center, bandwidth/2,
                          requested_power, measured_power, setpoint)
            print('Measuring at: %4.1f +/- %3.1f nm, Req. Power = %5.2f, '
                  'Measured = %5.2f, setpoint = %4.1f' % print_vals)
        else:
            print_vals = (center, bandwidth/2, requested_power, setpoint)
            print('Skipping point at: %4.1f +/- %3.1f nm, Req. Power = %5.2f, '
                  'setpoint = %4.1f' % print_vals)

    df = pd.DataFrame(data, columns=['center', 'bandwidth',
                                     'requested_power', 'measured_power'])
    return df


def plot_verification(results, savedata=True):
    """
    Plot measured vs predicted values from randomized measurment test.

    Parameters
    ----------
    results : pandas.DataFrame
        Randomized power measurements with columns ['center', 'bandwidth',
        'requested_power', 'measured_power']
    savedata : `bool`, optional
        Whether or not to save the csv, svg, png for test, by default True

    Returns
    -------
    tuple(matplotlib.figure.Figure, matplotlib.axes._axes.Axes)
        Figure and Axis handles for plotted experiment
    """
    fig, ax = plt.subplots()
    results.plot(ax=ax, x='requested_power', y='measured_power', style='o')
    ax.plot(np.linspace(0, results['requested_power'].max(), 4),
            np.linspace(0, results['requested_power'].max(), 4), '--')
    if savedata:
        folder = os.path.dirname(os.path.abspath(__file__))
        results.to_csv(os.path.join(folder, 'calibration_verification.csv'))
        fig.savefig(os.path.join(folder, 'calibration_verification.svg'))
        fig.savefig(os.path.join(folder, 'calibration_verification.png'))
    return (fig, ax)


def main(laser_system, meter):
    """
    Runs and analyzes calibration verification experiment.

    Calls generate_data() and plot_verification()

    Parameters
    ----------
    laser_system : catalight.equipment.light_sources.nkt_system.NKT_System
        NKT laser system (laser + varia)
    meter : catalight.equipment.power_meter.newport.NewportMeter
        Compatible power meter used for measurements
    """
    folder = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(folder, "nkt_calibration.pkl")
    calibration = pd.read_pickle(path)
    results = generate_data(calibration, 50, laser_system, meter)
    plot_verification(results)


if __name__ == '__main__':
    meter = newport.NewportMeter()
    laser = nkt_system.NKT_System()

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

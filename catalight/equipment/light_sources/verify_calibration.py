import time
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from catalight.equipment.light_sources import nkt_system
from catalight.equipment.power_meter import newport


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


def generate_data(calibration, num_measurements, laser, powermeter):
    data = []

    while len(data) < num_measurements:
        bandwidth = get_random_with_precision(10, 50, 1)
        center = get_random_with_precision(400+bandwidth/2, 800-bandwidth/2, 1)
        requested_power = random.uniform(1, bandwidth*4)
        setpoint = nkt_system.determine_setpoint(calibration, requested_power,
                                                 center, bandwidth)
        if setpoint != 0:
            laser.central_wavelength = center
            laser.bandwidth = bandwidth
            laser.set_power(requested_power)
            time.sleep(30)
            measured_power = make_measurement(powermeter)
            data.append([center, bandwidth, requested_power, measured_power])
        else:
            print('skipping point', [center, bandwidth, requested_power, measured_power])

    df = pd.DataFrame(data, columns=['center', 'bandwidth',
                                     'requested_power', 'measured_power'])
    return df


if __name__ == '__main__':
    meter = newport.NewportMeter()
    laser = nkt_system.NKT_System()

    path = (r"G:\Shared drives\Ensemble Photoreactor"
            r"\Reactor Baseline Experiments\nkt_calibration\nkt_calibration.pkl")
    calibration = pd.read_pickle(path)
    results = generate_data(calibration, 10, laser, meter)
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

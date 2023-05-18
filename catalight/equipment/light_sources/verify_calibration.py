import time
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from catalight.equipment.light_sources import nkt_system
from catalight.equipment.power_meter import newport

def predict_power(calibration, power, center, bandwidth):
    """_summary_
    650 nm center with 45 nm bandwidth:
    627.5 [628-638, 638-648, 648-658, 658-668] 669, 670, 671, 672, 672.5
    Parameters
    ----------
    center : _type_
        _description_
    bandwidth : _type_
        _description_
    data : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """
    mask = ((calibration.index > center - bandwidth/2)
            & (calibration.index <= center + bandwidth/2))
    roi = calibration[mask]

    # Duplicate the first row until the desired size is reached
    while len(roi) < bandwidth:
        if roi.index[0] == calibration.index[0]:
            roi = pd.concat([roi, roi.iloc[0:1]], ignore_index=True)
        else:
            roi = pd.concat([roi, roi.iloc[-1:]], ignore_index=True)
    p = np.array(roi['fit params'].to_list())
    V = roi['covariance matrix']
    degree = p.shape[1]-1
    x = power  # The x values for interpolation
    powers = np.arange(degree, -1, -1)  # The power to raise x to [x^2, x^1...]
    # If x [a, b, c, d...] is an array,
    # we want to raise each value to each power [n, n-1, ... 2, 1, 0]
    # [[a^2, a^1, a^0],
    #  [b^2, b^1, b^0],
    #     ...
    #  [d^2, d^1, d^0]]
    x_powers = np.power.outer(x, powers)
    y = p @ x_powers.T
    prediction = y.sum(axis=0)
    #x_error = np.sqrt(x_powers.dot(V).dot(x_powers))
    return prediction


def determine_setpoint(calibration, power_requested, center, bandwidth):
    setpoints = np.arange(10, 100.1, 0.1)
    values = predict_power(calibration, setpoints, center, bandwidth)
    optimal_index = np.abs(values-power_requested).argmin()
    if (optimal_index == 0) or (optimal_index == (len(values))):
        optimal_value = 0
    else:
        optimal_value = setpoints[optimal_index]
    return optimal_value


def get_random_with_precision(min_val, max_val, precision):
    random_num = np.random.uniform(min_val, max_val)
    scaled_num = round(random_num, precision)
    return scaled_num


def make_measurement(meter, tolerance=2.5):
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
    return avg


def generate_data(calibration, num_measurements, laser, powermeter):
    data = []

    while len(data) < num_measurements:
        bandwidth = get_random_with_precision(10, 50, 1)
        center = get_random_with_precision(400+bandwidth/2, 800-bandwidth/2, 1)
        requested_power = random.uniform(1, bandwidth*4)
        setpoint = determine_setpoint(calibration, requested_power,
                                      center, bandwidth)
        if setpoint != 0:
            laser.central_wavelength = center
            laser.bandwidth = bandwidth
            laser.setpower(requested_power)
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
    plt.show()

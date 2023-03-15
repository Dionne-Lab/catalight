"""
Module used to calibrate diode laser and save calibration data.

User does not need to update the file, except to change the wavelength of the
diode laser being used. Works for Newport power meter and Thorlabs diode driver
powered by MCC DAQ.
Created on Tue Feb 22 23:15:23 2022
@author: Briley Bourgeois
"""
import numpy as np
import pandas as pd
from catalight.equipment.light_sources.diode_control import Diode_Laser
from catalight.equipment.power_meter.newport import NewportMeter


def main(current_range=(150, 800, 35), wavelength=450, tolerance=10):
    """
    Runs a calibration on the connected Diode_Laser.

    The current is varied based on the supplied current_range and the power
    is measured using the attached NewportMeter. The sampling time is the
    default defined in the NewportMeter class (0.5 sec/sample). Data is
    collected until 20 samples and the desired tolerance factor is met.
    Calibration results are saved locally to be accessed when initializing the
    Diode_Laser class. A plot showing the fit is produced. Only linear fits
    are supported at the moment (2023/02/09).

    Hardware Configuration: The laser should be on, connected to the DAQ board,
    and the current turned to 0 on the current controller. The power meter
    needs to be placed in the beam path at the location in which the user would
    like to calibrate the output (i.e. at the sample)

    Parameters
    ----------
    current_range : tuple, optional
        (I_min, I_max, step) tuple sent to range(). Used to control the testing
        range. Current cycled from I_min to I_max in steps.
        The default is (150, 800, 35).
    wavelength : int or float, optional
        Wavelength of diode. The default is 450.
    tolerance : int or float, optional
        Tolerance for each data point in percent. Sampling will continue until
        20 points have been collected and the standard deviation is less than
        the requested tolerance. Default sampling time is 0.5 seconds/point.
        The default is 10.

    Returns
    -------
    fig : matplotlib.pyplot.figure
        Figure handle for calibration plot.
    ax : matplotlib.pyplot.axis
        Axis handle for calibration plot.

    """

    diode = Diode_Laser()
    power_meter = NewportMeter()
    power_meter.change_wavelength(wavelength)

    data = pd.DataFrame(columns=['Power', 'error'])
    print('Running Calibration...')

    for current in range(current_range):
        diode.set_current(current)
        error = 100
        power_readings = np.array([-1000])  # Set unreal number
        while error > tolerance:
            power_readings = np.append(power_readings, power_meter.read()[1])
            if len(power_readings) > 20:
                power_readings = np.delete(power_readings, 0)
                std = np.std(power_readings)
                avg = np.average(power_readings)
                error = std / avg * 100

        print('Power Reading = %.2f +/- %.2f\n' % (avg, std))
        data.loc[current] = [avg, std]
    x_data, y_data, y_err = (data.index, data['Power'], data['error'])
    ax = data.plot(y=['Power'], ylabel='Power (mW)',
                   xlabel='Current (mA)', yerr=y_err)
    try:
        p, V = np.polyfit(x_data, y_data, 1, cov=True, w=1 / y_err)
        m, b, err_m, err_b = (*p, np.sqrt(V[0][0]), np.sqrt(V[1][1]))
        label = '\n'.join(["m: %4.2f +/- %4.2f" % (m, err_m),
                           "b: %4.2f +/- %4.2f" % (b, err_b)])
    except (np.linalg.LinAlgError):
        p = np.polyfit(x_data, y_data, 1)
        m, b = (p[0], p[1])
        label = '\n'.join(["m: %4.2f" % m,
                           "b: %4.2f" % b])
    x_fit = np.linspace(0, max(x_data), 100)
    ax.plot(x_fit, (p[0] * x_fit + p[1]), '--r')
    diode.update_calibration(p[0], p[1])
    diode.shut_down()
    fig = ax.get_figure()
    fig.savefig('diode_laser/calibration_plot.svg', format="svg")
    print(label)
    return fig, ax


if __name__ == "__main__":
    main()

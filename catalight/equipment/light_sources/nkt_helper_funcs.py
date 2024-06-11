import numpy as np
import pandas as pd
import warnings


def predict_power(calibration, power_setpoint, center, bandwidth):
    """
    Determine the power output (mW) expected from the given laser conditions.

    Takes in calibration and bandpass filter info to estimate the laser power
    output (in mW) that can be achieved  by the provided power_setpoint values.

    Parameters
    ----------
    calibration : pandas.DataFrame
        Calibration fits for nkt_laser system.
        Fit parameters for each wavelength. Index is wavelength.
        Columns are [fit params, relative error, covariance matrix]
        Each item within the DataFrame is a list itself.
    power_setpoint: int or float or list[float]
        The power setpoint (in %) the user desires. This can also be supplied
        as a pandas.DataFrame or numpy.array.
    center : float or int
        The central wavelength of the laser.
    bandwidth : float or int
        The bandwidth setting for the laser.

    Returns
    -------
    float
        The power output (in mW) expected from the given setpoint.
    """
    mask = ((calibration.index > center - bandwidth/2)
            & (calibration.index <= center + bandwidth/2))
    roi = calibration[mask]
    #print(roi)
    # Duplicate the first row until the desired size is reached
    while len(roi) < bandwidth:
        if roi.index[0] == calibration.index[0]:
            roi = pd.concat([roi, roi.iloc[0:1]], ignore_index=True)
        else:
            roi = pd.concat([roi, roi.iloc[-1:]], ignore_index=True)
    p = np.array(roi['fit params'].to_list())
    V = roi['covariance matrix']
    degree = p.shape[1]-1
    x = power_setpoint  # The x values for interpolation
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
    # x_error = np.sqrt(x_powers.dot(V).dot(x_powers))
    return prediction


def determine_setpoint(calibration, power_requested, center, bandwidth):
    """
    Determine the power setpoint (%) needed to reach a certain output power.

    Predicts the power output of the NKT over the full range of power
    setpoints [12% - 100%]. Returns the power setpoint that should produce the
    power output closest to the user supplied power_requested parameter.

    Parameters
    ----------
    calibration : pandas.DataFrame
        Calibration fits for nkt_laser system.
        Fit parameters for each wavelength. Index is wavelength.
        Columns are [fit params, relative error, covariance matrix]
        Each item within the DataFrame is a list itself.
    power_requested: int or float
        The power setpoint (in mW) the user desires.
    center : float or int
        The central wavelength of the laser.
    bandwidth : float or int
        The bandwidth setting for the laser.

    Returns
    -------
    float
        Closest laser setpoint (%) to achieve the requested power output (mW)/
        Automatically rounded to the nearest 0.1%.
    """
    if power_requested == 0:
        return 0
    
    setpoints = np.arange(12, 100.1, 0.1)
    values = predict_power(calibration, setpoints, center, bandwidth)
    optimal_index = np.abs(values-power_requested).argmin()
    optimal_setpoint = setpoints[optimal_index]
    optimal_value = values[optimal_index]
    if (abs(optimal_value - power_requested)) / power_requested > 0.02:
        # Define color escape sequences
        YELLOW = '\033[93m'
        RESET = '\033[0m'
        msg = ((YELLOW + '\nRequested NKT power = %4.2f mW\n'
               + 'Closest power at given conditions = %4.2f mW (%4.1f%%)\n' + RESET)
               % (power_requested, optimal_value, optimal_setpoint))
        warnings.warn(msg)
    return round(optimal_setpoint, 1)

"""
Generic light source template.
Some methods involving data logging and voice readout do not need to be editted
"""
import datetime as dt
import os
import re
import time
from ctypes import POINTER, cast
from threading import Timer

import numpy as np
import pandas as pd
import pyttsx3
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from nkt_tools import (extreme, varia)

# Sets path when file is imported
package_dir = os.path.dirname(os.path.abspath(__file__))
calibration_path = os.path.join(package_dir, 'nkt_calibration.pkl')


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
    if (optimal_index == 0) or (optimal_index == (len(values))-1):
        optimal_value = 0
    else:
        optimal_value = setpoints[optimal_index]
    return round(optimal_value, 1)


class NKT_System():
    """
    Vi
    """

    def __init__(self):
        # Set public attr
        self.is_busy = False  #: Used to block access from multiple threads

        # Set non-public attr
        self._calibration = [0, 0]
        self._P_set = 0
        self._laser = extreme.Extreme()
        self._bandpass = varia.Varia()
        self._bandwidth = (self._bandpass.long_setpoint
                           - self._bandpass.short_setpoint)
        self._central_wavelength = (self._bandpass.long_setpoint
                                    + self._bandpass.short_setpoint)/2

        self.read_calibration()

        # Initiate a voice control object to send alert messages
        self.voice_control = pyttsx3.init()
        self.voice_control.setProperty('volume', 1.0)
        rate = self.voice_control.getProperty('rate')
        self.voice_control.setProperty('rate', rate + 1)

        # Initiate control over speakers
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_,
                                     CLSCTX_ALL, None)
        self.volume_control = cast(interface, POINTER(IAudioEndpointVolume))

    P_set = property(lambda self: self._P_set)  #: Current laser setpoint

    @property
    def central_wavelength(self):
        """
        U
        """
        return self._central_wavelength

    @central_wavelength.setter
    def central_wavelength(self, value):
        short_setpoint = value - self.bandwidth/2
        long_setpoint = value + self.bandwidth/2
        if (short_setpoint <= 400) and (long_setpoint >= 800):
            self._laser.set_emission(False)
            self._bandpass.short_setpoint = short_setpoint
            self._bandpass.long_setpoint = long_setpoint
            self._central_wavelength = value
            self.set_power(self._P_set)
            self._laser.set_emission(True)
        else:
            print('Wavelength conditions outside range!')

    @property
    def bandwidth(self):
        """
        U
        """
        return self._bandwidth

    @bandwidth.setter
    def bandwidth(self, value):
        short_setpoint = self.central_wavelength - value/2
        long_setpoint = self.central_wavelength + value/2
        if (short_setpoint <= 400) and (long_setpoint >= 800):
            self._laser.set_emission(False)
            self._bandpass.short_setpoint = short_setpoint
            self._bandpass.long_setpoint = long_setpoint
            self._bandwidth = value
            self.set_power(self._P_set)
            self._laser.set_emission(True)
        else:
            print('Wavelength conditions outside range!')

    def set_power(self, P_set):
        """
        Send signal to DAQ to reach desired P_set value based on calibration.

        The necessary current is sent based on a externally performed
        calibration.
        * Raises speaker volume
        * Sends voice warning
        * Prints time to complete ramp
        * ramps from current setpoint to P_set at 650 mA/min to avoid equipment damage
        * Redefined _P_set along the way, printing status at each step
        * Calls print_output() on completion


        Parameters
        ----------
        P_set : int or float
            Desired laser output power in mW
        """
        # TODO put check on max power
        self.voice_control.setProperty('volume', 1.0)
        # TODO can i make this try to be int
        self.voice_control.say('Warning: Setting power to %6.2f milliwatts' % P_set)
        self.voice_control.runAndWait()
        self.voice_control.stop()

        while self.is_busy:
            time.sleep(0)
        self.is_busy = True
        setpoint = determine_setpoint(self._calibration, P_set,
                                      self.central_wavelength, self.bandwidth)
        print('Setpoint = ', setpoint)
        self._laser.set_power(setpoint)
        self.is_busy = False
        self._P_set = P_set
        print('\n', time.ctime())
        self.print_output()

        # ---------------------------------------------------------------------
        # TODO Print setpoint current and/or power
        # ---------------------------------------------------------------------

    def print_output(self):
        """Print the output current and power to console."""
        print('NKT power reading not supported')
        bandpass = (self._bandpass.short_setpoint,
                    self._bandpass.long_setpoint)
        print('Extreme/Fianium Setpoint = %4.1f %%' % self._laser.power_level)
        print('Varia Filter set for %4.1f nm - %4.1f nm' % bandpass)
        print('Expected System Output = %4.1f mW' % self._P_set)

    def shut_down(self):
        """Set power of laser to 0 by... """
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True

        self._laser.set_emission(False)
        self._laser.set_power(12)

        self.is_busy = False

    def update_calibration(self, slope, intercept):
        """
        Write calibration info to file.

        Calibration file path is defined at module level on import.
        Also saves date of calibration. Overwrites previous calibration!

        Parameters
        ----------
        slope : float
            Slope of linear calibration (mW/mA)
        intercept : float
            Y intercept of linear calibration (mA)
        """
        pass

    def read_calibration(self):
        """
        Update calibration attr based on module level calibration file.

        Also prints out calibration date and values to console.
        """
        self._calibration = pd.read_pickle(calibration_path)
        t = os.path.getmtime(calibration_path)
        print('Last laser calibration was:')
        print(dt.datetime.fromtimestamp(t).strftime('%Y-%m-%d'))

    def time_warning(self, time_left):
        """
        Play audio warning that laser will engage in time_left minutes.

        Parameters
        ----------
        time_left : int or float
            (min) Time to read out until setting laser
        """
        # Consider upgrading this to use asyncio or threading.Timer and have
        # the code put out 5 4 3 2 1 minute warnings on a separate thread
        # Unmutes and sets Vol in dB -0.0 is 100%
        self.volume_control.SetMute(0, None)
        self.voice_control.say(f'Warning: Diode laser will automatically'
                               f'engage in {time_left} minutes')
        self.voice_control.runAndWait()

    def start_logger(self, log_frequency=0.1, save_path=None):
        """
        Start the data log function to record the laser set point.

        Records constantly until stop_logger() is called. Creates self.timer
        and self.save_path when called.

        Parameters
        ----------
        log_frequency : float or int, optional
            (seconds) interval to record data with. The default is 0.1 sec.
        save_path : str, optional
            Full tile path to save data to. If None, saves in module directory
            with file name 'YYYYMMDDlaser_log.txt'. Appends int to end of file
            name if file name already exists.
        """
        if save_path is None:  # if savepath is unspecified, saves in cwd
            save_path = os.path.join(os.getcwd(),
                                     dt.date.today().strftime('%Y%m%d') + 'laser_log.txt')
        while os.path.isfile(save_path):  # check if log w/ default name exists
            m = 1
            save_path = save_path.removesuffix('.txt')
            # checks if save_path has number at end
            if re.findall(r'\d+$', save_path):
                m += int(re.findall(r'\d+$', save_path)[-1])
            # append number and .txt to filename,
            # then check if name still exists
            save_path = re.split(r'\d+$', save_path)[0] + str(m)
            save_path = save_path + '.txt'

        self.save_path = save_path  # assign local pathname to class attribute
        # create update thread
        self.timer = RepeatTimer(log_frequency, self.log_power)
        self.timer.start()

    def log_power(self):
        """Append (date and current power setpoint) to the log at save_path."""
        with open(self.save_path, 'a') as output_log:
            entry = ('%s, %6.2f \n' % (dt.datetime.now(), self.P_set))
            output_log.write(entry)

    def stop_logger(self):
        """Cancel timer initialized w/ start_logger() and delete it."""
        if self.timer:
            self.timer.cancel()
            del self.timer
        else:
            print('No Timer')


class RepeatTimer(Timer):
    """
    Subclass of threading.Timer. Runs at interval until cancelled.

    Parameters
    ----------
    interval : float or int
        Time interval in seconds to call function.
    function : func
        Functions to call
    args
        Arguments of function.
    kwargs
        Key word arguments of function.
    """

    def run(self):
        """Run function until finished supplying args and kwargs."""
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


if __name__ == "__main__":
    laser_controller = Diode_Laser()
    laser_controller.start_logger()
    laser_controller.time_warning(1)
    laser_controller.print_output()
    laser_controller.stop_logger()
    laser_controller.shut_down()

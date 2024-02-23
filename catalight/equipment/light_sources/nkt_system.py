"""
NKT Extreme/Fianium laser + Varia.

This module also includes some utility functions for working with the
nkt_system.
"""
import os
import re
import time
import datetime as dt
from ctypes import POINTER, cast
from threading import Timer

import numpy as np
import pandas as pd
import pyttsx3
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from nkt_tools import (extreme, varia)

from catalight.equipment.light_sources import (nkt_collect_calibration,
                                               nkt_analyze_calibration,
                                               nkt_verify_calibration)

import catalight.equipment.light_sources as optics_tools
from catalight.equipment.light_sources.nkt_helper_funcs import (predict_power,
                                                                determine_setpoint)


# Sets path when file is imported
package_dir = os.path.dirname(os.path.abspath(__file__))
calibration_path = os.path.join(package_dir, 'nkt_calibration.pkl')


class NKT_System():
    """
    This class wraps together the Varia and Extreme classes of nkt_tools.

    The methods contained within are compatible with the rest of catalight.
    Not that this class is not compatible with NKT hardware different from
    an Extreme/Fianium laser connected to a Varia. Users with other hardwawre
    will need to develop their own plug in, but a guide was developed to
    demonstrate how the NKT_System and nkt_tool was written and integrated.
    """
    is_tunable = True
    """bool: Defines whether laser class is tunable. NKT system is."""

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
        self._wavelength_range = [400, 800]
        self._bandwidth_range = [10, 100]
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
    wavelength_range = property(lambda self: self._wavelength_range)
    """[min, max] Min/Max wavelength of tunable laser, read-only"""
    bandwidth_range = property(lambda self: self._bandwidth_range)
    """[min, max] Min/Max bandwidth of tunable laser, read-only"""

    @property
    def central_wavelength(self):
        """
        The center wavelength for the nkt laser, read-only.

        Set with set_bandpass()
        """
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True

        self._central_wavelength = (self._bandpass.long_setpoint
                                    + self._bandpass.short_setpoint)/2

        self.is_busy = False
        return self._central_wavelength

    @property
    def bandwidth(self):
        """
        The bandwidth for the nkt laser, read-only.

        Set with set_bandpass()
        """
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True

        self._bandwidth = (self._bandpass.long_setpoint
                           - self._bandpass.short_setpoint)

        self.is_busy = False
        return self._bandwidth

    def set_bandpass(self, center, width):
        """
        Updates the bandpass setting of the connected Varia.

        The setting provided must ensure the bandpass doesn't extend past 400
        or 800 nm. The code will check and abort adjustment if the check fails.
        This method will also update the power setpoint of the NKT laser such
        that the emission after adjusting the wavelength is consistent with the
        last requested output power.

        Parameters
        ----------
        center : int or float
            [nm] Central wavelength to be used when tuning bandpass filter.
        width : int or float
            [nm] Bandpass width.
        """
        short_setpoint = center - width/2
        long_setpoint = center + width/2
        print("going into bandpass setting method, is_busy is - " + str(self.is_busy))
        if ((short_setpoint >= self.wavelength_range[0])
                and (long_setpoint <= self.wavelength_range[1])):
            while self.is_busy:
                time.sleep(0)
            self.is_busy = True
            self._bandpass.short_setpoint = short_setpoint
            self._bandpass.long_setpoint = long_setpoint
            self._central_wavelength = center
            self._bandwidth = width
            # Reset Power setpoint [%] to keep constant output in mW
            setpoint = determine_setpoint(self._calibration, self.P_set,
                                          center, width)
            self._laser.set_power(setpoint)  # Note this is power setpoint
            self.is_busy = False
        else:
            print('Wavelength conditions outside range!')

    def set_power(self, P_set):
        """
        Estimates a power setpoint for NKT laser based on calibration.

        Takes into account current bandpass filter settings to predict the
        power setpoint needed to achieve the requested emitted power.

        * Raises speaker volume
        * Sends voice warning
        * Redefined _P_set
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

        # NKT cannot be set to 0% so turn off emission is user requests 0 power
        if P_set == 0:
            self._laser.set_emission(False)

        elif P_set > 0:  # Make sure emission is on
            self._laser.set_emission(True)

            setpoint = determine_setpoint(self._calibration, P_set,
                                          self._central_wavelength,
                                          self._bandwidth)
            print('Setpoint = ', setpoint)
            self._laser.set_power(setpoint)

        self.is_busy = False
        self._P_set = P_set
        print('\n', time.ctime())
        self.print_output()

        # ---------------------------------------------------------------------
        # TODO Print setpoint current and/or power
        # ---------------------------------------------------------------------

    def set_setpoint(self, setpoint):
        """
        Sets power setpoint (in %) directly.

        Parameters
        ----------
        setpoint : int or float
            Desired laser output power in %
        """
        # TODO put check on max power
        self.voice_control.setProperty('volume', 1.0)
        # TODO can i make this try to be int
        self.voice_control.say('Warning: Setting power to %6.2f percent' % setpoint)
        self.voice_control.runAndWait()
        self.voice_control.stop()

        while self.is_busy:
            time.sleep(0)
        self.is_busy = True

        # NKT cannot be set to 0% so turn off emission is user requests 0 power
        if setpoint == 0:
            self._laser.set_emission(False)

        elif setpoint > 0:  # Make sure emission is on
            self._laser.set_emission(True)
            self._laser.set_power(setpoint)

        self.is_busy = False

        print('\n', time.ctime())
        self.print_output()

        # ---------------------------------------------------------------------
        # TODO Print setpoint current and/or power
        # ---------------------------------------------------------------------

    def get_output_setpoint(self):
        """
        Get output power based on laser setpoint.

        Returns
        -------
        setpoint : float or int
            Power [%] rounded to nearest decimal point
        """
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True

        if self._laser.emission_state == True:
            setpoint = self._laser.power_level
        elif self._laser.emission_state == False:
            setpoint = 0
        elif self._laser.emission_state == 'Unknown':
            print('Unknown emission state')
            setpoint = 0

        self.is_busy = False

        return (setpoint)

    def get_output_power(self):
        """
        Get output power based on laser setpoint and saved calibration.

        Returns
        -------
        P : float or int
            Power [mW] rounded to 3 decimal points
        """
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True

        state = self._laser.emission_state
        current_setpoint = self._laser.power_level

        self.is_busy = False

        if state == True:
            setpoint = current_setpoint
            P = predict_power(self._calibration, setpoint,
                              self.central_wavelength, self.bandwidth)
            return (P)

        elif state == False:
            setpoint = 0
            return 0

        elif state == 'Unknown':
            print('Unknown emission state')
            return

    def print_output(self):
        """Print the bandpass settings, power setpoint, and expected power."""
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True
        bandpass = (self._bandpass.short_setpoint,
                    self._bandpass.long_setpoint)
        print('Extreme/Fianium Setpoint = %4.1f %%' % self._laser.power_level)
        print('Varia Filter set for %4.1f nm - %4.1f nm' % bandpass)
        print('Expected System Output = %4.1f mW' % self._P_set)
        self.is_busy = False

    def shut_down(self):
        """Set power of laser to 0 by turning off emission.
        Also lowers setpoint power to 12%."""
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
        try:
            self._calibration = pd.read_pickle(calibration_path)
            t = os.path.getmtime(calibration_path)
            print('Last laser calibration was:')
            print(dt.datetime.fromtimestamp(t).strftime('%Y-%m-%d'))
        except FileNotFoundError:
            print('No Calibration File Found!!')

    def run_calibration(self, meter):
        """
        Perform a calibration experiment, analyze results, and verify quality.

        Will run the scripts: nkt_collect_calibration, nkt_analyze_calibration,
        and nkt_verify_calibration. Loads the collected calibration before
        proceeding to verification experiment.

        Parameters
        ----------
        meter : catalight.equipment.power_meter.newport.NewportMeter
            Compatible power meter to use for calibration experiments.
        """
        self._laser.set_emission(True)
        nkt_collect_calibration.main(self._laser, self._bandpass, meter)
        nkt_analyze_calibration.main()
        self.read_calibration()  # Update to new calibration
        nkt_verify_calibration.main(self, meter)
        self.set_power(0)
        self._laser.set_emission(False)
        print("Calibration process complete!")

    def max_constant_power(self, bandwidth, wavelength_range):
        """
        Estimate the maximum power that can be acheived across a given range.

        Predicts the maximum power that can be delivered across the wavelength
        range for a given bandwidth, then returns the minimum value.

        Parameters
        ----------
        bandwidth : float or int
            Bandwidth to use for estimation
        wavelength_range : list[float or int]
            [lambda_min, lambda_max] center wavelength range to be tested.

        Returns
        -------
        float
            [mW] Maximum constant power for given parameters.
        """
        data = []
        lambda_min = wavelength_range[0]
        lambda_max = wavelength_range[-1]
        lower_lim = self.wavelength_range[0]
        upper_lim = self.wavelength_range[1]

        # Do not proceed if the given range is invalid
        if not (lower_lim <= lambda_min < upper_lim
                and lower_lim < lambda_max <= upper_lim):
            return 0

        # Predict power over given range, return smallest value
        for wavelength in np.arange(lambda_min, lambda_max+0.01):
            value = predict_power(self._calibration, 100, wavelength, bandwidth)
            data.append(value)

        return min(data)

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
        log_frequency : `float` or `int`, optional
            (seconds) interval to record data with. The default is 0.1 sec.
        save_path : `str`, optional
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
    function : `function`
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
    print('test')

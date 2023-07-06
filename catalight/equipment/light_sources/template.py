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
import pyttsx3
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Sets path when file is imported
package_dir = os.path.dirname(os.path.abspath(__file__))
calibration_path = os.path.join(package_dir, 'nkt_calibration.csv')
# TODO: Update calibration path w/ lightsource name


class Template_Laser():
    """
    Vi
    """
    is_tunable = False
    """bool: Defines whether laser class is tunable."""

    def __init__(self):
        # Set public attr
        self.is_busy = False  #: Used to block access from multiple threads

        self._calibration = [0, 0]

        # Set non-public attr
        self._P_set = 0
        #TODO Update for hardware
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

        # Turn power to zero on initialization
        self.set_power(0)

    P_set = property(lambda self: self._P_set)  #: Current laser setpoint
    wavelength_range = property(lambda self: self._wavelength_range)
    """[min, max] Min/Max wavelength of tunable laser, read-only"""
    bandwidth_range = property(lambda self: self._bandwidth_range)
    """[min, max] Min/Max bandwidth of tunable laser, read-only"""

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

        # ---------------------------------------------------------------------
        # TODO Device specific set power command
        # Check manual to see if device power should be ramped slowly
        # See diode_control for example
        # ---------------------------------------------------------------------

        self.is_busy = False
        self._P_set = P_set
        print('\n', time.ctime())
        self.print_output()

        # ---------------------------------------------------------------------
        # TODO Print setpoint current and/or power
        # ---------------------------------------------------------------------

    def get_output_power(self):
        """
        Get output power based on current measured and saved calibration.

        Returns
        -------
        P : float or int
            Power [mW] rounded to 3 decimal points
        """
        I = self.get_output_current()  # noqa I==current
        P = round(self.I_to_P(I), 3)
        return P

    def print_output(self):
        """Print the output current and power to console."""
        I = self.get_output_current()  # noqa I==current
        P = self.get_output_power()
        print('Measured Laser output = %7.2f mW / %7.2f mA' % (P, I))


    def shut_down(self):
        """Set power of laser to 0 by setting DAQ Voltage to 0."""
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True

        # ---------------------------------------------------------------------
        # TODO turn off device in a way that doesn't rely on calibration
        # ---------------------------------------------------------------------

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
        # open and write to calibration file
        with open(calibration_path, 'r+') as old_cal_file:
            new_cal_file = []

            for line in old_cal_file:  # read values after '=' line by line
                if re.search('m = ', line):
                    line = ('m = ' + str(slope) + ' \n')
                elif re.search('b = ', line):
                    line = ('b = ' + str(intercept) + ' \n')
                elif re.search('date = ', line):
                    line = ('date = ' + dt.date.today().strftime('%Y-%m-%d') + '\n')

                new_cal_file += line

            old_cal_file.seek(0)  # Starting from beginning line
            old_cal_file.writelines(new_cal_file)
        self.read_calibration()

    def read_calibration(self):
        """
        Update calibration attr based on module level calibration file.

        Also prints out calibration date and values to console.
        """
        with open(calibration_path, 'r') as calibration:

            for line in calibration:  # read values after '=' line by line
                if re.search('m = ', line):
                    self._calibration[0] = float(
                        line.split('=')[-1].strip(' \n'))
                elif re.search('b = ', line):
                    self._calibration[1] = float(
                        line.split('=')[-1].strip(' \n'))
                elif re.search('date = ', line):
                    print('Last laser calibration was:')
                    print(line)
        print(f'Power = {self._calibration[0]}*Current'
              f'+ {self._calibration[1]}\n')

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
    print('test code')

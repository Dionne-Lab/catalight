"""Control Diode laser via DAQ board."""
import datetime as dt
import os
import re
import time
from ctypes import POINTER, cast
from threading import Timer

import numpy as np
import pyttsx3
from comtypes import CLSCTX_ALL
from mcculw import ul
from mcculw.device_info import DaqDeviceInfo
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Sets path when file is imported
package_dir = os.path.dirname(os.path.abspath(__file__))
calibration_path = os.path.join(package_dir, 'diode_calibration.txt')


class Diode_Laser():
    """
    Virtual instance of diode laser.

    Virtual object for interfacing with Thorlabs diode driver system via an
    MCC DAQ device. The DAQ board should be connected to the current control
    system via BNC cables. A voltage is supplied by the DAQ board to send a
    current from the current controller to the diode driver, thus emitting
    a specified power from the laser. The user must perform a calibration of
    the system prior to using this class!
    """
    is_tunable = False
    """bool: Defines whether laser class is tunable. Diode is not."""

    def __init__(self):
        # Set public attr
        self.is_busy = False  #: Used to block access from multiple threads
        self.board_num = 0  #: Location of DAQ in "instacal" software.
        self.memhandle = None
        self.channel = 0
        self.dev_id_list = []
        self._calibration = [0, 0]

        # Set non-public attr
        self._I_max = 2000  #: (mA) Max current of current controller
        self._k_mod = self._I_max / 10  #: (mA/V)
        self._P_set = 0
        self._bandwidth = 0
        self._central_wavelength = 450
        self._wavelength_range = [450, 450]
        self._bandwidth_range = [0, 0]

        # Initiate DAQ
        self._daq_dev_info = DaqDeviceInfo(self.board_num)
        self._ao_info = self._daq_dev_info.get_ao_info()

        if self._ao_info.is_supported:
            self._ao_range = self._ao_info.supported_ranges[0]
        else:
            print('Warning: Output not supported by DAQ')

        self._ai_info = self._daq_dev_info.get_ai_info()

        if self._ai_info.is_supported:
            self._ai_range = self._ai_info.supported_ranges[0]
        else:
            print('Warning: Input not supported by DAQ')

        # Initialize equipment
        print('Active DAQ device: ', self._daq_dev_info.product_name, ' (',
              self._daq_dev_info.unique_id, ')\n', sep='')
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
        try:
            self.read_calibration()
            # Turn power to zero on initialization
            self.set_power(0)
        except FileNotFoundError:
            print('Warning, no cabration found.')



    # Read Only Attributes
    I_max = property(lambda self: self._I_max)  #: (mA) Max current
    k_mod = property(lambda self: self._k_mod)  #: (mA/V) Conversion Factor
    daq_dev_info = property(lambda self: self._daq_dev_info)  #: DAQ info
    ao_info = property(lambda self: self._ao_info)  #: Analog output info
    ao_range = property(lambda self: self._ao_range)  #: Analog output range
    ai_info = property(lambda self: self._ai_info)  #: Analog input info
    ai_range = property(lambda self: self._ai_range)  #: Analog input range
    P_set = property(lambda self: self._P_set)  #: Current laser setpoint
    wavelength_range = property(lambda self: self._wavelength_range)
    """[min, max] Min/Max wavelength of tunable laser, read-only"""
    bandwidth_range = property(lambda self: self._bandwidth_range)
    """[min, max] Min/Max bandwidth of tunable laser, read-only"""
    central_wavelength = property(lambda self: self._central_wavelength)
    """Current wavelength of laser, read-only"""
    bandwidth = property(lambda self: self._bandwidth)
    """Current bandwidth of laser, read-only"""

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
        # speak('Warning: Setting power to' + str(P_set) + 'milliwatts')
        I_set = self.P_to_I(P_set)  # (mA) Based on calibration
        I_start = self.get_output_current()
        # TODO can i round this to 0 if negative?
        P_start = self.I_to_P(I_start)
        if P_start < 0:
            I_start = self.P_to_I(0)
        refresh_rate = 20  # 1/min
        ramp_time = (I_set - I_start) / 650  # [min] - spans 1300mA in 2 min
        setpoints = np.linspace(I_start, I_set,
                                abs(int(ramp_time * refresh_rate)))
        setpoints = np.append(setpoints, I_set)
        if P_set != 0:
            print('ramp time = %6.4f minutes' % ramp_time)

        while self.is_busy:
            time.sleep(0)
        self.is_busy = True

        for I in setpoints: # noqa I==current
            # Ramps the current slowly
            Vout = I / self._k_mod  # (V) Voltage output set point
            if (P_set == 0) and self._ao_info.is_supported:
                Vout = 0
                # Convert to 16bit
                Vout_value = ul.from_eng_units(self.board_num, self._ao_range, Vout)
                # Send signal to DAQ Board
                ul.a_out(self.board_num, 0, self._ao_range, Vout_value)
                break

            elif (P_set != 0) and self._ao_info.is_supported:
                # Convert to 16bit
                Vout_value = ul.from_eng_units(self.board_num, self._ao_range, Vout)
                # Send signal to DAQ Board
                ul.a_out(self.board_num, 0, self._ao_range, Vout_value)
                time.sleep(60 / refresh_rate)  # wait
                self._P_set = self.I_to_P(I)
                print('Set Point = %7.2f mW / %7.2f mA' % (self.P_set, I))

            else:
                print('DAQ Write Not Supported')

        self.is_busy = False
        self._P_set = P_set
        print('\n', time.ctime())
        self.print_output()
        print('Set Point = %7.2f mW / %7.2f mA \n' % (self.P_set, I_set))

    def get_output_current(self):
        """
        Convert DAQ voltage to current measurement.

        Returns
        -------
        float or int
            Current measured by DAQ

        """
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True

        if self._ai_info.is_supported:
            # Get input value into DAQ
            Vin_value = ul.a_in(self.board_num, self.channel, self._ai_range)
            Vin_eng_units_value = ul.to_eng_units(self.board_num,
                                                  self._ai_range, Vin_value)
            # Convert to relevant output numbers
            V = Vin_eng_units_value
            I = round(V * self._k_mod, 3)  # noqa I==current
        else:
            print('DAQ Read Not Supported')
            I = 0  # noqa I==current

        self.is_busy = False
        return (abs(I))

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
        return (P)

    def print_output(self):
        """Print the output current and power to console."""
        I = self.get_output_current()  # noqa I==current
        P = self.get_output_power()
        print('Measured Laser output = %7.2f mW / %7.2f mA' % (P, I))

    def I_to_P(self, I):  # noqa I==current
        """
        converts a current to power based on read calibration

        Parameters
        ----------
        I : float
            Current you'd like to convert [mA]

        Returns
        -------
        P : float
            Power [mW]

        """
        m = self._calibration[0]
        b = self._calibration[1]
        P = I * m + b
        return (P)

    def P_to_I(self, P):
        """
        Convert a power to current based on read calibration.

        Parameters
        ----------
        P : int or float
            Power you'd like to convert [mW]

        Returns
        -------
        I : float
            Equivalent current [mA]

        """
        m = self._calibration[0]
        b = self._calibration[1]
        I = (P-b)/m  # (mA) Based on calibration #noqa I==current
        return(I)

    def shut_down(self):
        """Set power of laser to 0 by setting DAQ Voltage to 0."""
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True
        Vout = 0  # (V) Voltage output set point
        # Convert to 16bit
        Vout_value = ul.from_eng_units(self.board_num, self._ao_range, Vout)
        # Send signal to DAQ Board
        ul.a_out(self.board_num, 0, self._ao_range, Vout_value)
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
        with open(calibration_path, 'w+') as cal_file:
            cal_file.write('m = ' + str(slope) + ' \n')
            cal_file.write('b = ' + str(intercept) + ' \n')
            cal_file.write('date = ' + dt.date.today().strftime('%Y-%m-%d') + '\n')

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

    def set_current(self, I_set):
        """
        Set current output of controller.

        Use this when running calibration. Reads warning messages when
        changing power

        Parameters
        ----------
        I_set : int or float
            Current setpoint to send to controller (mA)
        """
        Vout = I_set / self._k_mod  # (V) Voltage output set point
        print('Current set to %.2f\nVoltage set to %.2f' % (I_set, Vout))
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True
        # Convert to 16bit
        Vout_value = ul.from_eng_units(self.board_num, self._ao_range, Vout)

        # Send signal to DAQ Board
        ul.a_out(self.board_num, 0, self._ao_range, Vout_value)
        Vin_value = ul.a_in(self.board_num, self.channel, self._ai_range)
        Vin_eng_units_value = ul.to_eng_units(self.board_num,
                                              self._ai_range, Vin_value)
        self.is_busy = False

        self.print_output()
        print(time.ctime())
        # Unmutes and sets Vol in dB -0.0 is 100%
        self.volume_control.SetMute(0, None)
        self.volume_control.SetMasterVolumeLevel(-2.0, None)
        self.voice_control.say('Warning: Setting current to %6.2f milliamps' % I_set)
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
    laser_controller = Diode_Laser()
    laser_controller.start_logger()
    laser_controller.time_warning(1)
    laser_controller.print_output()
    laser_controller.stop_logger()
    laser_controller.shut_down()

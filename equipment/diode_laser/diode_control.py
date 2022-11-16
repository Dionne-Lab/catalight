# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
from mcculw import ul
from mcculw.device_info import DaqDeviceInfo
from PyQt5.QtCore import (QTimer)
import datetime as dt
import numpy as np
import time
import re
import os
import pyttsx3
from threading import Thread, Timer


# Sets path when file is imported
package_dir = os.path.dirname(os.path.abspath(__file__))
calibration_path = os.path.join(package_dir, 'diode_calibration.txt')

# Initiate a voice control object to send alert messages
voice_control = pyttsx3.init()
voice_control.setProperty('volume', 1.0)
rate = voice_control.getProperty('rate')
voice_control.setProperty('rate', rate + 1)


# This is some code I took off the internet to get control over the speakers
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume_control = cast(interface, POINTER(IAudioEndpointVolume))


# def speak(phrase):

#     # Make sure volume is turned up
#     volume_control.SetMute(0, None) # Unmutes and sets Vol in dB -0.0 is 100%
#     volume_control.SetMasterVolumeLevel(-2.0, None)

#     voice_control.setProperty('volume', 1.0)
#     voice_control.say(phrase)
#     voice_control.runAndWait()
#     voice_control.stop()
#     del(voice_control) # Delete because controller bugs on 2nd call
#     voice_control = pyttsx3.init() #init controller

class Diode_Laser():
    def __init__(self):

        # Set public attr
        self.board_num = 0
        self.memhandle = None
        self.channel = 0
        self.dev_id_list = []
        self._calibration = [0, 0]

        # Set non-public attr
        self._I_max = 2000  # (mA) Max current of current controller
        self._k_mod = self._I_max/10  # mA/V
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
            print('Warning: Output not supported by DAQ')

        # Initialize equipment
        print('Active DAQ device: ', self._daq_dev_info.product_name, ' (',
              self._daq_dev_info.unique_id, ')\n', sep='')
        self.read_calibration()
        self.set_power(0)


    # Read Only Attributes
    I_max = property(lambda self: self._I_max)
    k_mod = property(lambda self: self._k_mod)
    daq_dev_info = property(lambda self: self._daq_dev_info)
    ao_info = property(lambda self: self._ao_info)
    ao_range = property(lambda self: self._ao_range)
    ai_info = property(lambda self: self._ai_info)
    ai_range = property(lambda self: self._ai_range)

    def set_power(self, P_set):
        '''Reads in laser power and sends signal to DAQ to match input power.
        The necessary current is sent based on a externally performed
        calibration. Outputs read power, set point, and time to console.
        reads warning messages when changing power'''
        #TODO put check on max power
        voice_control.setProperty('volume', 1.0)
        voice_control.say('Warning: Setting power to' + str(P_set) + 'milliwatts')
        voice_control.runAndWait()
        voice_control.stop()
        #speak('Warning: Setting power to' + str(P_set) + 'milliwatts')
        self.P_set = str(P_set)
        m = self._calibration[0]
        b = self._calibration[1]
        I_set = (P_set-b)/m  # (mA) Based on calibration
        I_start = self.get_output_current()
        refresh_rate = 20  # 1/min
        ramp_time = (I_set - I_start)/650  # min - reaches max in 2 min
        setpoints = np.linspace(I_start, I_set, abs(int(ramp_time*refresh_rate)))
        setpoints = np.append(setpoints, I_set)
        print('ramp time = ', ramp_time)
        print(setpoints)
        for I in setpoints:
            # Ramps the current slowly
            Vout = I/self._k_mod  # (V) Voltage output set point
            if P_set == 0:
                Vout = 0
                # Convert to 16bit
                Vout_value = ul.from_eng_units(self.board_num, self._ao_range, Vout)

                # Send signal to DAQ Board
                ul.a_out(self.board_num, 0, self._ao_range, Vout_value)
                Vin_value = ul.a_in(self.board_num, self.channel, self._ai_range)
                Vin_eng_units_value = ul.to_eng_units(self.board_num,
                                                      self._ai_range, Vin_value)
                break
            # Convert to 16bit
            Vout_value = ul.from_eng_units(self.board_num, self._ao_range, Vout)

            # Send signal to DAQ Board
            ul.a_out(self.board_num, 0, self._ao_range, Vout_value)
            time.sleep(60/refresh_rate)  # wait
            print(I)

        self.print_output()
        print('Set Point = ' + str(P_set))
        print(time.ctime())


    def get_output_current(self):
        '''returns the current measured by DAQ'''
        # Get input value into DAQ
        Vin_value = ul.a_in(self.board_num, self.channel, self._ai_range)
        Vin_eng_units_value = ul.to_eng_units(self.board_num,
                                              self._ai_range, Vin_value)
        # Convert to relevant output numbers
        V = Vin_eng_units_value
        I = round(V*self._k_mod, 3)
        return(abs(I))

    def get_output_power(self):
        '''returns the calculates output power from
        current measured and saved calibration'''
        m = self._calibration[0]
        b = self._calibration[1]
        I = self.get_output_current()
        P = round(I*m+b, 3)
        return(P)

    def print_output(self):
        '''prints the output current and power to console'''
        I = self.get_output_current()
        P = self.get_output_power()
        print('Laser output = ' + str(I) + ' mA / ' + str(P) + ' mW')

    def shut_down(self):
        '''Sets power of laser to 0'''
        Vout = 0  # (V) Voltage output set point
        # Convert to 16bit
        Vout_value = ul.from_eng_units(self.board_num, self._ao_range, Vout)
        # Send signal to DAQ Board
        ul.a_out(self.board_num, 0, self._ao_range, Vout_value)
        print('Finished')

    def update_calibration(self, slope, intercept):
        '''takes in new calibration data and updates calibration file,
        updates class properties'''
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

    def read_calibration(self):
        '''Reads calibration file stored in module directory, updates internal
        properties accordingly'''
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
            print(
                f'Power = {self._calibration[0]}*Current + {self._calibration[1]}')

    def time_warning(self, time_left):
        '''Enter time in minutes until activation of laser,
        read outs warning message'''
        # Consider upgrading this to use asyncio or threading.Timer and have
        # the code put out 5 4 3 2 1 minute warnings on a seperate thread
        # Unmutes and sets Vol in dB -0.0 is 100%
        volume_control.SetMute(0, None)
        voice_control.say(
            f'Warning: Diode laser will automatically engage in {time_left} minutes')
        voice_control.runAndWait()

    def set_current(self, I_set):
        '''Sets current output of controller. Use this only when running
        calibration reads warning messages when changing power'''
        Vout = I_set/self._k_mod  # (V) Voltage output set point
        print(I_set)
        print(Vout)
        # Convert to 16bit
        Vout_value = ul.from_eng_units(self.board_num, self._ao_range, Vout)

        # Send signal to DAQ Board
        ul.a_out(self.board_num, 0, self._ao_range, Vout_value)
        Vin_value = ul.a_in(self.board_num, self.channel, self._ai_range)
        Vin_eng_units_value = ul.to_eng_units(self.board_num,
                                              self._ai_range, Vin_value)

        self.print_output()
        print(time.ctime())
        # Unmutes and sets Vol in dB -0.0 is 100%
        volume_control.SetMute(0, None)
        volume_control.SetMasterVolumeLevel(-2.0, None)
        voice_control.say('Warning: Setting current to'
                          + str(I_set) + 'milliamps')
        voice_control.runAndWait()

    def start_logger(self, log_frequency=0.1, save_path=None):
        '''starts the data log function to record the laser set point at 
        log_frequency intervals (seconds). Takes an optional arugment of the 
        desired save path. If none is entered the log gets saved in the driver
        directory. auto increments file name'''
        if save_path is None: # if savepath is unspecified, saves in cwd
            save_path = os.path.join(os.getcwd(),
                                     dt.date.today().strftime('%Y%m%d')+'laser_log.txt')
        while os.path.isfile(save_path): # checks if log w/ default name exists
            m = 1
            save_path = save_path.removesuffix('.txt')
            if re.findall(r'\d+$', save_path): # checks if save_path has number at end
                m += int(re.findall(r'\d+$', save_path)[-1])
            # append number and .txt to filename, then check if name still exists
            save_path = re.split(r'\d+$',save_path)[0]+str(m)
            save_path = save_path+'.txt'

        self.save_path = save_path # assign local pathname to class attribute
        self.timer = RepeatTimer(log_frequency, self.log_power) # create update thread
        self.timer.start()

    def log_power(self):
        '''appends the date at current power setpoint to the outputlog'''
        with open(self.save_path, 'a') as output_log:
            output_log.write(str(dt.datetime.now())+', '+self.P_set+'\n')


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

if __name__ == "__main__":
    laser_controller = Diode_Laser()
    laser_controller.start_logger()
    time.sleep(3)
    laser_controller.timer.cancel()
    # laser_controller.time_warning(round(0.5/60))
    # laser_controller.set_power(0)
    # time.sleep(10)
    # laser_controller.set_power(0)
    # laser_controller.shut_down()

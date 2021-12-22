# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from mcculw import ul
from mcculw.enums import ScanOptions, FunctionType, Status
from mcculw.device_info import DaqDeviceInfo
import numpy as np
import time

dev_id_list = []
board_num = 0
memhandle = None
channel = 0

PowerSweep = np.arange(0, 110, 10)
t_trans = np.append(34, np.ones(len(PowerSweep-1))*)*60
Imax = 2000  # (mA) Max current of current controller
k_mod = Imax/10  # mA/V
P_set = 10  # mW
I_set = (P_set+77.473)/0.4741  # (mA) Based on calibration
I_set = 0 # mA

daq_dev_info = DaqDeviceInfo(board_num)
print('Active DAQ device: ', daq_dev_info.product_name, ' (',
       daq_dev_info.unique_id, ')\n', sep='')

ao_info = daq_dev_info.get_ao_info()
ao_range = ao_info.supported_ranges[0]

ai_info = daq_dev_info.get_ai_info()
ai_range = ai_info.supported_ranges[0]

for n in range(0, len(PowerSweep)):
    P_set = PowerSweep[n]
    I_set = (P_set+77.473)/0.4741  # (mA) Based on calibration
    Vout = I_set/k_mod  # (V) Voltage output set point
    Vout_value = ul.from_eng_units(board_num, ao_range, Vout)  # Convert to 16bit

    ul.a_out(board_num, 0, ao_range, Vout_value)  # Send signal to DAQ Board
    Vin_value = ul.a_in(board_num, channel, ai_range)
    Vin_eng_units_value = ul.to_eng_units(board_num, ai_range, Vin_value)

    print(Vin_eng_units_value*k_mod)
    print(P_set)
    print(time.ctime())
    time.sleep(t_trans[n])

I_set = 0
Vout = I_set/k_mod  # (V) Voltage output set point
Vout_value = ul.from_eng_units(board_num, ao_range, Vout)  # Convert to 16bit
ul.a_out(board_num, 0, ao_range, Vout_value)  # Send signal to DAQ Board
print('Finished')
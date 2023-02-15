"""
Created on Wed Jan 19 15:32:48 2022

@author: DLAB
"""
from alicat import FlowController, FlowMeter

for port_name in ['COM6', 'COM7', 'COM8', 'COM9', 'COM10', 'COM11']:
    for address_name in ['A', 'B', 'C', 'D', 'E']:
        if FlowController.is_connected(port_name, address=address_name):
            print(port_name + ' ' + address_name + ' is flow controller')
            break
        elif FlowMeter.is_connected(port_name, address=address_name):
            print(port_name + ' ' + address_name + ' is flow meter')
            break

# for port_name in ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM11']:
#     for address_name in ['A', 'B', 'C', 'D', 'E']:
#         if FlowController.is_connected(port_name, address=address_name):
#             print(port_name + ' ' + address_name + ' is flow controller')
#         elif FlowMeter.is_connected(port_name, address=address_name):
#             print(port_name + ' ' + address_name + ' is flow meter')

# import sys
# import glob
# import serial


# def serial_ports():
#     """ Lists serial port names

#         :raises EnvironmentError:
#             On unsupported or unknown platforms
#         :returns:
#             A list of the serial ports available on the system
#     """
#     if sys.platform.startswith('win'):
#         ports = ['COM%s' % (i + 1) for i in range(256)]
#     elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
#         # this excludes your current terminal "/dev/tty"
#         ports = glob.glob('/dev/tty[A-Za-z]*')
#     elif sys.platform.startswith('darwin'):
#         ports = glob.glob('/dev/tty.*')
#     else:
#         raise EnvironmentError('Unsupported platform')

#     result = []
#     for port in ports:
#         try:
#             s = serial.Serial(port)
#             s.close()
#             result.append(port)
#         except (OSError, serial.SerialException):
#             pass
#     return result

# import serial.tools.list_ports
# print(list(serial.tools.list_ports.comports()))
# []

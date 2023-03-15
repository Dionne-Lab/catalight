"""
Port connection tester module returns the comport name/address of MFCs.

Utilizes the is_connected method of the alicat module's FlowController and
FlowMeter classes. Usual serial module to list all comports on computer, then
sweeps through every alphabetic letter in alphabet to checking for MFC
connections. Each comport loop breaks if a MFC is found. Prints summary at end.

Created on Wed Jan 19 15:32:48 2022
@author: Briley Bourgeois
"""
from string import ascii_uppercase as alphabet

import serial.tools.list_ports
from alicat import FlowController, FlowMeter

if __name__ == '__main__':
    comports = list(serial.tools.list_ports.comports())
    positive_cases = []

    print('Beginning search: This process will take several minutes')
    for port in comports:
        port_name = port.name
        for address_name in alphabet:
            test_case_str = (port_name + ' ' + address_name)
            if FlowController.is_connected(port_name, address=address_name):
                print(test_case_str + ' is flow controller')
                positive_cases.append(test_case_str + ' is flow controller\n')
                break
            elif FlowMeter.is_connected(port_name, address=address_name):
                print(test_case_str + ' is flow meter')
                positive_cases.append(test_case_str + ' is flow meter\n')
                break
            else:
                print(test_case_str + ' is not MFC')

    print('Search concluded. Results:')
    print(*positive_cases)

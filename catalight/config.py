"""Configuration file containing hardware setup specifc information."""

data_path = r"C:\Users\dionn\GC\GC_Data"
"""This is the folder in which experimental data will be saved"""


peaksimple_path = r"C:\Users\dionn\GC\Peak495Win10\Peak495Win10.exe"
"""This is the full path to Peaksimple .exe"""


mfc_list = [{'port': 'COM7', 'unit': 'A'},
            {'port': 'COM6', 'unit': 'B'},
            {'port': 'COM4', 'unit': 'C'},
            {'port': 'COM3', 'unit': 'D'},
            {'port': 'COM5', 'unit': 'E'}]
"""COM address info for mass flow controllers"""

heater_address = {'port': 'COM9', 'address': '1'}
"""COM address info for heater"""

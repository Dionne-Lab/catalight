# -*- coding: utf-8 -*-
"""
Created on Fri Jan  6 17:10:25 2023

@author: brile
"""


import os
import sys  # We need sys so that we can pass argv to QApplication

import analysis_tools
import matplotlib.pyplot as plt
from data_extractor import DataExtractor
from gcdata import GCData
from PyQt5.QtWidgets import QFileDialog

starting_dir = ("G:\Shared drives\Photocatalysis Projects\AgPd Polyhedra"
                "\Ensemble Reactor\\")

prompt = 'select all files to plot'
dialog = DataExtractor(starting_dir, '.ASC', data_depth=0)
if dialog.exec_() == DataExtractor.Accepted:
    file_list, data_labels = dialog.get_output()

plt.close('all')
fig, ax = plt.subplots()
analysis_tools.set_plot_style((5,3.65))
for filename, data_label in zip(file_list, data_labels):

    data = GCData(filename, basecorrect = False)
    datacorr = GCData(filename, basecorrect = True)
    ax.plot(data.time, data.signal, label=data_label)
    plt.xlim([2, 3.2])
    plt.legend()

# Standard figsize
# 1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
# 1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);

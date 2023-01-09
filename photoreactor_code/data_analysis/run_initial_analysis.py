# -*- coding: utf-8 -*-
"""
Created on Fri Jan  6 12:11:00 2023

@author: brile
"""
import os
import sys
import pandas as pd
import analysis_tools
import matplotlib.pyplot as plt
from PyQt5 import QtWidgets

# getting the name of the directory where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))

# Getting the parent directory name where the current directory is present.
parent = os.path.dirname(current)

# adding the parent directory to the sys.path.
sys.path.append(parent)

from experiment_control import Experiment

def plot_expts_in_folder(main_dir, calDF, target_molecule, mass_bal, reactant, figsize):
    kwargs = {'calDF': calDF,
              'target_molecule': target_molecule,
              'mass_bal': mass_bal,
              'reactant': reactant,
              'figsize': figsize}
    for dirpath, dirnames, filenames in os.walk(main_dir):
        for filename in filenames:
            if filename == 'expt_log.txt':
                log_path = os.path.join(dirpath, filename)
                expt_path = os.path.dirname(log_path)
                expt = Experiment()  # Initialize experiment obj
                expt.read_expt_log(log_path)  # Read expt parameters from log
                expt.update_save_paths(expt_path)  # update file paths

                (concentrations, avg, std) = analysis_tools.run_analysis(expt, calDF) # first run
                #(concentrations, avg, std) = load_results(expt)  # if you already ran analysis
                (ax1, ax2, ax3) = analysis_tools.plot_expt_summary(expt, **kwargs)

def get_dirs(starting_dir = None):
    dialog = QtWidgets.QFileDialog()
    dialog.setWindowTitle('Choose Directories')
    dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
    dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
    if starting_dir is not None:
        dialog.setDirectory(starting_dir)
    dialog.setGeometry(50, 100, 1000, 400)
    dialog.setViewMode(1)
    # This loop cycles through dialog and sets multi-item selection
    for view in dialog.findChildren(
        (QtWidgets.QListView, QtWidgets.QTreeView)):
        if isinstance(view.model(), QtWidgets.QFileSystemModel):
            view.setSelectionMode(
                QtWidgets.QAbstractItemView.ExtendedSelection)

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        expt_dirs = dialog.selectedFiles()
        return expt_dirs

if __name__ == "__main__":

    # User inputs
    ###########################################################################

    # Calibration Location Info:
    # Format [ChemID, slope, intercept, start, end]
    prompt = "Please select the desired calibration file"
    calibrations_folder = (r"G:\Shared drives\Ensemble Photoreactor"
                           "\Reactor Baseline Experiments\GC Calibration")
    calibration_path = QtWidgets.QFileDialog \
                                .getOpenFileName(None, prompt,
                                                 calibrations_folder,
                                                 "csv file (*.csv)")[0]

    calDF = pd.read_csv(calibration_path, delimiter=',', index_col='Chem ID')

    dirs_to_analyze = get_dirs('G:\Shared drives\Photocatalysis Projects')
    plt.ioff() # suppress plot windows
    for main_dir in dirs_to_analyze:
        plot_expts_in_folder(main_dir, calDF, target_molecule='c2h4',
                             mass_bal='c', reactant='c2h2', figsize=(4.35, 3.25))


    # Standard figsize
    # 1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
    # 1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);
    print('Finished!')

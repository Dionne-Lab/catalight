# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 17:28:48 2022

@author: brile
"""

# to actually run some analysis!

import os
import re
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from gcdata import GCData
from data_extractor import DataExtractor

# getting the name of the directory where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))

# Getting the parent directory name where the current directory is present.
parent = os.path.dirname(current)

# adding the parent directory to the sys.path.
sys.path.append(parent)

from experiment_control import Experiment

# Helper functions
##############################################################################

def get_bool(prompt):
    while True:
        acceptable_answers = {"true":True,
                              "false":False,
                              'yes':True,
                              'no':False}
        try:
           return acceptable_answers[input(prompt).lower()]
        except KeyError:
           print("Invalid input please enter True or False!")

def load_results(expt):
    fol = expt.results_path
    avg = pd.read_csv(os.path.join(fol, 'avg_conc.csv'), index_col=(0))
    std = pd.read_csv(os.path.join(fol, 'std_conc.csv'), index_col=(0))
    results = np.load(os.path.join(fol, 'results.npy'))
    return(results, avg, std)

def calculate(expt, reactant, s):
    results, avg, std = load_results(expt)
    unit = re.sub("\d+", "", avg.index[0])
    avg.drop('Over_Run_Data', errors='ignore', inplace=True)
    std.drop('Over_Run_Data', errors='ignore', inplace=True)
    x_data = avg.index.str.replace(r'\D', '', regex=True).astype(float)
    avg.index = x_data
    std.index = x_data

    # Calculations:
    C_Tot = avg.sum(axis=1)  # total conc of all molecules
    C_reactant = avg[reactant]  # total conc of reactant molecule
    X = (1 - C_reactant/C_Tot)*100  # conversion assuming 100% mol bal
    rel_err = std/avg
    X_err = ((rel_err**2).sum(axis=1))**(1/2)*rel_err[reactant]
    S = (avg[s[0]]/(C_Tot*X/100))*100  # selectivity
    S = S.fillna(0)
    results = pd.concat([X, S, X_err], axis=1)
    results.columns = ['Conversion', 'Selectivity', 'Error']
    return results

def plot_results(results_dict, figsize=(6.5, 4.5)):
    # Plotting
    ###########################################################################
    print('Plotting...')
    plt.close('all')

    if figsize[0] < 6:
        fontsize = [11, 14]
    elif figsize[0] > 7:
        fontsize = [16, 20]
    else:
        fontsize = [14, 18]

    # Some Plot Defaults
    plt.rcParams['axes.linewidth'] = 2
    plt.rcParams['lines.linewidth'] = 1.5
    plt.rcParams['xtick.major.size'] = 6
    plt.rcParams['xtick.major.width'] = 1.5
    plt.rcParams['ytick.major.size'] = 6
    plt.rcParams['ytick.major.width'] = 1.5
    plt.rcParams['figure.figsize'] = figsize
    plt.rcParams['font.size'] = fontsize[0]
    plt.rcParams['axes.labelsize'] = fontsize[1]

    # Initilize Conv and Selectivity plot
    figX, axX = plt.subplots()
    figS, axS = plt.subplots()

    for data_set in results_dict.items():
        data_label = data_set[0]
        results = data_set[1]
        X = results['Conversion']
        S = results['Selectivity']
        X_err = results['Error']*results['Conversion']
        S_err = results['Error']*results['Selectivity']
        X.plot(ax=axX, yerr=X_err, fmt='--o', label=data_label)
        S.plot(ax=axS, yerr=S_err, fmt='--^', label=data_label)

    axX.set_ylabel('Conversion [%]')
    axX.set_xlabel('Blank')
    axX.set_ylim([0, 100])
    plt.legend()
    plt.tight_layout()

    axS.set_ylabel('Selectivity [%]')
    axS.set_xlabel('Blank')
    axS.set_ylim([0, 100])
    plt.legend()
    plt.tight_layout()
    plt.show()


    return ((figX, axX), (figS, axS))


if __name__ == "__main__":


    dialog = DataExtractor()
    if dialog.exec_() == DataExtractor.Accepted:
        file_list, data_labels = dialog.get_output()

    results_dict = {}

    for expt_path, data_label in zip(file_list, data_labels):
        log_path = os.path.join(expt_path, 'expt_log.txt')
        expt = Experiment()  # Initialize experiment obj
        expt.read_expt_log(log_path)  # Read expt parameters from log
        expt.update_save_paths(expt_path)  # update file paths
        print(os.path.split(expt_path)[1])
        result = calculate(expt, 'c2h2', ['c2h4'])
        results_dict[data_label] = result
    plot_results(results_dict)
    # Standard figsize
    # 1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
    # 1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);
    print('Finished!')

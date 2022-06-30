# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 15:33:01 2022

@author: brile
"""
import re, os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from data_extractor import DataExtractor

def plot_results(file_list, s, reactant, figsize=(6.5, 4.5)):
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
    fig3, ax3 = plt.subplots()

    for file_path in file_list:
        avg = pd.read_csv(os.path.join(file_path, 'results', 'avg_conc.csv'), index_col=(0))
        std = pd.read_csv(os.path.join(file_path, 'results', 'std_conc.csv'), index_col=(0))
        x_data = avg.index.str.replace(r'\D', '').astype(float)
        unit = re.sub("\d+", "", avg.index[0])
        # Calculations:
        C_Tot = avg.sum(axis=1)  # total conc of all molecules
        C_reactant = avg[reactant]  # total conc of reactant molecule
        X = (1 - C_reactant/C_Tot)*100  # conversion assuming 100% mol bal
        rel_err = std/avg
        X_err = ((rel_err**2).sum(axis=1))**(1/2)*rel_err[reactant]
        S = (avg[s[0]]/(C_Tot*X/100))*100  # selectivity
        S = S.fillna(0)

        # Plotting:
        ax3.errorbar(x_data, X, yerr=X_err*X, fmt='--o')
        # X.iloc[0:len(x_data)].plot(ax=ax3, yerr=X_err*X, fmt='--o')
        # S.iloc[0:len(x_data)].plot(ax=ax3, yerr=X_err*S, fmt='--^')
    ax3.set_xlabel(unit)
    ax3.set_ylabel('Conv./Selec. [%]')
    plt.legend(['Conversion', 'Selectivity'])
    ax3.set_ylim([0, 100])
    plt.tight_layout()

    return (fig3, ax3)


# Sample Location Info:
main_dir = (r'G:\Shared drives\Photocatalysis Projects\AgPd Polyhedra'
            r'\Ensemble Reactor')

expt1 = (r'20220602_Ag5Pd95_6wt%_3.45mg_sasol900_300C_3hr\postreduction'
          r'\20220618temp_sweep_0.0mW_0.01C2H2_0.94Ar_0.05H2frac_50sccm')
expt2 = (r'20220602_Ag5Pd95_6wt%_3.45mg_sasol900_300C_3hr\postreduction'
          r'\20220618power_sweep_300K_0.01C2H2_0.94Ar_0.05H2frac_50sccm')
expt3 = (r'20220602_Ag5Pd95_6wt%_20.18mg_sasol900_300C_3hr\postreduction'
          r'\20220608temp_sweep_0.0mW_0.01C2H2_0.94Ar_0.05H2frac_50sccm')
expt4 = (r'20220602_Ag5Pd95_6wt%_20.18mg_sasol900_300C_3hr\postreduction'
          r'\20220608power_sweep_300K_0.01C2H2_0.94Ar_0.05H2frac_50sccm')
file_list = []
for expt_path in [expt1, expt2, expt3, expt4]:
    file_path = os.path.join(main_dir, expt_path)
    file_list.append(file_path)


# dialog = DataExtractor()
# if dialog.exec_() == DataExtractor.Accepted:
#     file_list, data_labels = dialog.get_output()

fig1, ax1 = plot_results([file_list[i] for i in [0, 2]], s=['c2h4'], reactant='c2h2')
fig2, ax2 = plot_results([file_list[i] for i in [1, 3]], s=['c2h4'], reactant='c2h2')
ax1.get_legend().remove()
ax1.set_xlabel('Temperature [K]')
ax1.set_ylabel('Conversion [%]')
ax2.get_legend().remove()
ax2.set_xlabel('Power [mW]')
ax2.set_ylabel('Conversion [%]')
fig1.show()
fig2.show()

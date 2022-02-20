# to actually run some analysis!

import os
import re
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from gcdata import GCData

# getting the name of the directory where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))

# Getting the parent directory name where the current directory is present.
parent = os.path.dirname(current)

# adding the parent directory to the sys.path.
sys.path.append(parent)

from experiment_control import Experiment

# Helper functions
##############################################################################


def list_FID(folder_path):
    """Returns the .ASC files for FID data in the specified path."""
    files_list = []
    for filename in sorted(os.listdir(folder_path)):
        # Only assessing files that end with specified filetype
        if (filename.endswith('.ASC')) & ('FID' in filename):
            # id = filename[:len(filename)-4] # Disregards the file type and run number
            # if id[:-2].endswith('FID'): # Only selects for FID entries
            files_list.append(filename)
    return files_list


def list_TCD(folder_path):
    """Returns the .ASC files for TCD data in the specified path."""
    files_list = []
    for filename in sorted(os.listdir(folder_path)):
        # Only assessing files that end with specified filetype
        if (filename.endswith('.ASC')) & ('TCD' in filename):
            files_list.append(filename)
    return files_list


def get_run_number(filename):
    """returns run number based on filename"""
    parts = filename.split('.')  # Seperate filename at each period
    # Second to last part always has run num
    run_num_part = parts[len(parts)-2]
    # \d digit; + however many; $ at end
    run_number = re.search(r'\d+$', run_num_part)
    return int(run_number.group()) if run_number else None


def analyze_cal_data(Expt1, calDF, figsize=(11, 6.5), force_zero=True):
    # do something
    print('Analyzing Calibration data')
    plt.close('all')

    # Returns raw counts with error bars for each chemical in each folder
    results, avg, std = run_analysis(Expt1, calDF)

    # if figsize[0] < 6:
    #     fontsize = [11, 14]
    # elif figsize[0] > 7:
    #     fontsize = [16, 20]
    # else:
    #     fontsize = [14, 18]

    # # Some Plot Defaults
    # plt.rcParams['axes.linewidth'] = 2
    # plt.rcParams['lines.linewidth'] = 1.5
    # plt.rcParams['xtick.major.size'] = 6
    # plt.rcParams['xtick.major.width'] = 1.5
    # plt.rcParams['ytick.major.size'] = 6
    # plt.rcParams['ytick.major.width'] = 1.5
    plt.rcParams['figure.figsize'] = figsize
    # plt.rcParams['font.size'] = fontsize[0]
    # plt.rcParams['axes.labelsize'] = fontsize[1]

    # Calculations:
    calchemIDs = calDF.index.to_numpy()  # get chem IDs from calibration files
    new_calibration = calDF.copy()

    n_rows = len(calchemIDs)//3
    n_cols = -(-len(calchemIDs)//n_rows)  # Gives Ceiling
    # Initilize run num plot
    fig1, subplots1 = plt.subplots(n_rows, n_cols)
    # Initilize ppm vs ind_var plot
    fig2, subplots2 = plt.subplots(n_rows, n_cols)

    calgas_flow = np.array([])
    for condition in avg.index:
        calgas_flow = np.append(calgas_flow,
                                float(re.findall(r"([\d.]*\d+)"+'CalGas',
                                                 condition, re.IGNORECASE)[0]))

    # Plotting:
    for chem_num in range(len(calchemIDs)):
        chemical = calchemIDs[chem_num]

        ind_results = results[:, chem_num, :]
        ind_results = ind_results[~np.isnan(ind_results)]
        ax1 = subplots1.ravel()[chem_num]
        ax1.plot(ind_results/1000, 'o', label=chemical)
        ax1.text(.5, .85, chemical,
                 horizontalalignment='center',
                 transform=ax1.transAxes)

        ax2 = subplots2.ravel()[chem_num]
        expected_ppm = calDF.loc[chemical, 'ppm']*calgas_flow
        ax2.errorbar(expected_ppm, avg[chemical]/1000, yerr=std[chemical]/1000, fmt='o')

        if force_zero:
            x_data = np.append(0, expected_ppm)
            y_data = np.append(0, avg[chemical].to_numpy())
            y_err = np.append(1e-19, std[chemical].to_numpy())
        else:
            x_data = expected_ppm
            y_data = avg[chemical].to_numpy()
            y_err = std[chemical].to_numpy()
        try:
            p, V = np.polyfit(x_data, y_data, 1, cov=True, w=1/y_err)
            m, b, err_m, err_b = (*p, np.sqrt(V[0][0]), np.sqrt(V[1][1]))
            x_fit = np.linspace(0, max(x_data), 100)

            ax2.plot(x_fit, (p[0]*x_fit+p[1])/1000, '--r')
            label = '\n'.join([chemical,
                               "m: %4.2f +/- %4.2f" % (m, err_m),
                               "b: %4.2f +/- %4.2f" % (b, err_b)])

            ax2.text(.02, .75, label,
                     horizontalalignment='left',
                     transform=ax2.transAxes, fontsize=8)
        except(np.linalg.LinAlgError):
            label = chemical + '\nBad Fit'
            ax2.text(.02, .75, label,
                     horizontalalignment='left',
                     transform=ax2.transAxes, fontsize=8)
        new_calibration.loc[chemical, 'slope':'err_intercept'] = [m, err_m, b, err_b]

    ax1 = fig1.add_subplot(111, frameon=False)
    # hide tick and tick label of the big axis
    ax1.tick_params(labelcolor='none', which='both',
                    top=False, bottom=False, left=False, right=False)
    ax1.set_xlabel("Run Number")
    ax1.set_ylabel('Counts/1000')

    ax2 = fig2.add_subplot(111, frameon=False)
    # hide tick and tick label of the big axis
    ax2.tick_params(labelcolor='none', which='both',
                    top=False, bottom=False, left=False, right=False)
    ax2.set_xlabel("ppm")
    ax2.set_ylabel('Counts/1000')

    # Figure Export
    fig1.savefig(os.path.join(Expt1.results_path, str(
        figsize[0])+'w_run_num_plot_individuals.svg'), format="svg")
    fig2.savefig(os.path.join(Expt1.results_path, str(
        figsize[0])+'w_calibration_plot.svg'), format="svg")
    new_calibration.to_csv(os.path.join(Expt1.results_path, 'calibration.csv'))

    return(subplots1, subplots2)


def run_analysis(Expt1, calDF, basecorrect='True'):
    # Analysis Loop
    # TODO add TCD part
    ##############################################################################
    print('Analyzing Data...')

    expt_data_fol = Expt1.data_path
    expt_results_fol = Expt1.results_path
    os.makedirs(expt_results_fol, exist_ok=True)  # Make dir if not there
    calchemIDs = calDF.index.to_numpy()  # get chem IDs from calibration files
    max_runs = 0
    step_path_list = []
    for dirpath, dirnames, filenames in os.walk(expt_data_fol):
        num_data_points = len(list_FID(dirpath))  # only looks at .ASC
        if not dirnames:  # determine bottom most dirs
            step_path_list.append(dirpath)
        if num_data_points > max_runs:  # Determines largest # of runs in any dir
            max_runs = num_data_points

    num_fols = len(step_path_list)
    num_chems = int(len(calchemIDs))
    condition = np.full(num_fols, 0, dtype=object)
    results = np.full((num_fols, num_chems+1, max_runs), np.nan)

    # Loops through the ind var step and calculates conc in each data file
    for step_path in step_path_list:
        step_num, step_val = os.path.basename(step_path).split(' ')
        step_num = int(step_num)-1
        data_list = list_FID(step_path)
        condition[step_num] = step_val
        conc = []
        for file in data_list:
            filepath = os.path.join(step_path, file)
            # data is an instance of a class, for signal use data.signal etc
            data = GCData(filepath, basecorrect=True)

            values = data.get_concentrations(calDF)
            conc.append(values.tolist())

        num_runs = len(conc)
        # [Condition x [Timestamps, ChemID] x run number]
        results[step_num, :, 0:num_runs] = np.asarray(conc).T

    # Results
    ###########################################################################
    avg_dat = np.nanmean(results[:, 1:, :], axis=2)
    avg = pd.DataFrame(avg_dat, columns=calchemIDs, index=condition)
    std_dat = np.nanstd(results[:, 1:, :], axis=2)
    std = pd.DataFrame(std_dat, columns=calchemIDs, index=condition)

    np.save(os.path.join(expt_results_fol, 'results'), results)
    avg.to_csv(os.path.join(expt_results_fol, 'avg_conc.csv'))
    std.to_csv(os.path.join(expt_results_fol, 'std_conc.csv'))
    return(results, avg, std)


def plot_results(Expt1, calDF, data_list, s, reactant, mass_bal='c', figsize=(6.5, 4.5)):
    # Plotting
    ###########################################################################
    print('Plotting...')
    plt.close('all')

    results, avg, std = data_list

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

    # Initilize run num plot
    fig1, ax1 = plt.subplots()
    # Calculations:
    calchemIDs = calDF.index  # get chem IDs from calibration files
    stoyk = pd.Series(0, index=calchemIDs)
    time_stamps = results[:, 0, :].reshape(-1)
    time_stamps = time_stamps[~np.isnan(time_stamps)]
    switch_to_hours = 2  # number of hours when axis changes from minutes
    if np.max(time_stamps) > (switch_to_hours*60*60):
        time_passed = (time_stamps-np.min(time_stamps))/60/60
        time_unit = 'hr'
    else:
        time_passed = (time_stamps-np.min(time_stamps))/60
        time_unit = 'min'

    # Plotting:
    for chemical in calchemIDs:
        chem_num = calchemIDs.get_loc(chemical)+1  # index 0 is timestamp
        # read number after 'c' in each chem name
        count = re.findall(mass_bal+r"(\d+)", chemical, re.IGNORECASE)
        if not count:
            if re.findall(mass_bal, chemical, re.IGNORECASE):
                count = 1
            else:
                count = 0
        else:
            count = int(count[0])

        stoyk[chemical] = count
        ind_results = results[:, chem_num, :]
        ind_results = ind_results[~np.isnan(ind_results)]
        ax1.plot(time_passed, ind_results, 'o', label=chemical)

    ax1.legend()
    plt.xlabel('Time ['+time_unit+']')
    # TODO add second x axis
    plt.ylabel('Conc [ppm]')
    plt.tight_layout()

    # Initilize ppm vs ind_var plot
    fig2, ax2 = plt.subplots()
    # Calculations:
    units = (Expt1.expt_list['Units']
             [Expt1.expt_list['Active Status']].to_string(index=False))
    try:
        x_data = getattr(Expt1, Expt1.ind_var)
    except AttributeError:
        order = np.argsort(time_passed)
        x_data = time_passed[order]
        avg = pd.DataFrame(results[0,1:,order])
        avg.columns = calchemIDs
        avg.index = x_data
        std = 0*avg
        units = time_unit

    mol_count = avg @ (np.array(stoyk, dtype=int))
    print(mass_bal)
    mol_count.columns = ['Total ' + mass_bal]
    mol_error = std @ (np.array(stoyk, dtype=int))

    # Plotting:
    avg.iloc[0:len(x_data)].plot(ax=ax2, marker='o', yerr=std)
    mol_count.iloc[0:len(x_data)].plot(ax=ax2, marker='o', yerr=mol_error.iloc[0:len(x_data)])
    ax2.set_xlabel(Expt1.ind_var + ' ['+units+']')
    ax2.set_ylabel('Conc (ppm)')
    plt.tight_layout()

    # Initilize Conv and Selectivity plot
    fig3, ax3 = plt.subplots()
    # Calculations:
    C_Tot = avg.sum(axis=1)  # total conc of all molecules
    C_reactant = avg[reactant]  # total conc of reactant molecule
    X = (1 - C_reactant/C_Tot)*100  # conversion assuming 100% mol bal
    rel_err = std/avg
    X_err = ((rel_err**2).sum(axis=1))**(1/2)*rel_err[reactant]
    S = (avg[s[0]]/(C_Tot*X/100))*100  # selectivity
    S = S.fillna(0)

    # Plotting:
    X.iloc[0:len(x_data)].plot(ax=ax3, yerr=X_err*X, fmt='--o')
    S.iloc[0:len(x_data)].plot(ax=ax3, yerr=X_err*S, fmt='--^')
    ax3.set_xlabel(Expt1.ind_var + ' ['+units+']')
    ax3.set_ylabel('Conv./Selec. [%]')
    plt.legend(['Conversion', 'Selectivity'])
    ax3.set_ylim([0, 100])
    plt.tight_layout()

    # Figure Export
    fig1.savefig(os.path.join(Expt1.results_path, str(
        figsize[0])+'w_run_num_plot.svg'), format="svg")
    fig2.savefig(os.path.join(Expt1.results_path, str(
        figsize[0])+'w_avg_conc_plot.svg'), format="svg")
    fig3.savefig(os.path.join(Expt1.results_path, str(
        figsize[0])+'w_Conv_Sel_plot.svg'), format="svg")

    return (ax1, ax2, ax3)


if __name__ == "__main__":

    # User inputs
    ###########################################################################

    # Calibration Location Info:
    # Format [ChemID, slope, intercept, start, end]

    # We need to put the calibration data somewhere thats accessible with a common path

    # calibration_path = ('/Users/ccarlin/Google Drive/Shared drives/'
    #                     'Photocatalysis Reactor/Reactor Baseline Experiments/'
    #                     'GC Calibration/calib_202012/HayD_FID_SophiaCal.csv')

    # calibration_path = ("G:\\Shared drives\\Photocatalysis Reactor\\"
    #                     "Reactor Baseline Experiments\\GC Calibration\\"
    #                     "calib_202012\\HayD_FID_Sophia_RawCounts.csv")

    calibration_path = ("G:\\Shared drives\\Photocatalysis Reactor\\"
                        "Reactor Baseline Experiments\\GC Calibration\\"
                        "20210930_DummyCalibration\\HayN_FID_C2H2_DummyCal.csv")

    # Sample Location Info:
    main_dir = (r'G:\Shared drives\Photocatalysis Projects\AgPd Polyhedra'
                r'\Ensemble Reactor\20220201_Ag95Pd5_2wt%_25.2mg_shaken')

    # Main Script
    ###########################################################################
    for dirpath, dirnames, filenames in os.walk(main_dir):
        for filename in filenames:
            if filename == 'expt_log.txt':
                log_path = os.path.join(dirpath, filename)
                expt_path = os.path.dirname(log_path)
                # import all calibration data
                calDF = pd.read_csv(
                    calibration_path, delimiter=',', index_col='Chem ID')
                Expt1 = Experiment()  # Initialize experiment obj
                Expt1.read_expt_log(log_path)  # Read expt parameters from log
                Expt1.update_save_paths(expt_path)  # update file paths

                (results, avg, std) = run_analysis(Expt1, calDF)
                (ax1, ax2, ax3) = plot_results(Expt1, calDF, (results, avg, std), s=['c2h4'], mass_bal='C',
                                               reactant='c2h2', figsize=(4.35, 3.25))
# Standard figsize
# 1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
# 1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);
    print('Finished!')

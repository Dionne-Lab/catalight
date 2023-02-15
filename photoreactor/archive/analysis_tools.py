"""
Helper functions to assist in the analysis of catalysis data.

To optimally use this module, data is expected to be organized by the
Experiment class. This ensure uniformity for processing. This module was
originally designed to work with gas chromatography data, but future
development should expand its functionality and generality to work with all
data types, and individual data types should be handled in their own classes,
such as GCData.
"""
import os
import pickle
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from photoreactor.data_analysis.gcdata import GCData
from photoreactor.equipment.experiment_control import Experiment


def list_matching_files(main_dirs, target, suffix):
    """
    Return files containing 'target' and ending in 'suffix' within a folder.

    Returns the full path of all files within the give folder path that contain
    the phrase 'target' and ends with 'suffix'. This function crawls the ENTIRE
    directory provided, inclusing all subfolders down to bottom depth.

    Parameters
    ----------
    main_dirs : list of str
        List of string paths to main directories to crawl for data.
        Can be a list of one to search a single directory.
    target : str
        String of target phrase for finding files.
    suffix : str
        String target for the file type to search for.

    Returns
    -------
    filepath_list : list of str
        List of filepaths ending with 'suffix' and containing 'target'
    """
    filepath_list = []
    for root in main_dirs:
        for dirpath, dirnames, filenames in os.walk(root):
            for filename in filenames:
                if (filename.endswith(suffix)) & (target in filename):
                    filepath = os.path.join(dirpath, filename)
                    filepath_list.append(filepath)
    return filepath_list

def list_expt_obj(file_paths):
    """
    Get list of experiments.

    Parameters
    ----------
    file_paths : list of str
        List of full paths to expt_log.txt files.

    Returns
    -------
    experiments : list of Experiment
        List of Experiment objects from provided filepaths.
    """
    experiments = []
    for log_path in file_paths:
        if filename == 'expt_log.txt':  # Double check filename is correct
            expt_path = os.path.dirname(log_path)
            expt = Experiment()  # Initialize experiment obj
            expt.read_expt_log(log_path)  # Read expt parameters from log
            expt.update_save_paths(expt_path)  # update file paths
            experiments.append(expt)
    return experiments

def build_results_dict(file_list, data_labels, reactant, target):
    """
    Generate a results dictionary containing [X, S, err] for given datasets.

    Parameters
    ----------
    file_list : list of str
        List of file paths to experiment folders then used to initiate
        experiment objects and calculate conversion and selectivity.
    data_labels : list of str
        List of data labels used for generating plot legends.
    reactant : str
        String identity of reactant molecule to track. Must match what exists
        in the calibration file exactly.
    target : str
        String identity of the target to use when calculating selectivity. Must
        match what exists in the calibration file exacly.

    Returns
    -------
    results_dict : dict
        Dictionary of results (produced by calculate_X_and_S) in the form
        {data label: result}
        where data label is a string with the desired legend label and
        result is a pandas.DataFrame with column headers
        ['Conversion', 'Selectivity', 'Error']
        This function is most easily used in conjunction with DataExtractor
        such as in the run_plot_comparison script.

    """
    results_dict = {}
    expt_list = list_expt_obj(file_list)
    for expt, data_label in zip(expt_list, data_labels):
        result = analysis_tools.calculate_X_and_S(expt, reactant, target)
        results_dict[data_label] = result
    return results_dict

def get_run_number(filename):
    """
    Return run number based on filename.

    Parameters
    ----------
    filename : str
        string possibly containing number ID at end

    Returns
    -------
    int or None
        returns number suffix if present from file name.

    """
    parts = filename.split('.')  # Seperate filename at each period
    # Second to last part always has run num
    run_num_part = parts[len(parts) - 2]
    # \d digit; + however many; $ at end
    run_number = re.search(r'\d+$', run_num_part)
    return int(run_number.group()) if run_number else None


def get_bool(prompt):
    """Convert common strings to bool."""
    while True:
        acceptable_answers = {"true": True,
                              "false": False,
                              'yes': True,
                              'no': False}
        try:
            return acceptable_answers[input(prompt).lower()]
        except KeyError:
            print("Invalid input please enter True or False!")


def load_results(expt):
    """
    Load analysis results of previously analyzed experiment.

    Parameters
    ----------
    expt : Experiment
        Experiment object that has data and has been analyzed.

    Returns
    -------
    concentrations : numpy.ndarray
        3D matrix of concentrations for each molecule, gc collection,
        and condition
        [Condition x [Timestamps, ChemID] x run number
    avg : pandas.DataFrame
        average concentration for each molecule and experiment condition
    std : pandas.DataFrame
        one standard deviation of concentration measurements
    """
    fol = expt.results_path
    avg = pd.read_csv(os.path.join(fol, 'avg_conc.csv'), index_col=(0))
    std = pd.read_csv(os.path.join(fol, 'std_conc.csv'), index_col=(0))
    concentrations = np.load(os.path.join(fol, 'concentrations.npy'))
    return(concentrations, avg, std)


def convert_index(dataframe):
    """
    Take in dataframe, convert index from string to float.

    If overrun data exists, drops those rows.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Pandas dataframe containing index with string labels

    Returns
    -------
    dataframe : pandas.DataFrame
        Same Pandas dataframe, now containing index with float labels
    """
    # scrub letters from first entry - old
    # unit = re.sub(r"\d+", "", dataframe.index[0])

    # very old data collected before automated control can have overflow data
    dataframe.drop('Over_Run_Data', errors='ignore', inplace=True)
    # remove letter and convert num string to float
    x_data = dataframe.index.str.replace(r'\D', '', regex=True).astype(float)
    dataframe.index = x_data
    return dataframe


def get_timepassed(concentrations, switch_to_hours=2):
    """
    Convert time stamps to array of cumulative time passed.

    Parameters
    ----------
    concentrations : numpy.ndarray
        3D matrix of concentrations for each molecule, gc collection,
        and condition
        [Condition x [Timestamps, ChemID] x run number
    switch_to_hours : float, optional
        Time in hours when the output should switch units to
        hours instead of minutes. The default is 2.

    Returns
    -------
    time_passed : numpy.ndarray
        Numpy array of cumulative time passed since the start of the experiment.
    time_unit : str
        Either 'min' or 'hr' based on the length of total time and parameters.

    """
    time_stamps = concentrations[:, 0, :].reshape(-1)
    time_stamps = time_stamps[~np.isnan(time_stamps)]

    if np.max(time_stamps) > (switch_to_hours * 60 * 60):
        time_passed = (time_stamps - np.min(time_stamps)) / 60 / 60
        time_unit = 'hr'
    else:
        time_passed = (time_stamps - np.min(time_stamps)) / 60
        time_unit = 'min'

    return time_passed, time_unit


def analyze_cal_data(expt, calDF, figsize=(6.5, 4.5), force_zero=True):
    """
    Run analysis on previously collected calibration data.

    Calibration data should look like a composition sweep experiment and a
    calibration data frame containing the gasses to be analyzed, their
    respective starting concentrations, and the elution time from the gc needs
    to be provided.

    Parameters
    ----------
    expt : Experiment
        Experiment object for already run calibration experiment
    calDF : pandas.DataFrame
        Formated DataFrame containing gc calibration data.
        Specific to control file used!
        Format [ChemID, slope, intercept, start, end, ppm]
    figsize : tuple, optional
        Desired size of output figure in inches (x,y), Default is (6.5, 4.5).
        figsize suggestions:
        1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
        1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);
    force_zero : bool, optional
        Add point (x=0, y=0) to data set. The default is True.

    Returns
    -------
    None.

    """
    print('Analyzing Calibration data')
    plt.close('all')

    # Returns raw counts with error bars for each chemical in each folder
    concentrations, avg, std = run_analysis(expt, calDF)
    set_plot_style(figsize)

    # Calculations:
    calchemIDs = calDF.index.to_numpy()  # get chem IDs from calibration files
    new_calibration = calDF.copy()

    n_rows = len(calchemIDs) // 3
    n_cols = -(-len(calchemIDs) // n_rows)  # Gives Ceiling
    # Initilize run num plot
    fig_run_num, run_num_plots = plt.subplots(n_rows, n_cols)
    # Initilize ppm vs expected ppm plot
    fig_calibration, calibration_plots = plt.subplots(n_rows, n_cols)

    calgas_flow = np.array([])
    for condition in avg.index:
        calgas_flow = np.append(calgas_flow,
                                float(re.findall(r"([\d.]*\d+)" + 'CalGas',
                                                 condition, re.IGNORECASE)[0]))

    # Plotting:
    for chem_num in range(len(calchemIDs)):
        chemical = calchemIDs[chem_num]

        # +1 offsets from timestamps in row 0
        ind_concentrations = concentrations[:, chem_num + 1, :]
        ind_concentrations = ind_concentrations[~np.isnan(ind_concentrations)]

        ax_run_num = run_num_plots.ravel()[chem_num]  # flattens to 1d array
        ax_run_num.plot(ind_concentrations / 1000, 'o', label=chemical)
        ax_run_num.text(.5, .85, chemical,
                        horizontalalignment='center',
                        transform=ax_run_num.transAxes)

        ax_calibration = calibration_plots.ravel()[chem_num]
        expected_ppm = calDF.loc[chemical, 'ppm'] * calgas_flow
        ax_calibration.errorbar(expected_ppm, avg[chemical] / 1000,
                                yerr=std[chemical] / 1000, fmt='o')

        if force_zero:
            x_data = np.append(0, expected_ppm)
            y_data = np.append(0, avg[chemical].to_numpy())
            y_err = np.append(1e-19, std[chemical].to_numpy())
        else:
            x_data = expected_ppm
            y_data = avg[chemical].to_numpy()
            y_err = std[chemical].to_numpy()
        try:
            p, V = np.polyfit(x_data, y_data, 1, cov=True, w=1 / y_err)
            m, b, err_m, err_b = (*p, np.sqrt(V[0][0]), np.sqrt(V[1][1]))
            x_fit = np.linspace(0, max(x_data), 100)

            # add fit to plot
            ax_calibration.plot(x_fit, (p[0] * x_fit + p[1]) / 1000, '--r')
            label = '\n'.join([chemical,
                               "m: %4.2f +/- %4.2f" % (m, err_m),
                               "b: %4.2f +/- %4.2f" % (b, err_b)])

            ax_calibration.text(.02, .75, label,
                                horizontalalignment='left',
                                transform=ax_calibration.transAxes, fontsize=8)
        except(np.linalg.LinAlgError):
            label = chemical + '\nBad Fit'
            ax_calibration.text(.02, .75, label,
                                horizontalalignment='left',
                                transform=ax_calibration.transAxes, fontsize=8)
        new_calibration.loc[chemical, 'slope':'err_intercept'] = [m, err_m,
                                                                  b, err_b]

    ax_run_num = fig_run_num.add_subplot(111, frameon=False)
    # hide tick and tick label of the big axis
    ax_run_num.tick_params(labelcolor='none', which='both',
                           top=False, bottom=False, left=False, right=False)
    ax_run_num.set_xlabel("Run Number")
    ax_run_num.set_ylabel('Counts/1000')

    ax_calibration = fig_calibration.add_subplot(111, frameon=False)
    # hide tick and tick label of the big axis
    ax_calibration.tick_params(labelcolor='none', which='both',
                               top=False, bottom=False, left=False, right=False)
    ax_calibration.set_xlabel("ppm")
    ax_calibration.set_ylabel('Counts/1000')

    # Figure Export
    fig_run_num_path = os.path.join(expt.results_path,
                                    str(figsize[0])
                                    + 'w_run_num_plot_individuals')
    fig_calibration_path = os.path.join(expt.results_path,
                                        str(figsize[0])
                                        + 'w_calibration_plot')

    fig_run_num.savefig(fig_run_num_path + '.svg', format="svg")
    fig_calibration.savefig(fig_calibration_path + '.svg', format="svg")
    new_calibration.to_csv(os.path.join(expt.results_path, 'calibration.csv'))

    pickle.dump(fig_run_num, open(fig_run_num_path + '.pickle', 'wb'))
    pickle.dump(fig_calibration, open(fig_calibration_path + '.pickle', 'wb'))

    return(run_num_plots, calibration_plots)


def run_analysis(expt, calDF, basecorrect='True', savedata='True'):
    """
    Compute the concentrations, averages, and error from GC runs.

    Sweeps gc data in an experiment data directory and computes ppm
    concentrations for every requested molecules in the .asc files. Returns
    a 3D matrix of concentrations, a 2D matrix of avg concentrations for each
    experimental condition, and a 2D matrix of errors (1 standard deviation)

    Parameters
    ----------
    expt : Experiment
        Experiment object for desired analysis.
    calDF : pandas.DataFrame
        Formated DataFrame containing gc calibration data.
        Specific to control file used!
        Format [ChemID, slope, intercept, start, end]
    basecorrect : bool, optional
        Indicates whether or not to baseline correct individual gc data.
        The default is 'True'.
    savedata : bool, optional
        Indicates whether or not to save data. The default is 'True'.

    Returns
    -------
    concentrations : numpy.ndarray
        3D matrix of concentrations for each molecule, gc collection,
        and condition
        [Condition x [Timestamps, ChemID] x run number
    avg : pandas.DataFrame
        average concentration for each molecule and experiment condition
    std : pandas.DataFrame
        one standard deviation of concentration measurements

    """
    # Analysis Loop
    # TODO add TCD part
    ##############################################################################
    print('Analyzing Data...')

    expt_data_fol = expt.data_path
    expt_results_fol = expt.results_path
    os.makedirs(expt_results_fol, exist_ok=True)  # Make dir if not there
    calchemIDs = calDF.index.to_numpy()  # get chem IDs from calibration files
    max_runs = 0
    step_path_list = []
    for dirpath, dirnames, filenames in os.walk(expt_data_fol):
        # only looks at .ASC
        num_data_points = len((dirpath, 'FID', '.asc'))

        # determine bottom most dirs
        if not dirnames:
            step_path_list.append(dirpath)

        # Determines largest # of runs in any dir
        if num_data_points > max_runs:
            max_runs = num_data_points

    # Preallocate empty numpy array with NAN values
    num_fols = len(step_path_list)
    num_chems = int(len(calchemIDs))
    condition = np.full(num_fols, 0, dtype=object)
    concentrations = np.full((num_fols, num_chems + 1, max_runs), np.nan)

    # Loops through the ind var step and calculates conc in each data file
    for step_path in step_path_list:
        step_num, step_val = os.path.basename(step_path).split(' ')
        step_num = int(step_num) - 1
        data_list = list_matching_files(step_path, 'FID', '.asc')
        condition[step_num] = step_val
        conc = []
        for file in data_list:
            # data is an instance of a class, for signal use data.signal etc
            data = GCData(filepath, basecorrect=True)

            values = data.get_concentrations(calDF)
            conc.append(values.tolist())

        num_runs = len(conc)
        # [Condition x [Timestamps, ChemID] x run number]
        concentrations[step_num, :, 0:num_runs] = np.asarray(conc).T

    units = (expt.expt_list['Units']
             [expt.expt_list['Active Status']].to_string(index=False))
    idx_name = (expt.ind_var + ' [' + units + ']')  # Sweep Parameter
    # Redefine condition list as pandas index so we can assign a name
    condition = pd.Index(condition, name=idx_name)

    # Results
    ###########################################################################
    avg_dat = np.nanmean(concentrations[:, 1:, :], axis=2)
    avg = pd.DataFrame(avg_dat, columns=calchemIDs, index=condition)
    std_dat = np.nanstd(concentrations[:, 1:, :], axis=2)
    std = pd.DataFrame(std_dat, columns=calchemIDs, index=condition)
    if savedata:
        np.save(os.path.join(expt_results_fol, 'concentrations'), concentrations)
        avg.to_csv(os.path.join(expt_results_fol, 'avg_conc.csv'))
        std.to_csv(os.path.join(expt_results_fol, 'std_conc.csv'))
    return(concentrations, avg, std)


def calculate_X_and_S(expt, reactant, target_molecule):
    """
    Calculate conversion and selectivity for analyzed GC data.

    Parameters
    ----------
    expt : Experiment
        Experiment object which has data and has been analyzed
        (i.e. has avg_conc.csv etc.)
    reactant : str
        String identity of reactant molecule to track. Must match what exists
        in the calibration file exactly.
    target_molecule : str
        String identity of the target to use when calculating selectivity. Must
        match what exists in the calibration file exacly.

    Returns
    -------
    results : pandas.DataFrame
        DataFrame with column header ['Conversion', 'Selectivity', 'Error']
        Error is one standard deviation.

    """
    concentrations, avg, std = load_results(expt)
    C_Tot = avg.sum(axis=1)  # total conc of all molecules
    C_reactant = avg[reactant]  # total conc of reactant molecule
    X = (1 - C_reactant / C_Tot) * 100  # conversion assuming 100% mol bal
    rel_err = std / avg
    X_err = ((rel_err**2).sum(axis=1))**(1 / 2) * rel_err.max(axis=1)
    S = (avg[target_molecule] / (C_Tot * X / 100)) * 100  # selectivity
    S = S.fillna(0)
    results = pd.concat([X, S, X_err], axis=1)
    results.columns = ['Conversion', 'Selectivity', 'Error']
    return results


def set_plot_style(figsize=(6.5, 4.5)):
    """
    Update default plot styles. Varies font size with figure size.

    Parameters
    ----------
    figsize : tuple, optional
        Desired size of output figure in inches (x,y), Default is (6.5, 4.5).
        figsize suggestions:
        1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
        1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);
    """
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
    # plt.rcParams['text.usetex'] = False
    plt.rcParams['svg.fonttype'] = 'none'


def plot_expt_summary(expt, calDF, reactant, target_molecule,
                      mole_bal='c', figsize=(6.5, 4.5), savedata='True'):
    """
    Call 'typical' plotting functions and save output to results path.

    Plots and saves "run_num", "ppm", and "X and S" for given experiment.
    run_num: ppm concentration as a function of run number
    ppm: average ppm concentration w/ error for each experiment condition
    X and S: Plots the average convertion and selectivity as a function of
    experimental condition

    If savedata=True, will save figures as both .svg and .pickle

    Parameters
    ----------
    expt : Experiment
        Experiment object which has data and has been analyzed
        (i.e. has avg_conc.csv etc.)
    calDF : pandas.DataFrame
        Formated DataFrame containing gc calibration data.
        Specific to control file used!
        Format [ChemID, slope, intercept, start, end]
    reactant : str
        String identity of reactant molecule to track. Must match what exists
        in the calibration file exactly.
    target_molecule : str
        String identity of the target to use when calculating selectivity. Must
        match what exists in the calibration file exacly.
    mole_bal : str, optional
        Code will perform a mole balance for the element provided.
        The default is 'c'. (i.e. carbon balance)
    figsize : tuple, optional
         Desired size of output figure in inches (x,y), Default is (6.5, 4.5).
         figsize suggestions:
         1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
         1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);
    savedata : bool, optional
        Indicates whether or not to save data. The default is 'True'.

    Returns
    -------
    ax1 : :func:`matplotlib.pyplot.axis`
        Axis handle for "run_num" plot
    ax2 : `matplotlib.pyplot.axis`
        Axis handle for "ppm" plot
    ax3 : matplotlib.pyplot.axis
        Axis handle for "X and S" plot

    """
    # Plotting
    ###########################################################################
    print('Plotting...')
    plt.close('all')

    set_plot_style(figsize)
    fig1, ax1 = plot_run_num(expt, calDF, mole_bal)
    fig2, ax2 = plot_ppm(expt)
    fig3, ax3 = plot_X_and_S(expt)

    # Figure Export
    if savedata:
        fig1_path = os.path.join(expt.results_path,
                                 str(figsize[0]) + 'w_run_num_plot')
        fig2_path = os.path.join(expt.results_path,
                                 str(figsize[0]) + 'w_avg_conc_plot')
        fig3_path = os.path.join(expt.results_path,
                                 str(figsize[0]) + 'w_Conv_Sel_plot')

        fig1.savefig(fig1_path + '.svg', format="svg")
        fig2.savefig(fig2_path + '.svg', format="svg")
        fig3.savefig(fig3_path + '.svg', format="svg")

        pickle.dump(fig1, open(fig1_path + '.pickle', 'wb'))
        pickle.dump(fig2, open(fig2_path + '.pickle', 'wb'))
        pickle.dump(fig3, open(fig3_path + '.pickle', 'wb'))

    return (ax1, ax2, ax3)


def plot_run_num(expt, calDF, switch_to_hours=2):
    """
    Plot the individual concentrations for each molecule vs. run number.

    Parameters
    ----------
    expt : Experiment
        Experiment object which has data and has been analyzed
        (i.e. has avg_conc.csv etc.)
    calDF : pandas.DataFrame
        Formated DataFrame containing gc calibration data.
        Specific to control file used!
        Format [ChemID, slope, intercept, start, end]
    switch_to_hours : float, optional
        Time in hours when the output should switch units to
        hours instead of minutes. The default is 2.

    Returns
    -------
    fig : matplotlib.pyplot.figure
        Figure handle for "run_num" plot
    ax : matplotlib.pyplot.axis
        Axis handle for "run_num" plot
    """
    # Initilize run num plot
    fig, ax = plt.subplots()
    concentrations, avg, std = load_results(expt)
    # Calculations:
    calchemIDs = calDF.index  # get chem IDs from calibration files
    time_passed, time_unit = get_timepassed(concentrations, switch_to_hours)

    # use regex to determine number of carbons (or other) in molecule name
    for chemical in calchemIDs:
        chem_num = calchemIDs.get_loc(chemical) + 1  # index 0 is timestamp
        # Concentrations for individual chemical
        ind_concentrations = concentrations[:, chem_num, :]
        ind_concentrations = ind_concentrations[~np.isnan(ind_concentrations)]
        ax.plot(time_passed, ind_concentrations, 'o', label=chemical)

    ax.legend()
    plt.xlabel('Time [' + time_unit + ']')
    # TODO add second x axis as run number instead of time
    plt.ylabel('Conc [ppm]')
    plt.tight_layout()
    return (fig, ax)


def plot_ppm(expt, concentrations, calDF, mole_bal='c', switch_to_hours=2):
    """
    Plot average concentration in ppm for each molecule vs reaction condition.

    Parameters
    ----------
    expt : Experiment
        Experiment object which has data and has been analyzed
        (i.e. has avg_conc.csv etc.)
    concentrations : numpy.ndarray
        3D matrix of concentrations for each molecule, gc collection,
        and condition
        [Condition x [Timestamps, ChemID] x run number
    calDF : pandas.DataFrame
        Formated DataFrame containing gc calibration data.
        Specific to control file used!
        Format [ChemID, slope, intercept, start, end]
    mole_bal : str, optional
        Code will perform a mole balance for the element provided.
        The default is 'c'. (i.e. carbon balance)
    switch_to_hours : float, optional
        Time in hours when the output should switch units to
        hours instead of minutes. The default is 2.

    Returns
    -------
    fig : matplotlib.pyplot.figure
        Figure handle for "ppm" plot
    ax : matplotlib.pyplot.axis
        Axis handle for "ppm" plot
    """
    # Initilize ppm vs ind_var plot
    fig, ax = plt.subplots()
    concentrations, avg, std = load_results(expt)
    calchemIDs = calDF.index  # get chem IDs from calibration files
    time_passed, time_unit = get_timepassed(concentrations, switch_to_hours)
    units = (expt.expt_list['Units']
             [expt.expt_list['Active Status']].to_string(index=False))
    try:
        x_data = getattr(expt, expt.ind_var)
    except AttributeError:  # Fails for stability test
        order = np.argsort(time_passed)
        x_data = time_passed[order]
        avg = pd.DataFrame(concentrations[0, 1:, order])
        avg.columns = calchemIDs
        avg.index = x_data
        std = 0 * avg
        units = time_unit

    if units == 'frac':
        avg.index = avg.index.str.replace('_', '\n')
        avg.index = avg.index.str.replace('frac', '')
        std.index = std.index.str.replace('_', '\n')
        std.index = std.index.str.replace('frac', '')
    else:
        avg = convert_index(avg)
        std = convert_index(std)

    stoyk = pd.Series(0, index=calchemIDs)
    # use regex to determine number of carbons (or other) in molecule name
    for chemical in calchemIDs:
        chem_num = calchemIDs.get_loc(chemical) + 1  # index 0 is timestamp
        # read number after 'c' in each chem name
        count = re.findall(mole_bal + r"(\d+)", chemical, re.IGNORECASE)
        if not count:
            if re.findall(mole_bal, chemical, re.IGNORECASE):
                count = 1
            else:
                count = 0
        else:
            count = int(count[0])

        stoyk[chemical] = count

    mol_count = avg @ (np.array(stoyk, dtype=int))
    mol_count.columns = ['Total ' + mole_bal]
    mol_error = std @ (np.array(stoyk, dtype=int))

    # Plotting:
    avg.iloc[0:len(x_data)].plot(ax=ax, marker='o', yerr=std)
    mol_count.iloc[0:len(x_data)].plot(ax=ax, marker='o', yerr=mol_error.iloc[0:len(x_data)])
    ax.set_xlabel(expt.ind_var + ' [' + units + ']')
    ax.set_ylabel('Conc (ppm)')
    # ax.set_xticklabels(avg.iloc[0:len(x_data)], rotation=90)
    plt.tight_layout()
    return (fig, ax)


def plot_X_and_S(expt, reactant, target_molecule):
    """
    Plot conversion and selectivity vs reaction condition with error.

    This method will call calculate_X_and_S() to generate the plotting values.

    Parameters
    ----------
    expt : Experiment
        Experiment object which has data and has been analyzed
        (i.e. has avg_conc.csv etc.)
    reactant : str
        String identity of reactant molecule to track. Must match what exists
        in the calibration file exactly.
    target_molecule : str
        String identity of the target to use when calculating selectivity. Must
        match what exists in the calibration file exacly.

    Returns
    -------
    fig : matplotlib.pyplot.figure
        Figure handle for "X and S" plot
    ax : matplotlib.pyplot.axis
        Axis handle for "X and S" plot

    """
    # Initilize Conv and Selectivity plot
    fig, ax = plt.subplots()
    results = calculate_X_and_S(expt, reactant, target_molecule)
    units = (expt.expt_list['Units']
             [expt.expt_list['Active Status']].to_string(index=False))
    X = results['Conversion']
    S = results['Selectivity']
    X_err = results['Error'] * results['Conversion']
    S_err = results['Error'] * results['Selectivity']
    X.plot(ax=ax, yerr=X_err, fmt='--ok')
    S.plot(ax=ax, yerr=S_err, fmt='--^r')
    ax.set_xlabel(expt.ind_var + ' [' + units + ']')
    ax.set_ylabel('Conv./Selec. [%]')
    plt.legend(['Conversion', 'Selectivity'])
    ax.set_ylim([0, 105])
    plt.tight_layout()
    return (fig, ax)


def multiplot_X_and_S(results_dict, figsize=(6.5, 4.5)):
    """
    Seperately plot 1) conversion and 2) selectivity for multiple experiments.

    Produces two plots:
        (1) conversion vs reaction condition
        (2) selectivity vs reaction condition

    Each plot can have multiple experiments listed. The independent variable
    should be the same between all experiments provided.

    Parameters
    ----------
    results_dict : dict
        Dictionary of results (produced by calculate_X_and_S) in the form
        {data label: result}
        where data label is a string with the desired legend label and
        result is a pandas.DataFrame with column headers
        ['Conversion', 'Selectivity', 'Error']
        This function is most easily used in conjunction with DataExtractor
        such as in the run_plot_comparison script.
    figsize : tuple, optional
        Desired size of output figure in inches (x,y), Default is (6.5, 4.5).
        figsize suggestions:
        1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
        1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);

    Returns
    -------
    tuple of tuple of (matplotlib.pyplot.figure, matplotlib.pyplot.axis)
        two tuples, each containing the (figure, axis) handles for the
        conversion and selectivity plots, respectively.

    """
    # Initilize Conv and Selectivity plots
    # Note: if desired, results_dict could instead be expt_dict and
    # calculate_X_and_S() called within this function
    figX, axX = plt.subplots()
    figS, axS = plt.subplots()

    for data_set in results_dict.items():
        data_label = data_set[0]
        results = data_set[1]
        X = results['Conversion']
        S = results['Selectivity']
        X_err = results['Error'] * results['Conversion']
        S_err = results['Error'] * results['Selectivity']
        X.plot(ax=axX, yerr=X_err, fmt='--o', label=data_label)
        S.plot(ax=axS, yerr=S_err, fmt='--^', label=data_label)

    axX.set_ylabel('Conversion [%]')
    axX.set_xlabel('Blank')
    axX.set_ylim([0, 105])
    plt.legend()
    figX.tight_layout()

    axS.set_ylabel('Selectivity [%]')
    axS.set_xlabel('Blank')
    axS.set_ylim([0, 105])
    plt.legend()
    figS.tight_layout()
    figX.show()
    figS.show()

    return ((figX, axX), (figS, axS))


def multiplot_X_vs_S(results_dict, figsize=(6.5, 4.5)):
    """
    Produce a combo plot of selectivity as a function of conversion.

    This function can compare multiple experiments, and the independent
    variables do not need to match.

    Parameters
    ----------
    results_dict : dict
        Dictionary of results (produced by calculate_X_and_S) in the form
        {data label: result}
        where data label is a string with the desired legend label and
        result is a pandas.DataFrame with column headers
        ['Conversion', 'Selectivity', 'Error']
        This function is most easily used in conjunction with DataExtractor
        such as in the run_plot_comparison script.
    figsize : tuple, optional
        Desired size of output figure in inches (x,y), Default is (6.5, 4.5).
        figsize suggestions:
        1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
        1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);

    Returns
    -------
    fig : matplotlib.pyplot.figure
        Figure handle for "X vs S" plot
    ax : matplotlib.pyplot.axis
        Axis handle for "X vs S" plot

    """
    print('Plotting...')
    plt.close('all')

    set_plot_style(figsize)
    # Initilize Conv and Selectivity plot
    fig, ax = plt.subplots()

    for data_set in results_dict.items():
        data_label = data_set[0]
        results = data_set[1]
        X = results['Conversion']
        S = results['Selectivity']
        X_err = results['Error'] * results['Conversion']
        S_err = results['Error'] * results['Selectivity']
        ax.plot(X, S, '--o', label=data_label)
        # TODO implement x and y error bars

    ax.set_ylabel('Selectivity [%]')
    ax.set_xlabel('Conversion [%]')
    ax.set_xlim([0, 105])
    ax.set_ylim([0, 105])
    plt.legend()
    fig.tight_layout()
    fig.show()
    return (fig, ax)


def open_pickled_fig(fig_path):
    """
    Open a pickled figure for editting.

    Parameters
    ----------
    fig_path : str
        Path to .pickle file. Must be matplotlib.pyplot.figure

    Returns
    -------
    fig : matplotlib.pyplot.figure
        Figure handle for plot
    ax : matplotlib.pyplot.axis
        Axis handle for plot

    """
    plt.rcParams['svg.fonttype'] = 'none'
    fig = pickle.load(open(fig_path, 'rb'))
    ax = fig.get_axes()[0]
    fig.show()  # Show the figure, edit it, etc.!
    return (fig, ax)

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

    calibration_path = ("G:\\Shared drives\\Ensemble Photoreactor\\"
                        "Reactor Baseline Experiments\\GC Calibration\\"
                        "20210930_DummyCalibration\\HayN_FID_C2H2_DummyCal.csv")

    # # Sample Location Info:
    # root = (r'G:\Shared drives\Photocatalysis Projects\AgPd Polyhedra'
    #             r'\Ensemble Reactor\20220602_Ag5Pd95_6wt%_3.45mg_sasol900_300C_3hr')
    # # dir_list = ['20220602_Ag5Pd95_6wt%_20.18mg_sasol900_300C_3hr',
    # #             '20220602_Ag5Pd95_6wt%_3.45mg_sasol900_300C_3hr',
    # #             '20220201_Ag95Pd5_6wt%_20mg_sasol',
    # #             '20220201_Ag95Pd5_6wt%_3.5mg_sasol']

    # dir_list = ['postreduction']
    # plt.ioff() # suppress plot windows
    # for dir_name in dir_list:
    #     main_dir = os.path.join(root, dir_name)
    main_dir = r"G:\Shared drives\Photocatalysis Projects\AgPd Polyhedra\Ensemble Reactor\20220602_Ag5Pd95_6wt%_3.45mg_sasol900_300C_3hr\postreduction\20220618comp_sweep_340K_0.0mW_50sccm"
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
                expt = Experiment()  # Initialize experiment obj
                expt.read_expt_log(log_path)  # Read expt parameters from log
                expt.update_save_paths(expt_path)  # update file paths

                (concentrations, avg, std) = run_analysis(expt, calDF)  # first run
                # (concentrations, avg, std) = load_results(expt)  # if you already ran analysis
                (ax1, ax2, ax3) = plot_expt_summary(expt,
                                                    calDF,
                                                    target_molecule='c2h4',
                                                    mole_bal='C',
                                                    reactant='c2h2',
                                                    figsize=(6.5, 4.5))
# Standard figsize
# 1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
# 1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);
    print('Finished!')

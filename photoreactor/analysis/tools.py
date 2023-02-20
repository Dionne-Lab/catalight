"""
Tools to help with performing data analysis.

These were originally built specifically for managing and interacting with FID
gas chromatograms. Future development should treat data sets as ambiguously as
possible so any data types (e.g. mass spec, FTIR) can utilize the same tools.
Created on Mon Feb  6 11:46:49 2023.
@author: Briley Bourgeois
"""
import os
import pickle
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import photoreactor.analysis.plotting as plotting
from photoreactor.analysis.gcdata import GCData
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
    if isinstance(main_dirs, str):
        main_dirs = [main_dirs]  # If user supplies str, convert to 1 item list
    filepath_list = []
    for root in main_dirs:
        for dirpath, dirnames, filenames in os.walk(root):
            for filename in filenames:
                if (filename.lower().endswith(suffix.lower())
                        & (target.lower() in filename.lower())):
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
        if log_path == 'expt_log.txt':  # Double check filename is correct
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
        result = calculate_X_and_S(expt, reactant, target)
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
    run_num_plots : matplotlib.pyplot.axis
        Axis handle for "run_num" plot
    calibration_plots : matplotlib.pyplot.axis
        Axis handle for plots showing expected ppm vs measured counts

    """
    print('Analyzing Calibration data')
    plt.close('all')

    # Returns raw counts with error bars for each chemical in each folder
    concentrations, avg, std = run_analysis(expt, calDF)
    plotting.set_plot_style(figsize)

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
        for filepath in data_list:
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

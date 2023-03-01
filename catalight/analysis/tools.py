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
from math import sqrt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from catalight.analysis.gcdata import GCData
from catalight.equipment.experiment_control import Experiment


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
    file_paths : list[str]
        List of full paths to expt_log.txt files.

    Returns
    -------
    experiments : list[Experiment]
        List of Experiment objects from provided filepaths.
    """
    experiments = []
    # If user enters one filepath as str, convert to list for them.
    if isinstance(file_paths, str):
        file_paths = [file_paths]

    for log_path in file_paths:
        # Double check filename is correct
        if os.path.basename(log_path) == 'expt_log.txt':
            expt_path = os.path.dirname(log_path)
            expt = Experiment()  # Initialize experiment obj
            expt.read_expt_log(log_path)  # Read expt parameters from log
            expt.update_save_paths(expt_path)  # update file paths
            experiments.append(expt)
        else:
            print('Path other than expt_log.txt passed to list_expt_obj()')
    return experiments


def build_results_dict(file_list, data_labels, reactant, target):
    """
    Generate a results dictionary of X/S and data labels for paths given.

    Results dict contains [X, S, X Error, S Error] for given datasets and
    labels typically for use with plotting.

    Parameters
    ----------
    file_list : list of str
        List of file paths to experiment folders or experiment log paths then
        used to initiate experiment objects and calculate conversion and
        selectivity.
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
        ['Conversion', 'Selectivity', 'X Error', 'S Error']
        This function is most easily used in conjunction with DataExtractor
        such as in the run_plot_comparison script.

    """
    results_dict = {}
    # If the file_list is expt folders, convert to experiment log paths
    if (not file_list[0].endswith('expt_log.txt')
            and os.path.isfile(os.path.join(file_list[0], 'expt_log.txt'))):
        for n in range(len(file_list)):
            file_list[n] = os.path.join(file_list[n], 'expt_log.txt')
    elif file_list[0].endswith('expt_log.txt'):
        # Atleast first file is ok to move on
        pass
    else:
        msg = 'Item 1 of file_list is not experiment log or experiment folder'
        raise AttributeError(msg)

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
    return (concentrations, avg, std)


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


def get_timepassed(concentrations, switch_to_hours=2, expt=None):
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
    numpy.ndarray
        Numpy array of cumulative time passed since the start of experiment.
    str
        Either 'min' or 'hr' based on the length of total time and parameters.

    """
    time_stamps = concentrations[:, 0, :].reshape(-1)
    time_stamps = time_stamps[~np.isnan(time_stamps)]

    # Experiments after 20230225 save w/ timestamp
    if isinstance(expt.start_time, float):
        start_time = expt.start_time

    else:  # Method before 20230225 (less accurate)
        start_time = np.min(time_stamps)

    if np.max(time_stamps) > (switch_to_hours * 60 * 60):
        time_passed = (time_stamps - start_time) / 60 / 60
        time_unit = 'hr'
    else:
        time_passed = (time_stamps - start_time) / 60
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
    print('Analyzing calibration data')
    plt.close('all')

    # Returns raw counts with error bars for each chemical in each folder
    concentrations, avg, std = run_analysis(expt, calDF)
    # plotting.set_plot_style(figsize)
    plt.rcParams['figure.figsize'] = figsize
    plt.rcParams['svg.fonttype'] = 'none'

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
        ax_calibration.errorbar(avg[chemical] / 1000, expected_ppm,
                                xerr=std[chemical] / 1000, fmt='o')
        ax_calibration.ticklabel_format(axis='both', style='sci',
                                        scilimits=[-2, 2])

        # Fit w/ counts as 'y' and 'y_err'
        if force_zero:  # Add point (0, 0) w/ infinitesimal error
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

            # Convert linear fit of ppm vs counts
            # to linear fit of counts vs ppm (flip axes)
            m = 1 / m
            err_m = err_m
            # Propogate error using error propogation formula
            b = b / m
            err_b = sqrt(err_b**2 + b**2 * err_m**2) / m

            counts_fit = np.linspace(0, max(y_data), 100)
            ppm_fit = m * counts_fit + b

            # add fit to plot
            ax_calibration.plot(counts_fit / 1000, ppm_fit, '--r')
            fit_label = '\n'.join(["m: %4.2f\n+/- %4.2f" % (m, err_m),
                                   "b: %4.2f\n+/- %4.2f" % (b, err_b)])

            ax_calibration.text(.02, .5, fit_label,
                                horizontalalignment='left',
                                transform=ax_calibration.transAxes, fontsize=8)
            ax_calibration.text(1, 1.05, chemical,
                                horizontalalignment='right',
                                transform=ax_calibration.transAxes, fontsize=8)
        except (np.linalg.LinAlgError):
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
                               top=False, bottom=False,
                               left=False, right=False)
    ax_calibration.set_ylabel("Expected ppm")
    ax_calibration.set_xlabel('Counts/1000')

    # Figure Export
    fig_run_num.tight_layout(pad=1, w_pad=0.4, h_pad=0.4)
    fig_calibration.tight_layout(pad=1, w_pad=0.4, h_pad=0.4)
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
    plt.show()
    print('Finished calibration analysis')
    return (run_num_plots, calibration_plots)


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
    ###########################################################################
    print('Analyzing data...')
    print(expt.date + expt.expt_type + '_' + expt.expt_name)
    expt_data_fol = expt.data_path
    expt_results_fol = expt.results_path
    os.makedirs(expt_results_fol, exist_ok=True)  # Make dir if not there
    calchemIDs = calDF.index.to_numpy()  # get chem IDs from calibration files
    max_runs = 0
    step_path_list = []
    for dirpath, dirnames, filenames in os.walk(expt_data_fol):
        # only looks at .ASC
        num_data_points = len(list_matching_files(dirpath, 'FID', '.asc'))

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
    # TODO create err np.array
    # err_concentrations = np.full((num_fols, num_chems + 1, max_runs), np.nan)

    # Loops through the ind var step and calculates conc in each data file
    for step_path in step_path_list:
        print(os.path.basename(step_path))
        step_num, step_val = os.path.basename(step_path).split(' ')
        step_num = int(step_num) - 1
        data_list = list_matching_files(step_path, 'FID', '.asc')
        condition[step_num] = step_val
        conc = []
        # conc_err = [] TODO
        for filepath in data_list:
            # data is an instance of a class, for signal use data.signal etc
            data = GCData(filepath, basecorrect=True)

            values = data.get_concentrations(calDF)
            # TODO add error output to GC_Data.get_concentrations()
            # values, err = data.get_concentrations(calDF)
            # conc_err.append(err.tolist())
            conc.append(values.tolist())

        num_runs = len(conc)
        # [Condition x [Timestamps, ChemID] x run number]
        concentrations[step_num, :, 0:num_runs] = np.asarray(conc).T
        # err_concentrations[step_num, :, 0:num_runs] = np.asarray(conc).T

    # Pull out "Active" Units from expt_list DF
    units = (expt.expt_list['Units']
             [expt.expt_list['Active Status']].to_string(index=False))

    if expt.expt_type == 'stability_test':
        # Reset "condition" to be time passed for stability tests
        # TODO This could check unit if expt_list updates
        # to have time instead of temp in future.

        # Don't switch unit, get time passed in minutes.
        time_passed, _ = get_timepassed(concentrations,
                                        switch_to_hours=1e9, expt=expt)
        # Make sure time is chronological
        order = np.argsort(time_passed)
        condition = time_passed[order]  # Rewrite condition as time passed

        idx_name = 'time [min]'  # We can get rid of this and else if TODO done
        avg_dat = concentrations[0, 1:, order]
        # TODO add err_concentration values to std
        std_dat = avg_dat * 0

    else:
        idx_name = (expt.ind_var + ' [' + units + ']')  # Sweep Parameter
        avg_dat = np.nanmean(concentrations[:, 1:, :], axis=2)
        # TODO add err_concentration values to std
        std_dat = np.nanstd(concentrations[:, 1:, :], axis=2)

    # Redefine condition list as pandas index so we can assign a name
    condition = pd.Index(condition, name=idx_name)

    if units == 'frac':  # Change label style to stacked compositions.
        condition = condition.str.replace('_', '\n')
        condition = condition.str.replace('frac', '')

    elif expt.expt_type == 'stability_test':
        pass  # Already Float

    else:  # Convert filenames to float w/o units.
        condition = condition.str.replace(r'\D', '', regex=True).astype(float)

    # Results
    ###########################################################################
    avg = pd.DataFrame(avg_dat, columns=calchemIDs, index=condition)
    # TODO add err_concentration values to std
    std = pd.DataFrame(std_dat, columns=calchemIDs, index=condition)
    if savedata:
        np.save(os.path.join(expt_results_fol, 'concentrations'),
                concentrations)
        avg.to_csv(os.path.join(expt_results_fol, 'avg_conc.csv'))
        std.to_csv(os.path.join(expt_results_fol, 'std_conc.csv'))
    print('Finished analyzing ' + expt.expt_name)
    return (concentrations, avg, std)


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

    Notes
    -----
    Conversion and error are calculated in fraction assumming a total mole
    balance of 1. Error calculations are based off the error propogation
    formula, resulting in the equations below:
    .. math::

      &X = 1 - \\frac{C_{reactant}}{C_{total}}

      &S = \\frac{C_{target}}{C_{total}*X}

      &\\sigma_{C_{tot}} = \\sqrt{\\sigma_{Molecule A}^{2} + ...
                                 + \\sigma_{Molecule N}^{2}}

      &\\sigma_{X} = \\sqrt{(\\frac{\\sigma_{C_{reactant}}} {C_{total}})^{2}
                            + (\\frac{\\sigma_{C_{total}}*C_{reactant}}
                                     {C_{total}^{2}})^{2}}

      &\\sigma_{S} = \\sqrt{(\\frac{\\sigma_{C_{target}}} {C_{total}*X})^{2}
                            + (\\frac{\\sigma_{C_{total}}*C_{target}}
                                     {C_{total}^{2}*X})^{2}
                            + (\\frac{\\sigma_{X}*C_{target}}
                                     {C_{total}*X^{2}})^{2}}

    """
    concentrations, avg, std = load_results(expt)
    # Compute relevant concentrations
    C_tot = avg.sum(axis=1)  # total conc. of all molecules
    C_reactant = avg[reactant]  # total conc. of reactant molecule
    C_tar = avg[target_molecule]  # total conc. of target molecule

    # Alternative method of calculating:
    # C_tot = concentrations[:,1:,:].sum(axis=1)
    # C_reactant = concentrations[:,1,:]
    # C_tar = concentrations[:, 2, :]
    # X = 1- C_reactant / C_tot
    # np.average(X, axis=1)
    # np.std(X, axis=1)
    # S = (C_tar / (C_tot * X))
    # np.average(S, axis=1)
    # np.std(S, axis=1)

    # Compute errors in concentrations
    # Error in total conc = quad sum of errors
    err_Ctot = np.sqrt((std**2).sum(axis=1))
    err_Cr = std[reactant]  # Error in reactant concentration
    err_Ctar = std[target_molecule]  # Error in target molecule concentration

    # Computs Conversion and Selectivity
    X = (1 - C_reactant / C_tot)  # conversion assuming mol bal of 1
    S = (C_tar / (C_tot * X))  # Selectivity
    S = S.fillna(0)

    # Compute total errors using error propogation formula
    X_err = np.sqrt((err_Cr/C_tot)**2
                    + (err_Ctot * C_reactant/C_tot**2)**2)
    # Simple Formula. Gives different numbers but should be same...
    # X_err_2 = X * np.sqrt((err_Ctot/C_tot)**2 + (err_Cr/C_reactant)**2)

    # Need check for is X is zero
    S_err = np.sqrt(
                    (err_Ctar / (C_tot * X))**2
                    + ((C_tar * err_Ctot) / (C_tot**2 * X))**2
                    + ((C_tar * X_err) / (C_tot / X**2))**2
                    )
    # Error in selectivity undefined when conversion is zero.
    X_err.replace([np.inf, -np.inf], 0, inplace=True)
    S_err.replace([np.inf, -np.inf], 0, inplace=True)
    X_err.fillna(0, inplace=True)
    S_err.fillna(0, inplace=True)
    # rel_err = std / avg
    # X_err = ((rel_err**2).sum(axis=1))**(1 / 2) * rel_err.max(axis=1)

    results = pd.concat([X, S, X_err, S_err], axis=1)*100
    results.columns = ['Conversion', 'Selectivity', 'X Error', 'S Error']
    return results

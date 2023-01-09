# to actually run some analysis!

import os
import re
import sys
import pickle
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


def list_data_files(folder_path, target):
    """
    Returns the .ASC files for FID data in the specified path.

    Parameters
    ----------
    folder_path : str
        string path to directory containing data
    target : str
        string of target phrase for finding files

    Returns
    -------
    list
        list of filenames ending with .asc and containing 'target' (FID/TCD)
    """
    files_list = []
    for filename in sorted(os.listdir(folder_path)):
        # Only assessing files that end with specified filetype
        if (filename.endswith('.ASC')) & (target in filename):
            files_list.append(filename)
    return files_list

def get_run_number(filename):
    """
    returns run number based on filename

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
    run_num_part = parts[len(parts)-2]
    # \d digit; + however many; $ at end
    run_number = re.search(r'\d+$', run_num_part)
    return int(run_number.group()) if run_number else None

def set_plot_style(figsize):
    '''
    updates default plot styles. varies font size with figure size

    Parameters
    ----------
    figsize : tuple
        (x dimension, y dimension) of figure
    '''
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
    #plt.rcParams['text.usetex'] = False
    plt.rcParams['svg.fonttype'] = 'none'

def get_bool(prompt):
    '''converts common strings to bool'''
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
    concentrations = np.load(os.path.join(fol, 'concentrations.npy'))
    return(concentrations, avg, std)

def convert_index(dataframe):
    '''take in dataframe, convert index from string to float
    if overrun data exists, drops those rows'''
    # scrub letters from first entry
    unit = re.sub("\d+", "", dataframe.index[0])
    # very old data collected before automated control can have overflow data
    dataframe.drop('Over_Run_Data', errors='ignore', inplace=True)
    # remove letter and convert num string to float
    x_data = dataframe.index.str.replace(r'\D', '', regex=True).astype(float)
    dataframe.index = x_data
    return dataframe

def get_timepassed(concentrations, switch_to_hours=2):
    time_stamps = concentrations[:, 0, :].reshape(-1)
    time_stamps = time_stamps[~np.isnan(time_stamps)]

    if np.max(time_stamps) > (switch_to_hours*60*60):
        time_passed = (time_stamps-np.min(time_stamps))/60/60
        time_unit = 'hr'
    else:
        time_passed = (time_stamps-np.min(time_stamps))/60
        time_unit = 'min'

    return time_passed, time_unit

def analyze_cal_data(expt, calDF, figsize=(11, 6.5), force_zero=True):
    """
    runs analysis on previously collected calibration data. Calibration data
    should look like a composition sweep experiment and a calibration data frame
    containing the gasses to be analyzed, their respective starting concentrations,
    and the elution time from the gc needs to be provided.

    Parameters
    ----------
    expt : Experiment()
        DESCRIPTION.
    calDF : Dataframe
        DESCRIPTION.
    figsize : tuple, optional
        DESCRIPTION. The default is (11, 6.5).
    force_zero : Boolean, optional
        add point (x=0, y=0) to data set. The default is True.

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

    n_rows = len(calchemIDs)//3
    n_cols = -(-len(calchemIDs)//n_rows)  # Gives Ceiling
    # Initilize run num plot
    fig_run_num, run_num_plots = plt.subplots(n_rows, n_cols)
    # Initilize ppm vs expected ppm plot
    fig_calibration, calibration_plots = plt.subplots(n_rows, n_cols)

    calgas_flow = np.array([])
    for condition in avg.index:
        calgas_flow = np.append(calgas_flow,
                                float(re.findall(r"([\d.]*\d+)"+'CalGas',
                                                 condition, re.IGNORECASE)[0]))

    # Plotting:
    for chem_num in range(len(calchemIDs)):
        chemical = calchemIDs[chem_num]

        ind_concentrations = concentrations[:, chem_num+1, :] #+1 offsets from timestamps in row 0
        ind_concentrations = ind_concentrations[~np.isnan(ind_concentrations)]

        ax_run_num = run_num_plots.ravel()[chem_num] # flattens to 1d array
        ax_run_num.plot(ind_concentrations/1000, 'o', label=chemical)
        ax_run_num.text(.5, .85, chemical,
                 horizontalalignment='center',
                 transform=ax_run_num.transAxes)

        ax_calibration = calibration_plots.ravel()[chem_num]
        expected_ppm = calDF.loc[chemical, 'ppm']*calgas_flow
        ax_calibration.errorbar(expected_ppm, avg[chemical]/1000, yerr=std[chemical]/1000, fmt='o')

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

            ax_calibration.plot(x_fit, (p[0]*x_fit+p[1])/1000, '--r') # add fit to plot
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
        new_calibration.loc[chemical, 'slope':'err_intercept'] = [m, err_m, b, err_b]

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
    fig_run_num.savefig(os.path.join(expt.results_path, str(
        figsize[0])+'w_run_num_plot_individuals.svg'), format="svg")
    fig_calibration.savefig(os.path.join(expt.results_path, str(
        figsize[0])+'w_calibration_plot.svg'), format="svg")
    new_calibration.to_csv(os.path.join(expt.results_path, 'calibration.csv'))

    return(run_num_plots, calibration_plots)

def run_analysis(expt, calDF, basecorrect='True', savedata='True'):
    """
    sweeps gc data in an experiment data directory and computes ppm
    concentrations for every requested molecules in the .asc files. returns
    a 3D matrix of concentrations, avg concentrations for each experimental
    condition, and error (1 standard deviation)

    Parameters
    ----------
    expt : Experiment()
        Experiment object for desired analysis.
    calDF : Dataframe
        formated data frame containing gc calibration data.
        Specific to control file used!
    basecorrect : Boolean, optional
        Indicates whether or not to baseline correct individual gc data.
        The default is 'True'.
    savedata : Boolean, optional
        Indicates whether or not to save data. The default is 'True'.

    Returns
    -------
    concentrations : numpy array
        concentrations for each molecule, gc collection, and condition
        [Condition x [Timestamps, ChemID] x run number]
    avg : Dataframe
        average concentration for each molecule and experiment condition
    std : Dataframe
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
        num_data_points = len(list_data_files(dirpath, 'TCD'))  # only looks at .ASC
        if not dirnames:  # determine bottom most dirs
            step_path_list.append(dirpath)
        if num_data_points > max_runs:  # Determines largest # of runs in any dir
            max_runs = num_data_points

    num_fols = len(step_path_list)
    num_chems = int(len(calchemIDs))
    condition = np.full(num_fols, 0, dtype=object)
    concentrations = np.full((num_fols, num_chems+1, max_runs), np.nan)

    # Loops through the ind var step and calculates conc in each data file
    for step_path in step_path_list:
        step_num, step_val = os.path.basename(step_path).split(' ')
        step_num = int(step_num)-1
        data_list = list_data_files(step_path, 'TCD')
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
        concentrations[step_num, :, 0:num_runs] = np.asarray(conc).T

    units = (expt.expt_list['Units']
             [expt.expt_list['Active Status']].to_string(index=False))
    idx_name = (expt.ind_var + ' ['+units+']') # Sweep Parameter
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
    concentrations, avg, std = load_results(expt)
    C_Tot = avg.sum(axis=1)  # total conc of all molecules
    C_reactant = avg[reactant]  # total conc of reactant molecule
    X = (1 - C_reactant/C_Tot)*100  # conversion assuming 100% mol bal
    rel_err = std/avg
    X_err = ((rel_err**2).sum(axis=1))**(1/2)*rel_err.max(axis=1)
    S = (avg[target_molecule[0]]/(C_Tot*X/100))*100  # selectivity
    S = S.fillna(0)
    results = pd.concat([X, S, X_err], axis=1)
    results.columns = ['Conversion', 'Selectivity', 'Error']
    return results


def plot_expt_summary(expt, calDF, reactant, target_molecule,
                      mass_bal='c', figsize=(6.5, 4.5), savedata='True'):
    # Plotting
    ###########################################################################
    print('Plotting...')
    plt.close('all')

    set_plot_style(figsize)
    fig1, ax1 = plot_run_num(expt, calDF, mass_bal)
    fig2, ax2 = plot_ppm(expt)
    fig3, ax3 = plot_X_and_S(expt)

    # Figure Export
    if savedata:
        fig1_path = os.path.join(os.path.join(expt.results_path,
                                              str(figsize[0])+'w_run_num_plot'))
        fig2_path = os.path.join(os.path.join(expt.results_path,
                                              str(figsize[0])+'w_avg_conc_plot'))
        fig3_path = os.path.join(os.path.join(expt.results_path,
                                              str(figsize[0])+'w_Conv_Sel_plot'))

        fig1.savefig(fig1_path+'.svg', format="svg")
        fig2.savefig(fig2_path+'.svg', format="svg")
        fig3.savefig(fig3_path+'.svg', format="svg")

        pickle.dump(fig1, open(fig1_path+'.pickle', 'wb'))
        pickle.dump(fig2, open(fig2_path+'.pickle', 'wb'))
        pickle.dump(fig3, open(fig3_path+'.pickle', 'wb'))

    return (ax1, ax2, ax3)

def plot_run_num(expt, calDF, switch_to_hours=2):
    # Initilize run num plot
    fig, ax = plt.subplots()
    concentrations, avg, std = load_results(expt)
    # Calculations:
    calchemIDs = calDF.index  # get chem IDs from calibration files
    time_passed, time_unit = get_timepassed(concentrations, switch_to_hours)

    # use regex to determine number of carbons (or other) in molecule name
    for chemical in calchemIDs:
        chem_num = calchemIDs.get_loc(chemical)+1  # index 0 is timestamp
        # Concentrations for individual chemical
        ind_concentrations = concentrations[:, chem_num, :]
        ind_concentrations = ind_concentrations[~np.isnan(ind_concentrations)]
        ax.plot(time_passed, ind_concentrations, 'o', label=chemical)

    ax.legend()
    plt.xlabel('Time ['+time_unit+']')
    # TODO add second x axis as run number instead of time
    plt.ylabel('Conc [ppm]')
    plt.tight_layout()
    return (fig, ax)

def plot_ppm(expt, concentrations, calDF, mass_bal='c', switch_to_hours=2):
    # Initilize ppm vs ind_var plot
    fig, ax = plt.subplots()
    concentrations, avg, std = load_results(expt)
    calchemIDs = calDF.index  # get chem IDs from calibration files
    time_passed, time_unit = get_timepassed(concentrations, switch_to_hours)
    units = (expt.expt_list['Units']
             [expt.expt_list['Active Status']].to_string(index=False))
    try:
        x_data = getattr(expt, expt.ind_var)
    except AttributeError: # Fails for stability test
        order = np.argsort(time_passed)
        x_data = time_passed[order]
        avg = pd.DataFrame(concentrations[0,1:,order])
        avg.columns = calchemIDs
        avg.index = x_data
        std = 0*avg
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

    mol_count = avg @ (np.array(stoyk, dtype=int))
    mol_count.columns = ['Total ' + mass_bal]
    mol_error = std @ (np.array(stoyk, dtype=int))

    # Plotting:
    avg.iloc[0:len(x_data)].plot(ax=ax, marker='o', yerr=std)
    mol_count.iloc[0:len(x_data)].plot(ax=ax, marker='o', yerr=mol_error.iloc[0:len(x_data)])
    ax.set_xlabel(expt.ind_var + ' ['+units+']')
    ax.set_ylabel('Conc (ppm)')
    # ax.set_xticklabels(avg.iloc[0:len(x_data)], rotation=90)
    plt.tight_layout()
    return (fig, ax)

def plot_X_and_S(expt, reactant, target_molecule):
    # Initilize Conv and Selectivity plot
    fig, ax = plt.subplots()
    results = calculate_X_and_S(expt, reactant, target_molecule)
    units = (expt.expt_list['Units']
             [expt.expt_list['Active Status']].to_string(index=False))
    X = results['Conversion']
    S = results['Selectivity']
    X_err = results['Error']*results['Conversion']
    S_err = results['Error']*results['Selectivity']
    X.plot(ax=ax, yerr=X_err, fmt='--ok')
    S.plot(ax=ax, yerr=S_err, fmt='--^r')
    ax.set_xlabel(expt.ind_var + ' ['+units+']')
    ax.set_ylabel('Conv./Selec. [%]')
    plt.legend(['Conversion', 'Selectivity'])
    ax.set_ylim([0, 105])
    plt.tight_layout()
    return (fig, ax)

def multiplot_X_and_S(results_dict, figsize=(6.5, 4.5)):
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
        X_err = results['Error']*results['Conversion']
        S_err = results['Error']*results['Selectivity']
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
        X_err = results['Error']*results['Conversion']
        S_err = results['Error']*results['Selectivity']
        ax.plot(X, S, '--o', label=data_label)

    ax.set_ylabel('Selectivity [%]')
    ax.set_xlabel('Conversion [%]')
    ax.set_xlim([0, 105])
    ax.set_ylim([0, 105])
    plt.legend()
    fig.tight_layout()
    fig.show()
    return (fig, ax)

def open_pickled_fig(fig_path):
    plt.rcParams['svg.fonttype'] = 'none'
    fig = pickle.load(open(fig_path, 'rb'))
    ax = fig.get_axes()[0]
    fig.show() # Show the figure, edit it, etc.!
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
                print(os.path.split(expt_path)[1])
                if os.path.split(dirpath)[1] == '20220317temp_sweep_0.0mW_0C2H2_0.95Ar_0.05H2frac_50sccm':
                    continue
                # import all calibration data
                calDF = pd.read_csv(
                    calibration_path, delimiter=',', index_col='Chem ID')
                expt = Experiment()  # Initialize experiment obj
                expt.read_expt_log(log_path)  # Read expt parameters from log
                expt.update_save_paths(expt_path)  # update file paths

                (concentrations, avg, std) = run_analysis(expt, calDF) # first run
                #(concentrations, avg, std) = load_results(expt)  # if you already ran analysis
                (ax1, ax2, ax3) = plot_expt_summary(expt,
                                                    calDF,
                                                    target_molecule=['c2h4'],
                                                    mass_bal='C',
                                                    reactant='c2h2',
                                                    figsize=(6.5, 4.5))
# Standard figsize
# 1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
# 1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);
    print('Finished!')

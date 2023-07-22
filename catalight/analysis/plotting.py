"""
Tools specifically related to plotting data.

This module was broken out from analysis.tools for clarity. Helper functions
and command specifically related to plotting data of any type should be placed
here.
Created on Mon Feb  6 11:46:49 2023.
@author: Briley Bourgeois
"""
import os
import pickle
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import catalight.analysis.tools as analysis_tools


def set_plot_style(figsize=(6.5, 4.5)):
    """
    Update default plot styles. Varies font size with figure size.

    Parameters
    ----------
    figsize : `tuple`, optional
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
    plt.rcParams['legend.fontsize'] = fontsize[0]-2
    # plt.rcParams['text.usetex'] = False
    plt.rcParams['svg.fonttype'] = 'none'


def plot_expt_summary(expt, calDF, reactant, target_molecule, mole_bal='c',
                      figsize=(6.5, 4.5), savedata='True', switch_to_hours=2):
    """
    Call 'typical' plotting functions and save output to results path.

    Plots and saves "run_num", "ppm", and "X and S" for given experiment.
    run_num: ppm concentration as a function of run number
    ppm: average ppm concentration w/ error for each experiment condition
    X and S: Plots the average conversion and selectivity as a function of
    experimental condition

    If savedata=True, will save figures as both .svg and .pickle

    Parameters
    ----------
    expt : Experiment
        Experiment object which has data and has been analyzed
        (i.e. has avg_conc.csv etc.)
    calDF : pandas.DataFrame
        Formatted DataFrame containing gc calibration data.
        Specific to control file used!
        Format [ChemID, slope, intercept, start, end]
    reactant : str
        String identity of reactant molecule to track. Must match what exists
        in the calibration file exactly.
    target_molecule : str
        String identity of the target to use when calculating selectivity. Must
        match what exists in the calibration file exactly.
    mole_bal : `str`, optional
        Code will perform a mole balance for the element provided.
        The default is 'c'. (i.e. carbon balance)
    figsize : `tuple`, optional
         Desired size of output figure in inches (x,y), Default is (6.5, 4.5).
         figsize suggestions:
         1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
         1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);
    savedata : `bool`, optional
        Indicates whether or not to save data. The default is 'True'.
    switch_to_hours : `float`, optional
        Time in hours when the output should switch units to
        hours instead of minutes. The default is 2.

    Returns
    -------
    tuple(:class:`~matplotlib.axes._axes.Axes`,
    :class:`~matplotlib.axes._axes.Axes`,
    :class:`~matplotlib.axes._axes.Axes`) :
        (ax1, ax2, ax3) Axis handles for "run_num",  "ppm", and "X and S" plots

    """
    # Plotting
    ###########################################################################
    print('Plotting...')
    plt.close('all')

    set_plot_style(figsize)
    fig1, ax1 = plot_run_num(expt, calDF, switch_to_hours)
    fig2, ax2 = plot_ppm(expt, calDF, mole_bal, switch_to_hours)
    fig3, ax3 = plot_X_and_S(expt, reactant, target_molecule)

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
        Formatted DataFrame containing gc calibration data.
        Specific to control file used!
        Format [ChemID, slope, intercept, start, end]
    switch_to_hours : `float`, optional
        Time in hours when the output should switch units to
        hours instead of minutes. The default is 2.

    Returns
    -------
    tuple(matplotlib.figure.Figure, matplotlib.axes._axes.Axes) :
        Figure and Axis handle for "run_num" plot
    """
    # Initialize run num plot
    fig, ax = plt.subplots()
    concentrations, avg, std = analysis_tools.load_results(expt)
    # Calculations:
    calchemIDs = calDF.index  # get chem IDs from calibration files
    time_passed, time_unit = analysis_tools.get_timepassed(concentrations,
                                                           switch_to_hours,
                                                           expt)

    # use regex to determine number of carbons (or other) in molecule name
    for chemical in calchemIDs:
        chem_num = calchemIDs.get_loc(chemical) + 1  # index 0 is timestamp
        # Concentrations for individual chemical
        ind_concentrations = concentrations[:, chem_num, :]
        ind_concentrations = ind_concentrations[~np.isnan(ind_concentrations)]
        if sum(ind_concentrations) == 0:
            continue  # Skip chemicals with no values
        ax.plot(time_passed, ind_concentrations, 'o', label=chemical)

    ax.legend()
    plt.xlabel('Time [' + time_unit + ']')
    # TODO add second x axis as run number instead of time
    plt.ylabel('Conc [ppm]')
    plt.tight_layout()
    return (fig, ax)


def plot_ppm(expt, calDF, mole_bal='c', switch_to_hours=2):
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
        Formatted DataFrame containing gc calibration data.
        Specific to control file used!
        Format [ChemID, slope, intercept, start, end]
    mole_bal : `str`, optional
        Code will perform a mole balance for the element provided.
        The default is 'c'. (i.e. carbon balance)
    switch_to_hours : `float`, optional
        Time in hours when the output should switch units to
        hours instead of minutes. The default is 2.

    Returns
    -------
    tuple(matplotlib.figure.Figure, matplotlib.axes._axes.Axes) :
        Figure and Axis handle for "ppm" plot
    """
    # Initialize ppm vs ind_var plot
    fig, ax = plt.subplots()
    concentrations, avg, std = analysis_tools.load_results(expt)
    calchemIDs = calDF.index  # get chem IDs from calibration files

    units = (expt.expt_list['Units']
             [expt.expt_list['Active Status']].to_string(index=False))

    if expt.expt_type == 'stability_test':
        # TODO This could check unit if expt_list updates
        # to have time instead of temp in future.
        if np.max(avg.index) > switch_to_hours:
            avg.index = avg.index / 60  # convert minutes to hours
            units = 'hr'

    stoyk = pd.Series(0, index=calchemIDs)
    # use regex to determine number of carbons (or other) in molecule name
    for chemical in calchemIDs:
        # Use chem_num to access by index number instead of name.
        # chem_num = calchemIDs.get_loc(chemical) + 1  # index 0 is timestamp
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
    # Don't plot molecules that don't show up
    undetected = avg.sum(axis=0) == 0
    if avg.to_numpy().sum() == 0:
        print('No Molecules Detected')
        return (fig, ax)

    avg.loc[:, ~undetected].plot(ax=ax, marker='o',
                                 yerr=std.loc[:, ~undetected])
    mol_count.plot(ax=ax, marker='o', yerr=mol_error)
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
        match what exists in the calibration file exactly.

    Returns
    -------
    tuple(matplotlib.figure.Figure, matplotlib.axes._axes.Axes) :
        Figure and Axis handle for "X and S" plot

    """
    # Initialize Conv and Selectivity plot
    fig, ax = plt.subplots()
    results = analysis_tools.calculate_X_and_S(expt, reactant, target_molecule)
    units = (expt.expt_list['Units']
             [expt.expt_list['Active Status']].to_string(index=False))
    X = results['Conversion']
    S = results['Selectivity']
    if 'X Error' in results.columns:
        X_err = results['X Error']
        S_err = results['S Error']
    else:  # Older data calculated one Error
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
    Separately plot 1) conversion and 2) selectivity for multiple experiments.

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
    figsize : `tuple`, optional
        Desired size of output figure in inches (x,y), Default is (6.5, 4.5).
        figsize suggestions:
        1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
        1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);

    Returns
    -------
    tuple(tuple(matplotlib.figure.Figure, matplotlib.axes._axes.Axes)) :
        two tuples, each containing the (figure, axis) handles for the
        conversion and selectivity plots, respectively.

    """
    # Initialize Conv and Selectivity plots
    # Note: if desired, results_dict could instead be expt_dict and
    # calculate_X_and_S() called within this function
    figX, axX = plt.subplots()
    figS, axS = plt.subplots()
    xlabel = None
    for data_set in results_dict.items():
        data_label = data_set[0]
        results = data_set[1]
        X = results['Conversion']
        S = results['Selectivity']
        if 'X Error' in results.columns:
            X_err = results['X Error']
            S_err = results['S Error']
        else:
            X_err = results['Error'] * results['Conversion']
            S_err = results['Error'] * results['Selectivity']
        X.plot(ax=axX, yerr=X_err, fmt='--o', label=data_label)
        S.plot(ax=axS, yerr=S_err, fmt='--^', label=data_label)
        xlabel = results.index.name

    axX.set_ylabel('Conversion [%]')
    axX.set_xlabel(xlabel)
    axX.set_ylim([0, 105])
    axX.legend()
    figX.tight_layout()

    axS.set_ylabel('Selectivity [%]')
    axS.set_xlabel(xlabel)
    axS.set_ylim([0, 105])
    axS.legend()
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
    figsize : `tuple`, optional
        Desired size of output figure in inches (x,y), Default is (6.5, 4.5).
        figsize suggestions:
        1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
        1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);

    Returns
    -------
    tuple(matplotlib.figure.Figure, matplotlib.axes._axes.Axes) :
        Figure and Axis handle for "X vs S" plot

    """
    print('Plotting...')
    plt.close('all')

    set_plot_style(figsize)
    # Initialize Conv and Selectivity plot
    fig, ax = plt.subplots()

    for data_set in results_dict.items():
        data_label = data_set[0]
        results = data_set[1]
        X = results['Conversion']
        S = results['Selectivity']
        X_err = results['X Error']
        S_err = results['S Error']
        # Defunct. Older data had single error output.
        # X_err = results['Error'] * results['Conversion']
        # S_err = results['Error'] * results['Selectivity']

        ax.errorbar(X, S, yerr=S_err, xerr=X_err, fmt='--o', label=data_label)

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
    Open a pickled figure for editing.

    Parameters
    ----------
    fig_path : str
        Path to .pickle file. Must be matplotlib.pyplot.figure

    Returns
    -------
    tuple(matplotlib.figure.Figure, matplotlib.axes._axes.Axes) :
        Figure and Axis handle for plot
    """
    plt.rcParams['svg.fonttype'] = 'none'
    fig = pickle.load(open(fig_path, 'rb'))
    ax = fig.get_axes()[0]
    fig.show()  # Show the figure, edit it, etc.!
    return (fig, ax)

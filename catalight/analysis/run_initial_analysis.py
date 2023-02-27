"""
Executable script to run basic analysis on existing data sets.

Created on Fri Jan  6 12:11:00 2023.
@author: Briley Bourgeois
"""
import sys

import matplotlib.pyplot as plt
import pandas as pd
from PyQt5.QtWidgets import QFileDialog, QApplication, QDialog
import catalight.analysis as analysis
from catalight.analysis.user_inputs import (DirectorySelector,
                                            PlotOptionsDialog,
                                            PlotOptionList)


def get_user_inputs(starting_dir=None, cal_folder=None):
    """
    Take user input using GUI for running initial analysis.

    Parameters
    ----------
    starting_dir : str, optional
        Path to initialize file dialog in. The default is None.
    cal_folder : str, optional
        Path containing calibration files. The default in None.

    Returns
    -------
    expt_dirs : list of str
        Paths to main directories for running analysis.
    calDF : pandas.DataFrame
        Formated DataFrame containing gc calibration data.
        Specific to control file used!
        Format [ChemID, slope, intercept, start, end]
    response_dict : dict
        Dictionary of user plot options.
        Dict Keys depend on options proved to PlotOptionsDialog.
        {'overwrite': bool, 'basecorrect': bool, 'reactant': str,
        'target_molecule': str, 'mole_bal': str, 'figsize': tuple,
        'savedata': bool, 'switch_to_hours': float}

    """
    app = QApplication(sys.argv)  # noqa
    # Prompt user to select calibration file
    cal_file = QFileDialog.getOpenFileName(None, 'Select Calibration File',
                                           cal_folder, "csv file (*.csv)")[0]
    calDF = pd.read_csv(cal_file, delimiter=',', index_col='Chem ID')

    # Prompt user to select multiple experiment directories
    data_dialog = DirectorySelector(starting_dir)
    if data_dialog.exec_() == QDialog.Accepted:
        expt_dirs = data_dialog.get_output()

    # Edit Options specifically for initial analysis dialog
    include_dict = {'overwrite': True, 'basecorrect': True, 'reactant': True,
                    'target_molecule': True, 'mole_bal': True, 'figsize': True,
                    'savedata': True, 'switch_to_hours': True}
    options = PlotOptionList()  # Create default gui options list
    options.change_includes(include_dict)  # Modify gui components
    options_dialog = PlotOptionsDialog(options)  # Build dialog w/ options
    if options_dialog.exec_() == PlotOptionsDialog.Accepted:
        response_dict = options.values_todict()
        print('options acccepted')

    return expt_dirs, calDF, response_dict


def main(main_dirs, calDF, reactant, target_molecule, mole_bal='c',
         figsize=(6.5, 4.5), savedata=False, switch_to_hours=2,
         overwrite=False, basecorrect=True):
    """
    Run initial analysis.

    Finds existing expt_log.txt files within the provided directories, creates
    expt objects, runs analysis.run_analysis and analysis.plot_expt_summary
    where appropriate based on input parameters.

    Parameters
    ----------
    main_dirs : list of str
        Paths to main directories for running analysis. All expt_log.txt files
        within the main directory will be analyzed.
    calDF : pandas.DataFrame
        Formated DataFrame containing gc calibration data.
        Specific to control file used!
        Format [ChemID, slope, intercept, start, end]
    new_x : list
        Array of new data to be used inplace of old x axis
    units : str
        new units for new x axis data
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
    switch_to_hours : float, optional
        Time in hours when the output should switch units to
        hours instead of minutes. The default is 2.
    overwrite : bool, optional
        True will rerun calculations for experiments containing avg_conc.csv
        files. False will only plot these. The default is False.
    basecorrect : bool, optional
        True will perform baseline correction on GC data. The default is True.

    Returns
    -------
    None.

    """
    print('inside main')
    plt.ioff()  # suppress plot windows
    options = (reactant, target_molecule, mole_bal,
               figsize, savedata, switch_to_hours)
    filepaths = analysis.tools.list_matching_files(main_dirs,
                                                   'expt_log', '.txt')
    expts = analysis.tools.list_expt_obj(filepaths)
    print(expts)
    for expt in expts:
        has_data = analysis.tools.list_matching_files(expt.results_path,
                                                      'avg_conc', '.csv')
        if not has_data or overwrite:  # skip if has data and overwrite=False
            calculations = analysis.tools.run_analysis(expt, calDF,
                                                       basecorrect, savedata)
            (concentrations, avg, std) = calculations

        (ax1, ax2, ax3) = analysis.plotting.plot_expt_summary(expt, calDF,
                                                              *options)

        # These outputs are defined to make it a little easier for output
        # if that is ever desired. Otherwise open pickled figs!!


if __name__ == "__main__":

    plt.close('all')
    expt_dirs, calDF, response_dict = get_user_inputs()
    print('out of inputs...')
    main(expt_dirs, calDF, **response_dict)

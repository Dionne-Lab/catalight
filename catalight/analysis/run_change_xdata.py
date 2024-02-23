"""
Executable script prompting the user to select experiments and enter new xdata.

Created on Sat Mar 19 15:33:01 2022
@author: Briley Bourgeois
"""
import sys
import re
import os

import pandas as pd
import matplotlib.pyplot as plt
import catalight.analysis as analysis
from PyQt5.QtWidgets import (QApplication, QFileDialog)
from catalight.analysis.user_inputs import (DataExtractor,
                                            PlotOptionsDialog,
                                            PlotOptionList)


def parse_input(input_string):
    """
    Enter user input string to extract all numbers as floats and return
    a list of those floats

    Parameters
    ----------
    input_string : str
        Users raw response for new x data from get_user_inputs

    Returns
    -------
    list[float]
        List of users float-like entries
    """
    # Regular expression to match floats
    float_pattern = r'-?\d*\.?\d+'
    # Find all float matches in the input string
    floats = re.findall(float_pattern, input_string)
    # Convert strings to floats
    return [float(num) for num in floats]


def get_user_inputs(starting_dir=None, cal_folder=None):
    """
    Get user inputs for changing x axis data.

    Parameters
    ----------
    starting_dir : `str`, optional
        Path to initialize file dialog in. The default is None.
    cal_folder : `str`, optional
        Path containing calibration files. The default in None.

    Returns
    -------
    file_list : list
        list of paths to expt_logs
    calDF : pandas.DataFrame
        Formatted DataFrame containing gc calibration data.
        Specific to control file used!
        Format [ChemID, slope, intercept, start, end]
    response_dict : dict
        Dictionary of user plot options.
        Dict Keys depend on options proved to PlotOptionsDialog.
        {'xdata': list, 'units': str, 'reactant': str,
        y'target_molecule': str, 'mole_bal': str, 'figsize': tuple,
        'savedata': bool, 'switch_to_hours': float}

    """
    # Prompt user to select calibration file
    app = QApplication(sys.argv)
    cal_file = QFileDialog.getOpenFileName(None, 'Select Calibration File',
                                           cal_folder, "csv file (*.csv)")[0]
    calDF = pd.read_csv(cal_file, delimiter=',', index_col='Chem ID')

    # Prompt user to select multiple experiment directories. Label unused.
    data_dialog = DataExtractor(starting_dir)
    if data_dialog.exec_() == DataExtractor.Accepted:
        file_list, data_labels = data_dialog.get_output()
        file_list = analysis.tools.list_matching_files(file_list, 'expt_log', '.txt')

    # Edit Options specifically for initial analysis dialog
    include_dict = {'xdata': True, 'units': True, 'reactant': True,
                    'target_molecule': True, 'mole_bal': True, 'figsize': True,
                    'savedata': True, 'switch_to_hours': True}
    options = PlotOptionList()  # Create default gui options list
    options.change_includes(include_dict)  # Modify gui components
    options_dialog = PlotOptionsDialog(options)  # Build dialog w/ options
    if options_dialog.exec_() == PlotOptionsDialog.Accepted:
        response_dict = options.values_todict()

    return file_list, calDF, response_dict


def main(expt_paths, calDF, xdata, units, reactant, target_molecule,
         mole_bal='c', figsize=(6.5, 4.5), savedata=False, switch_to_hours=2):
    """
    Change the x axis data for previously plotted experiments.

    Parameters
    ----------
    expt_paths : list of str
        List of full paths to expt_log.txt files.
    calDF : pandas.DataFrame
        Formatted DataFrame containing gc calibration data.
        Specific to control file used!
        Format [ChemID, slope, intercept, start, end]
    xdata : list
        Array of new data to be used inplace of old x axis
    units : str
        new units for new x axis data
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
    None

    """
    options = (calDF, reactant, target_molecule, mole_bal,
               figsize, savedata, switch_to_hours)

    expts = analysis.tools.list_expt_obj(expt_paths)
    new_x = parse_input(xdata)
    for expt in expts:
        # Must have previously analyzed data
        (results, avg, std) = analysis.tools.load_results(expt)
        # Redefine x axis and update units
        expt.expt_list['Units'][2] = units
        avg.index = pd.Index(new_x, name=units)
        std.index = pd.Index(new_x, name=units)

        # Save results as csv with new x axis
        avg.to_csv(os.path.join(expt.results_path, 'avg_conc.csv'))
        std.to_csv(os.path.join(expt.results_path, 'std_conc.csv'))

        # Replot data using new axes data
        (ax1, ax2, ax3) = analysis.plotting.plot_expt_summary(expt, *options)


if __name__ == "__main__":
    plt.close('all')
    file_list, calDF, response_dict = get_user_inputs()
    main(file_list, calDF, **response_dict)

"""
Executable script prompting the user to select experiments and enter new xdata.

Created on Sat Mar 19 15:33:01 2022
@author: Briley Bourgeois
"""
import sys

import pandas as pd
import matplotlib.pyplot as plt
import catalight.analysis.tools as analysis_tools
from PyQt5.QtWidgets import (QApplication, QFileDialog)
from catalight.analysis.user_inputs import (DataExtractor,
                                               PlotOptionsDialog,
                                               PlotOptionList)


def get_user_inputs(starting_dir=None, cal_folder=None):
    """
    Get user inputs for changing x axis data.

    Parameters
    ----------
    starting_dir : str, optional
        Path to initialize file dialog in. The default is None.
    cal_folder : str, optional
        Path containing calibration files. The default in None.

    Returns
    -------
    file_list : list
        list of paths to expt_logs
    calDF : pandas.DataFrame
        Formatted DataFrame containing gc calibration data.
        Specific to control file used!
        Format [ChemID, slope, intercept, start, end]
    new_x : list
        Array of new data to be used inplace of old x axis
    units : str
        new units for new x axis data
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

    # Edit Options specifically for initial analysis dialog
    include_dict = {'xdata': True, 'units': True, 'reactant': True,
                    'target_molecule': True, 'mole_bal': True, 'figsize': True,
                    'savedata': True, 'switch_to_hours': True}
    options = PlotOptionList()  # Create default gui options list
    options.change_includes(include_dict)  # Modify gui components
    options_dialog = PlotOptionsDialog(options)  # Build dialog w/ options
    if options_dialog.exec_() == PlotOptionsDialog.Accepted:
        response_dict = options.values_todict()

    return(file_list, calDF, response_dict)


def main(expt_paths, calDF, new_x, units, reactant, target_molecule,
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
    new_x : list
        Array of new data to be used inplace of old x axis
    units : str
        new units for new x axis data
    reactant : str
        String identity of reactant molecule to track. Must match what exists
        in the calibration file exactly.
    target_molecule : str
        String identity of the target to use when calculating selectivity. Must
        match what exists in the calibration file exactly.
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

    Returns
    -------
    None.

    """
    options = (calDF, reactant, target_molecule, mole_bal,
               figsize, savedata, switch_to_hours)

    expts = analysis_tools.list_expt_obj(expt_paths)
    for expt in expts:
        # Must have previously analyzed data
        (results, avg, std) = analysis_tools.load_results(expt)
        # Redefine x axis and update units
        avg.index = new_x
        std.index = new_x
        expt.expt_list['Units'][2] = units
        # Replot data using new axes data
        (ax1, ax2, ax3) = analysis_tools.plot_expt_summary(expt, *options)


if __name__ == "__main__":
    plt.close('all')
    file_list, calDF, response_dict = get_user_inputs()
    main(file_list, calDF, **response_dict)

"""
Prompt user for inputs and run calibration analysis on data set.

Created on Thu Feb  3 09:25:10 2022
@author: Briley Bourgeois
"""
import os

import pandas as pd
import catalight.analysis.tools as analysis_tools
from catalight.analysis.user_inputs import PlotOptionsDialog, PlotOptionList
from catalight.equipment.experiment_control import Experiment
from PyQt5.QtWidgets import QFileDialog


def get_user_inputs(starting_dir=None, cal_folder=None):
    """
    Get inputs from user before running calibration.

    Parameters
    ----------
    starting_dir : str, optional
        Directory to start filedialog in. The default is None.
    cal_folder : str, optional
        Directory containing calibrations. The default is None.

    Returns
    -------
    expt : Experiment
        Experiment object for already run calibration experiment
    calDF : pandas.DataFrame
        Formated DataFrame containing gc calibration data.
        Specific to control file used!
        Format [ChemID, slope, intercept, start, end, ppm]
    figsize : tuple
        Desired size of output figure in inches (x,y).
    force_zero : bool
        Add point (x=0, y=0) to data set.

    """
    # Prompt user to select calibration file
    prompt = "Please select the desired calibration file"
    calibration_path = QFileDialog.getOpenFileName(None, prompt, cal_folder,
                                                   "csv file (*.csv)")[0]
    calDF = pd.read_csv(calibration_path, delimiter=',', index_col='Chem ID')

    # Build Expt object from user selected expt directory
    expt_dir = QFileDialog.getExistingDirectory('Select Calibration Experiment')
    log_path = os.path.join(expt_dir, 'expt_log.txt')
    expt = Experiment()  # Initialize experiment obj
    expt.read_expt_log(log_path)  # Read expt parameters from log
    expt.update_save_paths(os.path.dirname(log_path))  # update file paths

    # Edit Options specifically for calibration dialog
    include_dict = {'forcezero': True, 'figsize': True}
    options = PlotOptionList()  # Create default gui options list
    options.change_includes(include_dict)  # Modify gui components
    options_dialog = PlotOptionsDialog(options)  # Build dialog w/ options
    if options_dialog.exec_() == PlotOptionsDialog.Accepted:
        response_dict = options.values_todict()

    return expt, calDF, response_dict


def main(expt, calDF, figsize=(6.5, 4.5), forcezero=True):
    """
    Run analysis.tools.analyze_cal_data. Wrapped w/ Main for consistency.

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
    cal_plots : matplotlib.pyplot.axis
        Axis handle for plots showing expected ppm vs measured counts

    """
    run_num_plots, cal_plots = analysis_tools.analyze_cal_data(expt, calDF)
    return run_num_plots, cal_plots


if __name__ == "__main__":

    options = get_user_inputs()
    run_num_plots, cal_plots = main(*options)

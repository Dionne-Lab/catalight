"""
Generate conversion and selectivity plots for multiple experiments using GUI.

Created on Fri Jun 24 17:28:48 2022
@author: Briley Bourgeois
"""
import sys

import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication
import catalight.analysis.tools as analysis_tools
from catalight.analysis.user_inputs import (DataExtractor,
                                               PlotOptionsDialog,
                                               PlotOptionList)


def get_user_inputs(starting_dir=None):
    """
    Take user input using GUI for running multiplot comparison.

    Parameters
    ----------
    starting_dir : str, optional
        Path to initialize file dialog in. The default is None.

    Returns
    -------
    file_list : list of str
        List of file paths to experiment folders then used to initiate
        experiment objects and calculate conversion and selectivity.
    data_labels : list of str
        List of data labels used for generating plot legends.
    response_dict : dict
        Dictionary of user plot options.
        Dict Keys depend on options proved to PlotOptionsDialog.
        {'reactant': str, 'target_molecule': str,
        'XandS': bool, 'XvsS': bool, 'figsize': tuple}
    """
    app = QApplication(sys.argv)

    # Prompt user to select multiple experiment directories and label them
    data_dialog = DataExtractor(starting_dir)
    if data_dialog.exec_() == DataExtractor.Accepted:
        file_list, data_labels = data_dialog.get_output()

    # Edit Options specifically for initial analysis dialog
    include_dict = {'reactant': True, 'target_molecule': True,
                    'XandS': True, 'XvsS': True, 'figsize': True}
    options = PlotOptionList()  # Create default gui options list
    options.change_includes(include_dict)  # Modify gui components
    options_dialog = PlotOptionsDialog(options)  # Build dialog w/ options
    if options_dialog.exec_() == PlotOptionsDialog.Accepted:
        response_dict = options.value_todict()

    return (file_list, data_labels, response_dict)


def main(file_list, data_labels, reactant, target_molecule,
         plot_XandS, plot_XvsS, figsize=(6.5, 4.5)):
    """
    Plot multi-experiment comparison.

    Parameters
    ----------
    file_list : list of str
        List of file paths to experiment folders then used to initiate
        experiment objects and calculate conversion and selectivity.
    data_labels : list of str
        List of data labels used for generating plot legends.
    reactant : str
        String identity of reactant molecule to track. Must match what
        exists in the calibration file exactly.
    target_molecule : str
        String identity of the target_molecule to use when calculating
        selectivity. Must match what exists in the calibration file exacly.
    plot_XandS : bool
        True plots comparison plots of conversion and selectivity individually
        as a function of the independent variable. Ind. Var. should be the same
        between all provided values.
    plot_XvsS : bool
        True plots plot selectivity as a function of conversion for all
        provided experiments on one plot.
    figsize : tuple, optional
         Desired size of output figure in inches (x,y), Default is (6.5, 4.5).
         figsize suggestions:
         1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
         1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);

    Returns
    -------
    ((figX, axX), (figS, axS))
        if plot_XandS == True, returns fig and ax handles for two plots
    fig, ax
        if plot_XvsS == True, returns fig and ax handles for selectivity vs
        conversion plot

    """
    results_dict = analysis_tools.build_results_dict(file_list, data_labels,
                                                     reactant, target_molecule)

    if plot_XandS:
        plot_results = analysis_tools.multiplot_X_and_S(results_dict, figsize)
        ((figX, axX), (figS, axS)) = plot_results
        plt.show()
        return ((figX, axX), (figS, axS))

    elif plot_XvsS:
        fig, ax = analysis_tools.multiplot_X_vs_S(results_dict, figsize)
        plt.show()
        return fig, ax
    print('Test if this line is executed')


if __name__ == "__main__":
    plt.close('all')
    file_list, data_labels, response_dict = get_user_inputs()
    main(file_list, data_labels, **response_dict)

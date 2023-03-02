"""
Executable file that asks user for inputs and plot GC data on one plot.

Opens 3 UIs requesting, data directory, target .asc file w/ labels and plotting
options. Plots .asc file data on a single figure.

Created on Fri Jan  6 17:10:25 2023.
@author: Briley Bourgeois
"""
import sys

import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication
import catalight.analysis.plotting as plot_tools
from catalight.analysis.gcdata import GCData
from catalight.analysis.user_inputs import (DataExtractor,
                                            PlotOptionList,
                                            PlotOptionsDialog)


def get_user_inputs(starting_dir=None):
    """
    Prompt user to enter select directory and choose .asc files from it.

    Opens 3 UI screens. Prompts user for directory, then displays .asc files
    within that directory and asks user to click the ones to plot and provide
    a data label, finally opens a UI to ask for plotting options
    (baseline correction and figure size)

    Parameters
    ----------
    starting_dir : str, optionalr
        Directory to start file dialog in. The default is None.

    Returns
    -------
    file_list : list of str
        List of files selected by user.
    data_labels : list of str
        List of data labels provided by user for plot legend.
    response_dict : dict
        Dictionary of user plot options.
        Dict Keys depend on options proved to PlotOptionsDialog.
        {'basecorrect': bool, 'figsize': tuple}

    """
    app = QApplication(sys.argv)  # noqa
    # Prompt user to select .asc files and label them
    data_dialog = DataExtractor(starting_dir, '', '.asc', data_depth=0)
    if data_dialog.exec_() == DataExtractor.Accepted:
        file_list, data_labels = data_dialog.get_output()

    # Open UI and request plot options from user
    include_dict = {'basecorrect': True, 'figsize': True}
    options = PlotOptionList()  # Create default gui options list
    options.change_includes(include_dict)  # Modify gui components
    options_dialog = PlotOptionsDialog(options)  # Build dialog w/ options
    if options_dialog.exec() == PlotOptionsDialog.Accepted:
        response_dict = options.values_todict()

    return file_list, data_labels, response_dict


def main(file_list, data_labels, figsize=(6.5, 4.5), basecorrect=True):
    """
    Plot multiple .asc files on one plot with data_labels as legend.

    Parameters
    ----------
    file_list : list of str
        list of full filepaths to ".asc" files for GC data.
    data_labels : list of str
        List of data labels used for generating plot legends.
    figsize : tuple, optional
        Desired size of output figure in inches (x,y), Default is (6.5, 4.5).
        figsize suggestions:
        1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
        1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);
    basecorrect : bool, optional
        Indicates whether or not to baseline correct individual gc data.
        The default is 'True'.

    Returns
    -------
    fig : matplotlib.pyplot.figure
        Figure handle for plot.
    ax : matplotlib.pyplot.axis
        Axis handle for plot.

    """
    fig, ax = plt.subplots()
    plot_tools.set_plot_style(figsize)
    for filename, data_label in zip(file_list, data_labels):
        data = GCData(filename, basecorrect)
        ax.plot(data.time, data.signal, label=data_label)
    plt.legend()
    plt.show()
    return fig, ax


if __name__ == "__main__":
    plt.close('all')
    file_list, data_labels, response_dict = get_user_inputs()
    fig, ax = main(file_list, data_labels, **response_dict)

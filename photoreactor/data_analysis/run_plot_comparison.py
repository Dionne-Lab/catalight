"""
Created on Fri Jun 24 17:28:48 2022

@author: brile
"""

# to actually run some analysis!

import os

import matplotlib.pyplot as plt
from photoreactor.data_analysis import analysis_tools
from photoreactor.data_analysis.data_extractor import DataExtractor
from photoreactor.data_analysis.gcdata import GCData
from photoreactor.equipment.experiment_control import Experiment

if __name__ == "__main__":

    plt.close('all')
    dialog = DataExtractor()
    if dialog.exec_() == DataExtractor.Accepted:
        file_list, data_labels = dialog.get_output()

    results_dict = {}

    for expt_path, data_label in zip(file_list, data_labels):
        log_path = os.path.join(expt_path, 'expt_log.txt')
        expt = Experiment()  # Initialize experiment obj
        expt.read_expt_log(log_path)  # Read expt parameters from log
        expt.update_save_paths(expt_path)  # update file paths
        print(os.path.split(expt_path)[1])
        result = analysis_tools.calculate_X_and_S(expt, 'c2h2', ['c2h4'])
        results_dict[data_label] = result

    ((figX, axX), (figS, axS)) = analysis_tools.multiplot_X_and_S(results_dict)
    # fig, ax = analysis_tools.multiplot_X_and_S(results_dict)
    # TODO pop up a selection box asking user which they'd like to plot

    # Standard figsize
    # 1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
    # 1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);
    print('Finished!')

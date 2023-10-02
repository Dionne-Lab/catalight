import matplotlib.pyplot as plt
import catalight.analysis.plotting as plot_tools
from catalight.equipment.experiment_control import Experiment

# get all the file names
# assign save folder
filenames = [r"G:\Shared drives\Photocatalysis Projects\catalight_experiments\20230925\20230504_Au95Pd5_4wt_3mg\20230927temp_sweep_0mW_530nm_0.94Ar_0.01C2H2_0.05H2_0N2frac_10sccm\Results\4.35w_Conv_Sel_plot.pickle"]
for file in filenames:
    fig, ax = plot_tools.open_pickled_fig(file)
    ax.set_ylim([0, 10])
    plt.show()
    #save figure

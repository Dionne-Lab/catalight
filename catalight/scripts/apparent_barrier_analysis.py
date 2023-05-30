import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import catalight.analysis.tools as analysis_tools

main_dir = (r"G:\Shared drives\Photocatalysis Projects\AgPd Polyhedra"
            r"\Ensemble Reactor\20230504_Au95Pd5_4wt")
filepaths = analysis_tools.list_matching_files(main_dir,
                                               'expt_log', '.txt')
expts = analysis_tools.list_expt_obj(filepaths)

data_list = []
fig, axes = plt.subplots(3, 4)
main_ax = fig.add_subplot(111, frameon=False)
# hide tick and tick label of the big axis
main_ax.tick_params(labelcolor='none', which='both',
                    top=False, bottom=False, left=False, right=False)
main_ax.set_xlabel('1/T [1/K]', fontsize=18)
main_ax.set_ylabel('Rate [umol/mg/s]', fontsize=18)
axes = axes.flatten()
switch = int(len(filepaths)/len(axes))+1
n = 1
for expt in expts:
    results = analysis_tools.calculate_X_and_S(expt, reactant='C2H2',
                                               target_molecule='C2H4')

    rate_abs = results['Conversion'] * expt.tot_flow / (60 * 22400) * 10**6
    mass = 19.2
    wt_per = 0.04
    rate = rate_abs/(mass * wt_per)
    T = np.array(expt.temp)+273
    p, V = np.polyfit(1/T, rate, deg=1, cov=True)
    std_dev = np.sqrt(V.diagonal())
    rel_error = std_dev/p
    barrier = p[0]
    axes[n//switch-1].plot(1/T, rate, 'o')
    axes[n//switch-1].plot(1/T, p[0]/T + p[1], '--k')
    data_list.append([expt.power[0], expt.wavelength[0], barrier])
    n+=1
plt.tight_layout()
data = pd.DataFrame(data_list, columns=['Power', 'Wavelength', 'Barrier'])
fig = plt.figure()
ax = Axes3D(fig)
surf = ax.plot_trisurf(data['Power'], data['Wavelength'], data['Barrier'])
plt.show()

import os
import pdb

import gcdata
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

# User inputs
##############################################################################

calibrationPath = '/Users/ccarlin/Google Drive/Shared drives/Photocatalysis Reactor/Reactor Baseline Experiments/GC Calibration/calib_202012/HayD_FID_SophiaCal.csv'
calDF = pd.read_csv(calibrationPath, delimiter=',', index_col='Chem ID') # import all calibration data
index=calDF.index[0:] # getting an error that it can't access index, thinks calDF is a textfilereader, but it shouldn't be bc iterator defaults to False?
calchemIDs = calDF.index.to_numpy() # get chem IDs from calibration files
# Sample Location Info:
main = '/Users/ccarlin/src/Dionne-Lab/photoreactor/SRI_GC/gcanalysis/IntegrationTesting/20211007_TroubleChromatograms/20201217_calibration100ppm_FID01.ASC'
data = gcdata.GCData(main)
datacorrected = gcdata.GCData(main, basecorrect = True)
#pdb.set_trace()
conc = datacorrected.get_concentrations(calDF)
print(conc)
datacorrected.plot_integration()
# Plot to test
##############################################################################
#plt.close('all')
## Plotting Things Unique to Matplotlib
#plt.rcParams.update({'font.size': 14})
#plt.rcParams['axes.linewidth'] = 2
## Another way to change tick width and length
#plt.gca().tick_params(which='both', width=1.5, length=6)
#plt.gca().tick_params(which='minor', width=1.5, length=3)
#
#plt.figure
#data.integration_ind()
#[left_idx, right_idx] = (np.rint(data.left_idx).astype('int'), np.rint(data.right_idx).astype('int'))
## Plot signal
#plt.plot(data.time, data.signal, linewidth=2.5, label = 'original')
## Plot background that will be subtracted
##plt.plot(data.time, data.signal-datacorrected.signal, linewidth=2.5, label = 'subtracted')
### Plot Derivative
#plt.plot(data.time, 10*np.gradient(data.signal), label = 'derivative x10')
## Plot peak and bounds
#plt.plot(data.time[data.peak_idx], data.signal[data.peak_idx], 'o', label = 'peak index')
#plt.plot(data.time[left_idx], data.signal[left_idx], 'o', label = 'left index')
#plt.plot(data.time[right_idx], data.signal[right_idx], 'o', label = 'right index')
#
#plt.xlabel('Retention (min)', fontsize=18)
#plt.ylabel('Signal (a.u.)', fontsize=18)
#plt.xlim([0, 13])
#plt.tight_layout()
#plt.legend()
#plt.show()


# Helper functions
##############################################################################
def listfiles(folder_path):
    """Returns the .ASC files for FID data in the specified path."""
    files_list = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith('.ASC'): # Only assessing files that end with specified filetype
            id = filename[:len(filename)-4] # Disregards the file type and run number
            if id[:-2].endswith('FID'): #Only selects for FID entries
                files_list.append(id)
    return files_list

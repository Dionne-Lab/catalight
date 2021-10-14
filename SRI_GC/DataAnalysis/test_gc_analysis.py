import pandas as pd
import os
import numpy as np
import gcdata
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.cm as cm

# User inputs
##############################################################################

calibrationPath = '/Users/ccarlin/Google Drive/Shared drives/Photocatalysis Reactor/Reactor Baseline Experiments/GC Calibration/calib_202012/HayD_FID_SophiaCal.csv'
calDF = pd.read_csv(calibrationPath, delimiter=',', index_col='Chem ID') # import all calibration data
index=calDF.index[0:] # getting an error that it can't access index, thinks calDF is a textfilereader, but it shouldn't be bc iterator defaults to False?
calchemIDs = calDF.index.to_numpy() # get chem IDs from calibration files

# Sample Location Info:
main = '/Users/ccarlin/src/Dionne-Lab/photoreactor/SRI_GC/DataAnalysis/IntegrationTesting/20211007_TroubleChromatograms/20201217_calibration100ppm_FID01.ASC'
data = gcdata.GCData(main)
datacorrected = gcdata.GCData(main, basecorrect = True)


# Plot to test
##############################################################################
plt.close('all')
# Plotting Things Unique to Matplotlib
plt.rcParams.update({'font.size': 14})
plt.rcParams['axes.linewidth'] = 2
# Another way to change tick width and length
plt.gca().tick_params(which='both', width=1.5, length=6)
plt.gca().tick_params(which='minor', width=1.5, length=3)

plt.figure
data.integration_ind()
[left_idx, right_idx] = (np.rint(data.left_idx).astype('int'), np.rint(data.right_idx).astype('int'))
# Plot signal
plt.plot(data.time, data.signal, linewidth=2.5)
# Plot background that will be subtracted
plt.plot(data.time, data.signal-datacorrected.signal, linewidth=2.5)
## Plot Derivative
#plt.plot(time, 10*np.gradient(signal))
## Plot peak and bounds
#plt.plot(time[peak_idx], signal[peak_idx], 'o')
#plt.plot(time[left_idx], signal[left_idx], 'o')
#plt.plot(time[right_idx], signal[right_idx], 'o')

plt.xlabel('Retention (min)', fontsize=18)
plt.ylabel('Signal (a.u.)', fontsize=18)
plt.xlim([0, 13])
plt.tight_layout()
plt.show()


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

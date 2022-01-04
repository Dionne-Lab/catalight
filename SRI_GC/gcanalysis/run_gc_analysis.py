# to actually run some analysis!
import pandas as pd
import os
import numpy as np
from .gcdata import GCData


# User inputs
##############################################################################

# Calibration Location Info:
# Format [ChemID, slope, intercept, start, end]
calibrationPath = '/Users/ccarlin/Google Drive/Shared drives/Photocatalysis Reactor/Reactor Baseline Experiments/GC Calibration/calib_202012/HayD_FID_SophiaCal.csv'
calDF = pd.read_csv(calibrationPath, delimiter=',', index_col='Chem ID') # import all calibration data
index=calDF.index[0:] # getting an error that it can't access index, thinks calDF is a textfilereader, but it shouldn't be bc iterator defaults to False?
calchemIDs = calDF.index.to_numpy() # get chem IDs from calibration files

# Sample Location Info:
main = '/Users/ccarlin/Google Drive/Shared drives/Photocatalysis Reactor/Reactor Baseline Experiments/GC Calibration/calib_202012/SophiasSelectDataSets/'
subfolders = [ f.name for f in os.scandir(main) if f.is_dir() ]
maxRuns = 0

# processing options
basecorrect = True # True = data will be baseline corrected MOVE THIS TO INITIALIZATION OF CLASS

# Analysis Loop
##############################################################################
numFols = len(subfolders)
numChems = int(len(calchemIDs))

for fol in subfolders: # Determines largest # of runs in subfolder
    alist = listfiles(main+fol)
    if len(alist)>maxRuns:
        maxRuns = len(alist)

run_number = []
conversion = []
results = np.full( (numFols, numChems, maxRuns), np.nan )

# Eventually, the conditions will be defined by the subfolder names (pressure, Temp, Power)
for condition in range(len(subfolders)):
    fol = subfolders[condition]
    alist = listfiles(main+fol)
    conc = []
    for files in alist:
        filepath = main + fol + "/" + files + '.ASC'
        data = GCData(filepath) # data is an instance of a class, for signal use data.signal etc
        if basecorrect == True:
            data.baseline_correction()
        conc.append(data.get_concentrations(calDF).tolist())

    numRuns = len(conc)
    results[condition, :, 0:numRuns] = np.asarray(conc).T

# Results
##############################################################################
avgDat = np.nanmean(results, axis=2)
avg = pd.DataFrame(avgDat, columns=calchemIDs, index=subfolders)
stdDat = np.nanstd(results, axis=2)
std = pd.DataFrame(stdDat, columns=calchemIDs, index=subfolders)
print('finished')


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

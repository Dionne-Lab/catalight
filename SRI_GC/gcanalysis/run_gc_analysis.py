# to actually run some analysis!
import pandas as pd
import os, re
import numpy as np
import matplotlib.pyplot as plt
from gcdata import GCData


# Helper functions
##############################################################################
def listfiles(folder_path):
    """Returns the .ASC files for FID data in the specified path."""
    files_list = []
    for filename in sorted(os.listdir(folder_path)):
        if (filename.endswith('.ASC')) & ('FID' in filename): # Only assessing files that end with specified filetype
#            id = filename[:len(filename)-4] # Disregards the file type and run number
#            if id[:-2].endswith('FID'): # Only selects for FID entries
            files_list.append(filename)
    return files_list

def get_run_number(filename):
    """returns run number based on filename"""
    parts = filename.split('.') # Seperate filename at each period
    # Second to last part always has run num
    run_num_part = parts[len(parts)-2] 
    run_number = re.search(r'\d+$', run_num_part) # \d digit; + however many; $ at end
    return int(run_number.group()) if run_number else None

# User inputs
##############################################################################

# Calibration Location Info:
# Format [ChemID, slope, intercept, start, end]

# We need to put the calibration data somewhere thats accessible with a common path

# calibration_path = '/Users/ccarlin/Google Drive/Shared drives/Photocatalysis Reactor/Reactor Baseline Experiments/GC Calibration/calib_202012/HayD_FID_SophiaCal.csv'

#calibration_path = "G:\\Shared drives\\Photocatalysis Reactor\\Reactor Baseline Experiments\\GC Calibration\\calib_202012\\HayD_FID_SophiaCal.csv"

calibration_path = "G:\\Shared drives\\Photocatalysis Reactor\\Reactor Baseline Experiments\\GC Calibration\\20210930_DummyCalibration\\HayN_FID_C2H2_DummyCal.csv"

calDF = pd.read_csv(calibration_path, delimiter=',', index_col='Chem ID') # import all calibration data
index=calDF.index[0:] # getting an error that it can't access index, thinks calDF is a textfilereader, but it shouldn't be bc iterator defaults to False?
calchemIDs = calDF.index.to_numpy() # get chem IDs from calibration files

# Sample Location Info:
#expt_data_fol = '/Users/ccarlin/Google Drive/Shared drives/Photocatalysis Reactor/Reactor Baseline Experiments/GC Calibration/calib_202012/SophiasSelectDataSets/'

expt_data_fol = "G:\\Shared drives\\Hydrogenation Projects\\AgPd Polyhedra\\Ensemble Reactor\\202111_pretreatment_tests_sorted\\20210524_8%AgPdMix_1wt%__200C_24.8mg\\PostReduction\\Data"

max_runs = 0

# processing options
basecorrect = True # True = data will be baseline corrected MOVE THIS TO INITIALIZATION OF CLASS

# Analysis Loop
##############################################################################
print('Analyzing Data...')
plt.close('all')
expt_results_fol = os.path.join(os.path.dirname(expt_data_fol), 'Results')
os.makedirs(expt_results_fol, exist_ok=True)

plt.rcParams.update({'font.size': 14})
plt.rcParams['axes.linewidth'] = 1.5

step_path_list = [] 
for dirpath, dirnames, filenames in os.walk(expt_data_fol):
    num_data_points = len(listfiles(dirpath)) # only looks at .ASC
    if not dirnames: # determine bottom most dirs
        step_path_list.append(dirpath)
    if num_data_points>max_runs: # Determines largest # of runs in any dir
        max_runs = num_data_points
        

fig1, ax1 = plt.subplots() # initilize run num plot

num_fols = len(step_path_list)
num_chems = int(len(calchemIDs))

run_number = []
conversion = []
condition = np.full( num_fols, 0, dtype=object)
results = np.full( (num_fols, num_chems, max_runs), np.nan )

# Eventually, the conditions will be defined by the subfolder names (pressure, Temp, Power)
for step_num in range(0, len(step_path_list)):
    step_path = step_path_list[step_num]
    data_list = listfiles(step_path)
    condition[step_num] = os.path.basename(step_path)
    conc = []
    for file in data_list:
        filepath = os.path.join(step_path, file)
        data = GCData(filepath) # data is an instance of a class, for signal use data.signal etc
        if basecorrect == True:
            data.baseline_correction()
        run_num = get_run_number(file)
        values = data.get_concentrations(calDF)
        conc.append(values.tolist())
        
    num_runs = len(conc)
    # [Condition x ChemID x run number]
    results[step_num, :, 0:num_runs] = np.asarray(conc).T

for chem_num in range(len(calchemIDs)):
    chemical = calchemIDs[chem_num]
    ind_results = results[:, chem_num, :]
    ind_results = ind_results[~np.isnan(ind_results)]
    ax1.plot(ind_results, 'o', label=chemical)
    ax1.legend()
    
# Results
##############################################################################
avg_dat = np.nanmean(results, axis=2)
avg = pd.DataFrame(avg_dat, columns=calchemIDs, index=condition)
std_dat = np.nanstd(results, axis=2)
std = pd.DataFrame(std_dat, columns=calchemIDs, index=condition)

# Plotting
##############################################################################

plt.xlabel('Run Number (#)', fontsize=18)
plt.ylabel('Conc (ppm)', fontsize=18)
plt.gca().tick_params(which='both', width=1.5, length=6)
plt.gca().tick_params(which='minor', width=1.5, length=3)
plt.tight_layout()

ax2 = avg.plot(marker='o', yerr=std)
ax2.set_xlabel('Temperature (K)', fontsize=18)
ax2.set_ylabel('Conc (ppm)', fontsize=18)

print('Finished!')

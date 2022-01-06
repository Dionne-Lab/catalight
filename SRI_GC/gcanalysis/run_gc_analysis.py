# to actually run some analysis!
import os, re, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from gcdata import GCData

# getting the name of the directory where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))
  
# Getting the parent directory name where the current directory is present.
parent = os.path.dirname(current)
  
# adding the parent directory to the sys.path.
sys.path.append(parent)

from experiment_control import Experiment

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

def run_analysis(Expt1, calDF, basecorrect='True'):
    # Analysis Loop
    ##############################################################################
    print('Analyzing Data...')

    expt_data_fol = Expt1.data_path
    expt_results_fol = Expt1.results_path
    os.makedirs(expt_results_fol, exist_ok=True)
    calchemIDs = calDF.index.to_numpy() # get chem IDs from calibration files
    max_runs = 0
    step_path_list = [] 
    for dirpath, dirnames, filenames in os.walk(expt_data_fol):
        num_data_points = len(listfiles(dirpath)) # only looks at .ASC
        if not dirnames: # determine bottom most dirs
            step_path_list.append(dirpath)
        if num_data_points>max_runs: # Determines largest # of runs in any dir
            max_runs = num_data_points
    
    num_fols = len(step_path_list)
    num_chems = int(len(calchemIDs))
    
    run_number = []
    conversion = []
    condition = np.full( num_fols, 0, dtype=object)
    results = np.full( (num_fols, num_chems, max_runs), np.nan )
    
    # Loops through the ind var step and calculates conc in each data file
    for step_num in range(0, len(step_path_list)):
        step_path = step_path_list[step_num]
        data_list = listfiles(step_path)
        condition[step_num] = os.path.basename(step_path)
        conc = []
        for file in data_list:
            filepath = os.path.join(step_path, file)
            # data is an instance of a class, for signal use data.signal etc
            data = GCData(filepath) 
            
            if basecorrect == True:
                data.baseline_correction()
                
            run_num = get_run_number(file)
            values = data.get_concentrations(calDF)
            conc.append(values.tolist())
            
        num_runs = len(conc)
        # [Condition x ChemID x run number]
        results[step_num, :, 0:num_runs] = np.asarray(conc).T
        
    # Results
    ###########################################################################
    avg_dat = np.nanmean(results, axis=2)
    avg = pd.DataFrame(avg_dat, columns=calchemIDs, index=condition)
    std_dat = np.nanstd(results, axis=2)
    std = pd.DataFrame(std_dat, columns=calchemIDs, index=condition)
    
    np.save(os.path.join(expt_results_fol, 'results'), results)
    avg.to_csv(os.path.join(expt_results_fol, 'avg_conc.csv'))
    std.to_csv(os.path.join(expt_results_fol, 'std_conc.csv'))
    return(results, avg, std)

def plot_results(Expt1, CalDF):
    # Plotting
    ###########################################################################
    print('Plotting...')
    plt.close('all')
    plt.rcParams.update({'font.size': 14})
    plt.rcParams['axes.linewidth'] = 1.5
    calchemIDs = calDF.index.to_numpy() # get chem IDs from calibration files
    
    fig1, ax1 = plt.subplots() # initilize run num plot
    for chem_num in range(len(calchemIDs)):
        chemical = calchemIDs[chem_num]
        ind_results = results[:, chem_num, :]
        ind_results = ind_results[~np.isnan(ind_results)]
        ax1.plot(ind_results, 'o', label=chemical)
        ax1.legend()
        
    plt.xlabel('Run Number (#)', fontsize=18)
    plt.ylabel('Conc (ppm)', fontsize=18)
    plt.gca().tick_params(which='both', width=1.5, length=6)
    plt.gca().tick_params(which='minor', width=1.5, length=3)
    plt.tight_layout()
    
    ax2 = avg.plot(marker='o', yerr=std)
    fig2 = ax2.get_figure()
    ax2.set_xlabel('Temperature (K)', fontsize=18)
    ax2.set_ylabel('Conc (ppm)', fontsize=18)
    plt.tight_layout()
    
    fig1.savefig(os.path.join(Expt1.results_path, 'run_num_plot.svg'), format="svg")
    fig2.savefig(os.path.join(Expt1.results_path, 'avg_conc_plot.svg'), format="svg")
    
    return (ax1, ax2)
if __name__ == "__main__":
    
    # User inputs
    ###########################################################################
    
    # Calibration Location Info:
    # Format [ChemID, slope, intercept, start, end]
    
    # We need to put the calibration data somewhere thats accessible with a common path
    
    # calibration_path = ('/Users/ccarlin/Google Drive/Shared drives/'
    #                     'Photocatalysis Reactor/Reactor Baseline Experiments/'
    #                     'GC Calibration/calib_202012/HayD_FID_SophiaCal.csv')
    
    # calibration_path = ("G:\\Shared drives\\Photocatalysis Reactor\\"
    #                     "Reactor Baseline Experiments\\GC Calibration\\"
    #                     "calib_202012\\HayD_FID_SophiaCal.csv")
    
    calibration_path = ("G:\\Shared drives\\Photocatalysis Reactor\\"
                        "Reactor Baseline Experiments\\GC Calibration\\"
                        "20210930_DummyCalibration\\HayN_FID_C2H2_DummyCal.csv")
     
    # Sample Location Info:
    log_path = (r'C:/Users/brile/Documents/Temp Files/'
                '20210524_8%AgPdMix_1wt%__200C_24.8mg/PostReduction/expt_log.txt')
    
    # Main Script
    ###########################################################################
    # import all calibration data
    calDF = pd.read_csv(calibration_path, delimiter=',', index_col='Chem ID') 
    Expt1 = Experiment()
    Expt1.read_expt_log(log_path)
    Expt1.update_save_paths(log_path)
    
    (results, avg, std) = run_analysis(Expt1, calDF)
    (ax1, ax2) = plot_results(Expt1, calDF)

    print('Finished!')
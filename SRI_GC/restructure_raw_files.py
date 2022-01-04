# -*- coding: utf-8 -*-
"""
Created on Wed Dec 22 14:20:44 2021
The code is meant to restructure the data hierarchy of raw data from GC runs
prior to the development of the photoreactor GUI. Input information about a set
of files (an experiment) and output reorganized data in the new format (ready for analysis)
@author: brile
"""

from experiment_control import Experiment
import os, shutil, time, re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def listfiles(folder_path):
    """Returns the .ASC files for FID data in the specified path."""
    # I could pull this from the analysis module 
# but there are import issues under current config
    files_list = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith('.ASC'): # Only assessing files that end with specified filetype
            id = filename[:len(filename)-4] # Disregards the file type and run number
            if id[:-2].endswith('FID'): #Only selects for FID entries
                files_list.append(id)
    return files_list

def get_run_number(filename):
    """returns run number based on filename"""
    parts = filename.split('.') # Seperate filename at each period
    # Second to last part always has run num
    run_num_part = parts[len(parts)-2] 
    run_number = re.search(r'\d+$', run_num_part) # \d digit; + however many; $ at end
    return int(run_number.group()) if run_number else None

def get_run_name(filename):
    '''    
    Parameters
    ----------
    filename : filename for data set. can have extension or not.
    '.' in filename should be ok.

    Returns
    -------
    run_name : str containing filename without appended number or extension
    returns False if filename doesn't contain FID or TCD

    '''
    if 'FID' in filename:
        parts = filename.split('FID') # Seperate filename at each period
        run_name = parts[0]+'FID'
    elif 'TCD' in filename:
        parts = filename.split('TCD') # Seperate filename at each period
        run_name = parts[0]+'TCD'
    else:
        run_name = False
    return(run_name)

def calc_tempsweep(T1_K, T2_K, delta_T, SampleRate, SampleSetSize, t_Buffer, t_Ramp):
    T1_C = T1_K - 273
    T2_C = T2_K - 273
    NumSteps = int(np.ceil((T2_C-T1_C) / delta_T))
    SampleTot = SampleSetSize*(NumSteps+1)
    t_Samples = np.arange(0, (SampleTot)*SampleRate, SampleRate)
    t_Step = SampleRate*(SampleSetSize-1)+t_Buffer  # Runs t_Buffer min after last sample starts
    t_steady = SampleRate-t_Ramp-t_Buffer
    TempStarts = np.append(0, 
                           (t_Step + t_Ramp + 
                            np.arange(0, NumSteps)*(t_Step + t_Ramp + t_steady)
                           )
                          )
    TempEnds = np.append(t_Step, TempStarts[1:]+t_Step+t_steady)
    Temps = np.arange(T1_C, T2_C+delta_T, delta_T)
    t_StepEvents = np.sort(np.concatenate((TempStarts, TempEnds)))
    T_StepEvents = np.repeat(Temps, 2)
    return (t_Samples, TempStarts, TempEnds, Temps)

def plot_tempsweep(t_Samples, TempStarts, TempEnds, Temps):
    # Plotting
    ##############################################################################
    # Sections Inputs: t_Samples, TempStarts, TempEnds, Temps
    plt.close('all')
    ylim_max = 1.1*Temps[-1]
    ylim_min = 0
    plt.vlines(t_Samples, ylim_min, ylim_max, linestyle='dashed', color = 'black')
    plt.plot(TempStarts, Temps, 'o')
    plt.plot(TempEnds, Temps, 'ro')
    
    # Concantenates time and Temp events in correct order for plotting
    t_StepEvents = np.sort(np.concatenate((TempStarts, TempEnds)))
    T_StepEvents = np.repeat(Temps, 2)
    
    plt.plot(t_StepEvents, T_StepEvents)
    
    return

def restructure_data(sample_path, Temps, SampleSetSize):
    '''
    Calling this function will sort unorganized data in sample_path into a data
    hierarchy ready for analysis by GUI's analysis script
    TODO: this code currently only accepts temperature sweeps, but could be generalized
    
    Parameters
    ----------
    sample_path : Path to original experiment data. this should be a folder
    with unorganized raw data ready to be sorted
    Temps : numpy array of temperatures for a temperature sweep experiment
    SampleSetSize : number of samples that were collected at each sweep value

    Returns
    -------
    None.

    '''
    # Calculate num of samples based on sample set size and num temp values
    SampleTot = SampleSetSize*len(Temps)
    
    # List all files with .ASC extension (i.e. data files)
    raw_files = listfiles(sample_path)
    
    # List all files in main fol regardless of extension
    full_file_list = sorted(os.listdir(sample_path))
    
    # We create an "experiment" as if the GUI just ran
    Expt1 = Experiment()
    Expt1.set_expt_type('temp_sweep') # TODO this could be generalized
    Expt1.temp = Temps + 273 # Input numpy array of temps in K
    Expt1.create_dirs(sample_path)
    
    # Pulls correct units given expt_type
    units = (Expt1.expt_list['Units']
             [Expt1.expt_list['Active Status']].to_string(index=False))
    
    starting_run_num = get_run_number(raw_files[0])
    
    if starting_run_num != 1: # If the first run number isn't 1, renames every file
        
        # Create a new directory in which to place copy of files with original names
        uneditted_dir = os.path.join(sample_path, 'uneditted_files')
        os.makedirs(uneditted_dir, exist_ok=True)
        
        for filename in full_file_list: # Loop through files, copy original, change names
            
            run_name = get_run_name(filename)
            og_filepath = os.path.join(sample_path, filename)
            uneditted_filepath =  os.path.join(uneditted_dir, filename)
            shutil.copy(og_filepath, uneditted_filepath)
            
            if not run_name: # if filename doesn't have FID or TCD, skip
                continue
            
            # Change ending number and rename file
            run_num = get_run_number(filename)
            new_num = run_num - starting_run_num + 1
            extension = filename.split('.')[-1]
            new_filename = run_name + ("%02d" % (new_num)) + '.' + extension
            new_filepath = os.path.join(sample_path, new_filename)
            os.rename(og_filepath, new_filepath)
            
        # Rename Lists after renaming all the files!!
        raw_files = listfiles(sample_path)
        full_file_list = sorted(os.listdir(sample_path))
            
    
    for basename in raw_files: # Loop through files and move to new location
        
        run_num = int(get_run_number(basename)) # Get run number from filename
        run_type = get_run_name(basename)[-3:] # Returns FID or TCD
        new_name = run_type+str(run_num)
        expt_step = (run_num-1)//SampleSetSize # Starting at 0 for first step
        
        if expt_step < (SampleTot/SampleSetSize):
            step_val = Temps[expt_step]+273
            step_fol = (str(step_val) + units)
            
            # matching is list of files containing basename (all extensions)
            matching = [filename for filename in full_file_list if basename in filename]
            while not os.path.isdir(os.path.join(Expt1.data_path, step_fol)):
                time.sleep(0.01) # incase os.makedirs is slow
                print('Waiting on Directory Creation')
            for filename in matching: # for each file type, move to new location
                og_filepath = os.path.join(sample_path, filename)
                new_filepath = os.path.join(Expt1.data_path, step_fol, new_name+filename[-4:])
                os.renames(og_filepath, new_filepath)
                #shutil.copy(og_filepath, new_filepath)
    
        else:
            over_run_path = os.path.join(Expt1.data_path, 'Over Run Data')
            os.makedirs(over_run_path, exist_ok=True)
            time.sleep(1)
            matching = [filename for filename in full_file_list if basename in filename]

            while not os.path.isdir(over_run_path): # incase os.makedirs is slow
                time.sleep(0.01)
                print('Waiting on Directory Creation')
            for filename in matching:
                og_filepath = os.path.join(sample_path, filename)
                new_filepath = os.path.join(over_run_path, new_name+filename[-4:])
                os.renames(og_filepath, new_filepath)
                #shutil.copy(og_filepath, new_filepath)
                print('Over run - ' + str(run_num))
                
# User Inputs
##############################################################################
T1_K = 300  # Starting Temp
T2_K = 410  # Ending Temp
delta_T = 10  # Temp Spacing
SampleRate = 10  # Sample/min
SampleSetSize = 4  # Samples/Condition Set
t_Buffer = 4  # Time before transitioning after end of segment 
t_Ramp = 1  # Ramp rate between temp set points

# This should be the path where you want the data to be restructured.
# currently only supports temp sweeps, but you can send a main folder which
# which contains multiple folders worth of temp sweeps
main_dir = "G:\\Shared drives\\Hydrogenation Projects\\AgPd Polyhedra\\Ensemble Reactor\\202111_pretreatment_tests\\"
#main_dir = 'C:\\Users\\brile\\Documents\\Temp Files\\202111_pretreatment_tests - Copy'
#main_dir = "C:\\Users\\brile\\Documents\\Temp Files\\20211223_filecopytest\\"

# Main Script
##############################################################################
user_values = T1_K, T2_K, delta_T, SampleRate, SampleSetSize, t_Buffer, t_Ramp
sweep_values = calc_tempsweep(*user_values)
t_Samples, TempStarts, TempEnds, Temps = sweep_values

# Finds bottom most directories (original experiments)
sample_paths = [] 
for dirpath, dirnames, filenames in os.walk(main_dir):
    if not dirnames:
        sample_paths.append(dirpath)

# Loops through experiment dirs and reorganizes data within each
for sample_path in sample_paths:
    restructure_data(sample_path, Temps, SampleSetSize)
print('Finished!!')
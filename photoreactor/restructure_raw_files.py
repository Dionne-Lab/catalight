# -*- coding: utf-8 -*-
"""
Created on Wed Dec 22 14:20:44 2021
The code is meant to restructure the data hierarchy of raw data from GC runs
prior to the development of the photoreactor GUI. Input information about a set
of files (an experiment) and output reorganized data in the new format (ready for analysis)
TODO: show the user the produced experiment profile first, then ask to proceed
TODO: code an exception in the event that a file path is >260 characters
Known Bugs: if file path is >260 characters, os.renames will give an error
that sounds like the issue is a missing file
@author: brile
"""

import datetime as dt
import os
import re
import shutil
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from experiment_control import Experiment


def listfiles(folder_path):
    """Returns the .ASC files for FID data in the specified path."""
    # I could pull this from the analysis module
# but there are import issues under current config
    files_list = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith('.ASC'):  # Only assessing files that end with specified filetype
            # Disregards the file type and run number
            id = filename[:len(filename)-4]
            if id[:-2].endswith('FID'):  # Only selects for FID entries
                files_list.append(id)
    return files_list


def get_run_number(filename):
    """returns run number based on filename"""
    parts = filename.split('.')  # Seperate filename at each period
    # Second to last part always has run num
    run_num_part = parts[len(parts)-2]
    # \d digit; + however many; $ at end
    run_number = re.search(r'\d+$', run_num_part)
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
        parts = filename.split('FID')  # Seperate filename at each period
        run_name = parts[0]+'FID'
    elif 'TCD' in filename:
        parts = filename.split('TCD')  # Seperate filename at each period
        run_name = parts[0]+'TCD'
    else:
        run_name = False
    return(run_name)


def calc_tempsweep(T1_K, T2_K, delta_T, sample_rate, sample_set_size, t_buffer, t_ramp):
    T1_C = T1_K - 273
    T2_C = T2_K - 273
    num_steps = int(np.ceil((T2_C-T1_C) / delta_T))
    sample_tot = sample_set_size*(num_steps+1)
    t_samples = np.arange(0, (sample_tot)*sample_rate, sample_rate)
    # Runs t_buffer min after last sample starts
    t_Step = sample_rate*(sample_set_size-1)+t_buffer
    t_steady = sample_rate-t_ramp-t_buffer
    Temp_starts = np.append(0,
                            (t_Step + t_ramp +
                             np.arange(0, num_steps)*(t_Step + t_ramp + t_steady)
                             )
                            )
    Temp_ends = np.append(t_Step, Temp_starts[1:]+t_Step+t_steady)
    Temps = np.arange(T1_C, T2_C+delta_T, delta_T)
    t_step_events = np.sort(np.concatenate((Temp_starts, Temp_ends)))
    T_step_events = np.repeat(Temps, 2)
    return (t_samples, Temp_starts, Temp_ends, Temps)


def calc_powersweep(P1, P2, delta_P, sample_rate, sample_set_size, t_buffer, t_ramp):
    num_steps = int(np.ceil((P2-P1) / delta_P))
    sample_tot = sample_set_size*(num_steps+1)
    t_samples = np.arange(0, (sample_tot)*sample_rate, sample_rate)
    power_sweep = np.arange(P1, P2, delta_P)
    t1 = (sample_set_size-1) * sample_rate + t_buffer
    t_space = t1 + t_buffer + t_ramp
    t_trans = np.append(34, np.ones(len(power_sweep)-1)*t_space)*60
    return (t_samples, t_trans, power_sweep)


def plot_tempsweep(t_samples, Temp_starts, Temp_ends, Temps):
    # Plotting
    ##############################################################################
    # Sections Inputs: t_samples, Temp_starts, Temp_ends, Temps
    plt.close('all')
    ylim_max = 1.1*Temps[-1]
    ylim_min = 0
    plt.vlines(t_samples, ylim_min, ylim_max, linestyle='dashed', color='black')
    plt.plot(Temp_starts, Temps, 'o')
    plt.plot(Temp_ends, Temps, 'ro')

    # Concantenates time and Temp events in correct order for plotting
    t_step_events = np.sort(np.concatenate((Temp_starts, Temp_ends)))
    T_step_events = np.repeat(Temps, 2)

    plt.plot(t_step_events, T_step_events)
    plt.xlabel('time (min)')
    plt.ylabel('Temp (C)')
    plt.ylim([ylim_min, ylim_max])
    return


def plot_powersweep(t_samples, t_trans, power_sweep):
    plt.close('all')
    plt.figure()
    ylim_max = 1.1*np.max(power_sweep)
    ylim_min = 0
    plt.vlines(t_samples, ylim_min, ylim_max, linestyle='dashed', color='black')
    plt.plot(np.cumsum(t_trans)/60, power_sweep, 'ro')
    plt.plot((np.cumsum(t_trans)-t_trans)/60, power_sweep, 'o')
    plt.hlines(power_sweep, (np.cumsum(t_trans)-t_trans)/60, np.cumsum(t_trans)/60)
    plt.xlabel('time (min)')
    plt.ylabel('Power (mW)')
    plt.ylim([ylim_min-1, ylim_max])
    plt.xlim(-3, np.cumsum(t_trans)[-1]/60+3)
    return


def restructure_data(sample_path, Expt1, sample_set_size):
    '''
    Calling this function will sort unorganized data in sample_path into a data
    hierarchy ready for analysis by GUI's analysis script

    Parameters
    ----------
    sample_path : Path to original experiment data. this should be a folder
    with unorganized raw data ready to be sorted
    Expt1 : experiment object for the given run atleast containing sweep values
    sample_set_size : number of samples that were collected at each sweep value

    Returns
    -------
    None.

    '''
    # Calculate num of samples based on sample set size and num temp values
    sample_tot = sample_set_size*len(Temps)

    # List all files with .ASC extension (i.e. data files)
    raw_files = listfiles(sample_path)

    # List all files in main fol regardless of extension
    full_file_list = sorted(os.listdir(sample_path))

    # Pulls correct units given expt_type
    units = (Expt1.expt_list['Units']
             [Expt1.expt_list['Active Status']].to_string(index=False))

    starting_run_num = get_run_number(raw_files[0])
    starting_date = os.path.getmtime(os.path.join(sample_path, full_file_list[1]))
    Expt1._date = dt.datetime.utcfromtimestamp(starting_date).strftime('%Y%m%d')
    Expt1.create_dirs(sample_path)

    if starting_run_num != 1:  # If the first run number isn't 1, renames every file

        # Create a new directory in which to place copy of files with original names
        uneditted_dir = os.path.join(sample_path, 'uneditted_files')
        os.makedirs(uneditted_dir, exist_ok=True)

        for filename in full_file_list:  # Loop through files, copy original, change names

            run_name = get_run_name(filename)
            og_filepath = os.path.join(sample_path, filename)
            uneditted_filepath = os.path.join(uneditted_dir, filename)
            shutil.copy(og_filepath, uneditted_filepath)

            if not run_name:  # if filename doesn't have FID or TCD, skip
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

    for basename in raw_files:  # Loop through files and move to new location

        run_num = int(get_run_number(basename))  # Get run number from filename
        run_type = get_run_name(basename)[-3:]  # Returns FID or TCD
        new_name = run_type+str(run_num)
        expt_step = (run_num-1)//sample_set_size  # Starting at 0 for first step

        if expt_step < (sample_tot/sample_set_size):
            # getattr returns sweep list for ind. variable
            step_val = getattr(Expt1, Expt1.ind_var)[expt_step]
            step_fol = (str(expt_step+1) + '_' + str(step_val) + units)
            step_fol = ('%i %s%s' % (expt_step+1, step_val, units))
            # matching is list of files containing basename (all extensions)
            matching = [
                filename for filename in full_file_list if basename in filename]
            while not os.path.isdir(os.path.join(Expt1.data_path, step_fol)):
                time.sleep(0.01)  # incase os.makedirs is slow
                print('Waiting on Directory Creation')

            for filename in matching:  # for each file type, move to new location
                og_filepath = os.path.join(sample_path, filename)
                new_filepath = os.path.join(
                    Expt1.data_path, step_fol, new_name+filename[-4:])
                os.renames(og_filepath, new_filepath)
                #shutil.copy(og_filepath, new_filepath)

        else:
            over_run_path = os.path.join(Expt1.data_path, str(expt_step+1) + ' Over_Run_Data')
            os.makedirs(over_run_path, exist_ok=True)
            matching = [
                filename for filename in full_file_list if basename in filename]

            while not os.path.isdir(over_run_path):  # incase os.makedirs is slow
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
# Used if setting temp sweep
T1_K = 300  # Starting Temp
T2_K = 410  # Ending Temp
delta_T = 10  # Temp Spacing

# Used if setting power sweep
P1 = 0  # Starting Power
P2 = 100  # Ending Power
delta_P = 10  # Power Spacing

sample_rate = 10  # Sample/min
sample_set_size = 4  # Samples/Condition Set
t_buffer = 4  # Time before transitioning after end of segment
t_ramp = 1  # Ramp rate between temp set points

# We create an "experiment" as if the GUI just ran
Expt1 = Experiment()
# current options are 'temp_sweep' or 'power_sweep'
Expt1.expt_type = 'temp_sweep'
Expt1.gas_comp = [(np.array([0.5, 47, 2.5])/50).tolist()
                  ]  # [gas1, gas2, gas3] in sccm
Expt1.tot_flow = [50]
Expt1.gas_type = ['C2H2', 'Ar', 'H2']  # gas types for 3 MFCs

# This should be the path where you want the data to be restructured.
# currently only supports temp sweeps, but you can send a main folder which
# which contains multiple folders worth of temp sweeps
main_dir = (r'G:\Shared drives\Photocatalysis Projects\AgPd Polyhedra'
            r'\Ensemble Reactor\20210524_8%AgPdMix_1wt%_pretreatment_test')

#main_dir = 'C:\\Users\\brile\\Documents\\Temp Files\\202111_pretreatment_tests - Copy'
#main_dir = "C:\\Users\\brile\\Documents\\Temp Files\\20211223_filecopytest\\"
#main_dir = r"C:\Users\brile\Documents\Temp Files\20210524_8%AgPdMix_1wt%__400C_25mg"

# Main Script
##############################################################################
if Expt1.expt_type == 'temp_sweep':
    user_values = T1_K, T2_K, delta_T, sample_rate, sample_set_size, t_buffer, t_ramp
    sweep_values = calc_tempsweep(*user_values)
    t_samples, Temp_starts, Temp_ends, Temps = sweep_values
    Expt1.temp = Temps + 273  # Input numpy array of temps in K
    plot_tempsweep(t_samples, Temp_starts, Temp_ends, Temps)
elif Expt1.expt_type == 'power_sweep':
    user_values = P1, P2, delta_P, sample_rate, sample_set_size, t_buffer, t_ramp
    sweep_values = calc_powersweep(*user_values)
    t_samples, t_trans, power_sweep = sweep_values
    Expt1.power = power_sweep
    plot_powersweep(t_samples, t_trans, power_sweep)
else:
    raise ValueError('Experiment type not currently supported by program')

# Finds bottom most directories (original experiments)
sample_paths = []
for dirpath, dirnames, filenames in os.walk(main_dir):
    if not dirnames:
        sample_paths.append(dirpath)

# Loops through experiment dirs and reorganizes data within each
for sample_path in sample_paths:
    restructure_data(sample_path, Expt1, sample_set_size)
print('Finished!!')
print('Finished!!')

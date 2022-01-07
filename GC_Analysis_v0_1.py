# -*- coding: utf-8 -*-
"""
Created on Fri Sep 10 17:55:21 2021

@author: pringle bringle
"""

import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt
import scipy
import scipy.signal as scisig
from matplotlib.lines import Line2D
import matplotlib.cm as cm


def get_raw_gc_data(filename):
    """Uses Matthias Richter's example code (translated from Matlab) to read GC .ASC files"""
    with open(filename, 'r') as f:
        
        #Skip first 18 lines
        for i in range(18):
            next(f)
        
        # Line 19, date
        [month, day, year] = [int(i.strip()) for i in f.readline().split("=")[1].split('-')]
        
        # Line 20, time
        [hr, minute, second] = [int(i.strip()) for i in f.readline().split("=")[1].split(':')]
        timecode = dt.datetime(year, month, day, hr, minute, second).timestamp()
        
        # Line 21, sampling rate
        rate = int(f.readline().split('=')[1][0])
        
        # Line 22 # of data points
        size = int(f.readline().split("=")[1])
        
        #Skip next 3 lines
        for i in range(3):
            next(f)
        
        y=[]
        for line in f:
            if line.strip() == '': #Empty strings in between entries
                next
            elif "IPOINT" in line: #IPOINT numbers at the bottom of the code are disregarded if present
                next
            else:
                value = int(line.strip().split(',')[0])
                y.append(value/1000) # Dividing the signal by 1000, keeping within limits/units

        x = np.linspace(0,1/rate/60*(size - 1), num=size).tolist()
        raw_data = pd.DataFrame({'Time': x, 'Signal': y})
        GC_data = (timecode, raw_data) # GC_data includes timecode in order to be synced with EC data
    return raw_data

def list_files(folder_path):
    """Returns the .ASC files for FID data."""    
    files_list = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith('.ASC'): # Only assessing files that end with specified filetype
            id = filename[:len(filename)-4] # Disregards the file type and run number
            if id[:-2].endswith('FID'): #Only selects for FID entries
                files_list.append(id)
    return files_list

def convert_to_ppm(Counts, ChemID):
    """This function assumes you have imported the calibration data as a 
    global variable called CalDF. Turns integrated raw counts into real concentration."""
    #This function assumes you have imported the calibration data as a global variable called CalDF
    [m, b] = (CalDF.loc[ChemID, ['slope', 'intercept']]) # Pull Cal data for given chemical
    y = m * Counts + b # Simple Calibration equation will need to edit if calibration isn't linear
    return y # Counts in ppm

def integrate_peak(signal, left_index, right_index):
    """Integrates a single peak of a signal based on left and right indices.""" 
    # Indices have to be rounded as they are fractional coming from scisig.peak_widths
    left_index = round(left_index)
    right_index = round(right_index)
    counts = np.trapz(signal[left_index:right_index])
    if counts == 0:
        counts = 1
    return round(counts)

def get_concentrations(filepath):
    """Reads in filepath for data set and output a Pandas series of chemical
    concentrations in the same order as the calibration file"""
    data = get_raw_gc_data(filepath)
    [time, signal] = (np.asarray(data['Time']), np.asarray(data['Signal']))
    # Note to Claire:
    #This part of the analysis works ok for now. After working through the baseline
    #and the integration a bit, I'm going to want to fine tune the peak finding
    #using some challenging example sets (i.e. very low ethane)
    peak_idx, _ = scisig.find_peaks(signal, prominence=1)
    
    # Note to Claire:
    #This line and the integrate_peak fucntions are where I think we should work right now
    #The easiest addition would be to add a derivative test to search for dips 
    #in between peaks (overlaping). (i.e. setting better bounds)
    #TODO: We should add baseline fitting
    #TODO: We could add peak fitting rather than just setting bounds (Amy did this, but Dayne said its overkill)
    _, _, left_idx, right_idx = scisig.peak_widths(signal, peak_idx, rel_height=0.9)
    
    Conc = pd.Series(0, index=CalDF.index[0:]) # Creates empty series where index are ChemIDs from Cal file
    UnknownPeaks = 0
    for i in range(len(peak_idx)):
        peak_time = time[peak_idx[i]] # Determine peak time based on index
        # determine if peak falls within range for any calibration data set
        match = CalDF[(CalDF["start"] < peak_time) & (peak_time < CalDF["end"])].index
        if not match.empty: # if empty, there are no matches
            ChemID = match[0] #if not empty, names matching chemical: ChemID
            Counts = integrate_peak(signal, left_idx[i], right_idx[i]) # TODO add background subtraction
            Conc[ChemID] = (convert_to_ppm(Counts, ChemID)) # Convert counts to ppm and appends to conc list for the ChemID just found
        else:
            UnknownPeaks += 1
            # TODO I can take the ind_x and append this Unknown peak to the calibration df
            
    if UnknownPeaks>1:  # Theres always a peak from backflush right now
        print('Warning: %5d Unknown peaks detected' %(UnknownPeaks))
        
    if (Conc==0).all():  # Checks if all concentrations are zero
        print('Warning: Zero Molecules Detected')
        
    return (Conc)
    
# def find_conversion(filepath):
#     conversion = round((ethylene + ethane) / (ethylene + ethane + acetylene) * 100, 2)
#     return conversion

# def find_selectivity(filepath):
#     selectivity =  round(ethylene / (ethylene + ethane) * 100, 2)
#     return selectivity
    
def get_run_number(filename):
    parts = filename.split('_')
    run_number = int(parts[-1][-2:].lstrip("0"))
    return run_number


# User Inputs
##############################################################################
# Calibration Location Info:
# Format [ChemID, slope, intercept, start, end]
CalibrationFolder = ('G:/Shared drives/Photocatalysis Reactor/'
                   'Reactor Baseline Experiments/GC Calibration/'
                   'calib_202012/')
CalibrationFile = 'HayD_FID_SophiaCal.csv'
CalibrationPath = CalibrationFolder+CalibrationFile
CalDF = pd.read_csv(CalibrationPath, delimiter=',', index_col='Chem ID') # import all calibration data
CalChemIDs = CalDF.index.to_numpy() # get chem IDs from calibration files
                   

# Sample Location Info:
Main = "G:/Shared drives/Photocatalysis Reactor/Reactor Baseline Experiments/GC Calibration/calib_202012/SophiasSelectDataSets/"
subfolders = [ f.name for f in os.scandir(Main) if f.is_dir() ]
MaxRuns = 0
NumFols = len(subfolders)
NumChems = int(len(CalChemIDs))

for fol in subfolders: # Determines largest # of runs in subfolder
    alist = list_files(Main+fol)
    if len(alist)>MaxRuns:
        MaxRuns = len(alist)

# Analysis Loop
##############################################################################
run_number = []
conversion = []
results = np.full( (NumFols, NumChems, MaxRuns), np.nan )

# Eventually, the conditions will be defined by the subfolder names (pressure, Temp, Power)
for Condition in range(len(subfolders)):
    fol = subfolders[Condition]
    alist = list_files(Main + fol)
    Conc = []
    for files in alist:
        filepath = Main + fol + "/" + files + '.ASC'
        Conc.append(get_concentrations(filepath).tolist())
    
    NumRuns = len(Conc)
    results[Condition, :, 0:NumRuns] = np.asarray(Conc).T

# Results
##############################################################################
AvgDat = np.nanmean(results, axis=2)
Avg = pd.DataFrame(AvgDat, columns=CalChemIDs, index=subfolders)
StdDat = np.nanstd(results, axis=2)
Std = pd.DataFrame(StdDat, columns=CalChemIDs, index=subfolders)
print('finished')

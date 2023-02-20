# -*- coding: utf-8 -*-
"""
Created on Tue Jun 15 22:07:32 2021

@author: brile
"""

import datetime as dt
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.ndimage as nd
import scipy.signal as scisig


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
                y.append(value/1000) # Dividing the signal by 1000, convert from V to mV

        x = np.linspace(0, 1/rate/60*(size - 1), num=size).tolist()
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


# User Inputs
##############################################################################
# Calibration Location Info:
# Format [ChemID, slope, intercept, start, end]
#calibrationfolder = foldernamehere
#calibrationfile = 'HayD_FID_Sophia_RawCounts.csv'
#calibrationpath = calibrationfolder + calibrationfile
#CalDF = pd.read_csv(calibrationpath, delimiter=',', index_col='Chem ID') # import all calibration data
#CalChemIDs = CalDF.index.to_numpy() # get chem IDs from calibration files

# Sample Location Info:
folder = '/Users/ccarlin/src/Dionne-Lab/photoreactor/SRI_GC/DataAnalysis/IntegrationTesting/20211007_TroubleChromatograms/'
filename = '20201217_calibration100ppm_FID01'


# Calculations
##############################################################################
filepath = folder + filename +'.ASC'
data = get_raw_gc_data(filepath)
[time, signal] = (np.asarray(data['Time']), np.asarray(data['Signal']))

# Note to Claire:
    #This part of the analysis works ok for now. After working through the baseline
    #and the integration a bit, I'm going to want to fine tune the peak finding
    #using some challenging example sets (i.e. very low ethane)
# peak finding
peak_idx, _ = scisig.find_peaks(signal, prominence=1) # this works

# Note to Claire:
    #This line and the integrate_peak fucntions are where I think we should work right now
    #The easiest addition would be to add a derivative test to search for dips
    #in between peaks (overlaping). (i.e. setting better bounds)
#TODO: We should add baseline fitting
#TODO: We could add peak fitting rather than just setting bounds (Amy did this, but Dayne said its overkill)

# baseline correction
# this baseline fitting technique is based on that used in PyMassSpec (pyms/TopHat.py)
struct_elm_frac = 0.1 # default structural elemenet as fraction of total number of points
struct_pts = int(round(signal.size * struct_elm_frac))
str_el = np.repeat([1], struct_pts)
line = nd.generate_binary_structure(rank=1, connectivity=9)
signal_basesub = nd.white_tophat(input = signal, footprint=str_el)# structure = line)


# peak widths
_, _, left_idx, right_idx = scisig.peak_widths(signal, peak_idx, rel_height=0.9)


## This is essentially "get_concentrations" from the main script, if needed for testing"
#------------------------------------------------------------------------------
# Conc = pd.Series(0, index=CalDF.index[0:]) # Creates empty series where index are ChemIDs from Cal file

# UnknownPeaks = 0
# for i in range(len(peak_idx)):
#      peak_time = time[peak_idx[i]] # Determine peak time based on index
#      # determine if peak falls within range for any calibration data set
#      match = CalDF[(CalDF["start"] < peak_time) & (peak_time < CalDF["end"])].index
#      if not match.empty: # if empty, there are no matches
#          ChemID = match[0] #if not empty, names matching chemical: ChemID
#          Counts = integrate_peak(signal, left_idx[i], right_idx[i]) # TODO add background subtraction
#          Conc[ChemID] = (convert_to_ppm(Counts, ChemID)) # Convert counts to ppm and appends to conc list for the ChemID just found
#      else:
#          UnknownPeaks += 1
#          # TODO I can take the ind_x and append this Unknown peak to the calibration df

# if UnknownPeaks>1:  # Theres always a peak from backflush right now
#     print('Warning: %5d Unknown peaks detected' %(UnknownPeaks))

# if (Conc==0).all():  # Checks if all concentrations are zero
#     print('Warning: Zero Molecules Detected')
#------------------------------------------------------------------------------

# Plotting
##############################################################################

# This chunk is just setup for plotting
plt.close('all')
# Plotting Things Unique to Matplotlib
plt.rcParams.update({'font.size': 14})
plt.rcParams['axes.linewidth'] = 2
# Another way to change tick width and length
plt.gca().tick_params(which='both', width=1.5, length=6)
plt.gca().tick_params(which='minor', width=1.5, length=3)

plt.figure
[left_idx, right_idx] = (np.rint(left_idx).astype('int'), np.rint(right_idx).astype('int'))
# Plot signal
plt.plot(time, signal, linewidth=2.5)
# Plot signal with baseline subtracted
plt.plot(time, np.subtract(signal,signal_basesub), linewidth=2.5)
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
print('Finished')

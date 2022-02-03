import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt
import scipy
import scipy.signal as scisig
from matplotlib.lines import Line2D
import matplotlib.cm as cm
import scipy.ndimage as nd

class GCData:

    def __init__(self, filepath, basecorrect=False):
        # set basecorrect to True if you want correction, default is false
        """initialize the class with the attributes filename and data (which has been read from ASCII and is a pandas dataframe)"""
        self.filepath = filepath
        self.rawdata = self.getrawdata()
        self.time = np.asarray(self.rawdata['Time'])
        if basecorrect:
            self.signal = self.baseline_correction()
        else:
            self.signal = np.asarray(self.rawdata['Signal'])
        self.apex_ind = self.apex_inds()
        self.numpeaks = len(self.apex_ind)
        self.lind, self.rind = self.integration_inds()

    def getrawdata(self): # reads data from ASCII, returns pandas dataframe
        """Uses Matthias Richter's example code (translated from Matlab) to read GC .ASC files, returns pandas dataframe"""
        with open(self.filepath, 'r') as f:

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


    # Processing functions
    ##############################################################################

    def baseline_correction(self):
        """replaces signal with a signal with background subtraction using tophat filter (based on PyMassSpec/pyms/TopHat.py)"""
        self.signal = np.asarray(self.rawdata['Signal'])
        struct_elm_frac = 0.1 # default structural elemenet as fraction of total number of points
        struct_pts = int(round(self.signal.size * struct_elm_frac))
        str_el = np.repeat([1], struct_pts)
        line = nd.generate_binary_structure(rank=1, connectivity=9)
        signal_basesub = nd.white_tophat(input = self.signal, footprint=str_el)# structure = line)
        return signal_basesub


    def apex_inds(self):
        """uses scipy.signal.find_peaks to find peaks in signal, returns a numpy array with all peak indices (NOT times)"""
        apex_ind, _ = scisig.find_peaks(self.signal, prominence=4)
        return apex_ind

    def integration_inds(self, tol=0.5):
        """
        calculate the area under the peak with edge values determined by:
        1. the change in signal is less than 0.5% of the previous signal point (with averaging); or
        2. the added intensity starts increasing (i.e. when the ion is common to co-eluting compounds)

        adapted from pyMS function peak_sum_area by Andrew Isaac and Sean O'Callaghan
        https://github.com/ma-bio21/pyms/blob/master/pyms/Peak/Function.py
        """
        lind = np.zeros(len(self.apex_ind))
        rind = np.zeros(len(self.apex_ind))
        k = 0

        for apex in self.apex_ind:
            lhs = self.signal[:apex+1] # select all of the data just past the apex
            flhs = np.flip(lhs) # reverse list so that working forward works toward the left
            lind[k] = apex - self.half_index_search(flhs)
            rhs = self.signal[apex-1:]
            rind[k] = apex + self.half_index_search(rhs)
            k += 1

        return lind.astype(int), rind.astype(int)

    @staticmethod
    def half_index_search(dat, tol=0.5):

        tol = tol/200.0 # convert from percent, not sure why it should also be halved
        wide = 10 # number of points to sum new area across (increasing value increases smoothing)
        sig = dat[0]
        limit = len(dat)
        index = 1
        edge = float(sum(dat[0:wide]))/wide # edge is average value of num of pts defined by wide (NOT an index)
        delta = sig - edge
        old_edge = 2 * edge # make sure old_edge starts as larger than the current edge
        while abs(delta) > sig * tol and edge < old_edge and index < limit: # look for change is large, edge going down, limit not hit
            old_edge = edge
            sig = dat[index]
            edge = float(sum(dat[index:index+wide]))/wide
            delta = sig - edge
            index += 1

        index -= 1
        return index


    def integrate_peak(self):
        counts = np.zeros(self.numpeaks)
        for i in range(0,self.numpeaks):
           counts[i] = np.trapz(self.signal[self.lind[i]:self.rind[i]])
           if counts[i] == 0:
               counts[i] = 1

        return np.around(counts)


#    def integration_ind(self):
#        """OBSOLETE - TO BE DELETED"""
#        # Note to Claire:
#        #This part of the analysis works ok for now. After working through the baseline
#        #and the integration a bit, I'm going to want to fine tune the peak finding
#        #using some challenging example sets (i.e. very low ethane)
#        # Note to Claire:
#        #This line and the integrate_peak fucntions are where I think we should work right now
#        #The easiest addition would be to add a derivative test to search for dips
#        #in between peaks (overlaping). (i.e. setting better bounds)
#        self.peak_idx, _ = scisig.find_peaks(self.signal, prominence=1)
#        _, _, self.left_idx, self.right_idx = scisig.peak_widths(self.signal, self.peak_idx, rel_height=0.9)


#    def integrate_peak(self):
#        """OBSOLETE - TO BE DELETED Integrates a single peak of a signal based on left and right indices."""
#        # Indices have to be rounded as they are fractional coming from scisig.peak_widths
#        left_index = round(self.left_idx)
#        right_index = round(self.right_idx)
#        counts = np.trapz(self.signal[left_index:right_index])
#        if counts == 0:
#            counts = 1
#        return round(counts)

    def get_concentrations(self, calDF):
        """returns a Pandas series of chemical concentrations in the same order as the calibration file"""
        self.integration_inds()
        conc = pd.Series(0, index=calDF.index[0:]) # Creates empty series where index are ChemIDs from Cal file
        counts = self.integrate_peak()
        UnknownPeaks = 0
        for i in range(len(self.apex_ind)):
            peak_time = self.time[self.apex_ind[i]] # Determine peak time based on index
            # determine if peak falls within range for any calibration data set
            match = calDF[(calDF["start"] < peak_time) & (peak_time < calDF["end"])].index
            if not match.empty: # if empty, there are no matches
                chemID = match[0] #if not empty, names matching chemical: chemID
                conc[chemID] = (self.convert_to_ppm(calDF, counts[i], chemID)) # Convert counts to ppm and appends to conc list for the ChemID just found
            else:
                UnknownPeaks += 1
                # TODO I can take the ind_x and append this Unknown peak to the calibration df

        if UnknownPeaks>1:  # Theres always a peak from backflush right now
            print('Warning: %5d Unknown peaks detected' %(UnknownPeaks))

        if (conc==0).all():  # Checks if all concentrations are zero
            print('Warning: Zero Molecules Detected')

        return (conc)

    # Plotting functions
    ##############################################################################

    def plot_integration(self):
        plt.close('all')
        # Plotting Things Unique to Matplotlib
        plt.rcParams.update({'font.size': 14})
        plt.rcParams['axes.linewidth'] = 2
        # Another way to change tick width and length
        plt.gca().tick_params(which='both', width=1.5, length=6)
        plt.gca().tick_params(which='minor', width=1.5, length=3)

        plt.figure
        self.integration_inds()
        [left_idx, right_idx] = (np.rint(self.lind).astype('int'), np.rint(self.rind).astype('int'))
        # Plot signal
        plt.plot(self.time, self.signal, linewidth=2.5)
        ## Plot Derivative
        #plt.plot(time, 10*np.gradient(signal))
        ## Plot peak and bounds
        plt.plot(self.time[self.apex_ind], self.signal[self.apex_ind], 'bo', label='apex')
        plt.plot(self.time[left_idx], self.signal[left_idx], 'go', label='left')
        plt.plot(self.time[right_idx], self.signal[right_idx], 'ro', label='right')

        plt.xlabel('Retention (min)', fontsize=18)
        plt.ylabel('Signal (a.u.)', fontsize=18)
        plt.xlim([0, 13])
        plt.legend()
        plt.tight_layout()
        plt.show()

    # Helper functions
    ##############################################################################

    def get_run_number(self):
        """returns run number based on filename"""
        filename = os.path.basename(self.filepath)
        parts = filename.split('_')
        run_number = int(parts[-1][-2:].lstrip("0"))
        return run_number

    def convert_to_ppm(self,calDF, counts, chemID):
        """This function assumes you have imported the calibration data as a
        global variable called CalDF. Turns integrated raw counts into real concentration."""
        #This function assumes you have imported the calibration data as a global variable called CalDF
        [m, b] = (calDF.loc[chemID, ['slope', 'intercept']]) # Pull Cal data for given chemical
        y = m * counts + b # Simple Calibration equation will need to edit if calibration isn't linear
        return y # Counts in ppm

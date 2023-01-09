import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt
import scipy.signal as scisig
import scipy.ndimage as nd


class GCData:
    """
    A class for processing/analyzing gas chromatographer data from an ASCII file.

    Attributes
    ----------
    filepath (str) : filepath where data is stored (.ASC file)
    timestamp (float) : time since the epoch in seconds
    rawdata (pandas dataframe) : contains time and signal values from GC run
    time (numpy array) : np array version of time axis from rawdata (in minutes)
    signal (numpy array) : np array version of time axis from rawdata. If basecorrect=True it will be baseline
        corrected using baseline_correct()
    apex_ind (numppy array) : indices of all peaks identified by apex_inds()
    numpeaks (int) : length of apex_ind
    lind (numpy array) : indices of leftmost bound for integration for each peak identified
    rind (numpy array) : indices of rightmost bound for integration for each peak identified

    Methods
    -------
    getrawdata() : called on instantiation to convert asc to pandas array, returns timestamp and rawdata
    baseline_correction() : modifies signal to be corrected using a tophat baseline correction
    apex_inds() : scipy.signal.find_peaks to find peaks in signal, returns apex_ind
    integration_inds(tol=0.5) : finds the bounds of integration, returns lind and rind
    integrate_peak() : integrates peak trapezoidally in units of seconds*signalintensity, returns counts
    get_concentrations(calDF) : returns a Pandas series of chemical concentrations, requires dataframe
        of chem IDs from calibration file
    plot_integration() : plots the chromatogram with the peaks, left, and right indices indicated
    get_run_number() : get run number from end of filename
    convert_to_ppm(calDF, counts, chemID) : returns counts in ppm based on calibration dataframe and ID of chemical

    """
    def __init__(self, filepath, basecorrect=False):
        # set basecorrect to True if you want correction, default is false
        """
        initialize the class with the attributes filename and data
        (which has been read from ASCII and is a pandas dataframe)
        """
        self.filepath = filepath
        self.timestamp, self.rawdata = self.getrawdata()
        self.time = np.asarray(self.rawdata['Time']) # in minutes
        if basecorrect:
            self.signal = self.baseline_correction()
        else:
            self.signal = np.asarray(self.rawdata['Signal'])
        self.apex_ind = self.apex_inds()
        self.numpeaks = len(self.apex_ind)
        self.lind, self.rind = self.integration_inds()

    def getrawdata(self):  # reads data from ASCII, returns pandas dataframe
        """
        Uses Matthias Richter's example code (translated from Matlab)
        to read GC .ASC files

        Returns
        -------
        pandas dataframe containing time (min) and signal (arb units)
        """

        with open(self.filepath, 'r') as f:
            # Skip first 18 lines
            for i in range(18):
                next(f)
            # Line 19, date
            [month, day, year] = [int(i.strip()) for i in
                                  f.readline().split("=")[1].split('-')]
            # Line 20, time
            [hr, minute, second] = [int(i.strip()) for i in
                                    f.readline().split("=")[1].split(':')]
            timestamp = dt.datetime(year, month, day, hr, minute, second).timestamp()
            # Line 21, sampling rate
            rate = int(f.readline().split('=')[1][0])
            # Line 22 # of data points
            size = int(f.readline().split("=")[1])
            # Skip next 3 lines
            for i in range(3):
                next(f)

            y = []
            for line in f:
                if line.strip() == '':  # Empty strings in between entries
                    next
                elif "IPOINT" in line:  # Ignore IPOINT numbers at the bottom
                    next
                else:
                    value = int(line.strip().split(',')[0])
                    y.append(value/1000)  # Convert mV to V

            x = np.linspace(0, 1/rate/60*(size - 1), num=size).tolist()
            raw_data = pd.DataFrame({'Time': x, 'Signal': y})
            # GC_data includes timecode in order to be synced with EC data
            GC_data = (timestamp, raw_data)
        return GC_data

    # Processing functions
    ##############################################################################

    def baseline_correction(self):
        """
        replaces signal with a signal with background subtraction
        using tophat filter, based on PyMassSpec/pyms/TopHat.py

        Returns
        -------
        Numpy array of GC signal with baseline corrected
        """

        self.signal = np.asarray(self.rawdata['Signal'])
        struct_elm_frac = 0.1  # default struct element as frac of tot num points
        struct_pts = int(round(self.signal.size * struct_elm_frac))
        str_el = np.repeat([1], struct_pts)
        line = nd.generate_binary_structure(rank=1, connectivity=9)
        # structure = line
        signal_basesub = nd.white_tophat(input=self.signal, footprint=str_el)
        return signal_basesub

    def apex_inds(self):
        """
        Uses scipy.signal.find_peaks to find peaks in signal

        Returns
        -------
        Numpy array with all peak locations (as integer indices NOT times)
        """

        apex_ind, _ = scisig.find_peaks(self.signal, prominence=4)
        return apex_ind

    def integration_inds(self):
        """
        Calculates the area under each peak listed in apex_ind with edge values determined
        by _half_index_search

        Returns
        -------
        Numpy arrays in the same (time) order as the apex_ind array with the location (index)
        of the left and right points for integration

        """

        lind = np.zeros(len(self.apex_ind))
        rind = np.zeros(len(self.apex_ind))
        k = 0

        for apex in self.apex_ind:
            # select all of the data just past the apex
            lhs = self.signal[:apex+1]
            # reverse list so that working forward works toward the left
            flhs = np.flip(lhs)
            lind[k] = apex - self._half_index_search(flhs)
            rhs = self.signal[apex-1:]
            rind[k] = apex + self._half_index_search(rhs)
            k += 1

        return lind.astype(int), rind.astype(int)

    @staticmethod
    def _half_index_search(dat, tol=0.5):
        """
        Support function for integration_inds to search for integration bounds,
        determined where:
        1. the change in signal is less than 0.5%
            of the previous signal point (with averaging); or
        2. the added intensity starts increasing
            (i.e. when the ion is common to co-eluting compounds)

        adapted from pyMS function peak_sum_area by Andrew Isaac and Sean O'Callaghan
        https://github.com/ma-bio21/pyms/blob/master/pyms/Peak/Function.py

        Parameters
        ----------
        tol: double(?), optional
            When change in sum is less than tol percent of the current area, summing stops

        Returns
        -------
        Integer index of the integration bound
        """

        # convert from percent, not sure why it should also be halved
        tol = tol/200.0
        # number of points to sum new area across (increasing value increases smoothing)
        wide = 10
        sig = dat[0]
        limit = len(dat)
        index = 1
        # edge is average value of num of pts defined by wide (NOT an index)
        edge = float(sum(dat[0:wide]))/wide
        delta = sig - edge
        # make sure old_edge starts as larger than the current edge
        old_edge = 2 * edge
        # look for change is large, edge going down, limit not hit
        while abs(delta) > sig * tol and edge < old_edge and index < limit:
            old_edge = edge
            sig = dat[index]
            edge = float(sum(dat[index:index+wide]))/wide
            delta = sig - edge
            index += 1

        index -= 1
        return index

    def integrate_peak(self):
        """
        Finds the area under the peak using a trapezoidal method
        for each peak identified and using the bounds from integration_inds
        """
        counts = np.zeros(self.numpeaks)
        for i in range(0, self.numpeaks):
            counts[i] = np.trapz(self.signal[self.lind[i]:self.rind[i]], x=60*self.time[self.lind[i]:self.rind[i]])
            if counts[i] == 0:
                counts[i] = 1
        return np.around(counts)

    def get_concentrations(self, calDF):
        """
        Returns a Pandas series of chemical concentrations
        in the same order as the calibration file

        Parameters
        ----------
        calDF: Pandas DataFrame
            Calibration values by chemical ID

        Returns
        -------
        Array of concentrations for each peak in apex_ind, given in ppm

        """

        self.integration_inds()
        # Creates empty series where index are ChemIDs from Cal file
        conc = pd.Series(0.0, index=['timestamp', *calDF.index.to_list()])
        conc['timestamp'] = self.timestamp
        counts = self.integrate_peak()
        UnknownPeaks = 0
        for i in range(len(self.apex_ind)):
            # Determine peak time based on index
            peak_time = self.time[self.apex_ind[i]]
            # determine if peak falls within range for any calibration data set
            match = calDF[(calDF["start"] < peak_time) & (peak_time < calDF["end"])].index
            if not match.empty:  # if empty, there are no matches
                chemID = match[0]  # if not empty, names matching chemical:chemID
                # Convert counts to ppm and appends to conc list for the ChemID just found
                conc[chemID] = (self.convert_to_ppm(calDF, counts[i], chemID))
            else:
                UnknownPeaks += 1
                # TODO I can take the ind_x and append this Unknown peak to the calibration df

        if UnknownPeaks>1:  # Theres always a peak from backflush right now
            print('Warning: %5d Unknown peaks detected' %(UnknownPeaks))
            print(self.filepath)
        if (conc==0).all():  # Checks if all concentrations are zero
            print('Warning: Zero Molecules Detected')

        return conc

    # Plotting functions
    ##############################################################################

    def plot_integration(self):
        """
        Plots the chromatogram with the peaks, left, and right indices indicated
        """

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
        """
        Determine run number from filename

        Returns
        -------
        Integer run number extracted filename

        """

        filename = os.path.basename(self.filepath)
        parts = filename.split('_')
        run_number = int(parts[-1][-2:].lstrip("0"))
        return run_number

    def convert_to_ppm(self,calDF, counts, chemID):
        """
        Convert integrated raw counts into ppm based on calibration data

        Parameters
        ----------
        calDF: Pandas DataFrame
            Calibration values by chemical ID
        counts: double(?)
            Raw integrated counts determined by integrate_peaks()
        chemID: **** THIS MIGHT BE WRONG **** str
            Contains name of chemical from calDF to be converted to ppm

        Returns
        ------
        Counts for a single peak converted into ppm based on calDF
        """

        #This function assumes you have imported the calibration data as a global variable called CalDF
        [m, b] = (calDF.loc[chemID, ['slope', 'intercept']]) # Pull Cal data for given chemical
        y = m * counts + b # Simple Calibration equation will need to edit if calibration isn't linear
        return y # Counts in ppm

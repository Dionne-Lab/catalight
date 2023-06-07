"""
Template file for GC interaction. Currently (03/15/2023) these are all required
method names for any GC. An SRI GC is fundamentally controlled by its control
file, and the original code was written to manipulate the file first, then the
machine via the control file. Future developers may run into some issues if
their equipment isn't compatible with this work flow.

Created on Wed March 15 4:06 2023
@author: Briley Bourgeois
"""
import time


class GC_Connector():
    """
    Interface with some type of GC device.
    """

    def __init__(self):
        """Connect to GC and load control file."""
        print('Connecting to (GC name)...')
        # Define Attributes:
        # ------------------
        self.sample_set_size = 4
        """
        int:  Number of GC collections for each time GC is started. This attr
        should probably exist for any brand GC.
        """

        # Init Procedure:
        # ---------------
        self.connect()
        self._sample_rate = 0  # Dummy value
        self._min_sample_rate = 0  # Dummy value
        # TODO: pass some starting values to GC

    # Properties
    # ----------
    # Makes min_sample_rate read only
    min_sample_rate = property(lambda self: self._min_sample_rate)
    """`float`, read-only: (min) Minimum setpoint for sample_rate.
    Definition of this value may depend on GC type."""

    # Setting sample rate changes when connected to GC
    @property
    def sample_rate(self):
        """
        Time between setting collections in minutes.

        The GC will collect data every sample_rate minutes when sample_set_size
        is set >1. If the min_sample_rate is less than the entered value,
        prints a warning and resets sample_rate to min_sample_rate.
        """
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, value):
        if value >= self._min_sample_rate:
            self._sample_rate = value
        else:
            print('Minimum Sample Rate = %5.2f' % self.min_sample_rate)
            print('Sample rate set to minimum')
            self._sample_rate = self.min_sample_rate

    # Methods:
    # --------
    def update_gc_settings(self):
        """
        This method needs to tell the gc where the data will be saved, and how
        many samples will be run when set_running() is called.
        """
        # TODO: Update data save location
        # TODO: Update number of collection to make on run
        pass

    def read_gc_settings(self):
        """
        For SRI GC, this method gets gc runtime and postrun time.

        Currently updates min_sample_rate property by pulling run time and
        postrun cycle time from control file.
        Updates sample_rate if it is faster than the new min_sample_rate.
        """
        self._min_sample_rate = 1  # TODO: get minimum sample rate from GC

        if self.sample_rate < self.min_sample_rate:
            self.sample_rate = self.min_sample_rate

    def set_running(self):
        """
        Start data collection.

        Collection parameters should be updated w/ attributes and
        "update_gc_settings" method

        If better for future gc brands, this methods could take parameter:
        filepath, num_runs,
        """
        # TODO: Start GC
        pass

    def is_running(self, max_tries=3):
        """
        Request status of GC collection (running or not).

        Parameters
        ----------
        max_tries : `int`, optional
            Number of attempts to make before aborting. The default is 3.

        Raises
        ------
        Exception
            Exception raised on calling IsRunning() are suppressed up until
            max_tries is reached.

        Returns
        -------
        result : bool
            When successful, returns the status of GC collection (on/off)

        """
        for attempt in range(1, max_tries + 1):
            try:
                result = 1  # TODO: poll specific device
                return result
                break
            except Exception as e:
                print(e)
                if attempt < max_tries:
                    print('Retrying...')
                    time.sleep(1)
                    continue
                else:
                    print('Cannot Resolve')
                    raise e

    def connect(self, max_tries=1):
        """
        Not technically needed.

        Parameters
        ----------
        max_tries : `int`, optional
            Number of attempts to make before aborting. The default is 1.
        """
        # See sri_gc for an example of connection w/ multiple attempts
        pass

    def disconnect(self, max_tries=1):
        """
        Disconnect from gc.

        Parameters
        ----------
        max_tries : `int`, optional
            Number of attempts to make before aborting. The default is 1.

        Returns
        -------
        None

        """
        try:
            # TODO: disconnect function
            print('Disconnected!')

        except Exception as e:
            print(e)
            # try to handle some specific exception

if __name__ == "__main__":
    print('some example code here')

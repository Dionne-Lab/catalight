"""
Interface with SRI GC through Peaksimple interface via .dll file.

Created on Thu Oct 14 17:30:17 2021
@author: Briley Bourgeois
"""
import os
import re
import time

# python.NET is imported with the name clr (Common Language Runtime)
import clr

dir_path = os.path.dirname(os.path.realpath(__file__))
assemblydir = os.path.join(dir_path, 'PeaksimpleClient',
                           'PeaksimpleConnector.dll')

clr.AddReference(assemblydir)  # Add the assembly to python.NET
# Now that the Assembly has been added to python.NET,
# it can be imported like a normal module, though the name is different.
import Peaksimple  # Need add assembly before import. # noqa # type: ignore

# TODO some control file needs to be placed within package to work w/ any user.
# the default won't run from the repo for some reason
default_ctrl_file = os.path.join(dir_path, 'DEFAULT.CON')


class GC_Connector():
    """
    Interface with SRI GC through Peaksimple interface via .dll file.

    If the assembly can't be found, find the .dll file, right click,
    properties, check "unblock", click apply

    Parameters
    ----------
    ctrl_file : str
        Full path to the initial ctrl file to use.
    """

    def __init__(self, ctrl_file=default_ctrl_file):
        """Connect to GC and load control file."""
        print('Connecting to Peaksimple...')
        # Define Attributes:
        # ------------------
        self.peaksimple = Peaksimple.PeaksimpleConnector()
        """Create instance of PeaksimpleConnector.
        :ref:`sri_gc_doc` for more info on methods."""

        self.ctrl_file = ctrl_file
        """str: Full path to control file to use."""

        self.sample_set_size = 4
        """
        int:  Number of GC collection for each time set_running()
        is called. Can be changed per experiment by editing
        :attr:`Experiment.sample_set_size
        <catalight.equipment.experiment_control.Experiment.sample_set_size>`
        """

        # Init Procedure:
        # ---------------
        self.connect()
        self._sample_rate = 0  # Dummy value, reset when ctrl file loaded
        self._min_sample_rate = 0  # Dummy value, reset when ctrl file loaded
        # Sends ctrl file to GC, updates self w/ new data
        print('Loading', ctrl_file)
        self.load_ctrl_file()

    # Properties
    # ----------
    # Makes min_sample_rate read only
    min_sample_rate = property(lambda self: self._min_sample_rate)
    """float, read-only: (min) Minimum setpoint for sample_rate.
    Sum of Channel 1 Time and Channel 1 Posttime from GC control file.
    Value automatically updates when :meth:`read_gc_settings` is called."""

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
    def update_gc_settings(self, data_file_path):
        """
        Write over the currently loaded ctrl file to update settings.

        Updates data file path to that provided. Sets postrun repeat
        to sample_set_size. Goes line by line through the control file defined
        by ctrl_file attr and rewrites the line to set appropriate options.
        Ensures postrun cycle & repeat, autoincrement, and save image, data,
        & results are all turned on.

        Parameters
        ----------
        data_file_path : str
            Full path to the directory in which you'd like to save data files.
        """
        with open(self.ctrl_file, 'r+') as ctrl_file:
            new_ctrl_file = []
            for line in ctrl_file:  # read values after '=' line by line
                if re.search('<DATA FILE PATH>=', line):
                    line = ('<DATA FILE PATH>=' + data_file_path + '\n')
                elif re.search('<CHANNEL 1 POSTRUN CYCLE>=', line):
                    line = ('<CHANNEL 1 POSTRUN CYCLE>=1\n')
                elif re.search('<CHANNEL 1 POSTRUN REPEAT>=', line):
                    line = ('<CHANNEL 1 POSTRUN REPEAT>='
                            + str(self.sample_set_size) + '\n')

                elif re.search('<CHANNEL 1 FILE>=', line):
                    line = ('<CHANNEL 1 FILE>=FID\n')
                elif re.search('<CHANNEL 1 POSTRUN SAVE DATA>=', line):
                    line = ('<CHANNEL 1 POSTRUN SAVE DATA>=1\n')
                elif re.search('<CHANNEL 1 POSTRUN SAVE RESULTS>=', line):
                    line = ('<CHANNEL 1 POSTRUN SAVE RESULTS>=1\n')
                elif re.search('<CHANNEL 1 POSTRUN AUTOINCREMENT>=', line):
                    line = ('<CHANNEL 1 POSTRUN AUTOINCREMENT>=1\n')
                elif re.search('<CHANNEL 1 POSTRUN SAVE IMAGE>=', line):
                    line = ('<CHANNEL 1 POSTRUN SAVE IMAGE>=1\n')

                elif re.search('<CHANNEL 2 FILE>=', line):
                    line = ('<CHANNEL 2 FILE>=TCD\n')
                elif re.search('<CHANNEL 2 POSTRUN SAVE DATA>=', line):
                    line = ('<CHANNEL 2 POSTRUN SAVE DATA>=1\n')
                elif re.search('<CHANNEL 2 POSTRUN SAVE RESULTS>=', line):
                    line = ('<CHANNEL 2 POSTRUN SAVE RESULTS>=1\n')
                elif re.search('<CHANNEL 2 POSTRUN AUTOINCREMENT>=', line):
                    line = ('<CHANNEL 2 POSTRUN AUTOINCREMENT>=1\n')
                elif re.search('<CHANNEL 2 POSTRUN SAVE IMAGE>=', line):
                    line = ('<CHANNEL 2 POSTRUN SAVE IMAGE>=1\n')

                new_ctrl_file += line
            ctrl_file.seek(0)
            ctrl_file.writelines(new_ctrl_file)

        print(self.ctrl_file)
        self.load_ctrl_file()

    def load_ctrl_file(self, max_tries=3):
        """
        Load a new ctrl file to the GC based on .ctrl_file attr.

        Attempt to load a new control file. Waits 5 seconds after loading
        then calls read_ctr_file()

        Parameters
        ----------
        max_tries : int, optional
            Number of attempts to make before aborting. The default is 3.

        Raises
        ------
        Peaksimple.ConnectionWriteFailedException:
            Somewhat randomly occurring error usually fixed by reattempting.
        Peaksimple.NoConnectionException:
            Communication to peaksimple lost. Likely need to reboot peaksimple.
        """
        print('Loading Control File...')
        for attempt in range(0, max_tries):
            try:
                self.peaksimple.LoadControlFile(self.ctrl_file)
                print('Successful!')
                break
            except Peaksimple.ConnectionWriteFailedException:
                print('Write error. Retrying...')
                time.sleep(1)
                continue
            except Peaksimple.NoConnectionException:
                print('Write Error: GC Not Connected')
                break
        time.sleep(5)  # I think peaksimple is cranky when rushed
        self.read_gc_settings()

    def read_gc_settings(self):
        """
        Read loaded control file and updates object with values from file.

        Currently updates min_sample_rate property by pulling run time postrun
        cycle time from control file. Updates sample_rate if it is faster than
        the new min_sample_rate

        Returns
        -------
        None.

        """
        with open(self.ctrl_file, 'r+') as ctrl_file:
            for line in ctrl_file:  # read values after '=' line by line

                if re.search('<CHANNEL 1 TIME>=', line):
                    run_time = int(line.split('=')[-1].strip(' \n'))

                elif re.search('<CHANNEL 1 POSTRUN CYCLE TIME>=', line):
                    post_time = int(line.split('=')[-1].strip(' \n'))

            self._min_sample_rate = (run_time + post_time) / 1000

            if self.sample_rate < self.min_sample_rate:
                self.sample_rate = self.min_sample_rate

    def set_running(self):
        """
        Start data collection. Make sure correct GC settings are loaded first.

        Wraps over peaksimple set running function. Will set channel 1 running
        by default. This could be made flexible in the future if ever needed.
        I think most SRI GC interactions are controlled by channel 1 though.
        """
        self.peaksimple.SetRunning(1, True)

    def is_running(self, max_tries=3):
        """
        Request status of GC collection (running or not).

        Parameters
        ----------
        max_tries : int, optional
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
                result = self.peaksimple.IsRunning(1)
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
        Attempt to connect to running peaksimple software.

        Parameters
        ----------
        max_tries : int, optional
            Number of attempts to make before aborting. The default is 1.

        Raises
        ------
        Peaksimple.ConnectionFailedException
            Connection to GC was unsuccessful.

        Returns
        -------
        None.

        """
        for attempt in range(1, max_tries + 1):
            try:
                self.peaksimple.Connect()
                print('Connected!')
                break
            except Peaksimple.ConnectionFailedException:
                if attempt < max_tries:
                    print('Connection error. Retrying...')
                    time.sleep(1)
                    continue
                else:
                    print('Cannot Connect :(')
                    raise Peaksimple.ConnectionFailedException

    def disconnect(self, max_tries=1):
        """
        Disconnect from peaksimple software. Reconnection still usually fails.

        Runs Peaksimple.PeaksimpleConnector.Disconnect(), but attempts to
        reconnect still fail. The peaksimple software needs to be manually
        closed to reconnect. Note, programmatic attempts to close peaksimple
        using subprocesses have also failed.

        Parameters
        ----------
        max_tries : int, optional
            Number of attempts to make before aborting. The default is 1.

        Returns
        -------
        None.

        """
        try:
            self.peaksimple.Disconnect()
            print('Disconnected!')
            # TODO would deleting peaksimple here fix reconnect issues?
        except Exception as e:
            print(e)


if __name__ == "__main__":
    print(dir_path)
    gc1 = GC_Connector()
    data_path = 'C:\\Peak489Win10\\GCDATA\\20221117_CodeTest'
    gc1.sample_set_size = 2
    gc1.update_gc_settings(data_path)
    gc1.peaksimple.IsConnected()
    # gc1.set_running()
    # time.sleep(10)
    # for n in range(0, 31):
    #     print(time.ctime(), '---', gc1.peaksimple.IsRunning(1))
    #     # IsRunning returns false inbetween runs. Returns True during run
    #     time.sleep(60)
    # print('Finished')

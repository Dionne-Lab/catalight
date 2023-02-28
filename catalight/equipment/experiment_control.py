"""
This module contains the Experiment class and any future add ons.

Created on Tue Dec 21 08:30:33 2021.
@author: Briley Bourgeois
"""
import re
import os
import time
from ast import literal_eval
from datetime import date

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class Experiment:
    """
    Object containing all information necessary to run a particular experiment.

    The experiment class is the center piece of catalight. This class
    contains several type checked properties that should be updated with
    relevant experimental parameters by the user. The user sets a desired
    experimental procedure from the list provided in :py:attr:`expt_list`

    Most importantly, equipment object can be passed to each instance of
    Experiment and used to run the :py:meth:`run_experiment` method to control
    the hardware components.

    Parameters
    ----------
    eqpt_list: list of objects, optional
        List of equipment objects. Calls :py:meth:`update_eqpt_list`,
        if provided.
        Order of list should be:
        (:py:class:`~catalight.equipment.sri_gc.gc_control.GC_Connector`,
        :class:`~catalight.equipment.diode_laser.diode_control.Diode_Laser`,
        :class:`~catalight.equipment.alicat_MFC.gas_control.Gas_System`,
        :class:`~catalight.equipment.harrick_watlow.heater_control.Heater`)
    """

    def __init__(self, eqpt_list=False):
        """Init experiment object."""
        # This class attribute defines the possible experiments. This is an
        # important part of the class and should be altered with caution
        # noqa to suppress extra spaces PEP violation. Done for clarity.

        # TODO: ind_var of stability test should be changed to time, but
        # careful bug checking needs to be performed everywhere expt.ind_var
        # is used.
        self._expt_list = pd.DataFrame(
            [['temp_sweep',      'temp', False,    'K'],  # noqa
             ['power_sweep',    'power', False,   'mW'],  # noqa
             ['comp_sweep',  'gas_comp', False, 'frac'],  # noqa
             ['flow_sweep',  'tot_flow', False, 'sccm'],  # noqa
             ['calibration', 'gas_comp', False,  'ppm'],  # noqa
             ['stability_test',  'temp', False,  'min']], # noqa
            columns=['Expt Name',
                     'Independent Variable',
                     'Active Status',
                     'Units'])

        # Set default values of properties
        # --------------------------------
        # These are just random default values.
        # Descriptions below in property definitions
        self._temp = [273.0]
        self._power = [0.0]
        self._tot_flow = [0.0]
        self._gas_comp = [[0.0, 50.0, 0.0, 0.0]]
        self._gas_type = ['C2H2', 'Ar', 'H2', 'Ar']
        self._sample_rate = 10

        # Returns todays date as YYYYMMDD by default
        self._date = date.today().strftime('%Y%m%d')
        self._start_time = 'Undefined'
        self._expt_type = 'Undefined'
        self._sample_name = 'Undefined'
        self._ind_var = 'Undefined'
        self._expt_name = 'Undefined'
        self._results_path = 'Undefined'
        self._data_path = 'Undefined'

        # Define attributes and set default
        # ---------------------------------
        self.sample_set_size = 4
        """int: Number of GC samples to collect"""

        self.t_buffer = 5
        """
        int or float: (min) Time between last GC sample of a step and going to
        next condition
        """

        self.t_steady_state = 15
        """
        int or float: (min) Time between going to next condition and collecting
        first sample of a step
        """

        self.heat_rate = 15
        """int or float: (deg C/min) Ramp rate to use when heating reactor."""

        if eqpt_list is not False:
            self.update_eqpt_list(eqpt_list)

    # These setter functions apply rules for how certain properties can be set
    def _str_setter(attr):
        """
        Setter function for properties with str values.

        If type checking becomes necessary for string inputs,
        it can be done here

        Parameters
        ----------
        attr : str
            str for non-public attribute to change value of

        Returns
        -------
        set_any : function
            update function for setting string properties
        """

        def set_any(self, value):
            """
            Func to set value.

            Parameters
            ----------
            value : str
                value to attempt update

            Returns
            -------
            None.

            """
            setattr(self, attr, value)

        return set_any

    def _num_setter(attr):
        """
        Setter function for numbers used to set checks on value changes.

        Parameters
        ----------
        attr : `str`
            str for non-public attribute to change value of

        Raises
        ------
        AttributeError
            Attribute error is raised when value entered doesn't match with
            corresponding limits. These vary depending on attribute given.

        Returns
        -------
        set_any : function
            update function for setting string properties

        """

        def set_any(self, value):
            """
            Setter function for numbers.

            Converts np.ndarrays to list on call. Runs through value testing if
            statements based on attr supplied. All values provided must be a
            form of a list. Gas comp values must individually round to 1.
            Total flow is currently hard coded to max at 350.

            Parameters
            ----------
            value : list of float or numpy.ndarray
                if np array is given, converts to list in beginning of func.

            Raises
            ------
            AttributeError
                Attribute error is raised when value entered doesn't match with
                corresponding limits. These vary depending on attribute given.
            """
            if isinstance(value, np.ndarray):
                value = list(value)

            if not isinstance(value, list):
                raise AttributeError(attr + ' must be list')
            elif (attr == '_tot_flow') & (np.max(value) > 350):
                raise AttributeError('Total flow must be <= 350')
                # TODO, update this value if gas_system is connected or turn
                # into a class attribute.
            elif (attr == '_gas_comp'):
                for composition in value:
                    # convert % to fraction
                    if round(sum(composition), 6) == 100:
                        composition[:] = [x / 100 for x in composition]

                    if round(sum(composition), 6) != 1:
                        raise AttributeError(
                            'Gas comp. must be list of list == 1')

            setattr(self, attr, value)
        return set_any

    def _attr_getter(attr):
        """Getter function for all properties."""

        def get_any(self):
            return getattr(self, attr)
        return get_any

    # Property definitions
    # ====================
    # Number Properties
    # -----------------
    temp = property(fget=_attr_getter('_temp'),
                    fset=_num_setter('_temp'))
    """
    list[float]: List of temperature values to step through during experiment.
    One element if constant or multiple for sweep. Initial value of [273.0].
    """
    power = property(fget=_attr_getter('_power'),
                     fset=_num_setter('_power'))
    """
    list[float]: List of power (mW) values to step through during experiment.
    One element if constant or multiple for sweep. Initial value of [0.0].
    """

    tot_flow = property(fget=_attr_getter('_tot_flow'),
                        fset=_num_setter('_tot_flow'))
    """
    list[float]: List of flow rates (sccm) to step through during experiment.
    One element if constant or multiple for sweep. Initial value of [0.0].
    """

    gas_comp = property(fget=_attr_getter('_gas_comp'),
                        fset=_num_setter('_gas_comp'))
    """
    list[list[float]]: List of gas composition lists to sweep through.
    (ex. [[gas1, gas2, gas3],[...]]) Can be len=1 if not comp sweep.
    Each inner list must sum to 1 or 100.
    Initial value of  [[0.0, 50.0, 0.0, 0.0]].
    """

    # String Properties
    # -----------------
    gas_type = property(fget=_attr_getter('_gas_type'),
                        fset=_str_setter('_gas_type'))
    """
    list[str]: List of gas types for the MFCs to use to measure flow rates.
    (ex. [gasA, gasB, gasC, ...]) All values must be found in
    the gas library of the MFC system used.
    Initial value of ['C2H2', 'Ar', 'H2', 'Ar'].
    """

    sample_name = property(fget=_attr_getter('_sample_name'),
                           fset=_str_setter('_sample_name'))
    """str: Name of sample for building save paths"""

    # Read only properties
    # --------------------
    date = property(lambda self: self._date)
    """str, read-only: Update w/ :meth:`update_date` method. For logging"""

    start_time = property(lambda self: self._start_time)
    """
    str, read-only: Updates when :meth:`set_initial_conditions` method is
    called. For logging. Used to calculate time_passed during analysis.
    Given by time.time() at the **end** of initial conditions steps.
    """

    ind_var = property(lambda self: self._ind_var)
    """
    str, read-only: Describes the variable being modified. This gets updated
    when expt_type is updated based on what defined by :attr:`expt_list`.
    """

    expt_name = property(lambda self: self._expt_name)
    """str, read-only: Creates name using the fixed variables for expt"""

    results_path = property(lambda self: self._results_path)
    """
    str, read-only: Save location for analysis, defined relative to expt_log.
    Update using :meth:`update_save_paths`
    """

    data_path = property(lambda self: self._data_path)
    """
    str, read-only: Save location for raw data, defined relative to expt_log.
    Update using :meth:`update_save_paths`
    """

    expt_list = property(lambda self: self._expt_list)
    """
    pandas.DataFrame, read-only: This class attr defines the possible
    experiments. This is an important part of the class and should be altered
    with caution. Changing the units within this DF should allow different unit
    inputs for the rest of the codebase, but this feature is untested!!!
    """

    # Setting sample rate changes when connected to GC
    @property
    def sample_rate(self):
        """
        Sample rate in minutes (time it takes to collect a sample).

        Set sample rate based on whether GC is connected.
        If GC is connected, try to set sample rate to that defined by expt.
        If that failed, _gc_control.sample_rate will be set to min defined by
        ctrl file.
        """
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, value):
        """Returns sample rate value."""
        if hasattr(self, '_gc_control'):
            if value >= self._gc_control.min_sample_rate:
                # try to set sample rate to that defined by expt
                self._sample_rate = value
                self._gc_control.sample_rate = self.sample_rate
            else:
                # If that failed, _gc_control.sample_rate will be set to min
                # defined by ctrl file. This line makes sure gc and expt match.
                self._sample_rate = self._gc_control.sample_rate
                print('Error: Input Sample Rate is Lower Than GC Minimum')
                print('Sample rate set to: %.2f'
                      % self._gc_control.sample_rate)

        else:
            self._sample_rate = value

    @property
    def expt_type(self):
        """
        Define the desired experimental procedure selected from _expt_list.

        A key property directing much of the behavior of the class.For example,
        the run_experiment() method is guided by the expt_type provided. New
        values must be entered into the _expt_list attribute and the
        appropriate class methods must be editted to account for new
        experimental capabilities.
        Updates :attr:`ind_var` when called.
        Converts 'Active Status' in :attr:`expt_list` to True.
        """
        return self._expt_type

    @expt_type.setter
    def expt_type(self, expt_type):
        # Evaluate whether entered experiment type is in default list
        if expt_type not in self.expt_list['Expt Name'].tolist():
            raise AttributeError('Invalid Experiment Type Provided')

        self._expt_type = expt_type
        self._expt_list['Active Status'] = (
            self.expt_list['Expt Name'] == self._expt_type)

        # Defines Independent Variable as string provided by expt list
        var_list = self.expt_list['Independent Variable']  # Pull List
        # Compare Boolean
        ind_var_series = var_list[self.expt_list['Active Status']]
        # Convert to str
        self._ind_var = ind_var_series.to_string(index=False)

    def update_date(self):
        """Set :attr:`date` based on current date."""
        self._date = date.today().strftime('%Y%m%d')

    def update_expt_log(self, expt_path):
        """
        Update the experiment log based on current object parameters.

        Parameters
        ----------
        expt_path: str
            path to the experiment folder
        """
        with open(os.path.join(expt_path, 'expt_log.txt'), 'w+') as log:
            log_entry = [
                'Experiment Date = ' + self.date,
                'Experiment Start = ' + self.start_time,
                'Experiment Type = ' + self.expt_type,
                'Experiment Name = ' + self.expt_name,
                'Sample Name = ' + self.sample_name,
                'Temperature [' + self.expt_list['Units'][0] + '] = '
                + str(self.temp),
                'Power [' + self.expt_list['Units'][1] + '] = '
                + str(self.power),
                'Gas 1 type = ' + self.gas_type[0],
                'Gas 2 type = ' + self.gas_type[1],
                'Gas 3 type = ' + self.gas_type[2],
                'Gas 4 type = ' + self.gas_type[3],
                'Gas Composition [' + self.expt_list['Units'][2]
                + '] = ' + str(self.gas_comp),
                'Total Flow [' + self.expt_list['Units'][3]
                + '] = ' + str(self.tot_flow)
            ]
            log.write('\n'.join(log_entry))

    def read_expt_log(self, log_path):
        """
        Read data from an existing log file and update object parameters.

        Grows gas_type list if more gasses are found in the expt_log than
        contained in current gas_type list.

        Parameters
        ----------
        log_path : str
            string to the full file path of the log file ('./expt_log.txt').

        Returns
        -------
        None.

        """
        with open(log_path, 'r') as log:
            for line in log:  # Read file line by line
                # Read the values after '=' sign
                data = line.split('=')[-1].strip(' \n')

                # Check the text before '=' to pick which value to assign
                if re.search('Experiment Date =', line):
                    self._date = data
                elif re.search('Experiment Start =', line):
                    self._start_time = data
                elif re.search('Experiment Type =', line):
                    self.expt_type = data
                elif re.search('Experiment Name =', line):
                    self._expt_name = data
                elif re.search('Sample Name =', line):
                    self.sample_name = data
                elif re.search('Temperature', line):
                    self.temp = literal_eval(data)
                elif re.search('Power', line):
                    self.power = literal_eval(data)
                elif re.search('Gas \d+ type', line):  # \d+ is 1 or more digit
                    # Get left side of '=' sign
                    gas_str = line.split('=')[0].strip(' \n')
                    # Pull number from left side
                    for string in gas_str.split():
                        if string.isdigit():
                            num = int(string)
                    # If the gas_type list is shorter than this entry number,
                    # append extra blank values. Appending blanks vs just
                    # appending the value accounts for if gas # is out of order
                    if len(self.gas_type) < num:
                        for n in range(num - len(self.gas_type)):
                            self.gas_type.append([])
                    self.gas_type[num-1] = data

                elif re.search('Gas Composition', line):
                    self.gas_comp = literal_eval(data)
                elif re.search('Total Flow', line):
                    self.tot_flow = literal_eval(data)

            expt_path = os.path.dirname(log_path)
            # Will throw error if no data folders
            self.update_save_paths(expt_path)

    def _update_expt_name(self):
        """
        Non-public function that updates expt_name based on current settings.

        Returns
        -------
        None.
        """
        # Defines all settings to be included in path name and adds units
        expt_settings = pd.Series(
            [str(self.temp[0]), str(self.power[0]),
             '_'.join([str(m) + n for m, n in zip(self.gas_comp[0],
                                                  self.gas_type)]),
             str(self.tot_flow[0])]) + self.expt_list['Units'][0:4]

        # Only select fixed variable for path name
        fixed_vars = expt_settings[self.expt_list['Independent Variable']
                                   != self.ind_var]
        self._expt_name = '_'.join(fixed_vars.to_list())  # Define expt_name

    def update_save_paths(self, expt_path, should_exist=True):
        """
        Update data/results paths for the object.

        Used when reading expt from log file or creating new expt data set

        Parameters
        ----------
        expt_path : str
            string to the full file path of the experiments dir.
        should_exist : bool, optional
            If updating based on existing log file, set to true.
            The default is True.

        Raises
        ------
        ValueError
            Gives error if should_exist=True and
            no results/data directories exists,

        Returns
        -------
        None.

        """
        # Defines path for saving results
        self._results_path = os.path.join(expt_path, 'Results')

        # Defines path for saving raw data
        self._data_path = os.path.join(expt_path, 'Data')

        # If updating paths from file, paths should exist in log directory
        exists = (os.path.isdir(self.results_path)
                  | os.path.isdir(self.data_path))
        if (should_exist) & (not exists):
            raise ValueError('results/data path doesn''t exist where expected')

    def create_dirs(self, sample_path):
        """
        Create directory for storing experiment data and analysis.

        This function creates a set of directories to store experimental data
        for a given experiment and the results of the analysis. Updates the
        experiment name based on current expt settings and creates/updates the
        experiment log file in the sample path

        Parameters
        ----------
        sample_path: str
            Input the path where the data should be stored (sample folder)

        Raises
        ------
        AttributeError: Throws error if :attr:`expt_type` is undefined

        Returns
        -------
        None.

        """
        if self.expt_type == 'Undefined':
            raise AttributeError(
                'Experiment Type Must Be Defined Before Creating Directories')

        self._update_expt_name()
        expt_path = os.path.join(sample_path, self.date + self.expt_type
                                 + '_' + self.expt_name)

        self.update_save_paths(expt_path, should_exist=False)

        os.makedirs(self.results_path, exist_ok=True)
        step_num = 1
        if self.expt_type == 'stability_test':
            path = os.path.join(self.data_path, '1 Stability_Test')
            os.makedirs(path, exist_ok=True)
            self.update_expt_log(expt_path)
            return

        # Creates subfolders for each step of experiment
        for step in getattr(self, self._ind_var):
            # Compare Boolean
            units = (self.expt_list['Units']
                     [self.expt_list['Active Status']].to_string(index=False))

            if self._ind_var == 'gas_comp':
                step_str = '_'.join(
                    [str(m) + n for m, n in zip(step, self.gas_type)])
                path = os.path.join(self.data_path,
                                    ('%i %s%s' % (step_num, step_str, units)))
            else:
                path = os.path.join(self.data_path,
                                    ('%i %d%s' % (step_num, step, units)))

            os.makedirs(path, exist_ok=True)
            step_num += 1

        self.update_expt_log(expt_path)

    def plot_sweep(self, fig=None):
        """
        Plot the sweep parameter vs time.

        Parameters
        ----------
        fig : matplotlib.pyplot.figure, optional
            Can supply figure object to write plot to it. The default is None.

        Returns
        -------
        matplotlib.pyplot.figure
            figure object for experimental sweep. Two subplots for full and
            zoomed in versions. There is a hidden single subplot in background
            used for making shared axis titles
        matplotlib.pyplot.axis
            ax1 - top plot showing full experimental sweep
        matplotlib.pyplot.axis
            ax2 - bottom plot showing zoomed in version of experimental sweep
        float
            run_time - Calculate total time to run experiment

        """
        # have to get the sample run time from GC
        # Some Plot Defaults
        plt.rcParams['axes.linewidth'] = 2
        plt.rcParams['lines.linewidth'] = 1.5
        plt.rcParams['xtick.major.size'] = 6
        plt.rcParams['xtick.major.width'] = 1.5
        plt.rcParams['ytick.major.size'] = 6
        plt.rcParams['ytick.major.width'] = 1.5
        # plt.rcParams['figure.figsize'] = (6.5, 8)
        plt.rcParams['font.size'] = 14
        plt.rcParams['axes.labelsize'] = 18
        plt.style.use('seaborn-dark')

        sweep_val = getattr(self, self.ind_var)
        selector = self.expt_list['Active Status']
        sweep_title = (self.expt_list['Independent Variable']
                       [selector].to_string(index=False))
        units = self.expt_list['Units'][selector].to_string(index=False)

        # t_batch is the times for gc collection within one step
        t_batch = list(self.t_steady_state
                       + self.sample_rate * np.arange(0, self.sample_set_size))
        # setpoint0 is 0 or list of zeros for gasses
        setpoint0 = [0] * np.size(sweep_val[0])
        if self.expt_type == 'temp_sweep':
            if units == 'K':
                setpoint0 = 293
            elif units == 'C':
                setpoint0 = 20

            delta_T = np.diff(sweep_val)
            # sets time to change temps based on heat_rate
            t_trans = np.append((sweep_val[0] - setpoint0),
                                delta_T) / self.heat_rate
        else:
            t_trans = np.array([0] * len(sweep_val))  # 0 min transition time

        # Define the values for the first step condition
        # These two define time and value setting of reactor
        t_set = np.array([0, t_trans[0], t_batch[-1] + self.t_buffer])
        setpoint = np.vstack((setpoint0, sweep_val[0], sweep_val[0]))
        # These two define time and value GC collects data
        t_sample = np.array(t_batch)
        # sample_val = np.array([sweep_val[0]]*self.sample_set_size)
        sample_val = np.tile(sweep_val[0], (self.sample_set_size, 1))

        # Loop through remaining setpoints
        for step_num in range(1, len(sweep_val)):
            # new sample times: start at last sample,
            # add t_buffer, add new batch
            t_sample = np.append(t_sample,
                                 t_sample[-1] + self.t_buffer + t_batch)
            sample_val = np.concatenate((sample_val,
                                         np.tile(sweep_val[step_num],
                                                 (self.sample_set_size, 1))))
            # add two points to t_set:
            # 1) last set point time + transition time
            # 2) last set point + time of last gc run + buffer
            t_set = np.append(t_set, [t_set[-1] + t_trans[step_num],
                                      t_set[-1] + t_batch[-1] + self.t_buffer])
            setpoint = np.concatenate(
                (setpoint, np.tile(sweep_val[step_num], (2, 1))))

        if fig is None:
            fig = plt.figure()

        fig.clear()
        ax1 = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2)

        ax1.plot(t_set, setpoint, '-o')
        ax1.plot(t_sample, sample_val, 'x')
        ylim_max = 1.1 * np.max(sweep_val)
        ylim_min = 0.9 * np.min(sweep_val) - 0.05
        ax1.set_ylim([ylim_min, ylim_max])

        ax2.plot(t_set[0:3], setpoint[0:3], '-o')
        ax2.plot(t_sample[0:self.sample_set_size],
                 sample_val[0:self.sample_set_size], 'x')
        ylim_max = 1.1 * np.max(sample_val[self.sample_set_size - 1])
        ylim_min = 0.9 * np.max(sample_val[0]) - 0.05
        # ax2.set_ylim([ylim_min, ylim_max])
        ax2.set_xlim([t_set[0] - 5, t_set[2] + self.t_buffer + 5])

        fig.add_subplot(111, frameon=False)
        # hide tick and tick label of the big axis
        plt.tick_params(labelcolor='none', which='both',
                        top=False, bottom=False, left=False, right=False)
        plt.xlabel("time [min]")
        plt.ylabel(sweep_title + ' [' + units + ']')
        ax1.annotate('Experiment Overview', xy=(0.05, 0.95),
                     xycoords='axes fraction')
        line_names = ['Setpoint', "GC Sample"]
        if self.expt_type in ['comp_sweep', 'calibration']:
            line_names = self.gas_type + ["GC Sample"]

        ax2.legend(labels=line_names, loc='lower right')

        plt.tight_layout()

        run_time = t_set[-1]  # TODO break this out into seperate func
        return (fig, ax1, ax2, run_time)

    def update_eqpt_list(self, eqpt_list):
        """
        Assign equipment objects as attributes of Experiment object.

        Takes eqpt_list as tuple in format
        (gc controller, laser controller, gas controler, heater)
        and assigns each component to experiment object
        updates sample rate by given value in gc_control and updates heater
        ramp rate by the rate specified in experiment object

        Parameters
        ----------
        eqpt_list: list[object]
            (:py:class:`~catalight.equipment.sri_gc.gc_control.GC_Connector`,
            :class:`~catalight.equipment.diode_laser.diode_control.Diode_Laser`,
            :class:`~catalight.equipment.alicat_MFC.gas_control.Gas_System`,
            :class:`~catalight.equipment.harrick_watlow.heater_control.Heater`)
        """
        # eqpt_list needs to be tuple
        self._gc_control = eqpt_list[0]
        self._laser_control = eqpt_list[1]
        self._gas_control = eqpt_list[2]
        self._heater = eqpt_list[3]

        if self.sample_rate >= self._gc_control.min_sample_rate:
            # try to set sample rate to that defined by expt
            self._gc_control.sample_rate = self.sample_rate
        else:
            # If that failed, _gc_control.sample_rate will be set to min
            # defined by ctrl file. This line makes sure gc and expt match
            self._sample_rate = self._gc_control.sample_rate
        self._heater.ramp_rate = self.heat_rate

    def set_initial_conditions(self):
        """Set initial conditions for experiment.

        Uses the first element of each attributes list to define initial
        conditions. Will also check that the temperature is not more than
        10 degrees C above the first setpoint.
        The order is:
        1. Set temperature
        2. Give 1 minute time warning for laser
        3. Set initial laser power
        4. Set gas type
        5. Set gas flows
        6. Wait 2 minutes
        7. Print gas flows
        8. Update gc sample set size
        9. Update date, time, and update log
        """
        unit = self.expt_list['Units'][0]
        self._heater.ramp(self.temp[0], temp_units=unit)
        starting_temp = self._heater.read_temp()
        starting_sp = self._heater.read_setpoint()
        print('Starting Temp = ' + str(starting_temp) + ' C')
        while starting_temp > (starting_sp + 10):
            print('Reactor is hotter than starting setpoint. Cooling...')
            time.sleep(120)
            starting_temp = self._heater.read_temp()

        if self.power[0] > 0:
            self._laser_control.time_warning(1)
            # Wait for a minute before turning on laser for safety
            time.sleep(60)

        self._laser_control.set_power(self.power[0])
        self._gas_control.set_gasses(self.gas_type)
        self._gas_control.set_flows(self.gas_comp[0], self.tot_flow[0])
        time.sleep(120)  # Wait for gas to steady out
        self._gas_control.print_flows()
        self._gc_control.sample_set_size = self.sample_set_size

        # Update experiment start time and date, save to log.
        self.update_date()
        self._start_time = time.time()  # Log beginning of expt
        # TODO Its a little silly to do all this instead of define a higher
        # level path as a instance attr in the first place.
        log_path = os.path.join(os.path.dirname(self.data_path),
                                'expt_log.txt')
        self.update_expt_log(log_path)

    def run_experiment(self):
        """
        Directs connected equipment to run experiment based on attributes.

        Most critical method of the class/package. This method directs the
        equipiment to actually carry out the experiment based on the assigned
        attribute values for the object instance. This method currently works
        by using a series of if-statements to determine the experiment type
        and take the corresponding actions.
        """
        print('Starting ' + self.expt_type + self.expt_name)
        self.set_initial_conditions()
        step_num = 1
        # Creates subfolders for each step of experiment
        for step in getattr(self, self._ind_var):

            # Compare Boolean
            units = (self.expt_list['Units']
                     [self.expt_list['Active Status']].to_string(index=False))

            # This sets path for data storage according to expt type
            # ------------------------------------------------------
            if self._ind_var == 'gas_comp':  # merge gas_comp into name
                print(step)
                print(self.gas_type)
                step_str = '_'.join(
                    [str(m) + n for m, n in zip(step, self.gas_type)])
                path = os.path.join(self.data_path,
                                    ('%i %s%s' % (step_num, step_str, units)))
            elif self.expt_type == 'stability_test':
                path = os.path.join(self.data_path, '1 Stability_Test')
            else:
                path = os.path.join(self.data_path,
                                    ('%i %d%s' % (step_num, step, units)))
            step_num += 1

            # This chooses the run type and sets condition accordingly
            # --------------------------------------------------------
            # Python 3.10+ implements match/case which could replace these.
            if self.expt_type == 'temp_sweep':
                self._heater.ramp(step, temp_units=self.expt_list['Units'][0])
            elif self.expt_type == 'power_sweep':
                self._laser_control.set_power(step)
            elif self.expt_type in ['comp_sweep', 'calibration']:
                self._gas_control.set_flows(step, self.tot_flow[0])
                self._gas_control.print_flows()
            elif self.expt_type == 'flow_sweep':
                self._gas_control.set_flows(self.gas_comp[0], step)
                print(self.gas_type)
                print(np.array(self.gas_comp) * step)
                self._gas_control.print_flows()
            elif self.expt_type == 'stability_test':
                pass
                # Stability Test conditions set in initial conditions

            # This segment times when to start GC and prints status
            # -----------------------------------------------------
            print('Waiting for steady state: '
                  + time.strftime("%H:%M:%S", time.localtime()))
            t1 = time.time()
            while self._gc_control.is_running():
                time.sleep(10)  # Don't update ctrl file while running
            self._gc_control.update_ctrl_file(path)
            t2 = time.time()
            t_passed = round(t2 - t1)  # GC can take a while to respond
            for i in range(int(self.t_steady_state * 60 - t_passed)):
                time.sleep(1)  # Break sleep in bits so keyboard interupt works

            print('Starting Collection: '
                  + time.strftime("%H:%M:%S", time.localtime()))
            print('Starting Temp = ', self._heater.read_temp(), ' C')
            self._gc_control.peaksimple.SetRunning(1, True)
            # t_collect ends on last gc pull
            t_collect = self.sample_rate * (self.sample_set_size - 1) * 60

            for i in range(int(t_collect)):
                time.sleep(1)

            print('Finished Collecting: '
                  + time.strftime("%H:%M:%S", time.localtime()))
            time.sleep(self.t_buffer * 60)
            print('Ending = ', self._heater.read_temp(), ' C')

            print('Step Finished: '
                  + time.strftime("%H:%M:%S", time.localtime()))

        print('Finished ' + self.expt_type + self.expt_name)


if __name__ == "__main__":
    # This is just a demo which runs when you run this class file as the main
    # script as of 20221026 this demo will not run because an extra mfc was
    # added to setup
    plt.close('all')
    # main_fol = ("C:\\Users\\brile\\Documents\\Temp Files\\"
    #             "20210524_8%AgPdMix_1wt%__200C_24.8mg\\PostReduction")
    main_fol = 'C:\\Users\\brile\\Documents\\Temp Files'
    Expt1 = Experiment()
    Expt1.expt_type = 'temp_sweep'
    Expt1.temp = list(np.arange(30, 150, 10) + 273)
    Expt1.gas_comp = [[0.01, 1 - 0.06, 0.05]]
    Expt1.tot_flow = [50]
    Expt1.sample_name = '20211221_fakesample'
    Expt1.plot_sweep()
    print('finished expt1')
    # Expt1.create_dirs(main_fol)

    Expt2 = Experiment()
    Expt2.expt_type = 'power_sweep'
    Expt2.power = list(np.arange(30, 150, 10))
    Expt2.gas_comp = [[0.01, 1 - 0.06, 0.05]]
    Expt2.tot_flow = [50]
    Expt2.plot_sweep()
    print('finished expt 2')
    # Expt2.create_dirs(main_fol)

    Expt3 = Experiment()
    Expt3.expt_type = 'flow_sweep'
    Expt3.temp = [273]
    Expt3.gas_comp = [[0.01, 1 - 0.06, 0.05]]
    Expt3.tot_flow = list(np.arange(10, 60, 10))
    Expt3.sample_name = '20211221_fakesample'
    _, _, _, t = Expt3.plot_sweep()
    print('finished expt3')

    Expt4 = Experiment()
    Expt4.expt_type = 'comp_sweep'
    Expt4.temp = [273]
    P_c2h2 = np.arange(0.5, 3.1, 0.5) / 100
    P_h2 = P_c2h2 * 5
    P_Ar = 1 - P_c2h2 - P_h2
    Expt4.gas_comp = np.stack([P_c2h2, P_Ar, P_h2], axis=1).tolist()
    Expt4.tot_flow = [50]
    Expt4.sample_name = '20211221_fakesample'
    Expt4.plot_sweep()
    print('finished expt4')

    Expt5 = Experiment()
    Expt5.expt_type = 'calibration'
    Expt5.gas_type = ['CalGas', 'Ar', 'H2']
    Expt5.temp = [273]
    P_CalGas = np.array([100, 50, 10]) / 100  # pretend one 1000ppm gas
    P_H2 = P_CalGas * 0
    P_Ar = 1 - P_CalGas - P_H2
    Expt5.gas_comp = np.stack([P_CalGas, P_Ar, P_H2], axis=1).tolist()
    Expt5.tot_flow = [50]
    Expt5.sample_name = '20211221_fakesample'
    Expt5.plot_sweep()
    # Expt5.create_dirs(main_fol)
    print('finished expt5')

    Expt6 = Experiment()
    Expt6.expt_type = 'stability_test'
    Expt6.gas_type = ['c2h2', 'Ar', 'H2']
    Expt6.temp = [100]
    P_c2h2 = 1 / 100
    P_h2 = P_c2h2 * 5
    P_Ar = 1 - P_c2h2 - P_h2
    Expt6.gas_comp = [[P_c2h2, P_Ar, P_h2]]
    Expt6.tot_flow = [50]
    Expt6.sample_name = '20210524_8%AgPdMix_1wt%_25mg'
    Expt6._date = '20211208'
    Expt6.plot_sweep()
    # Expt6.create_dirs(main_fol)
    print('finished Expt6')

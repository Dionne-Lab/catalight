# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 08:30:33 2021
This is the experiment class file. Ultimately, this class will be capable of:
self.create_dirs : make directories for raw data and results
TODO setting experimental parameters
TODO running the experiment
TODO analyzing the data
TODO step number on folder incase nonmonotonic
TODO matlab cases? switch?
This File can likely get folded into gcdata.py to define experiment and data
classes in the same module in the future
@author: Briley Bourgeois
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from ast import literal_eval
from datetime import date
import os
import time


class Experiment:
    '''
    An object that contains all of the information necessary to run a
    particular experiment.

    Attributes
    ----------
        expt_list : pandas data frame; defines possible experiment types
        temp : list of floats; one element if constant or multiple for sweep
        power : list of floats; ''
        tot_flow : list of floats; ''
        gas_comp : list of list [[gas1, gas2, gas3],[...]]
        gas_type : list of strings
        date : str; update w/ method. For logging
        expt_type : str; allowable sweep type. New additions need to be coded
        sample_name : str; non-public attr for logging
        ind_var : str; non-public for internal use
        expt_name : str; list fixed variables for expt
        results_path : str; save location for analysis, defined relative to log
        data_path : str; save location for raw data, defined relative to log
    '''

    def __init__(self, eqpt_list=False):
        """

        Parameters
        ----------
        eqpt_list : , optional
            DESCRIPTION. The default is 'None'.

        Returns
        -------
        None.

        """

        # This class attribute defines the possible experiments. This is an
        # important part of the class and should be altered with caution
        self.expt_list = pd.DataFrame(
            [['temp_sweep',      'temp', False,    'K'],
             ['power_sweep',    'power', False,   'mW'],
             ['comp_sweep',  'gas_comp', False, 'frac'],
             ['flow_sweep',  'tot_flow', False, 'sccm'],
             ['calibration', 'gas_comp', False,  'ppm'],
             ['stability_test',  'time', False,  'min']],
            columns=['Expt Name',
                     'Independent Variable',
                     'Active Status',
                     'Units'])

        # These are just random default values.
        # these should all be numpy arrays and floats
        self._temp = [273.0]
        self._power = [0.0]
        self._tot_flow = [0.0]  # This can't be larger than 50
        # Every row should add to one
        self._gas_comp = [[0.0, 50.0, 0.0]]
        self._gas_type = ['C2H2', 'Ar', 'H2']

        # Returns todays date as YYYYMMDD by default
        self._date = date.today().strftime('%Y%m%d')
        self._expt_type = 'Undefined'
        self._sample_name = 'Undefined'
        self._ind_var = 'Undefined'
        self._expt_name = 'Undefined'
        self._results_path = 'Undefined'
        self._data_path = 'Undefined'

        if eqpt_list is not False:
            # eqpt_list needs to be tuple
            self._gc_control = eqpt_list[0]
            self._laser_control = eqpt_list[1]
            self._MFC_A = eqpt_list[2]
            self._MFC_B = eqpt_list[3]
            self._MFC_C = eqpt_list[4]
            self._MFC_D = eqpt_list[5]
            #self._heater = eqpt_list[6]

    # These setter functions apply rules for how certain properties can be set
    def _str_setter(attr):
        def set_any(self, value):

            setattr(self, attr, value)
        return set_any

    def _num_setter(attr):
        def set_any(self, value):
            if isinstance(value, np.ndarray):
                value = list(value)

            if not isinstance(value, list):
                raise AttributeError(attr+' must be list')
            elif (attr == '_tot_flow') & (np.max(value) > 50):
                raise AttributeError('Total flow must be <= 50')
            elif (attr == '_gas_comp'):
                for composition in value:
                    if sum(composition) != 1:
                        raise AttributeError(
                            'Gas comp. must be list of list == 1')
            setattr(self, attr, value)
        return set_any

    def _attr_getter(attr):
        def get_any(self):
            return getattr(self, attr)
        return get_any

    # Number Properties
    temp = property(fget=_attr_getter('_temp'),
                    fset=_num_setter('_temp'))
    power = property(fget=_attr_getter('_power'),
                     fset=_num_setter('_power'))
    tot_flow = property(fget=_attr_getter('_tot_flow'),
                        fset=_num_setter('_tot_flow'))
    gas_comp = property(fget=_attr_getter('_gas_comp'),
                        fset=_num_setter('_gas_comp'))

    # String Properties
    gas_type = property(fget=_attr_getter('_gas_type'),
                        fset=_str_setter('_gas_type'))
    sample_name = property(fget=_attr_getter('_sample_name'),
                           fset=_str_setter('_sample_name'))

    # Read only properties
    date = property(lambda self: self._date)
    ind_var = property(lambda self: self._ind_var)
    expt_name = property(lambda self: self._expt_name)
    results_path = property(lambda self: self._results_path)
    data_path = property(lambda self: self._data_path)

    @property
    def expt_type(self):
        return self._expt_type

    @expt_type.setter
    def expt_type(self, expt_type):
        # Evaluate whether entered experiment type is in default list
        if expt_type not in self.expt_list['Expt Name'].tolist():
            raise AttributeError('Invalid Experiment Type Provided')

        self._expt_type = expt_type
        self.expt_list['Active Status'] = (
            self.expt_list['Expt Name'] == self._expt_type)

        # Defines Independent Variable as string provided by expt list
        var_list = self.expt_list['Independent Variable'][0:4]  # Pull List
        # Compare Boolean
        ind_var_series = var_list[self.expt_list['Active Status']]
        # Convert to str
        self._ind_var = ind_var_series.to_string(index=False)

    def update_date(self):
        self._date = date.today().strftime('%Y%m%d')

    def update_expt_log(self, sample_path):
        with open(os.path.join(sample_path, 'expt_log.txt'), 'w+') as log:
            log_entry = [
                'Experiment Date = ' + self.date,
                'Experiment Type = ' + self.expt_type,
                'Experiment Name = ' + self.expt_name,
                'Sample Name = ' + self.sample_name,
                'Temperature [' + self.expt_list['Units'][0] + '] = '
                + str(self.temp),
                'Power ['+self.expt_list['Units'][1]+'] = ' + str(self.power),
                'Gas 1 type = ' + self.gas_type[0],
                'Gas 2 type = ' + self.gas_type[1],
                'Gas 3 type = ' + self.gas_type[2],
                'Gas Composition [' + self.expt_list['Units'][2] +
                '] = ' + str(self.gas_comp[0]),
                'Total Flow [' + self.expt_list['Units'][3] +
                '] = ' + str(self.tot_flow)
            ]
            log.write('\n'.join(log_entry))

    def read_expt_log(self, log_path):
        """
        Reads data from an existing log file and updates object parameters

        Parameters
        ----------
        log_path : str
            string to the full file path of the log file ('./expt_log.txt').

        Returns
        -------
        None.

        """

        with open(log_path, 'r') as log:
            data = []
            for line in log:  # read in the values after '=' sign line by line
                data.append(line.split('=')[-1].strip(' \n'))

            self._date = data[0]
            self.expt_type(data[1])
            self._expt_name = data[2]
            self.sample_name = data[3]
            self.temp = literal_eval(data[4])
            self.power = literal_eval(data[5])
            self.gas_type = [data[6], data[7], data[8]]
            self.gas_comp = literal_eval(data[9])
            self.tot_flow = literal_eval(data[10])
            self.update_save_paths()  # Will throw error if no data folders

    def _update_expt_name(self):
        """
        Non-public function that updates expt_name based on current settings

        Returns
        -------
        None.

        """

        # Defines all settings to be included in path name and adds units
        expt_settings = pd.Series(
            [str(self.temp[0]), str(self.power[0]),
             '_'.join([str(m)+n for m, n in zip(self.gas_comp[0],
                                                self.gas_type)]),
             str(self.tot_flow[0])]) + self.expt_list['Units']

        # Only select fixed variable for path name
        fixed_vars = expt_settings[~self.expt_list['Active Status']]
        self._expt_name = '_'.join(fixed_vars.to_list())  # Define expt_name

    def update_save_paths(self, log_path, should_exist=True):
        """
        Updates data/results paths for the object. Used when readin expt from
        log file or creating new expt data set

        Parameters
        ----------
        log_path : str
            string to the full file path of the log file ('./expt_log.txt').
        should_exist : Boolean, optional
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

        sample_path = os.path.dirname(log_path)

        # Defines path for saving results
        self._results_path = os.path.join(sample_path, 'Results',
                                          self.date + self.expt_type
                                          + '_' + self.expt_name)

        # Defines path for saving raw data
        self._data_path = os.path.join(sample_path, 'Data',
                                       self.date + self.expt_type
                                       + '_' + self.expt_name)

        # If updating paths from file, paths should exist in log directory
        exists = (os.path.isdir(self.results_path)
                  | os.path.isdir(self.data_path))
        if (should_exist) & (not exists):
            raise ValueError('results/data path doesn''t exist where expected')

    def create_dirs(self, sample_path):
        '''
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
        AttributeError: Throws error if expt_type is undefined

        Returns
        -------
        None.

        '''

        if self.expt_type == 'Undefined':
            raise AttributeError(
                'Experiment Type Must Be Defined Before Creating Directories')

        self._update_expt_name()
        self.update_save_paths(os.path.join(sample_path, 'expt_log.txt'),
                               should_exist=False)

        os.makedirs(self.results_path, exist_ok=True)
        step_num = 1
        # Creates subfolders for each step of experiment
        for step in getattr(self, self._ind_var):
            # Compare Boolean
            units = (self.expt_list['Units']
                     [self.expt_list['Active Status']].to_string(index=False))
            path = os.path.join(self.data_path,
                                ('%i %d%s' % (step_num, step, units)))
            os.makedirs(path, exist_ok=True)
            step_num += 1

        self.update_expt_log(sample_path)

    def plot_sweep(self, t_steady_state=15, sample_set_size=4, t_buffer=5):
        # plot the sweep parameter vs time
        # have to get the sample run time from GC
        # Some Plot Defaults
        plt.rcParams['axes.linewidth'] = 2
        plt.rcParams['lines.linewidth'] = 1.5
        plt.rcParams['xtick.major.size'] = 6
        plt.rcParams['xtick.major.width'] = 1.5
        plt.rcParams['ytick.major.size'] = 6
        plt.rcParams['ytick.major.width'] = 1.5
        plt.rcParams['figure.figsize'] = (6.5, 8)
        plt.rcParams['font.size'] = 14
        plt.rcParams['axes.labelsize'] = 18

        sample_rate = 10  # TODO import this, sample/min
        heat_rate = 10  # TODO import, deg/min
        sweep_val = getattr(self, self.ind_var)
        selector = self.expt_list['Active Status']
        sweep_title = (self.expt_list['Independent Variable']
                       [selector].to_string(index=False))
        units = self.expt_list['Units'][selector].to_string(index=False)

        t_batch = list(t_steady_state
                       + sample_rate*np.arange(0, sample_set_size))
        setpoint0 = [0]*np.size(sweep_val[0])
        if self.expt_type == 'temp_sweep':
            if units == 'K':
                setpoint0 = 293
            elif units == 'C':
                setpoint0 = 20

            heat_rate = 10  # TODO import, deg/min
            delta_T = np.diff(sweep_val)
            t_trans = np.append((sweep_val[0]-setpoint0), delta_T)/heat_rate
        else:
            t_trans = np.array([0]*len(sweep_val))

        # Define the values for the first step condition
        # These two define time and value setting of reactor
        t_set = np.array([0, t_trans[0], t_batch[-1]+t_buffer])
        setpoint = np.vstack((setpoint0, sweep_val[0], sweep_val[0]))
        # These two define time and value GC collects data
        t_sample = np.array(t_batch)
        # sample_val = np.array([sweep_val[0]]*sample_set_size)
        sample_val = np.tile(sweep_val[0], (sample_set_size, 1))

        # Loop through remaining setpoints
        for step_num in range(1, len(sweep_val)):
            t_sample = np.append(t_sample,
                                 t_sample[-1]+t_buffer+t_batch)
            sample_val = np.concatenate((sample_val, np.tile(sweep_val[step_num],
                                                             (sample_set_size, 1))))
            t_set = np.append(t_set, [t_set[-1] + t_trans[step_num],
                                      t_set[-1] + t_batch[-1] + t_buffer])
            setpoint = np.concatenate(
                (setpoint, np.tile(sweep_val[step_num], (2, 1))))

        fig, (ax1, ax2) = plt.subplots(2, 1)
        ax1.plot(t_set, setpoint, '-o')
        ax1.plot(t_sample, sample_val, 'x')
        ylim_max = 1.1*np.max(sweep_val)  # TODO what about gas comp
        ylim_min = 0.9*np.min(sweep_val)-0.05
        ax1.set_ylim([ylim_min, ylim_max])

        ax2.plot(t_set[1:6], setpoint[1:6], '-o')
        ax2.plot(t_sample[3:8], sample_val[3:8], 'x')
        ylim_max = 1.1*np.max(sample_val[7])  # TODO what about gas comp
        ylim_min = 0.9*np.max(sample_val[3])-0.05
        # ax2.set_ylim([ylim_min, ylim_max])
        ax2.set_xlim([t_sample[3]-5, t_sample[7]+t_buffer+5])

        fig.add_subplot(111, frameon=False)
        # hide tick and tick label of the big axis
        plt.tick_params(labelcolor='none', which='both',
                        top=False, bottom=False, left=False, right=False)
        plt.xlabel("time [min]")
        plt.ylabel(sweep_title + ' ['+units+']')
        plt.tight_layout()
        plt.show()

        return (fig, ax1, ax2)

    def run_experiment(self, t_steady_state=15, sample_set_size=4, t_buffer=5):
        print('running expt')

        # TODO create custom gas mix for this
        # Note: I could wrap all the MFCs in a single class
        self._MFC_A.set_gas(self.gas_type[0])
        self._MFC_B.set_gas(self.gas_type[1])
        self._MFC_C.set_gas(self.gas_type[2])
        self._MFC_D.set_gas(self.gas_type[1])

        step_num = 1
        # Creates subfolders for each step of experiment
        for step in getattr(self, self._ind_var):

            # Compare Boolean
            units = (self.expt_list['Units']
                     [self.expt_list['Active Status']].to_string(index=False))
            path = os.path.join(self.data_path,
                                ('%i %d%s' % (step_num, step, units)))
            step_num += 1

            # This chooses the run type and sets condition accordingly
            if self.expt_type == 'temp_sweep':
                print('temp_sweep no yet fully supported')
            elif self.expt_type == 'power_sweep':
                self._laser_control.set_power(step)
            elif self.expt_type == 'comp_sweep':

                self._MFC_A.set_flow_rate(float(step[0]*self.tot_flow[0]))
                self._MFC_B.set_flow_rate(float(step[1]*self.tot_flow[0]))
                self._MFC_C.set_flow_rate(float(step[2]*self.tot_flow[0]))
                print(self.gas_type)
                print(step*self.tot_flow)
                print('MFC A = ' + str(self._MFC_A.get()['setpoint'])
                      + self._MFC_A.get()['gas'])
                print('MFC B = ' + str(self._MFC_B.get()['setpoint'])
                      + self._MFC_B.get()['gas'])
                print('MFC C = ' + str(self._MFC_C.get()['setpoint'])
                      + self._MFC_C.get()['gas'])
                print('MFC D = ' + str(self._MFC_D.get()['mass_flow'])
                      + self._MFC_D.get()['gas'])

            elif self.expt_type == 'flow_sweep':

                self._MFC_A.set_flow_rate(float(self.gas_comp[0][0]*step))
                self._MFC_B.set_flow_rate(float(self.gas_comp[0][1]*step))
                self._MFC_C.set_flow_rate(float(self.gas_comp[0][2]*step))
                print(self.gas_type)
                print(np.array(self.gas_comp)*step)
                print('MFC A = ' + str(self._MFC_A.get()['setpoint'])
                      + self._MFC_A.get()['gas'])
                print('MFC B = ' + str(self._MFC_B.get()['setpoint'])
                      + self._MFC_B.get()['gas'])
                print('MFC C = ' + str(self._MFC_C.get()['setpoint'])
                      + self._MFC_C.get()['gas'])
                print('MFC D = ' + str(self._MFC_D.get()['mass_flow'])
                      + self._MFC_D.get()['gas'])

            # Very important to have a pause after using the GC!!
            print('Waiting for steady state:')
            print(time.strftime("%H:%M:%S", time.localtime()))
            t1 = time.time()
            self._gc_control.update_ctrl_file(path)
            t2 = time.time()
            t_passed = t2-t1
            time.sleep(t_steady_state*60-t_passed)

            print('Starting Collection:')
            print(time.strftime("%H:%M:%S", time.localtime()))
            self._gc_control.peaksimple.SetRunning(1, True)
            time.sleep(self._gc_control.sample_rate*sample_set_size*60)

            print('Finished Collecting:')
            print(time.strftime("%H:%M:%S", time.localtime()))
            time.sleep(t_buffer*60)

            print('Step Finished:')
            print(time.strftime("%H:%M:%S", time.localtime()))


if __name__ == "__main__":
    # This is just a demo which runs when you run this class file as the main script
    plt.close('all')
    main_fol = ("C:\\Users\\brile\\Documents\\Temp Files\\"
                "20210524_8%AgPdMix_1wt%__200C_24.8mg\\PostReduction")
    Expt1 = Experiment()
    Expt1.expt_type = 'temp_sweep'
    Expt1.temp = list(np.arange(30, 150, 10)+273)
    Expt1.gas_comp = [[0.01, 1-0.06, 0.05]]
    Expt1.tot_flow = [50]
    Expt1.sample_name = '20211221_fakesample'
    Expt1.plot_sweep()
    print('finished expt1')
    # Expt1.create_dirs(main_fol)
    Expt2 = Experiment()
    Expt2.expt_type = 'power_sweep'
    Expt2.power = list(np.arange(30, 150, 10))
    Expt2.gas_comp = [[0.01, 1-0.06, 0.05]]
    Expt2.tot_flow = [50]
    Expt2.plot_sweep()
    print('finished expt 2')
    # Expt2.create_dirs(main_fol)
    Expt3 = Experiment()
    Expt3.expt_type = 'flow_sweep'
    Expt3.temp = [273]
    Expt3.gas_comp = [[0.01, 1-0.06, 0.05]]
    Expt3.tot_flow = list(np.arange(10, 60, 10))
    Expt3.sample_name = '20211221_fakesample'
    Expt3.plot_sweep()
    print('finished expt3')
    Expt4 = Experiment()
    Expt4.expt_type = 'comp_sweep'
    Expt4.temp = [273]
    P_c2h2 = np.arange(0.5, 3.1, 0.5)/100
    P_h2 = P_c2h2*5
    P_Ar = 1-P_c2h2-P_h2
    Expt4.gas_comp = np.stack([P_c2h2, P_Ar, P_h2], axis=1).tolist()
    Expt4.tot_flow = [50]
    Expt4.sample_name = '20211221_fakesample'
    Expt4.plot_sweep()
    print('finished expt4')

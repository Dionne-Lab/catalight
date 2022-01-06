# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 08:30:33 2021
This is the experiment class file. Ultimately, this class will be capable of: 
self.create_dirs : make directories for raw data and results
TODO setting experimental parameters
TODO running the experiment
TODO analyzing the data
This File can likely get folded into gcdata.py to define experiment and data
classes in the same module in the future
@author: Briley Bourgeois
"""
import pandas as pd
import numpy as np
from datetime import date
import os

class Experiment: 
    """this is the general class for creating a new experiment"""
    
    def __init__(self, eqpt_list='None'):
        
        # This class attribute defines the possible experiments. This is an 
        # important part of the class and should be altered with caution
        self.expt_list = pd.DataFrame(
               [[ 'temp_sweep',      'temp', 0, 'K'],
                ['power_sweep',     'power', 0, 'mW'],
                [ 'comp_sweep',  'gas_comp', 0, 'sccm'],
                [ 'flow_sweep',  'tot_flow', 0, 'tot_sccm']],
               columns = ['Expt Name', 'Independent Variable', 'Active Status', 'Units'])
        
        # These are just random default values. only expt_type needs this so far
        self.temp = 273
        self.power = 0
        self.gas_comp = [0, 0, 0]
        self.gas_type = ['C2H2', 'Ar', 'H2']
        self.tot_flow = sum(self.gas_comp)
        self.expt_type = 'Undefined'
        self.sample_name = 'no_sample_name_given'
        self.date = date.today().strftime('%Y%m%d') # Returns todays date as YYYYMMDD by default
        
    def set_expt_type(self, expt_type):
        # Evaluate whether entered experiment type is in default list
        if expt_type not in self.expt_list['Expt Name'].tolist():
            raise AttributeError('Invalid Experiment Type Provided')
        
        self.expt_type = expt_type        
        self.expt_list['Active Status'] = (self.expt_list['Expt Name'] == self.expt_type)
        
        # Defines Independent Variable as string provided by experiment list
        var_list = self.expt_list['Independent Variable'] # Pull List
        ind_var_series = var_list[self.expt_list['Active Status']] # Compare Boolean
        self.ind_var = ind_var_series.to_string(index=False) # Convert to str
    
    def update_expt_log(self, sample_path):
        log = open(os.path.join(sample_path, 'expt_log.txt'),'w+')
        log_entry = [
            'Experiment Date = ' + self.date,
            'Experiment Type = ' + self.expt_type,
            'Experiment Name = ' + self.sample_name,
            'Temperature ['+ self.expt_list['Units'][0]+'] = ' + str(self.temp),
            'Power ['+self.expt_list['Units'][1]+'] = ' + str(self.power),
            'Gas 1 type = ' + self.gas_type[0],
            'Gas 2 type = ' + self.gas_type[1],
            'Gas 3 type = ' + self.gas_type[2],
            'Gas 1 Flow ['+ self.expt_list['Units'][2]+'] = ' + str(self.gas_comp[0]),
            'Gas 2 Flow ['+ self.expt_list['Units'][2]+'] = ' + str(self.gas_comp[1]),
            'Gas 3 Flow ['+ self.expt_list['Units'][2]+'] = ' + str(self.gas_comp[2]),
            'Total Flow ['+ self.expt_list['Units'][3]+'] = ' + str(self.tot_flow),
            ]
        log.write('\n'.join(log_entry))
        log.close()
        return
        
    def read_expt_log(self, log_path):
        log = open(log_path,'r')
        data = []
        for line in log: # read in the values after '=' sign line by line
            data.append(line.split('=')[-1].strip(' \n'))
        
        self.date = data[0]
        self.expt_type = data[1]
        self.sample_name = data[2] 
        
        # take in string of array, strip spaces and brackets from ends, 
        # seperate into list of strings, convert to np array
        self.temp = np.array(data[3].strip(' []').split(' '), dtype=np.float32)
        self.power = np.array(data[4].strip(' []').split(' '), dtype=np.float32)
        self.gas_type = [data[5], data[6], data[7]]
        self.gas_comp = [float(data[8]), float(data[9]), float(data[10])]
        self.tot_flow = float(data[11])
        log.close()
        return
        

    def create_dirs(self, MainFol):
        '''
        This function creates a set of directories to store experimental data 
        for a given experiment and the results of the experiment

        Parameters
        ----------
        MainFol : Input the path where the data should be stored (sample folder)

        Raises
        ------
        AttributeError : Throws error if expt_type is undefined

        Returns
        -------
        None.

        '''
        
        if self.expt_type == 'Undefined':
            raise AttributeError('Experiment Type Must Be Defined Before Creating Directories')
        
        # Defines all settings to be included in path name and adds units
        expt_settings = pd.Series(
            [str(self.temp),
             str(self.power),
             '_'.join([str(m)+n for m,n in zip(self.gas_comp, self.gas_type)]),
             str(self.tot_flow)]) + self.expt_list['Units']
        
        # Only select fixed variable for path name
        fixed_vars = expt_settings[~self.expt_list['Active Status']]
        self.expt_name = '_'.join(fixed_vars.to_list()) # Define expt_name
        
        # Defines path for saving results
        self.results_path = (MainFol + '\\Results\\' + self.date
                             + self.expt_type + '_' + self.expt_name)
        
        # Defines path for saving raw data
        self.data_path = (MainFol + '\\Data\\' + 
                          self.date+self.expt_type+'_'+self.expt_name)
        
        os.makedirs(self.results_path, exist_ok=True)
        # Creates subfolders for each step of experiment
        for step in getattr(self, self.ind_var):
            units = (self.expt_list['Units']
                     [self.expt_list['Active Status']].to_string(index=False)) # Compare Boolean
            path = os.path.join(self.data_path, str(step)+units)
            os.makedirs(path, exist_ok=True)
            
        self.update_expt_log(MainFol)
        return
    
             
if __name__ == "__main__":
    # This is just a demo which runs when you run this class file as the main script
    MainFol = ("G:/Shared drives/Hydrogenation Projects/AgPd Polyhedra/"
               "Ensemble Reactor/202111_pretreatment_tests/"
               "20210524_8%AgPdMix_1wt%__200C_24.8mg/PostReduction")
    Expt1 = Experiment()
    Expt1.set_expt_type('temp_sweep')
    Expt1.temp = np.arange(30, 150, 10)
    Expt1.gas_comp = [0.5, 47, 2.5]
    Expt1.sample_name = '20211221_fakesample'
    Expt1.create_dirs(MainFol)
    Expt2 = Experiment()
    Expt2.set_expt_type('power_sweep')
    Expt2.power = np.arange(30, 150, 10)
    Expt2.create_dirs(MainFol)

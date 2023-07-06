import time


class Gas_System:
    """MFC control."""
    # TODO update based on specific model
    factory_gasses = ['C2H2', 'Air', 'Ar', 'i-C4H10', 'n-C4H10', 'CO2', 'CO',
                      'D2', 'C2H6', 'C2H4', 'He', 'H2', 'Kr', 'CH4', 'Ne',
                      'N2', 'N2O', 'O2', 'C3H8', 'SF6', 'Xe']
    """Factory gas list saved to Alicat MFCs"""

    def __init__(self):
        """
        Connect MFCs based on COM port and address. User needs to update.

        The user needs to update the address and COM ports for each mfc
        based on their specific setup. This process can be assisted by using
        the "alicat_connection_tester.py" file
        """
        self.mfc_A = FlowController(port=cfg.mfc_list[0]['port'],
                                    address=cfg.mfc_list[0]['unit'])

        self.mfc_B = FlowController(port=cfg.mfc_list[1]['port'],
                                    address=cfg.mfc_list[1]['unit'])

        self.mfc_C = FlowController(port=cfg.mfc_list[2]['port'],
                                    address=cfg.mfc_list[2]['unit'])

        self.mfc_D = FlowController(port=cfg.mfc_list[3]['port'],
                                    address=cfg.mfc_list[3]['unit'])

        self.mfc_E = FlowMeter(port=cfg.mfc_list[4]['port'],
                               address=cfg.mfc_list[4]['unit'])
        self.is_busy = False

    def set_gasses(self, gas_list):
        """
        Update gas type to MFCs based on input list.

        Parameters
        ----------
        gas_list : list of str
            [gasA, gasB, gasC, gasD] Each must be within factory gasses.

        Returns
        -------
        None

        """
        # Custom mixes cannot be indexed by name in alicat package
        # mix 237 is designated as the calibration gas slot in this package
        # if calgas is given in gas_list, assign via mix number instead of name
        gas_list_copy = gas_list.copy()  # Don't edit global!!
        for i in range(len(gas_list_copy)):
            if gas_list_copy[i].lower() == 'calgas':
                gas_list_copy[i] = 237

        while self.is_busy:
            time.sleep(0)

        self.is_busy = True
        # set gas types here
        self.is_busy = False

    def set_flows(self, comp_list, tot_flow):
        """
        Set flow rates based as fraction of tot_flow from comp_list.

        Sets the flow rate of all mfc based on a desired total flow
        and the desired gas composition. Also call set_gasE
        TODO: add limit for tot_flow for each MFC

        Parameters
        ----------
        comp_list : list of float
            list of gas fraction for mfc [a, b, c, d]. Must sum to 1 or 100
        tot_flow : float
            Total flow to send.

        Raises
        ------
        AttributeError
            if gas comp doesn't sum to 1 or 100

        Returns
        -------
        None

        """
        comp_list = self.check_comp_total(comp_list)
        while self.is_busy:
            time.sleep(0)

        self.is_busy = True
        # set individual flow rate here
        self.is_busy = False

        self.set_gasE(comp_list)

    def set_gasE(self, comp_list):
        """
        Set gas E as a mixture of input gasses based on comp. and types.

        Parameters
        ----------
        comp_list : list of float
            list of gas fraction for mfc [a, b, c, d]. Must sum to 1 or 100

        Returns
        -------
        None

        """
        comp_list = self.check_comp_total(comp_list)

        while self.is_busy:
            time.sleep(0)

        self.is_busy = True
        gas_list = []
        for mfc in [self.mfc_A, self.mfc_B, self.mfc_C, self.mfc_D]:
            gas_name = mfc.get()['gas']
            if gas_name.lower() == 'calgas':
                gas_list.append('Ar')  # Can't handle custom mixes
            else:
                gas_list.append(gas_name)
        # convert to percents, make dict, drop zero values
        percents = np.array(comp_list, dtype=float) * 100
        gas_series = pd.Series(percents, gas_list)
        gas_series = gas_series.groupby(level=0).sum()  # sums duplicates
        gas_dict = gas_series.to_dict()
        gas_dict = {x: y for x, y in gas_dict.items() if y != 0}

        # Uses create_mix method to write to gas slot 236,
        # first custom gas slot on MFC
        if len(gas_dict) > 1:  # if more than 1 gas, creates mix
            self.mfc_E.create_mix(mix_no=236, name='output',
                                  gases=gas_dict)
            self.mfc_E.set_gas(236)
        else:  # If only one gas, sets that as output
            self.mfc_E.set_gas(list(gas_dict)[0])
        self.is_busy = False

    def check_comp_total(self, comp_list):
        """
        Takes in gas composition list, checks sum, returns as fractions.

        Parameters
        ----------
        comp_list : list of float or int
            Composition list in either percents or fractions.

        Raises
        ------
        AttributeError
            Composition list doesn't sum to 1 or 100

        Returns
        -------
        comp_list : list of float
            Updated composition list as fractions

        """

        if sum(comp_list) == 100:  # convert % to fraction
            comp_list[:] = [x / 100 for x in comp_list]

        if (sum(comp_list) != 1) and (sum(comp_list) != 0):
            raise AttributeError('Gas comp. must be list of list == 1')

        return comp_list

    def print_flows(self):
        """Print mass flow rates and gas type for each MFC to console."""
        while self.is_busy:
            time.sleep(0)

        self.is_busy = True
        print('MFC A = ' + str(self.mfc_A.get()['mass_flow'])
              + self.mfc_A.get()['gas'])
        print('MFC B = ' + str(self.mfc_B.get()['mass_flow'])
              + self.mfc_B.get()['gas'])
        print('MFC C = ' + str(self.mfc_C.get()['mass_flow'])
              + self.mfc_C.get()['gas'])
        print('MFC D = ' + str(self.mfc_D.get()['mass_flow'])
              + self.mfc_D.get()['gas'])
        print('MFC E = ' + str(self.mfc_E.get()['mass_flow'])
              + self.mfc_E.get()['gas'])
        self.is_busy = False

    def print_details(self):
        """
        Run mfc.get() for each mfc, printing full status details.

        Returns
        -------
        None

        """
        while self.is_busy:
            time.sleep(0)

        self.is_busy = True
        print(self.mfc_A.get())
        print(self.mfc_B.get())
        print(self.mfc_C.get())
        print(self.mfc_D.get())
        print(self.mfc_E.get())
        self.is_busy = False

    def read_flows(self):
        """
        Return full details of each mfc condition arranged in a dict.

        Returns
        -------
        flow_dict : dict of dict
            {mfc: mfc.get()}
        """
        while self.is_busy:
            time.sleep(0)

        self.is_busy = True
        flow_dict = {'mfc_A': self.mfc_A.get(),
                     'mfc_B': self.mfc_B.get(),
                     'mfc_C': self.mfc_C.get(),
                     'mfc_D': self.mfc_D.get(),
                     'mfc_E': self.mfc_E.get()}
        self.is_busy = False
        return (flow_dict)

    def shut_down(self):
        """Set MFC with Ar or N2 running to 1 sccm and others to 0."""
        while self.is_busy:
            time.sleep(0)

        self.is_busy = True
        mfc_list = [self.mfc_A, self.mfc_B, self.mfc_C, self.mfc_D]
        for mfc in mfc_list:
            if mfc.get()['gas'] in ['Ar', 'N2']:
                mfc.set_flow_rate(1.0)
            else:
                mfc.set_flow_rate(0.0)
        self.is_busy = False

    def disconnect(self):
        """Call Gas_System.shut_down then disconnect from MFCs."""
        self.shut_down()
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True
        self.mfc_A.close()
        self.mfc_B.close()
        self.mfc_C.close()
        self.mfc_D.close()
        self.mfc_E.close()
        self.is_busy = False
        del self

    def set_calibration_gas(self, mfc, calDF, fill_gas='Ar'):
        """
        Sets a custom gas mixture for the mfc of choice.

        Typically for calibration gas. Creates a gas mixture based on the
        largest 5 components calgas. Sets new mixture to slot 237 as name
        'CalGas'. This function uses the standard calDF format utilized
        elsewhere in this code. Please consult the alicat gas composer website
        for the official list of possible gasses.

        Parameters
        ----------
        mfc : alicat.FlowController | alicat.FlowMeter
            Mass flow controller or meter to update with calgas
        calDF : pandas.DataFrame
            Formatted DataFrame containing gc calibration data.
            Specific to control file used!
            Format [ChemID, slope, intercept, start, end]
        fill_gas : str
            Inert gas dilutant for calibration gas tank. The default is 'Ar'.
        """
        percents = calDF['ppm'] / 10000
        percents.index = percents.index.map(lambda x: x.split('_')[0])
        percents = percents[~percents.index.duplicated()]
        percents = percents.sort_values(ascending=False)
        new_idx = pd.DataFrame([False] * len(percents), index=percents.index)
        for chemical in percents.index:
            new_idx.loc[chemical] = chemical in Gas_System.factory_gasses
        percents = percents[new_idx[0]]
        percents = percents[0:4]  # TODO Handle if gas list short
        percents = percents.round(2)  # High precision breaks FlowController()
        percents[fill_gas] = 100 - percents.sum()
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True
        print(percents.to_dict())
        mfc.create_mix(mix_no=237, name='CalGas', gases=percents.to_dict())
        self.is_busy = False

    def test_pressure(self, savepath, flows, num_samples=5):
        """
        Ramp flow rate, measure pressure, plot results, save.

        Ramp flow rate from 5-50 sccm in steps of 5, measure pressure every
        minute for num_samples times. Waits 1 min before first collection.
        Plots results on yyplot w/ time on x-axis, and pressure and flow on y.

        Parameters
        ----------
        savepath : str
            Path to folder to save the results in.
        flows : list[int or float]
            Flow rate setpoints to sweep through when testing pressure build up
        num_samples : int, optional
            Number of samples to collect at each flow rate. Default is 5.
        """
        print('Testing Pressure Build-up...')
        output = pd.DataFrame(columns=['time', 'setpoint',
                                       'flow rate', 'pressure'])
        mfc_list = [self.mfc_A, self.mfc_B, self.mfc_C, self.mfc_D]
        sample_num = 0
        # Last MFC registered as inert gas gets used as tester.
        for mfc in mfc_list:
            if mfc.get()['gas'] in ['Ar', 'N2']:
                test_mfc = mfc
            else:
                mfc.set_flow_rate(0.0)

        self.mfc_E.set_gas(test_mfc.get()['gas'])
        print('Starting Conditions:')
        self.print_flows()
        start_time = time.time()
        # Loop through flow rate, record reading, save to output
        for setpoint in flows:
            test_mfc.set_flow_rate(setpoint)
            for sample in range(0, num_samples):
                time.sleep(60)
                pressure = test_mfc.get()['pressure']
                flow_rate = self.mfc_E.get()['mass_flow']
                reading = [(time.time() - start_time) / 60,
                           setpoint, flow_rate, pressure]
                print('time: %4.1f (min) setpoint: %4.2f (sccm) '
                      'flow rate: %4.2f (sccm) pressure: %4.2f (psia)'
                      % tuple(reading))
                output.loc[sample_num] = reading
                sample_num += 1
        # Plot Results
        ax1 = output.plot(x='time', y='pressure',
                          ylabel='Pressure (psia)', style='--ok')
        ax2 = ax1.twinx()
        ax2.spines['right'].set_position(('axes', 1.0))
        output.plot(ax=ax2, x='time',
                    y=['setpoint', 'flow rate'], ylabel='Flow Rate (sccm)')
        fig = ax1.get_figure()
        # Save Results
        fig.savefig(os.path.join(savepath, 'flow_test.svg'), format='svg')
        output.to_csv(os.path.join(savepath, 'flow_test.csv'))

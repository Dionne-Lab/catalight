"""
IR camera data and associated processing methods.

IRData compiles and acts on the data collected by a FLIR infrared camera. In
the current state, this class loads in a csv file of specific format
representing the mean/max temperature of an ROI representing the catalysts.
This is a developmental script and may change in future iterations of catalight
"""
import pandas as pd
import matplotlib.pyplot as plt


class IRData():
    """
    IR camera data and associated processing methods.

    IRData compiles and acts on the data collected by a FLIR infrared camera.
    In the current state, this class loads in a csv file of specific format
    representing the mean/max temperature of an ROI representing the catalysts.
    This is a developmental script and may change in future iterations of catalight
    """
    def __init__(self, IR_data_path):
        """Initiate IR camera data class using file location.

        On init, this calls :meth:`~IRData.import_data` and
        :meth:`~IRData.remove_dropped_frames`

        Parameters
        ----------
        IR_data_path : str
            full path string to filepath. Should be csv file.
        """

        self.raw_data = None
        """
        pandas.DataFrame: Uneditted data from csv imported with
        :meth:`~IRData.import_data()`
        """

        self.filtered_data = None
        """
        pandas.DataFrame: Filtered data after
        :meth:`~IRData.remove_dropped_frames()`
        """

        self.avg_surface_temps = None
        """
        pandas.DataFrame: Avg surface temperatures for each experiment step.

        Computed after running the :meth:`~IRData.compute_avg_surface_temps()`
        method.
        """

        self.date_format = '%Y-%m-%d %H:%M:%S.%f'
        """str: Date format used in the imported csv data."""

        self.import_data(IR_data_path)
        self.remove_dropped_frames(column_name='surface temperature - mean')

    def import_data(self, IR_data_path):
        """Import IR cam data as a csv using :func:`~pandas.read_csv`.

        data format should have ["abstime", "reltime", max temp, mean temp]
        The names of columns -1 and -2 are converted to
        'surface temperature - mean' and 'surface temperature - max',
        respectively

        Parameters
        ----------
        IR_data_path : str
            Full path to IR cam data as a csv file
        """
        df = pd.read_csv(IR_data_path, header=0)
        # Convert last column name to "surface temperature"
        df.columns.values[-1] = 'surface temperature - mean'
        df.columns.values[-2] = 'surface temperature - max'

        # Convert string to datetime object
        df['abstime'] = pd.to_datetime(df['abstime'],
                                       format=self.date_format)
        self.raw_data = df

    def remove_dropped_frames(self, column_name='surface temperature - mean',
                              window_size=50, threshold=10):
        """Attemps to remove odd frames that are sometimes captured.

        Drop frames that fall "threshold" away from the mean using rolling
        mean.

        Parameters
        ----------
        column_name : `str`, optional
            name of the column to use for computing the rolling mean and
            dropping frames, by default 'surface temperature - mean'
        window_size : `int`, optional
            number of datapoint to use when computing rolling mean,
            by default 50
        threshold : `int`, optional
            Degrees K to count as a normal deviation from the rolling mean.
            A variation larger than this is considered a "dropped" frame that
            was incorrectly measured by IR camera, by default 10
        """
        # Assuming df is your DataFrame with a column 'surface_temperature'
        df = self.raw_data
        # Calculate the rolling mean
        df['rolling_mean'] = df[column_name].rolling(window=window_size, center=True).mean()
        df['rolling_std'] = df[column_name].rolling(window=window_size, center=True).std()

        # Calculate the difference between the original data and the rolling mean
        df['diff'] = abs(df[column_name] - df['rolling_mean']) / df['rolling_mean'] * 100

        # Remove rows where the difference is above the threshold
        df_cleaned = df[df['diff'] <= threshold].copy()

        # Drop the auxiliary columns used for calculation
        df_cleaned = df_cleaned.drop(['rolling_mean', 'diff'], axis=1)

        # Display the cleaned DataFrame
        self.filtered_data = df_cleaned

    def compute_avg_surface_temps(self, expts, measurement_range=20):
        """Computes the average surface temperatures during experiments.

        Imports a list of catalight experiments. Uses the start time of the
        experiment and the abstime column of the imported IR camera data to
        determine the time averaged surface temperature of catalyst.

         All experiments will have a new attribute "surface_temps" added to
        it. "surface_temps is a python :class:`~dict` with keys "max" and
        "min" the value for each key is a list of time averaged
        temperatures for each step of the experiment.

        Parameters
        ----------
        expts : list[:class:`~catalight.equipment.experiment_control.Experiment`]
            List of catalight experiments to perform analysis on.

            All experiments will have a new attribute "surface_temps" added to
            it. "surface_temps is a python :class:`~dict` with keys "max" and
            "min" the value for each key is a list of time averaged
            temperatures for each step of the experiment.

        measurment_range : int or float
            [minutes] Length of time to average temp on each expt step.
        """

        surface_temps = []
        ramp_time = 0
        measurement_range = 60*measurement_range  # convert to seconds

        for expt in expts:
            if expt.expt_type == "stability_test":
                next  # skip stability test experiments

            T1 = 273  # Arbitrary start value

            # # These definitions should come from experiment in the future
            # # but the expt_log features need to be updated to save this data
            # expt.sample_rate = 30
            # expt.t_steady_state = 60
            # expt.t_buffer = 5
            # expt.sample_rate = 30  # Need to add to expt_log file
            # expt.t_steady_state = 30
            # expt.t_buffer = 5  # this shouldn't be right but seems like things are not going long enough


            # Create new empty attr
            expt.surface_temps = {'max': [], 'mean': []}

            step_length = (expt.t_steady_state
                            + expt.sample_rate*(expt.sample_set_size-1)
                            + expt.t_buffer)

            ramp_time = 0  # Reset value
            for plateau_ID, step_value in enumerate(getattr(expt, expt.ind_var)):
                # Determine the temperature setpoint to calculate ramp up time
                if expt.expt_type == "temp_sweep":
                    T2 = step_value
                else:
                    T2 = expt.temp[0]
                ramp_time += abs(T2-T1)/expt.heat_rate * 60
                T1 = T2  # Update for the next calculation

                # Calculate time range for averaging
                t1 = (expt.start_time + ramp_time
                      + 60*(expt.t_steady_state + plateau_ID*step_length))
                t2 = t1 + measurement_range
                # t2 = t1 + expt_length*60

                # Convert t1 and t2 to datetime objects
                t0_datetime = pd.to_datetime(expt.start_time, unit='s')
                t1_datetime = pd.to_datetime(t1, unit='s')
                t2_datetime = pd.to_datetime(t2, unit='s')

                # Filter rows between t1 and t2
                filtered_data = self.raw_data[
                    (self.raw_data['abstime'] >= t1_datetime)
                    & (self.raw_data['abstime'] <= t2_datetime)]

                # Compute time averaged surface temperature
                mean_temp = filtered_data['surface temperature - mean'].mean()+273
                max_temp = filtered_data['surface temperature - max'].mean()+273

                # Add avg surface temp to experiment object
                expt.surface_temps['mean'].append(mean_temp)
                expt.surface_temps['max'].append(max_temp)

                # Compile time averaged surface temps into a list
                surface_temps.extend([[t0_datetime,
                                       t1_datetime, t2_datetime,
                                       mean_temp, max_temp]])

            print('for experiment: ', expt.expt_name)
            print("Global Temperature = ", expt.temp)
            for key, value in expt.surface_temps.items():
                print(key, ':', value)
            print("Independent Variable = ", expt.ind_var)
        # save compiled time averaged surface temps as object attr
        self.avg_surface_temps = pd.DataFrame(surface_temps,
                                              columns=['t0', 't1', 't2',
                                                       'mean', 'max'])

    def rezero_time_axis(self, t0):
        """Adds new relative time to surface temp data sets starting a t0.

        Add the column "graph_time" to :attr:`~IRData.raw_data` and
        :attr:`~IRData.filtered_data` and adds ['t1 - rel'] and ['t2 - rel']
        columns to :attr:`~IRData.avg_surface_temps`. These new time values
        are relative times in which time zero starts at t0.

        This time rezeroing can be performed by calling
        :meth:`~IRData.plot_averaging`

        Parameters
        ----------
        t0 : pandas.Timestamp
            Pandas timestamp for the t0 value
        """

        self.raw_data['graph_time'] = (self.raw_data['abstime'] - t0) / pd.Timedelta(minutes=1)
        self.filtered_data['graph_time'] = (self.filtered_data['abstime'] - t0) / pd.Timedelta(minutes=1)
        avgs = self.avg_surface_temps
        avgs['t0 - rel'] = (avgs['t0'] - t0) / pd.Timedelta(minutes=1)
        avgs['t1 - rel'] = (avgs['t1'] - t0) / pd.Timedelta(minutes=1)
        avgs['t2 - rel'] = (avgs['t2'] - t0) / pd.Timedelta(minutes=1)

    def plot_averaging(self, rezero=True):
        """Plots results of temporal averaging of surface temp data.

        The point of this function is so that the user can verify whether the
        IR camera data is being temporally averaged in a satisfactory way.
        If called with rezero set to True, the user will be able to redefine
        the start point of the "experimental study" to not plot the full data
        collection range.

        Parameters
        ----------
        rezero : `bool`, optional
            If true, ask user to click new time = zero point, by default True
        """
        def set_t0(event):
            if event.dblclick:
                global t0
                t0 = event.xdata
                t0 = pd.to_datetime(t0, unit='D')
                ax.axvline(t0, color='black', linestyle='--')
                plt.draw()
                self.rezero_time_axis(t0)
                print('plot should rezero')

        # Set initial t0
        t0 = self.raw_data['abstime'].iloc[0]
        self.rezero_time_axis(t0)

        if rezero:
            # Plot the raw data, ask user to select new time = 0
            fig, ax = self.plot_raw_data()
            fig.suptitle("Double click on the time you'd like the plot to start at")
            ax.axvline(t0, color='black', linestyle='--')

            # Connect event handler
            cid = fig.canvas.mpl_connect('button_press_event', set_t0)

            plt.show(block=True)

        fig, ax = plt.subplots()
        self.filtered_data.plot(ax=ax, x='graph_time', y='surface temperature - mean', style='.b',
                            markersize=1, zorder=0, label='Mean Surface Temperature')
        self.filtered_data.plot(ax=ax, x='graph_time', y='surface temperature - max', style='.g',
                            markersize=1, zorder=0, label='Max Surface Temperature')
        for index, row in self.avg_surface_temps.iterrows():
            ax.hlines(xmin=row['t1 - rel'], xmax=row['t2 - rel'], y=row['mean']-273,
                      color='purple', linewidth=6, zorder=2)
            ax.hlines(xmin=row['t1 - rel'], xmax=row['t2 - rel'], y=row['max']-273,
                      color='magenta', linewidth=6, zorder=2)
            ax.axvline(x=row['t0 - rel'], color='r', linestyle='--', alpha=0.5)

        ax.set_xlim(left=0)
        ax.legend(markerscale=8, loc='upper left')
        ax.set_xlabel("Time [min]")
        ax.set_ylabel("Surface Temperature [°C]")
        return fig, ax

    def plot_raw_data(self):
        """Plots the raw and filtered data.

        Plot the raw and filtered data such that the user can verify if the
        filtering is satisfactory.

        Returns
        -------
        `~matplotlib.figure.Firgure`, `~matplotlib.axes.Axes`
            Figure and axes handles for graphic.
        """
        # Plot the raw data, ask user to select new time = 0
        fig, ax = plt.subplots()
        self.raw_data.plot(ax=ax, x='abstime', y='surface temperature - mean', style='.b',
                            markersize=1, zorder=0, label='Mean Surface Temperature (Raw)')
        self.raw_data.plot(ax=ax, x='abstime', y='surface temperature - max', style='.g',
                            markersize=1, zorder=0, label='Max Surface Temperature (Raw)')
        self.filtered_data.plot(ax=ax, x='abstime', y='surface temperature - mean', style='.r',
                            markersize=1, zorder=0, label='Mean Surface Temperature (Filtered)')
        self.filtered_data.plot(ax=ax, x='abstime', y='surface temperature - max', style='.r',
                            markersize=1, zorder=0, label='Max Surface Temperature (Filtered)')

        if self.avg_surface_temps is not None:
            for index, row in self.avg_surface_temps.iterrows():
                ax.hlines(xmin=row['t1'], xmax=row['t2'], y=row['mean']-273,
                        color='purple', linewidth=6, zorder=2)
                ax.hlines(xmin=row['t1'], xmax=row['t2'], y=row['max']-273,
                        color='magenta', linewidth=6, zorder=2)
        ax.legend(markerscale=8)
        ax.set_xlabel("Time [min]")
        ax.set_ylabel("Surface Temperature [°C]")
        return fig, ax

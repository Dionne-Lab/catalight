"""
Analysis portion of nkt calibration process.

The main function of this script will calculate the calibration fit parameters
based on the last run calibration experiment. Typically, this should be called
by the nkt_system's run_calibration() method.
"""
import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.optimize import curve_fit

from catalight.cl_tools import printProgressBar
from catalight.analysis.plotting import set_plot_style
from catalight.equipment.light_sources.nkt_helper_funcs import (predict_power,
                                                                determine_setpoint)


def correction_model(x, a):
    """Model used in regression between NKT prediction and measured spectra."""
    return a * x


def determine_correction_factor(calibration_measurement,
                                plot_results=False, savedata=False):
    """
    Perform regression between the predicted spectrum and measured spectrum.

    For each value in the wavelength vs avg. power (mW/nm) plot,
    perform a regression.

    Parameters
    ----------
    calibration_data : pandas.DataFrame
        Raw calibration data for NKT system.
        Index is wavelength and headers are NKT power setpoint in %.
    plot_results : `bool`, optional
        Indicate whether to plot results, by default False
    savedata : `bool`, optional
        Indicate whether to save results, by default False

    Returns
    -------
    pandas.DataFrame
        Correction values Index is wavelength.
        Columns are [fit params, relative error, covariance matrix]
    """
    print('Determining Correction Factors...')
    # Duplicate Calibration Axes to fill w/ data
    predicted_values = calibration_measurement * 0
    corrected_values = calibration_measurement * 0
    bandwidth = 10  # Bandwidth of calibration measurement
    # Retrieve the predicted Avg. Power for each wavelength
    for index, center in enumerate(predicted_values.index):
        index_neg = index - len(predicted_values)
        # For edge cases, fill by adding last data point
        if (index < 4):
            multiplier = (bandwidth/2 - index - 1)
            modifier = calibration_measurement.iloc[0, :] * multiplier
            print('for center = %i, multiplier = %i' % (center, multiplier))
        elif (index_neg >= -5):
            multiplier = (bandwidth/2 + index_neg + 1)
            modifier = calibration_measurement.iloc[-1, :] * multiplier
            print('for center = %i, multiplier = %i' % (center, multiplier))
        else:
            modifier = 0

        mask = ((predicted_values.index > center - bandwidth/2)
                & (predicted_values.index <= center + bandwidth/2))
        predicted_values.loc[center] = (calibration_measurement[mask].sum(axis=0)
                                        + modifier)
    # Convert from power to avg power
    predicted_values = predicted_values/10
    # Perform a regression for each column (power)
    fit_parameters = {}
    for column in predicted_values.columns:
        x_data = predicted_values[column]
        y_data = calibration_measurement[column]
        popt, _ = curve_fit(correction_model, x_data, y_data)
        fit_parameters[column] = popt
        corrected_values[column] = popt*predicted_values[column]
    if plot_results:
        plot_correction(calibration_measurement, predicted_values,
                        corrected_values, savedata=savedata)
    return corrected_values


def plot_correction(calibration_data, predicted_values,
                    corrected_values, savedata=False):
    """
    Plot the results of the determine_correction_factor() function.

    Parameters
    ----------
    calibration_data : pandas.DataFrame
        Raw calibration data for NKT system.
        Index is wavelength and headers are NKT power setpoint in %.
    predicted_values : pandas.DataFrame
        The predicted laser powers based on summing mW/nm values from cal data.
    corrected_values : pandas.DataFrame
        Calibration data adjusted to best match predicted values.
    savedata : `bool`, optional
        Whether or not to save correction plot, by default False
    """
    set_plot_style((9, 6.65))  # use catalight default plotting style
    fig, axes = plt.subplots(2, 2, sharex='col', sharey='row')
    fig.canvas.manager.set_window_title('Correction Factor Determination')
    # Plot Calibration data and initial predicted values
    # -------------------------------------------------------------------------
    axes[0, 0].plot(predicted_values, '.r')
    axes[0, 0].plot(calibration_data, '.k')
    # Create custom legend handles
    legend_handles = [Line2D([], [], linestyle='', marker='.',
                             color='r', label='Predicted'),
                      Line2D([], [], linestyle='', marker='.',
                             color='k', label='Measured')]
    # Add the legend using the custom handles
    axes[0, 0].legend(handles=legend_handles)

    # Plot percent difference between prediction and data
    # -------------------------------------------------------------------------
    error = abs(predicted_values-calibration_data)/calibration_data*100
    axes[1, 0].plot(error, '.r')

    # Plot calibration data and corrected values
    # -------------------------------------------------------------------------
    axes[0, 1].plot(corrected_values, '.r')
    axes[0, 1].plot(calibration_data, '.k')
    # Create custom legend handles
    legend_handles = [Line2D([], [], linestyle='', marker='.',
                             color='r', label='Predicted'),
                      Line2D([], [], linestyle='', marker='.',
                             color='k', label='Measured')]

    # Add the legend using the custom handles
    axes[0, 1].legend(handles=legend_handles)

    # Plot percent difference between correction and data
    # -------------------------------------------------------------------------
    error = abs(corrected_values-calibration_data)/calibration_data*100
    axes[1, 1].plot(error, '.r')

    # Add titles and labels to plots
    # -------------------------------------------------------------------------
    axes[0, 0].set_title('Raw')
    axes[0, 1].set_title('Corrected')
    axes[1, 0].set_xlabel('Wavelength [nm]')
    axes[1, 1].set_xlabel('Wavelength [nm]')
    axes[0, 0].set_ylabel('Avg. Power [mW/nm]')
    axes[1, 0].set_ylabel('Error [%]')
    axes[1, 0].set_ylim([0, 30])
    axes[1, 1].set_ylim([0, 30])
    fig.tight_layout()
    fig.subplots_adjust(hspace=0.1, wspace=0.05)
    if savedata:
        folder = os.path.dirname(os.path.abspath(__file__))
        savepath = os.path.join(folder, 'nkt_correction_factor')
        fig.savefig(savepath + '.svg')
        fig.savefig(savepath + '.png')
        pickle.dump(fig, open(savepath + '.pickle', 'wb'))


def determine_fits(corrected_data, deg=2):
    """
    Convert measured power values at different settings to fit values.

    Takes in measured power values (mW) as a function of power setpoint (%) and
    wavelength (nm) and performs polynomial fitting procedure for each
    wavelength. Returns the fit parameters at each wavelength to be used in
    power prediction.

    Parameters
    ----------
    corrected_data : pandas.DataFrame
        wavelength x power (%) dataframe of power measurements (mW).
    deg : `int`, optional
        Degree of polynomial to use for fit, by default 2

    Returns
    -------
    pandas.DataFrame
        Fit parameters for each wavelength.
        Index is wavelength.
        Columns are [fit params, relative error, covariance matrix]
        Each item within the DataFrame is a list itself.
    """
    print('Computing Calibration...')
    params_df = pd.DataFrame(columns=['fit params', 'relative error',
                                      'covariance matrix'],
                             index=corrected_data.index)
    for index, row in corrected_data.iterrows():
        y = row.values
        x = row.index.astype(float)
        p, V = np.polyfit(x, y, deg=deg, cov=True)
        std_dev = np.sqrt(V.diagonal())
        rel_error = std_dev/p
        params_df.loc[index] = [p, rel_error, V]
    return params_df


def plot_fits(calibration_data, calibration, savedata=False):
    """
    Create a multiplot figure with fits to calibration data.

    Parameters
    ----------
    calibration_data :  pandas.DataFrame
        Raw calibration data for NKT system.
        Index is wavelength and headers are NKT power setpoint in %.
    calibration : pandas.DataFrame
        Calibration fits for nkt_laser system.
        Fit parameters for each wavelength. Index is wavelength.
        Columns are [fit params, relative error, covariance matrix]
        Each item within the DataFrame is a list itself.
    savedata : `bool`, optional
        Indicate whether to save results, by default False
    """
    print('Plotting Linear Fits...')
    set_plot_style((9, 6.65))  # use catalight default plotting style
    fig, axes = plt.subplots(4, 4, sharex='col', sharey='row')
    fig.canvas.manager.set_window_title('Calibration Plots')
    main_ax = fig.add_subplot(111, frameon=False)
    # hide tick and tick label of the big axis
    main_ax.tick_params(labelcolor='none', which='both',
                        top=False, bottom=False, left=False, right=False)
    main_ax.set_xlabel('Power Setting [%]', fontsize=18)
    main_ax.set_ylabel('Power Reading [mW/nm]', fontsize=18)
    axes = axes.flatten()
    for center in calibration_data.index:
        if (center % 8) != 0:
            continue
        ax = axes[int((center-400)//25)]
        calibration_data.loc[center].plot(ax=ax, style='o')
        lines = ax.get_lines()
        last_line_color = lines[-1].get_color()
        x_fit = np.arange(0, 100, 1)
        y_fit = np.polyval(calibration['fit params'][center], x_fit)
        ax.plot(x_fit, y_fit, '--', color=last_line_color)
        ax.set_title(str(center), loc='left', y=1, x=0.05,
                     pad=-14, fontsize=12)
        printProgressBar(calibration_data.index.get_loc(center) + 1,
                         len(calibration_data.index))
    printProgressBar(1, 1)
    fig.tight_layout()

    if savedata:
        folder = os.path.dirname(os.path.abspath(__file__))
        savepath = os.path.join(folder, 'nkt_calibration_plots')
        fig.savefig(savepath + '.svg')
        fig.savefig(savepath + '.png')
        pickle.dump(fig, open(savepath + '.pickle', 'wb'))


def benchmark(calibration, savedata=False):
    """
    Compute and plot the results for the moving and growing window tests.

    Utilizes previously collected benchmarking tests results and plots the
    performance of the last run calibration.

    Parameters
    ----------
    calibration : pandas.DataFrame
        Calibration fits for nkt_laser system.
        Fit parameters for each wavelength. Index is wavelength.
        Columns are [fit params, relative error, covariance matrix]
        Each item within the DataFrame is a list itself.
    savedata : `bool`, optional
        Indicate whether to save results, by default False
    """
    set_plot_style((9, 6.65))  # use catalight default plotting style
    # Fixed Bandwidth Test
    # --------------------
    folder = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(folder, 'nkt_calibration_data.csv')
    data = pd.read_csv(data_path, index_col=0)
    # Convert column headers to float
    data.columns = data.columns.astype(float)

    fig, axes = plt.subplots(1, 2)
    fig.canvas.manager.set_window_title('Moving Window Benchmark')
    fig.set_size_inches(10, 5)
    error_ax = axes[0].twinx()

    predicted_values = pd.DataFrame(index=data.index, columns=data.columns)
    predicted_setpoints = predicted_values.copy()
    bandwidth = 10
    data = data*bandwidth  # convert data from avg power to power
    # this double for loop could probably be replaced with df.applymap()
    for power_setpoint in data.columns:
        for wavelength in data.index:
            measured_power = data[power_setpoint][wavelength]

            # Predict the power that should be supplied by given conditions
            predicted_power = predict_power(calibration, power_setpoint,
                                            wavelength, bandwidth)
            predicted_values[power_setpoint][wavelength] = predicted_power

            # Estimate setpoint need to reach recorded value
            predicted_setpoint = determine_setpoint(calibration, measured_power,
                                                    wavelength, bandwidth)
            predicted_setpoints[power_setpoint][wavelength] = predicted_setpoint

    data.plot(ax=axes[0], style='.r', legend=False)
    predicted_values.plot(ax=axes[0], style='.k', legend=False)
    error = 100*abs((data - predicted_values) / data)
    error = error.mean(axis=1)  # Show average error
    error.plot(ax=error_ax, style='.b', legend=False)
    axes[0].set_xlabel('Wavelength [nm]')
    axes[0].set_ylabel('Power [mW]')
    axes[0].set_title('Power Prediction')
    error_ax.set_ylabel('Error [%]', color='b')
    error_ax.set_ylim([0, 100])

    # Set the color of the right y-axis
    error_ax.spines['right'].set_color('b')
    # Set the color of the tick labels on the right y-axis
    error_ax.tick_params(axis='y', colors='b')

    # Create custom legend handles
    legend_handles = [Line2D([], [], linestyle='', marker='.',
                             color='k', label='Predicted'),
                      Line2D([], [], linestyle='', marker='.',
                             color='r', label='Measured'),
                      Line2D([], [], linestyle='', marker='.',
                             color='b', label='Average Error')]

    # Add the legend using the custom handles
    axes[0].legend(handles=legend_handles)

    # Inverse Test (What is power setpoint needed?)
    # ---------------------------------------------
    predicted_setpoints.plot(ax=axes[1], style='.', legend=False)
    for column in predicted_setpoints.columns:
        axes[1].axhline(y=column, color='r', linestyle='--')
    axes[1].set_ylim([0, 110])
    axes[1].set_xlabel('Wavelength [nm]')
    axes[1].set_ylabel('Power [%]')
    axes[1].set_title('Setpoint Prediction')
    # Create custom legend handles
    legend_handles = [Line2D([], [], linestyle='', marker='.',
                             color='k', label='Predicted'),
                      Line2D([], [], linestyle='--',
                             color='r', label='Actual Setpoint')]

    # Add the legend using the custom handles
    axes[1].legend(handles=legend_handles)

    fig.tight_layout()
    savepath = os.path.join(folder, 'nkt_moving_window_benchmark')
    if savedata:
        fig.savefig(savepath + '.svg')
        fig.savefig(savepath + '.png')
        pickle.dump(fig, open(savepath + '.pickle', 'wb'))

    # Growing Window Test
    # -------------------
    # Import window test data ['Cut-in', 'Cut-out', 'Meter Reading']
    window_test_path = os.path.join(folder, 'nkt_growing_window_test.csv')
    window_test = pd.read_csv(window_test_path, index_col=0)

    # Compute bandwidth and central values for each row of window test
    window_test['bandwidth'] = abs(window_test['Cut-in']
                                   - window_test['Cut-out'])
    window_test['center'] = abs(window_test['Cut-in']
                                + window_test['Cut-out']) / 2
    # Using those value, predict power output for each row using df.apply()
    window_test['prediction'] = window_test.apply(
        lambda row: predict_power(calibration, 50,
                                  row['center'], row['bandwidth']),
        axis=1)
    # Computer difference between prediction and measurement
    window_test['error'] = 100*(abs(window_test['prediction']
                                - window_test['Meter Reading'])
                                / window_test['Meter Reading'])

    fig, axes = plt.subplots(1, 2)
    fig.canvas.manager.set_window_title('Growing Window Benchmark')
    fig.set_size_inches(10, 5)
    error_ax = axes[0].twinx()
    axes[0].plot(window_test['bandwidth'], window_test['prediction'],
                 '.k', label='Prediction')
    axes[0].plot(window_test['bandwidth'], window_test['Meter Reading'],
                 '.r', label='Reading')
    error_ax.plot(window_test['bandwidth'], window_test['error'],
                  'ob', label='Error')
    axes[0].set_title('Power Prediction')
    axes[0].set_xlabel('Bandwidth [nm]')
    axes[0].set_ylabel('Power [mW]')
    error_ax.set_ylabel('Error [%]', color='b')
    error_ax.set_ylim([0, 100])
    # Set the color of the right y-axis
    error_ax.spines['right'].set_color('b')
    # Set the color of the tick labels on the right y-axis
    error_ax.tick_params(axis='y', colors='b')
    # Create custom legend handles
    legend_handles = [Line2D([], [], linestyle='', marker='.',
                             color='k', label='Predicted'),
                      Line2D([], [], linestyle='', marker='.',
                             color='r', label='Measured'),
                      Line2D([], [], linestyle='', marker='.',
                             color='b', label='Error')]
    # Add the legend using the custom handles
    axes[0].legend(handles=legend_handles)

    # Inverse Test (What is power setpoint needed?)
    # ---------------------------------------------
    # Use df.apply to determine setpoint to reach meter reading at each point
    window_test['setpoint'] = window_test.apply(
        lambda row: determine_setpoint(calibration, row['Meter Reading'],
                                       row['center'], row['bandwidth']),
        axis=1)

    axes[1].plot(window_test['bandwidth'], window_test['setpoint'],
                 '.k', label='Prediction')
    axes[1].plot(window_test['bandwidth'], 50*np.ones(len(window_test)),
                 '.r', label='Actual setpoint')
    axes[1].set_ylim([0, 100])
    axes[1].set_xlabel('Bandwidth [nm]')
    axes[1].set_ylabel('Power [%]')
    axes[1].set_title('Setpoint Prediction')
    axes[1].legend()
    fig.tight_layout()
    if savedata:
        savepath = os.path.join(folder, 'nkt_growing_window_benchmark')
        fig.savefig(savepath + '.svg')
        fig.savefig(savepath + '.png')
        pickle.dump(fig, open(savepath + '.pickle', 'wb'))


def main():
    """
    Determine correction factor, build calibration fits, run benchmarking.

    Loads last run nkt_calibration_data file. calls
    determine_correction_factor(), determine_fits(), plot_fits(), and
    benchmark() then saves data. This should typically be called by the
    nkt_system's run_calibration() method.
    """
    folder = os.path.dirname(os.path.abspath(__file__))
    cal_path = os.path.join(folder, 'nkt_calibration_data.csv')
    cal_data = pd.read_csv(cal_path, index_col=0)
    cal_data.columns = cal_data.columns.astype(float)
    corrected_data = determine_correction_factor(cal_data, plot_results=True,
                                                 savedata=True)
    calibration = determine_fits(corrected_data)
    plot_fits(cal_data, calibration, savedata=True)
    benchmark(calibration, savedata=True)
    calibration.to_pickle(os.path.join(folder, 'nkt_calibration.pkl'))


if __name__ == '__main__':
    plt.close('all')
    cal_path = (r"G:\Shared drives\Ensemble Photoreactor"
                r"\Reactor Baseline Experiments\nkt_calibration"
                r"\20230510_calibration.csv")
    cal_data = pd.read_csv(cal_path, index_col=0)
    cal_data.columns = cal_data.columns.astype(float)
    corrected_data = determine_correction_factor(cal_data, plot_results=True,
                                                 savedata=True)
    calibration = determine_fits(corrected_data)
    plot_fits(cal_data, calibration, savedata=True)
    benchmark(calibration, savedata=True)
    folder = os.path.dirname(cal_path)
    calibration.to_pickle(os.path.join(folder, 'nkt_calibration.pkl'))
    plt.show()

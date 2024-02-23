import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import catalight.analysis.tools as analysis_tools

plt.rcParams['svg.fonttype'] = 'none'


def remove_dropped_frames(df, window_size=50, threshold=10):
    # Assuming df is your DataFrame with a column 'surface_temperature'

    # Calculate the rolling mean
    df['rolling_mean'] = df['surface temperature'].rolling(window=window_size, center=True).mean()
    df['rolling_std'] = df['surface temperature'].rolling(window=window_size, center=True).std()

    # Calculate the difference between the original data and the rolling mean
    df['diff'] = abs(df['surface temperature'] - df['rolling_mean']) / df['rolling_mean'] * 100

    # Remove rows where the difference is above the threshold
    df_cleaned = df[df['diff'] <= threshold].copy()

    # Drop the auxiliary columns used for calculation
    df_cleaned = df_cleaned.drop(['rolling_mean', 'diff'], axis=1)

    # Display the cleaned DataFrame
    return df_cleaned


def add_surface_temps(expts, IR_data):
    measurements = []
    expt_start_times = []
    surface_temps = []
    for expt in expts:
        T1 = 300
        if expt.expt_type != "stability_test":
            expt.sample_rate = 30  # Need to add to expt_log file
            expt.t_steady_state = 30
            expt.t_buffer = 5  # this shouldn't be right but seems like things are not going long enough
            expt.surface_temp = []  # Create new empty attr
            measurements.append(expt)
            expt_start_times.append(expt.start_time)
            measurement_range = 20*60
            expt_length = (expt.t_steady_state
                           + expt.sample_rate*(expt.sample_set_size-1)
                           + expt.t_buffer)
            ramp_time = 0
            for plateau_ID, temp in enumerate(expt.temp):
                T2 = temp
                ramp_time += abs(T2-T1)/expt.heat_rate * 60
                T1 = T2
                t1 = (expt.start_time + ramp_time
                    + 60*(expt.t_steady_state + plateau_ID*expt_length))
                t2 = t1 + measurement_range
                # t2 = t1 + expt_length*60
                # Convert t1 and t2 to datetime objects
                t1_datetime = pd.to_datetime(t1, unit='s')
                t2_datetime = pd.to_datetime(t2, unit='s')

                # Filter rows between t1 and t2
                filtered_data = IR_data[
                    (IR_data['abstime'] >= t1_datetime)
                    & (IR_data['abstime'] <= t2_datetime)]
                expt.surface_temp.append(filtered_data['surface temperature'].mean()+273)
                surface_temps.extend([[t1_datetime, expt.surface_temp[-1]-273],
                                    [t2_datetime, expt.surface_temp[-1]-273]])

            print('for experiment: ', expt.expt_name)
            print(expt.temp)
            print(expt.surface_temp)


def calc_rate(expt):
    results = analysis_tools.calculate_X_and_S(expt, reactant='C2H2',
                                               target_molecule='C2H4')

    Yield = results['Conversion'] * results['Selectivity']
    mole_density = 1/22814  # mole/mL ethylene
    flow = expt.tot_flow[0] / 60  # flow in standard mL / sec
    rate_abs = Yield * flow * mole_density  # mole c2h4 / sec
    mass = 4  # mg
    wt_per = 0.04  # percent
    rate = rate_abs/(mass * wt_per)
    return rate



main_dir = (r"G:\Shared drives\Photocatalysis Projects\AgPd Polyhedra"
            r"\Ensemble Reactor\20230504_Au95Pd5_4wt")
main_dir = (r"G:\Shared drives\Photocatalysis Projects\catalight_experiments"
            r"\20231225\20230504_Au95Pd5_4wt_4mg")
filepaths = analysis_tools.list_matching_files(main_dir,
                                               'expt_log', '.txt')
expts = analysis_tools.list_expt_obj(filepaths)
IR_data_path = r"G:\Shared drives\Photocatalysis Projects\catalight_experiments\20231225\IR_cam\IR_data_raw_export.csv"
IR_data = pd.read_csv(IR_data_path, header=0)

# Convert last column name to "surface temperature"
IR_data.columns.values[-1] = 'surface temperature'
#data = data[data['reltime'] <1e5] # work with subset for speed of demo
# Convert string to datetime object
date_format = '%Y-%m-%d %H:%M:%S.%f'
IR_data['abstime'] = pd.to_datetime(IR_data['abstime'], format=date_format)
IR_data = remove_dropped_frames(IR_data)

add_surface_temps(expts, IR_data)

data_list = []
fig, axes = plt.subplots(2, 2, figsize=(9, 6.65))
main_ax = fig.add_subplot(111, frameon=False)
# hide tick and tick label of the big axis
main_ax.tick_params(labelcolor='none', which='both',
                    top=False, bottom=False, left=False, right=False)
main_ax.set_xlabel('1000/T [1/K]', fontsize=18)
main_ax.set_ylabel('Rate [mmol/mg/s]', fontsize=18)
axes = axes.flatten()
powers = [0, 20, 40, 60]

fig_WL, axes_WL = plt.subplots(2, 3, figsize=(12, 6.65))
main_ax_WL = fig_WL.add_subplot(111, frameon=False)
# hide tick and tick label of the big axis
main_ax_WL.tick_params(labelcolor='none', which='both',
                    top=False, bottom=False, left=False, right=False)
main_ax_WL.set_xlabel('1000/T [1/K]', fontsize=18)
main_ax_WL.set_ylabel('Rate [mmol/mg/s]', fontsize=18)
axes_WL = axes_WL.flatten()
wavelengths = [480, 530, 580, 630, 680]

Tfig, Taxes = plt.subplots(2, 2, figsize=(9, 6.65))
main_Tax = Tfig.add_subplot(111, frameon=False)
main_Tax.tick_params(labelcolor='none', which='both',
                     top=False, bottom=False, left=False, right=False)
Taxes = Taxes.flatten()
main_Tax.set_xlabel('Global Temperature [K]', fontsize=18)
main_Tax.set_ylabel('Surface Temperature [K]', fontsize=18)

for expt in expts:
    if expt.expt_type == "stability_test":
        continue

    rate = calc_rate(expt)
    T = np.array(expt.temp)+273
    Ts = np.array(expt.surface_temp)+273

    p, V = np.polyfit(1/Ts, np.log(rate), deg=1, cov=True)
    std_dev = np.sqrt(V.diagonal())
    rel_error = std_dev/p
    R = 8.314 / 96400
    E = -p[0] * R
    A = np.exp(p[1])

    # Calculate predicted values
    predicted_ln_rate = np.polyval(p, 1/T)

    # Calculate R-squared value
    mean_y = np.mean(np.log(rate))
    numerator = np.sum((np.log(rate) - predicted_ln_rate) ** 2)
    denominator = np.sum((np.log(rate) - mean_y) ** 2)
    r_squared = 1 - (numerator / denominator)

    ax_ID = powers.index(expt.power[0])
    data_line, = axes[ax_ID].plot(1000/Ts, rate*1000, 'o', label=str(expt.wavelength[0])+' nm')
    color = data_line.get_color()
    fit_line, = axes[ax_ID].plot(1000/Ts, np.exp(-E/R/Ts)*A*1000, '--', color=color)
    axes[ax_ID].set_title(str(expt.power[0]) + ' mW')
    axes[ax_ID].legend()
    axes[ax_ID].set_yscale('log')
    data_list.append([expt.power[0], expt.wavelength[0], E])

    Taxes[ax_ID].plot(T, Ts, '.', label=str(expt.wavelength[0])+' nm')
    Taxes[ax_ID].set_title(str(expt.power[0]) + ' mW')

    ax_ID = wavelengths.index(expt.wavelength[0])
    data_line, = axes_WL[ax_ID].plot(1000/Ts, rate*1000, 'o', label=str(expt.power[0])+' mW')
    color = data_line.get_color()
    fit_line, = axes_WL[ax_ID].plot(1000/Ts, np.exp(-E/R/Ts)*A*1000, '--', color=color)
    axes_WL[ax_ID].set_title(str(expt.wavelength[0]) + ' mW')
    axes_WL[ax_ID].legend()
    axes_WL[ax_ID].set_yscale('log')
    data_list.append([expt.power[0], expt.wavelength[0], E])

for ax in Taxes:
    ax.plot([600, 660], [600, 660], '--k', linewidth=2)
    ax.set_ylim([610, 680])
    ax.set_xlim([610, 655])
    ax.legend()

plt.tight_layout()
fig.tight_layout()
Tfig.tight_layout()
fig_WL.tight_layout()

# Make 3D plot
data = pd.DataFrame(data_list, columns=['Power', 'Wavelength', 'Barrier'])
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_trisurf(data['Power'], data['Wavelength'], data['Barrier'],
                       cmap='viridis', edgecolor='k', facecolors=plt.cm.viridis(data['Barrier']))
# Set labels
ax.set_xlabel('Power [mW]')
ax.set_ylabel('Wavelength [nm]')
ax.set_zlabel('Activation Barrier [eV]')
plt.show()

import os
import colorsys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import catalight.analysis.tools as analysis_tools
from matplotlib.ticker import ScalarFormatter, AutoLocator

from catalight.analysis.irdata import IRData

plt.rcParams['svg.fonttype'] = 'none'
plt.rcParams['font.size'] = 8
plt.rcParams['lines.markersize'] = 4


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


def change_lightness(power, color_dict):
    L_range = [85/255, 190/255]  # Lightness values to span
    P_range = [0, 60]  # Power value range to span
    # Mapping between L range and P range
    L = lambda power: (L_range[0]-L_range[1])/(P_range[1]-P_range[0])*power+L_range[1]
    h = color_dict["hls"][0]
    l = L(power)
    s = color_dict["hls"][2]
    new_color = color_dict.copy()
    new_color["hls"] = (h, l, s)
    new_color["rgb"] = colorsys.hls_to_rgb(*new_color["hls"])
    new_color['hex'] = rgb_to_hex(*new_color["rgb"])
    return(new_color)


def rgb_to_hex(r, g, b):
    """Convert RGB tuple to hexadecimal color representation."""
    # Convert each RGB value to the 0-255 range and then to hexadecimal
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    # Format the RGB values as hexadecimal and concatenate them
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def reorder_legend(ax):
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return
    # reorder the legend using sorted
    reordered_legend = sorted(zip(labels, handles))
    # Unpack the sorted tuples back into separate lists
    labels, handles = zip(*reordered_legend)
    ax.legend(handles, labels, frameon=False, labelspacing=0.1, handletextpad=0.3, borderaxespad=0)


main_dir = (r"G:\Shared drives\Photocatalysis Projects\AgPd Polyhedra"
            r"\Ensemble Reactor\20230504_Au95Pd5_4wt")
main_dir = (r"G:\Shared drives\Photocatalysis Projects\catalight_experiments"
            r"\20231225\20230504_Au95Pd5_4wt_4mg")

colors = [{"nominal": "480 nm", "rgb": (63/255, 147/255, 242/255)},
          {"nominal": "530 nm", "rgb":  (67/255, 144/255, 75/255)},
          {"nominal": "580 nm", "rgb": (246/255, 237/255, 64/255)},
          {"nominal": "630 nm", "rgb": (254/255, 164/255, 56/255)},
          {"nominal": "680 nm", "rgb":  (255/255, 54/255, 34/255)}]
for color in colors:
    color["hls"] = colorsys.rgb_to_hls(*color["rgb"])
    color['hex'] = rgb_to_hex(*color["rgb"])

filepaths = analysis_tools.list_matching_files(main_dir,
                                               'expt_log', '.txt')
expts = analysis_tools.list_expt_obj(filepaths)
IR_data_path = r"G:\Shared drives\Photocatalysis Projects\catalight_experiments\20231225\IR_cam\IR_data_raw_export.csv"
surface_temps =  IRData(IR_data_path)  # cleans data on init
surface_temps.compute_avg_surface_temps(expts)  # adds avg temp to expt
surface_temps.plot_averaging(rezero=False)

data_list = []
full_width = 17.4/2.54
half_width = 8.6/2.54
label_size=10
fig, axes = plt.subplots(2, 2, figsize=(full_width, 0.55*full_width))
main_ax = fig.add_subplot(111, frameon=False)
# hide tick and tick label of the big axis
main_ax.tick_params(labelcolor='none', which='both',
                    top=False, bottom=False, left=False, right=False)
main_ax.set_xlabel('1000/T [1/K]', fontsize=label_size)
main_ax.set_ylabel('Rate [mmol/mg/s]', fontsize=label_size)
axes = axes.flatten()
powers = [0, 20, 40, 60]

fig_WL, axes_WL = plt.subplots(2, 3, figsize=(full_width, 0.55*full_width))
main_ax_WL = fig_WL.add_subplot(111, frameon=False)
# hide tick and tick label of the big axis
main_ax_WL.tick_params(labelcolor='none', which='both',
                    top=False, bottom=False, left=False, right=False)
main_ax_WL.set_xlabel('1000/T [1/K]', fontsize=label_size)
main_ax_WL.set_ylabel('Rate [mmol/mg/s]', fontsize=label_size)
axes_WL = axes_WL.flatten()
wavelengths = [480, 530, 580, 630, 680]

Tfig, Taxes = plt.subplots(2, 2, figsize=(full_width, 0.55*full_width))
main_Tax = Tfig.add_subplot(111, frameon=False)
main_Tax.tick_params(labelcolor='none', which='both',
                     top=False, bottom=False, left=False, right=False)
Taxes = Taxes.flatten()
main_Tax.set_xlabel('Global Temperature [K]', fontsize=label_size)
main_Tax.set_ylabel('Surface Temperature [K]', fontsize=label_size)

fig_single, axes_single = plt.subplots(2, 1, sharex=True, figsize=(full_width/2, full_width))
# Remove vertical space between axes
fig_single.subplots_adjust(hspace=0)
axes_single[1].set_xlabel('1000/T [1/K]', fontsize=label_size)
axes_single[0].set_ylabel('Rate [mmol/mg/s]', fontsize=label_size)
axes_single[1].set_ylabel('Rate [mmol/mg/s]', fontsize=label_size)

title_offset = 0.8

for expt in expts:
    if expt.expt_type == "stability_test":
        continue

    rate = calc_rate(expt)
    T = np.array(expt.temp)
    Ts = np.array(expt.surface_temps['max'])

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

    color_dict = [x for x in colors if x.get("nominal") == str(expt.wavelength[0])+' nm'][0]
    color = color_dict['hex']

    # Plot this experiment on power figure
    ax_ID = powers.index(expt.power[0])
    data_line, = axes[ax_ID].plot(1000/Ts, rate*1000, 'o', label=str(expt.wavelength[0])+' nm', color=color)
    fit_line, = axes[ax_ID].plot(1000/Ts, np.exp(-E/R/Ts)*A*1000, '--', color=color)
    axes[ax_ID].set_title(str(expt.power[0]) + ' mW', y=title_offset)

    if expt.power[0] == 60:
        data_line, = axes_single[0].plot(1000/Ts, rate*1000, 'o', label=str(expt.wavelength[0])+' nm', color=color)
        fit_line, = axes_single[0].plot(1000/Ts, np.exp(-E/R/Ts)*A*1000, '--', color=color)

    # Plot this experiment on temperature figure
    Taxes[ax_ID].plot(T, Ts, 'o', label=str(expt.wavelength[0])+' nm', color=color)
    Taxes[ax_ID].set_title(str(expt.power[0]) + ' mW', y=title_offset)

    color_dict = change_lightness(expt.power[0], color_dict)
    color = color_dict['hex']
    # Plot this experiment on wavelength figure
    ax_ID = wavelengths.index(expt.wavelength[0])
    data_line, = axes_WL[ax_ID].plot(1000/Ts, rate*1000, 'o', label=str(expt.power[0])+' mW', color=color)
    fit_line, = axes_WL[ax_ID].plot(1000/Ts, np.exp(-E/R/Ts)*A*1000, '--', color=color)
    axes_WL[ax_ID].set_title(str(expt.wavelength[0]) + ' mW', y=title_offset)

    if expt.wavelength[0] == 530:
        data_line, = axes_single[1].plot(1000/Ts, rate*1000, 'o', label=str(expt.power[0])+' mW', color=color)
        fit_line, = axes_single[1].plot(1000/Ts, np.exp(-E/R/Ts)*A*1000, '--', color=color)

    data_list.append([expt.power[0], expt.wavelength[0], E])

for ax in Taxes:
    ax.plot([330, 400], [330, 400], '--k')
    ax.set_ylim([335, 415])
    ax.set_xlim([335, 385])
    ax.legend(frameon=False)
    reorder_legend(ax)

for ax in axes_WL.tolist() + axes.tolist() + axes_single.tolist():
    if ax.lines:
        ax.set_yscale('log')
        ax.legend(frameon=False)
        reorder_legend(ax)
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.yaxis.set_minor_formatter(ScalarFormatter())
    ax.yaxis.set_major_locator(AutoLocator())
    ax.yaxis.set_minor_locator(AutoLocator())
    ax.set_ylim([18, 95])
    ax.set_xlim([2.45, 2.95])

plt.tight_layout()
fig.tight_layout()
Tfig.tight_layout()
fig_WL.tight_layout()
fig_single.tight_layout()

# Make 3D plot
data = pd.DataFrame(data_list, columns=['Power', 'Wavelength', 'Barrier'])
fig_3d = plt.figure(figsize=(full_width/2, full_width/2))
ax_3d = fig_3d.add_subplot(111, projection='3d')

data_list = np.array(data_list)
# Sort the array by the second column
sorted_indices = np.lexsort((data_list[:, 0], data_list[:, 1]))  # Get indices that would sort the array by the second column
data_list = data_list[sorted_indices]      # Reorder the array using the sorted indices

print(data_list)
X = data_list[:, 0].reshape(len(wavelengths), len(powers))
Y = data_list[:, 1].reshape(len(wavelengths), len(powers))
Z = data_list[:, 2].reshape(len(wavelengths), len(powers))
print(X)
print(Y)
surf = ax_3d.plot_surface(X, Y, Z, cmap='viridis', edgecolor='k')


# Set labels
ax_3d.set_xlabel('Power [mW]')
ax_3d.set_ylabel('Wavelength [nm]')
ax_3d.set_zlabel('Activation Barrier [eV]')
ax_3d.invert_yaxis()
ax_3d.view_init(elev=21, azim=148)
ax_3d.set_box_aspect(aspect=[1, 1, 1], zoom=0.8)
ax_3d.set_xticks(powers)
ax_3d.set_yticks(wavelengths)
ax_3d.set_proj_type('ortho')
fig_3d.tight_layout()
plt.show(block=False)

save_fol = r"G:\Shared drives\Photocatalysis Projects\catalight_experiments\figures\20240425_barrier_expt_plots"
fig_list = [fig, Tfig, fig_WL, fig_single, fig_3d]
fig_names = ["power_dependence",
             "temp_differences",
             "wavelength_dependence",
             "arrenhius_fits",
             "arrenhius_surface"]
for f, name in zip(fig_list, fig_names):
    f.savefig(os.path.join(save_fol, name+'.svg'))
    f.savefig(os.path.join(save_fol, name+'.png'))

# Wait for the space bar to be pressed
print("Press the space bar to continue...")
while True:
    user_input = input()
    if user_input == " ":
        break

# Run your command after the space bar is pressed
print("Space bar pressed! Continuing with the command...")
print(ax_3d.elev)
print(ax_3d.azim)
plt.close('all')

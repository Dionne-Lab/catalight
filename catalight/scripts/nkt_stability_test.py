import time
import pickle
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt

from catalight.equipment.power_meter import newport
from nkt_tools import (extreme, varia)

date = dt.date.today().strftime('%Y%m%d')
print('Starting Experiment on ', date)
print('Initializing Equipment...')

meter = newport.NewportMeter()
laser = extreme.Extreme()
varia = varia.Varia()

laser.set_watchdog_interval(0)
laser.test_read_funcs()

varia.long_setpoint = 625
varia.short_setpoint = 575
laser.set_emission(False)
laser.set_power(50)
meter.change_wavelength(500)

expt_len = 20 * 60  # Experiment time in seconds
sample_period = 10  # Time between samples
num_samples = int(expt_len/sample_period)

laser.set_emission(True)
laser.test_read_funcs()

data = []

print('Beginning constant current test')
laser.set_mode(0)  # Constant Current Mode
time.sleep(60)
for n in range(num_samples):
    data.append(meter.read())
    time.sleep(sample_period)
    print('Current Readout = %.2f mW' % data[-1][1], end='\r')

current_result = pd.DataFrame(data, columns=['timestamp', 'power'])
data = []

print('Beginning constant power test')
laser.set_mode(1)  # Constant Power Mode
time.sleep(60)
for n in range(num_samples):
    data.append(meter.read())
    time.sleep(sample_period)
    print('Current Readout = %.2f mW' % data[-1][1], end='\r')

power_result = pd.DataFrame(data, columns=['timestamp', 'power'])

laser.set_emission(False)

fig, ax = plt.subplots()
ax.plot(power_result['timestamp']-power_result['timestamp'][0],
        power_result['power'], '.k', label='Constant Power Mode')
ax.plot(current_result['timestamp']-current_result['timestamp'][0],
        current_result['power'], '.r', label='Constant Current Mode')
ax.set_ylabel('Power [mW]', fontsize=18)
ax.set_xlabel('Time passed [s]', fontsize=18)
ax.legend()
savepath = date + '_stability_test'
power_result.to_csv(savepath + '_power.csv')
current_result.to_csv(savepath + '_current.csv')
fig.savefig(savepath + '.svg')
fig.savefig(savepath + '.png')
pickle.dump(fig, open(savepath + '.pickle', 'wb'))
plt.show()

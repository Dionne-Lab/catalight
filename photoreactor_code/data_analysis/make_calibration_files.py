import sys
sys.path.append("..")
import experiment_control
import numpy as np

main_fol = "/Users/ccarlin/Documents/calibration"

expt = experiment_control.Experiment()
expt.expt_type = 'calibration'
expt.gas_type = ['CalGas', 'Ar', 'H2']
expt.temp = [273]
P_CalGas = np.array([100, 50, 10])/100  # pretend one 1000ppm gas
P_H2 = P_CalGas*0
P_Ar = 1-P_CalGas-P_H2
expt.gas_comp = np.stack([P_CalGas, P_Ar, P_H2], axis=1).tolist()
expt.tot_flow = [50]
expt.sample_name = '20220418_caltest'
expt.plot_sweep()
expt.create_dirs(main_fol)
print('finished expt5')

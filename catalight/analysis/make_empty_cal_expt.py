'''
Create empty calibration experiment data structure.

This script was initially used to generate a "dummy" calibration experiment
using data collected before calibration experiments were automated. Use this
script if you have calibration data that is not organized in the appropriate
data structure. This will create expt log file and data layout. then copy paste
calibration data into appropriate folders.
'''
import numpy as np
from catalight.equipment.experiment_control import Experiment


def main(main_fol, filename, dilution, tot_flow=1):
    """
    Build an empty set of folders to put calibration data into.

    The main point of this module is to replicate a composition sweep
    experiment for users that will be performing a calibration using multiple
    sets of calibration gasses. This package generally assumes that calibration
    is performed using one calibration gas tank diluted with MFCs. If this is
    not your situation, this module may be useful.

    Parameters
    ----------
    main_fol : str
        Directory to save folders in.
    filename : str
        Folder name you'd like to use when saving 'calibration expt'
    dilution : list of float or int
        Percent amount you diluted the original calibration gas
        For example, you have 1000 ppm, 500 ppm, and 100 ppm calibration gasses
        This would mimic diluting a 1000 ppm gas by 100%, 50%, 10%
        So the list you provide would be [100, 50, 10]
    tot_flow : `float` or `int`, optional
        Enter if you'd like to specify/record flow rate used. The default is 1.

    Returns
    -------
    None

    """

    expt = Experiment()
    expt.expt_type = 'calibration'
    expt.gas_type = ['CalGas', 'Ar', 'Ar', 'Ar']
    P_CalGas = np.array(dilution) / 100   # pretend one 1000ppm gas
    P_Ar = P_CalGas * 0
    expt.gas_comp = np.stack([P_CalGas, P_Ar, P_Ar], axis=1).tolist()
    expt.tot_flow = tot_flow
    expt.sample_name = filename
    expt.create_dirs(main_fol)


if __name__ == "__main__":
    # Example usage:
    main_fol = "/Users/ccarlin/Documents/calibration"
    tot_flow = 50
    filename = '20200202_calibration'
    # Percent amount you diluted the original calibration gas
    # For example, you have 1000 ppm, 500 ppm, and 100 ppm calibration gasses
    # This would mimic diluting a 1000 ppm gas by 100%, 50%, 10%
    dilution = [100, 50, 10]
    main(main_fol, filename, dilution, tot_flow)

"""
Module is used to test the response time of the gas chromatograph.

The GC and gas system are used to check the response time of the system.
The user must make edits to this module in the current iteration. Update the
delay times, flow rates, and gas details to test for. The system will flow gas,
then wait the input delay time until starting the GC. This allows the user to
check how long the it takes for the gas supply to reach steady state to the GC.
For data analysis, see the "run_plot_chromatograms_stacked.py" module.

Created on Tue Dec 13 14:32:19 2022

@author: Briley Bourgeois
"""
import os
import time
from datetime import date

from catalight.equipment.alicat_MFC.gas_control import Gas_System
from catalight.equipment.sri_gc.gc_control import GC_Connector


def main(main_dir, delay_times, flows,
         gas_list, comp_list_on, comp_list_off):
    """
    Test the response time of the GC by collecting samples in controlled way.

    Loops through flows entered to test the GC response delay time after. The
    composition determined by comp_list_on is sent from the MFCs at the
    supplied flow rate. GC collection is started delay_times after in a loop.
    Data gets saved as in folder based on the flow rate and as files named with
    the delay time.

    Parameters
    ----------
    main_dir : str
        Directory in which experiment directories will be created/saved
    delay_times : list of float or int
        Time between setting comp_list_on and starting GC collection
    flows : list of float or int
        Total gas flow rate in sccm.
    gas_list : list of str
        Input gasses into MFC.
        Example: ['C2H4', 'C2H2', 'H2', 'Ar']
    comp_list_on : list of float or int
        Composition list for test mix.
        Example: [0, 0.1, 0, 0.9] sends 10% Gas B diluted by Gas D
    comp_list_off : list of float or int
        Composition list for flush mix.
        Example: [0, 0, 0, 1] sends 100 gas D, which should be inert gas

    Returns
    -------
    None.

    """
    expt_dir = os.path.join(main_dir,
                            (date.today().strftime('%Y%m%d') + '_gc_delay_test'))
    os.makedirs(expt_dir, exist_ok=True)

    gc = GC_Connector()
    gc.sample_set_size = 1  # Subsequent runs will be wrong delay!!
    gas_control = Gas_System()
    gas_control.set_gasses(gas_list)

    for tot_flow in flows:
        flow_dir = os.path.join(expt_dir, (str(tot_flow) + '_sccm'))
        for delay in delay_times:
            filename = (str(delay) + '_min_delay')
            filepath = os.path.join(flow_dir, filename)
            os.makedirs(filepath, exist_ok=True)
            gc.update_ctrl_file(filepath)  # Changes save path
            gas_control.set_flows(comp_list_on, tot_flow)  # Flow Target Gas

            for second in range(int(delay * 60)):
                time.sleep(1)  # 1 second at a time so script can be stopped

            # Turn on gc and pause a minute to be safe
            gc.peaksimple.SetRunning(1, True)
            time.sleep(60)

            gas_control.set_flows(comp_list_off, 50)  # Clear out line

            # Wait until gc collection is done
            for second in range(int((gc.sample_rate - 1) * 60)):
                time.sleep(1)  # 1 second at a time so script can be stopped
    gas_control.disconnect()


if __name__ == "__main__":
    # Example usage:
    # User Inputs:
    # ------------
    main_dir = r'C:\Peak489Win10\GCDATA'  # Save location
    delay_times = [5, 15, 25, 35, 45, 55]  # In minutes
    flows = [5, 25, 50]  # Total gas flow rate in sccm
    gas_list = ['C2H4', 'C2H2', 'H2', 'Ar']  # Input Gasses
    comp_list_on = ([0, 1, 0, 0])  # Composition to use for testing
    comp_list_off = ([0, 0, 0, 1])  # Composition to flush system
    # Function call
    main(main_dir, delay_times, flows,
         gas_list, comp_list_on, comp_list_off)
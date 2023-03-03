Calibration File Details
========================
Here we will provide extra details about the calibration file, what components are required, and at which stages of analysis you need to have different parts of the file completed.

Important Requirements:

* **The Chem ID column must contain strings which match the alicat gas library** if the user wishes to perform calibration with the catalight GUI. If this isn't possible, the user can perform a composition sweep using the fill gas of the mixture, but this will reduce the precision of the MFC control.
* **The elution times for each peak must be determined by the user** and entered into the calibration file. One way to do this is to look at the peaks inside peaksimple and mark the locations using the peaksimple component system. Opening the component file will then show the start and end times for each peak, which can be copied into a calibration file for use with catalight.
* **The GC control file must be tweaked by the user to achieve optimal results.** The catalight package does not attempt to alter the GC settings, though automated condition screening could programmed using the :class:`~catalight.equipment.sri_gc.gc_control.GC_Connector` class and editing the different system files used by the GC (i.e. the .tem and .evt files).


When first running the calibration experiment, the role of the calibration file is to build a custom CalGas mixture to be used by the MFC for accurate gas control. As such, the only important entries are the Chem ID column (must match gas library on MFC) and the expected concentrations (ppm column).

.. note::
    The data in the calibration file is accessed by the column name. The locations can technically vary, but the names of the columns must remain exact.

.. figure:: _static/images/calgas_precalibration.svg
    :width: 800

    In this file, all components of the calibration gas are listed with their concentration in ppm provided. The elution times are also included for illustration, but these columns do not need to be filled prior to running a calibration experiment.

For some gas mixtures and hardware configurations, total peak separation isn't possible. This can be handled by combining the peaks into one name and treating the resulting measured concentration as a sum of the components.

.. figure:: _static/images/calibration_peaksimple.png
    :width: 800

    A screenshot of the same gas analyzed in peaksimple. Note that the C\ :sub:`3`\ H\ :sub:`6`/C\ :sub:`3`\ H\ :sub:`8` peak here is completely overlapped and the C\ :sub:`4`\ H\ :sub:`10`/C\ :sub:`4`\ H\ :sub:`8` peaks are heavily convuluted.

When proceeding to the analysis portion of running a calibration, make sure that peak elution times do not overlap and that only numbers are entered into these cells. Notice that H\ :sub:`2` was removed from the calibration file since it is not picked up by the FID detector used here. It is also important that 1 and 0 be entered into the slope and intercept spaces respecitively. This makes the ppm conversion produce raw counts when integrating peaks.

.. figure:: _static/images/calgas_precalibration_truncated.svg
    :width: 800

    When using the calibration gas as an input for the :func:`~catalight.analysis.tools.analyze_cal_data` function, combine overlapped peaks as single entries. Here Propylene/Propane peaks and the Butane/Butene peaks are combined in the calibration file, and the expected ppm is supplied as the sum of the two individual components.

.. note::
    The catalight system utilizes regular expression to determine the number of atoms of a given element within a Chem ID. Entering C\ :sub:`3`\ H\ :sub:`6`/C\ :sub:`3`\ H\ :sub:`8` would cause double counting of the carbon components for this chemical, leading to error when calculating the mole balance.

.. figure:: _static/images/calgas_postcalibration.svg
    :width: 800

    An example of the calibration file output by calling the :func:`~catalight.analysis.tools.analyze_cal_data` function. The fit values for each molecule are now entered into the calibration file by the software, and this calibration file can be imported as calDF going forward for future analysis.

Make sure to read the :ref:`calibration` analysis section for a walkthrough on using the software tools to perform the calibration fits.

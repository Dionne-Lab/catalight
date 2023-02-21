The main toolboxes
------------------
analysis.plotting
^^^^^^^^^^^^^^^^^
analysis.user_inputs
^^^^^^^^^^^^^^^^^^^^
analysis.tools
^^^^^^^^^^^^^^

The GCData class
----------------

Helper scripts
--------------
A number of executable scripts have been written to perform basic data analysis with graphical user inputs. Files prefixed with the phrase "run/_" indicate that the file can be executed in command line and UI prompts will help the user run the respective analysis instructions. Alternatively, all of these files can be called in seperate, user-created scripts without executing the file entirely. Each "run" file in the analysis subpackage contains two function: "get_user_inputs()" and "main()". "get_user_inputs()" is designed to open UI dialogs, taking in user values for running analysis. This was done to make data processing as simple as possible for users without coding experience. "main()" is where the actual analysis gets performed. The main() functions typically have a large number of arguments, which may seem intimidating at first. This is mainly to increase flexibility, and many of these arguments can stay as their default values. If a user would like to run analysis in a scripted fashion, calling analysis.run/_"filename".main() with the desired arguments is a completely acceptable method! Of course, the user can bypass these helper functions all together for even more flexible data analysis options.

.. _calibration:

Running a calibration
---------------------

.. figure:: _static/images/running_calibration.png
    :width: 800

    An example of running the "analyze_cal_data" method in a scripted format. An empty calibration file containing chemical ID strings and GC elution times windows needs to be provided and a calibration experiment should already be run.

.. figure:: _static/images/calibration_output_runnum.png
    :width: 800

    An example of the output of running calibration analysis on a data set.  

.. figure:: _static/images/calibration_output_fits.png
    :width: 800

    An example of fitting to the calibration gas data set provided. Linear fit values are saved into the output calibration.csv file and can be loaded into the rest of the package wherever CalDF is used. Notice that c2h2 produces a bad fit output. This is because there is no c2h2 in the physical calibration gas, but it was entered into the calgas file.
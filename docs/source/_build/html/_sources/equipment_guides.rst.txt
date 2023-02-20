.. _alicat_doc:

Alicat MFCs
-----------
Alicat brand MFCs are accessed utilizing the Alicat python package developed by Patrick Fuller and Numat.
 | `numat/alicat: Python driver and command line tool for Alicat mass flow controllers. (github.com) <https://github.com/numat/alicat>`_
 | `Python and command prompt communication instructions  Alicat Scientific <https://www.alicat.com/using-your-alicat/alicat-python-and-command-prompt-communication/>`_

For proper gas monitoring, many mass flow controllers need to be supplied with the appropriate process gas composition. Alicat flow controllers are capable of creating custom gas mixtures comprised of some combination of the gas library hosted by the device. This feature is implemented in the gas_system class of Projectname for creating calibration gasses, and output gas compositions when using a flow meters after gas mixing. The following links provide additional information for Alicat systems:
 | `Gas Select™ and COMPOSER™ tutorial | Alicat Scientific <https://www.alicat.com/knowledge-base/how-to-use-gas-select-and-composer/>`_
 | `Gas Mix Calibration Firmware | Alicat Scientific <https://www.alicat.com/models/gas-select-composer-gas-mix-calibration-firmware/>`_
 | `Gas Select gas list | Alicat Scientific <https://www.alicat.com/knowledge-base/gas-select-gas-list/#g_tab-0-0-vert-0>`_

.. warning:: 
    This automated gas system has no ability to check gas mixing safety! It is your responsibility to ensure chemical compatibility before mixing gasses. Always check for leaks and ensure the system is free of pressure build ups before leaving the system unattended or flowing hazardous gasses.

.. admonition:: Making the Connection

    The COM ports for the individual MFC addresses are currently hard coded into the :class:`Gas_System.__init__ <photoreactor.equipment.alicat_MFC.gas_control.Gas_System.__init__>` method. New users need to edit these addresses in a forked version of the source code for successful connection. Additionally, the MFC count is hard coded for 4 MFCs and one output flow meter at the moment and code changes need to make a number of updates to the source code to change the MFC count. This will soon be updated such that the user only has to specify the number of MFCs in the init method. Eventually this will be replaced with a single configuration file. See :ref:`Areas for Future Development <future>` for more details. Additional software shouldn't be necessary.

.. _harrick_doc:

Harrick Heater/Watlow
---------------------
The `temperature controller <https://harricksci.com/temperature-controller-kit-110v/>`_ supplied by Harrick to control the heater builtin to  `Harrick reaction chambers <https://harricksci.com/praying-mantis-high-temperature-reaction-chambers/>`_ is controlled by a Watlow temperature controller. In place of using the `EZ-ZONE configurator software <https://www.watlow.com/products/controllers/software/ez-zone-configurator-software>`_, we utilize the `pywatlow package <https://pywatlow.readthedocs.io/en/latest/readme.html>`_ developped by Brendan Sweeny and Joe Reckwalder. Brendan has an excellent `write up <http://brendansweeny.com/posts/watlow>`_ describing the creation of the project. Our :class:`~photoreactor.equipment.harrick_watlow.heater_control.Heater` class simply add some additional utilities on top of the pywatlow project, such as unit conversions, and ramped heating. In theory, the :class:`~photoreactor.equipment.harrick_watlow.heater_control.Heater` class should work with any Watlow controlled heater, but we have only tested it with the Harrick system. 

.. tip::
     Other parameters are accessible using pywatlow. See the "Operations" section of the :download:`manual <../../photoreactor/equipment/harrick_watlow/manual_pmpmintegrated.pdf>` located in the photoreactor/equipment/harrick_watlow directory.

.. admonition:: Making the Connection

    The COM ports for the Watlow heater are currently hard coded into the :class:`Heater.__init__ <photoreactor.equipment.harrick_watlow.heater_control.Heater.__init__>` method. New users need to edit these addresses in a forked version of the source code for successful connection. Eventually this will be replaced with a single configuration file. See :ref:`Areas for Future Development <future>` for more details. Additional software should not be needed, thought testing your connection with the EZ zone configurator software can be helpful for troubleshooting.

.. _thorlabs_diode_doc:

ThorLabs Laser Diode Driver
---------------------------
.. Warning::
    Lasers present serious safety hazards, even in lab environments. This is especially true when software is used to automatically control them. Always take abundant safety precautions to ensure laser beams are physically contained. Never assume the code is working properly. Don't rely on the software to turn the laser off and assume you can enter the laser lab without safety glasses on. Always be in the room when engaging the laser via code, and always use safety interlocks and message boards to alert other users that an unattended laser is in action.

We use the `LDC200C Series <https://www.thorlabs.com/thorproduct.cfm?partnumber=LDC200CV>`_ Laser Diode Driver to control our diode laser excitation source. This part on its on does not have a computer interface, but supports current modulation via a 10 Volt analog signal supplied by a BNC connection at the rear of the device. To supply an analog signal to the current controller, we utilize a `USB-231 DAQ card from Measurment Computing Corporation (MCC) <https://www.mccdaq.com/usb-data-acquisition/USB-230-Series.aspx>`_. MCC publishes a `Python API for their Universal Library (mcculw) <https://github.com/mccdaq/mcculw>`_. We also utilize their `instacal software <https://www.mccdaq.com/daq-software/instacal.aspx>`_ for installing the DAQ and setting the board number, though this may not be strictly necessary when using the `mcculw library <https://www.mccdaq.com/PDFs/Manuals/Mcculw_WebHelp/ULStart.htm>`_. Our :class:`~photoreactor.equipment.diode_laser.diode_control.Diode_Laser` class hides interaction with the mcculw from the user, favoring method calls such as "Diode_Laser.set_power()" over interacting directly with the DAQ board. The intention is to ignore the existence of the DAQ interface when operating the laser programatically. In fact, this makes some troubleshooting activities a bit easier for the Diode_Laser class as the laser can remain off while the user interacts safely with the DAQ board. All commands will remain function, though voltage readings from the current driver output won't return realistic values. 

.. admonition:: Making the Connection

    Is isn't completely necessary to install software before using an :class:`~photoreactor.equipment.diode_laser.diode_control.Diode_Laser` instance, but you will need to install the MCC DAQ board in some way. We suggest you install and use `instacal <https://www.mccdaq.com/daq-software/instacal.aspx>`_, but there is a command line method documented in the `mcculw library <https://www.mccdaq.com/PDFs/Manuals/Mcculw_WebHelp/ULStart.htm>`_

.. figure:: _static/images/thorlabs_diode_driver.png
    :width: 800

    Screenshot from Thorlabs current driver manual showing where BNC connections need to be made along with the voltage to current conversion factors used. Note that these values may need to change if you have a different model number!

.. figure:: _static/images/DAQ.png
    :width: 800

    Screenshot of product page for the DAQ board used in D-Lab hardware configuration

.. _newport_meter_doc:

Power meter
-----------
entering some information here

.. _sri_gc_doc:

SRI Gas chromatograph
---------------------
In our lab, we use the 8610-0571 8610C MULTIPLE GAS ANALYZER #5 GC from SRI instruments. There is no python package availble to control SRI GCs as far as we know (2023/02/16). However, SRI provides a remote control interface in the form of an "API provided through a .NET assembly". This is downloaded when you install a version of peaksimple onto your lab computer within a zip file called PeaksimpleConnectorTestClient.zip. We include an unzipped version of this package within the photoreactor/equipment/sri_gc directory. The end-user does not need to install PeaksimpleConnector files, but will need an instance of peaksimple installed on the computer. The official documentation file from the SRI website is also stored in this directory as :download:`PeakSimpleRemoteControlJune2014.pdf <../../photoreactor/equipment/sri_gc/PeakSimpleRemoteControlJune2014.pdf>` if a user would like to see more information about SRI's API. 

What does this mean and what is a "`.NET assembly <https://dotnet.microsoft.com/en-us/learn/dotnet/what-is-dotnet>`_"? Essentially, .NET is a way of writing code that makes it accessible across multiple languages. Tools can be built using Visual Basic or C then accessed elsewhere in a differnt language through the "`Common Language Runtime <https://learn.microsoft.com/en-us/dotnet/standard/clr>`_" so long as they are built using .NET principles. For us, this means we can access the SRI API by loading it into python with a package called `python.NET <https://pypi.org/project/pythonnet/>`_. This interface works a bit differently from the other tools utilized in this package, like those for controlling MFCs and the Watlow heater, because the API connects us to peaksimple, the GC's software, rather than directly connecting us to the instrument. In practice, this means that an instance of peaksimple must be installed and running whenever python calls to the instrument are made.

.. note::
    There is a documented bug in SRI's "PeakSimpleRemoteControlJune2014" instructions stating that 
        "Once a connecton has been broken by stopping either Peaksimple or the calling program, the other must be restarted also before another connecton can be made."

    This means that Peaksimple must be manually closed and reopened each time the packagename GUI or scripted interface is closed. If you using this package with an interactive python kernel, you may also have to restart the kernel before reconnecting to peaksimple.

.. figure:: _static/images/peaksimple_client_contents.png
    :width: 800
    :class: with-border

    The contents of the PeaksimpleClient folder installed with Peaksimple. The three most important files are highlighted.

.. figure:: _static/images/peaksimple_client_executable.png
    :width: 800
    :class: with-shadow

    Running PeaksimpleClient.exe

.. figure:: _static/images/peaksimpleconnectortestclient_contents.png
    :width: 800

    PeaksimpleConnectorTestClient.sln file contents from Visual Studio

Now that we understand the files inside of SRI's automation toolkit, lets look at how we can import these tools into python. This is accomplished utilizing the python.NET package, and gives us access to every method you see within the PeaksimpleConnector.TestClient.sln file above.

.. code-block:: python
    :caption: Import the python.NET package by typing 'import clr'
        
    import os
    import clr

.. code-block:: python
    :caption: Reference the PeaksimpleConnector.dll file in the clr. Not these paths are show relative to our gc_control.py file.

    dir_path = os.path.dirname(os.path.realpath(__file__))
    assemblydir = os.path.join(dir_path, 'PeaksimpleClient', 'PeaksimpleConnector.dll')
    
    clr.AddReference(assmblydir) # Add the assembly to python.NET

.. code-block:: python
    :caption: Once the reference has been added, simply import the Peaksimple namespace

    # Now that the assembly has been added to python.NET,
    # it can be imported like a normal module
    import Peaksimple  # Import the assembly namespace, which has a different name

.. code-block:: python
    :caption: You can now create a PeaksimpleConnector object which has access to all the methods provided in the .NET assembly

    Connector = Peaksimple.PeaksimpleConnector()  # This class has all the functions

    Connector.Connect() # Connect to running instance of peaksimple using class method
    Connector.LoadControlFile(ctrl_file)  # Load ctrl file using class method

That pretty much gives you complete control over the GC. Notice that there are not a ton of attributes or methods within the PeaksimpleConnector class. The main interaction the user has with the equipment is acheived by editting the control files. Through editting the control file, the user can change many definitions that would usually be controlled by the peaksimple GUI, but programatically. Most importantly, you can now set the filename, save location, number of repeats, and use Connector.SetRunning() to start connection. These interactions get wrapped for the user in the :class:`~photoreactor.equipment.sri_gc.gc_connector.GC_Connector()` class. See `examples` for details on using the class.

.. figure:: _static/images/control_file_editting.png
    :width: 800

    The abbreviated contents of the .CON files, which you can open in a text editor. We edit key lines with the :class:`~photoreactor.equipment.sri_gc.gc_connector.GC_Connector()` class, which is the same as clicking check boxes and buttons in the editting window used by Peaksimple itself. 

.. admonition:: Making the Connection

    You shouldn't need to change source code to connect with an SRI GC, but you will need to download Peaksimple from SRI's website and open the program before launching :class:`~photoreactor.equipment.sri_gc.gc_connector.GC_Connector()` 
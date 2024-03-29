The purpose of this section is to demonstrate the connection process for specific pieces of equipment. This is less so a tutorial on how to use different code interfaces, and more about how we connect to the hardware in the first place. This section will describe the required python packages, external software, and source code edits necessary to connect to instruments. In nearly every circumstance, this initial connection is then wrapped by a new python class which provides slightly more convenient functions that can then interface with the rest of the package. Look out for the **"Making the Connection"** tips that describe the requirements for using each specific instrument!

.. _alicat_doc:

Alicat MFCs
-----------
Alicat brand MFCs are accessed utilizing the Alicat python package developed by Patrick Fuller and Numat.

| `numat/alicat: Python driver and command line tool for Alicat mass flow controllers. (github.com) <https://github.com/numat/alicat>`_
| `Python and command prompt communication instructions  Alicat Scientific <https://www.alicat.com/using-your-alicat/alicat-python-and-command-prompt-communication/>`_

For proper gas monitoring, many mass flow controllers need to be supplied with the appropriate process gas composition. Alicat flow controllers are capable of creating custom gas mixtures comprised of some combination of the gas library hosted by the device. This feature is implemented in the gas_system class of catalight for creating calibration gasses, and output gas compositions when using a flow meters after gas mixing. The following links provide additional information for Alicat systems:

| `Gas Select™ and COMPOSER™ tutorial | Alicat Scientific <https://www.alicat.com/knowledge-base/how-to-use-gas-select-and-composer/>`_
| `Gas Mix Calibration Firmware | Alicat Scientific <https://www.alicat.com/models/gas-select-composer-gas-mix-calibration-firmware/>`_
| `Gas Select gas list | Alicat Scientific <https://www.alicat.com/knowledge-base/gas-select-gas-list/#g_tab-0-0-vert-0>`_

.. warning::
    This automated gas system has no ability to check gas mixing safety! It is your responsibility to ensure chemical compatibility before mixing gasses. Always check for leaks and ensure the system is free of pressure build ups before leaving the system unattended or flowing hazardous gasses.

.. admonition:: Making the Connection

    The COM ports for the individual MFC addresses are currently hard coded into the :class:`Gas_System.__init__ <catalight.equipment.gas_control.alicat.Gas_System.__init__>` method. New users need to edit these addresses in a forked version of the source code for successful connection. Additionally, the MFC count is hard coded for 4 MFCs and one output flow meter at the moment and code changes need to make a number of updates to the source code to change the MFC count. This will soon be updated such that the user only has to specify the number of MFCs in the init method. Eventually this will be replaced with a single configuration file. See :ref:`Areas for Future Development <future>` for more details. Additional software shouldn't be necessary.

.. _harrick_doc:

Harrick Heater/Watlow
---------------------
`The Harrick reaction chamber <https://harricksci.com/praying-mantis-high-temperature-reaction-chambers/>`_'s `heating system <https://harricksci.com/temperature-controller-kit-110v/>`_ is controlled by a Watlow temperature controller. In place of using the `EZ-ZONE configurator software <https://www.watlow.com/products/controllers/software/ez-zone-configurator-software>`_, we utilize the `pywatlow package <https://pywatlow.readthedocs.io/en/latest/readme.html>`_ developed by Brendan Sweeny and Joe Reckwalder. Brendan has an excellent `write up <http://brendansweeny.com/posts/watlow>`_ describing the creation of the project. Our :class:`~catalight.equipment.heating.watlow.Heater` class simply add some additional utilities on top of the pywatlow project, such as unit conversions, and ramped heating. In theory, the :class:`~catalight.equipment.heating.watlow.Heater` class should work with any Watlow controlled heater, but we have only tested it with the Harrick system.

.. tip::
     Other parameters are accessible using pywatlow. See the "Operations" section of the :download:`manual <../../manuals/watlow_heater/manual_pmpmintegrated.pdf>` located in the catalight/equipment/harrick_watlow directory.

.. admonition:: Making the Connection

    The COM ports for the Watlow heater are currently hard coded into the :class:`Heater.__init__ <catalight.equipment.heating.watlow.Heater.__init__>` method. New users need to edit these addresses in a forked version of the source code for successful connection. Eventually this will be replaced with a single configuration file. See :ref:`Areas for Future Development <future>` for more details. Additional software should not be needed, though testing your connection with the EZ zone configurator software can be helpful for troubleshooting.

.. _thorlabs_diode_doc:

ThorLabs Laser Diode Driver
---------------------------
.. Warning::
    Lasers present serious safety hazards, even in lab environments. This is especially true when software is used to automatically control them. Always take abundant safety precautions to ensure laser beams are physically contained. Never assume the code is working properly. Don't rely on the software to turn the laser off and assume you can enter the laser lab without safety glasses on. Always be in the room when engaging the laser via code, and always use safety interlocks and message boards to alert other users that an unattended laser is active.

We use the `LDC200C Series <https://www.thorlabs.com/thorproduct.cfm?partnumber=LDC200CV>`_ Laser Diode Driver to control our diode laser excitation source. The driver does not have a computer interface, but supports current modulation via a 10 Volt analog signal supplied by a BNC connection at the rear of the device. To supply an analog signal to the current controller, we utilize a `USB-231 DAQ card from Measurment Computing Corporation (MCC) <https://www.mccdaq.com/usb-data-acquisition/USB-230-Series.aspx>`_. MCC publishes a `Python API for their Universal Library (mcculw) <https://github.com/mccdaq/mcculw>`_. We also utilize their `instacal software <https://www.mccdaq.com/daq-software/instacal.aspx>`_ for installing the DAQ and setting the board number, though this may not be strictly necessary when using the `mcculw library <https://www.mccdaq.com/PDFs/Manuals/Mcculw_WebHelp/ULStart.htm>`_. Our :class:`~catalight.equipment.light_sources.diode_control.Diode_Laser` class hides interaction with the mcculw from the user, favoring method calls such as "Diode_Laser.set_power()" over interacting directly with the DAQ board. The intention is to ignore the existence of the DAQ interface when operating the laser programmatically. In fact, this makes some troubleshooting activities a bit easier for the Diode_Laser class as the laser can remain off (by unplugging or pressing the physical off switch) while the user interacts safely with the DAQ board. All commands will remain functional, though voltage readings from the current driver output won't return realistic values.

.. admonition:: Making the Connection

    It isn't completely necessary to install additional software before using a :class:`~catalight.equipment.light_sources.diode_control.Diode_Laser` instance, but you will need to install the MCC DAQ board in some way. We suggest you install and use `instacal <https://www.mccdaq.com/daq-software/instacal.aspx>`_, but there is a command line method documented in the `mcculw library <https://www.mccdaq.com/PDFs/Manuals/Mcculw_WebHelp/ULStart.htm>`_

.. figure:: _static/images/thorlabs_diode_driver.png
    :width: 800

    Screenshot from Thorlabs current driver manual showing where BNC connections need to be made along with the voltage to current conversion factors used. Note that these values may need to change if you have a different model number!

.. figure:: _static/images/DAQ.png
    :width: 800

    Screenshot of product page for the DAQ board used in D-Lab hardware configuration

.. _newport_meter_doc:

Power meter
-----------
A power meter is programmatically controlled in order to run laser power calibrations. We currently use the :download:`Newport 843-R-USB <../../manuals/newport_powermeter/843-R-843-R-USB-User-Manual-rev-1.34-2.pdf>` accessed via :download:`Newports' PMManager's COM object <../../manuals/newport_powermeter/OphirLMMeasurement COM Object.doc>`. This method should also allow the user to control the `1919-R <https://www.newport.com/p/1919-R>`_, `843-R-USB <https://www.newport.com/p/843-R-USB>`_ , `844-PE-USB <https://www.newport.com/p/844-PE-USB>`_ , 845-PE-RS, `1938-R <https://www.newport.com/p/7Z01705>`_, and `2938-R <https://www.newport.com/p/7Z01706>`_ models with no additional changes, but these models have not been tested. Additional commands could be accessed via the provided COM object if desired. See the :download:`user commands manual <../../manuals/newport_powermeter/manual_newport _user_commands.pdf>` for more information.

.. admonition:: Making the Connection

    A version of Newport's PMManager COM object is required and needs to be installed in order to use the :class:`~catalight.equipment.power_meter.newport.NewportMeter` class. This can be installed from `<https://www.newport.com/t/PMManager-power-meter-application-software>`_. Installing the full PMManager software includes the COM object, and no additional code changes should be needed after the installation.

.. _sri_gc_doc:

SRI Gas chromatograph
---------------------
In our lab, we use the 8610C MULTIPLE GAS ANALYZER #5 GC from SRI instruments with an FID and TCD detector. There is no python package available to control SRI GCs as far as we know (2023/02/16). However, SRI provides a remote control interface in the form of an "API provided through a .NET assembly". This is downloaded when you install a version of peaksimple onto your lab computer within a zip file called PeaksimpleConnectorTestClient.zip. We include an unzipped version of this package within the catalight/equipment/gc_control directory. The end-user does not need to install PeaksimpleConnector files, but will need an instance of peaksimple installed on the computer. The official documentation file from the SRI website is also stored in this directory as :download:`PeakSimpleRemoteControlJune2014.pdf <../../manuals/sri_gc/PeakSimpleRemoteControlJune2014.pdf>` if a user would like to see more information about SRI's API.

What does this mean and what is a "`.NET assembly <https://dotnet.microsoft.com/en-us/learn/dotnet/what-is-dotnet>`_"? Essentially, .NET is a way of writing code that makes it accessible across multiple languages. Tools can be built using Visual Basic or C then accessed elsewhere in a different language through the "`Common Language Runtime <https://learn.microsoft.com/en-us/dotnet/standard/clr>`_" so long as they are built using .NET principles. For us, this means we can access the SRI API by loading it into python with a package called `python.NET <https://pypi.org/project/pythonnet/>`_. This interface works a bit differently from the other tools in this package, like those for controlling MFCs and the Watlow heater, because the API connects us to peaksimple, the GC's software, rather than directly connecting us to the instrument. In practice, this means that an instance of peaksimple must be installed and running whenever python calls to the instrument are made.

.. note::
    There is a documented bug in SRI's "PeakSimpleRemoteControlJune2014" instructions stating that
        "Once a connection has been broken by stopping either Peaksimple or the calling program, the other must be restarted also before another connection can be made."

    This means that Peaksimple must be manually closed and reopened each time the catalight GUI or scripted interface is closed. If you are using this package with an interactive python kernel, you may also have to restart the kernel before reconnecting to peaksimple. The catalight GUI will attempt to open Peaksimple automatically if it isn't already, but the user must close Peaksimple after closing the catalight GUI.

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

Now that we understand the files inside of SRI's automation toolkit, lets look at how we can import these tools into python. This is accomplished utilizing the python.NET package, which gives us access to every method you see within the PeaksimpleConnector.TestClient.sln file above.

.. code-block:: python
    :caption: Import the python.NET package by typing 'import clr'

    import os
    import clr  # Essentially python.NET

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

That pretty much gives you complete control over the GC. Notice that there are not a ton of attributes or methods within the PeaksimpleConnector class. The main interaction the user has with the equipment is achieved by editing the control files. Through editing the control file, the user can change many definitions that would usually be controlled by the peaksimple GUI, but programmatically. Most importantly, you can now set the filename, save location, number of repeats, and use Connector.SetRunning() to start connection. These interactions get wrapped for the user in the :class:`~catalight.equipment.gc_control.sri_gc.GC_Connector()` class. See :doc:`examples` for details on using the class.

.. figure:: _static/images/control_file_editing.png
    :width: 800

    The abbreviated contents of the .CON files, which you can open in a text editor. We edit key lines with the :class:`~catalight.equipment.gc_control.sri_gc.GC_Connector()` class, which is the same as clicking check boxes and buttons in the editing window used by Peaksimple itself.

.. admonition:: Making the Connection

    You shouldn't need to change source code to connect with an SRI GC, but you will need to download Peaksimple from SRI's website and open the program before launching :class:`~catalight.equipment.gc_control.sri_gc.GC_Connector()`

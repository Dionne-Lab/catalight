=======================
Welcome to projectname!
=======================
Projectname is tool set developed by scientists at Stanford to help automate photocatalysis experiments. Projectname is capable of connecting to hardware, coordinating instruments to run a variety of different experimental procedures, and organizing and analyzing data collected by the system. The project is designed in a modular format to enable users to bring their own unique hardware while still utilizing the core features of experiment management and data handling. The program functions in both a scripted version and a GUI to aid users in planning experimental procedures and manually controlling hardware.

To date, Projectname is compatible with Alicat mass flow controllers, heater systems controlled by Watlow components, Measurement Computing data acquisition boards (used for communication with ThorLabs laser diode drivers), NewPort 843-R power meter, and SRI gas chromatographs. Support for additional hardware is planned for the future, including FTIR data collection and analysis and NKT Photonics lasers. We strongly encourage interested users to consider contributing to the project by adding new device support and helping expand the Projectname functionality.


including temperature, laser power, flow rate, and composition sweeps

Areas for Future Development:
=============================
The current iteration of the system has been designed with modularity in mind, but additional improvements could be made to enable more seamless use by a variety of groups with different hardware configurations. This will become increasingly important as users develop their own equipment classes.
*Subclassing could be utilized to make generic system components (such as “gas_system”) that do not necessarily rely on specific hardware. Some configuration file could be utilized for selecting equipment types to fill into the generic system components. For example, an abstract gas_system class could be created with specific class method names compatible with the rest of the package, then a specific class can be initialized (Alicat_gas_system) that subclasses the abstract class and decorates the class methods to make them compatible with the specific hardware used by a particular lab. This would ideally be managed in a single location, such as a configuration file, that a new user could edit once in order to make the system compatible with their hardware. Ideally no other code components would need to be edited. The LightLab package is an excellent example of flexible lab configuration and could be a very helpful reference for development in this area (Welcome to Lightlab’s documentation! — Lightwave Laboratory Instrumentation 1.1.0 documentation).
*The gas_system class and the related GUI components are currently configured to work with a specific number of mass flow controllers. This could easily be amended by utilizing loops and list for accessing MFC data and controls. For example, the MFC class currently has attributes self.mfc_a, self.mfc_b, etc. This should be replaced by self.mfc_list which contains a list of all mfcs used by the system, allowing flexibility for different system configurations. Ideally this can be managed by a file outside the gas_system class. This also needs to be updated within the GUI code, which currently generates MFC components using QtDesigner. This would need to be done programmatically for flexibility.
*The data analysis sub-package was initially designed with only gas chromatography data in mind. The original authors intend to implement FTIR data in the near future, but additional consideration for adaptability with other data types needs to be considered to expand usability.

Equipment Specific Guides:
==========================
Alicat MFCs
-----------
Alicat brand MFCs are accessed utilizing the Alicat python package developed by Patrick Fuller and Numat.
numat/alicat: Python driver and command line tool for Alicat mass flow controllers. (github.com)
Python and command prompt communication instructions | Alicat Scientific

For proper gas monitoring, many mass flow controllers need to be supplied with the appropriate process gas composition. Alicat flow controllers are capable of creating custom gas mixtures comprised of some combination of the gas library hosted by the device. This feature is implemented in the gas_system class of Projectname for creating calibration gasses, and output gas compositions when using a flow meters after gas mixing. The following links provide additional information for Alicat systems:
Gas Select™ and COMPOSER™ tutorial | Alicat Scientific
Gas Mix Calibration Firmware | Alicat Scientific
Gas Select gas list | Alicat Scientific

Data Analysis:
==============

Auxiliary tools:
================
Laser Calibration
-----------------

Pressure drop measurement
-------------------------

GC delay measurement
--------------------

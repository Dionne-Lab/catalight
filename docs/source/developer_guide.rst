Providing feedback
------------------
The development of v1 of catalight took over a year. While that was a tremendous learning opportunity, the length of time means there are undoubtedly details left out from this documentation that may be crucial for first time users. Please feel free to reach out to the authors with questions, and we strongly encourage feedback on the documentation. A lot of work went into developing this project, and we want other labs to benefit from this effort and do more productive research! The original authors self learned Python while developing this project. There very well may be aspects of the project that could be improved, so please reach out of fork our Github project if you see any other areas for improvement. Your questions/feedback are not only welcome, but encouraged!

Developing equipment drivers
----------------------------
catalight was built with modularity in mind. We do not want to make a code project that only allows the automation of a single lab setup! That being said, its not feasible to create a universal code package that is both user friendly and compatible with all equipment immediatly. Drivers for specific pieces of equipment need to be written for users hoping to use other equipment types. Our :doc:`Equipment Specific Guides <equipment_guides>` section is meant to serve as both instructions for users attempting to connect the exact hardware we utilize in our lab and to serve as examples for users developing new equipment drivers.

We ask that users developing new hardware (a) fork our Github to eventually merge improvements to the main project, (b) provide manuals for equipment within the catalight/equipment/"specific_equipment_folder" directory for the new piece of equipment developed, (c) write a :doc:`Equipment Specific Guides <equipment_guides>` to help other users utilize your code, and (d) write your specific driver utilizing the same function names as comparable equipment that has already been developed (see :ref:`Areas for future development <future>` for more thoughts on how abstract classes could be created to aid this process).

An excellent example of a flexible automated lab design can be found in the `LightLab <https://lightlab.readthedocs.io/en/development/index.html>`_ package. catalight was developped by novice programmers to be (a) more specific in scope than LightLab and (b) utilize existing Python APIs in place of developing VISA-based drivers for equipment. The trade off is that catalight is a less flexible codebase that we hope is more user friendly for researchers working on photocatalysis experiment specifically, where as LightLab is a flexible project that seems best suited for optical characterization labs.

My equipment doesn't have a Python API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This is a tough situation and some additional programming will be required! Two approaches for this situation include (1) connecting with the equipment by interfacing with the providers software system and (2) writing low level or VISA communication interfaces, for example, by using pySerial/pyVISA.

Our SRI GC connection is an example of approach 1. There is no Python interface supported by the equipment developer or by found on PyPi or Github (that we could find). Fortunately, the equipment developer does supply a programing interface to thier control software, but it is not written specifically for Python. We were able to connect to this using the "`.NET infrastructure <https://dotnet.microsoft.com/en-us/learn/dotnet/what-is-dotnet>`_" which is a way to reuse code across multiple languages via something called "`Common Language Runtime <https://learn.microsoft.com/en-us/dotnet/standard/clr>`_" and `python.NET <https://pypi.org/project/pythonnet/>`_. If you've never heard of this, neither did we! Thankfully, this can look pretty simple in practice. See our :ref:`SRI GC <sri_gc_doc>` specific guide for more details on how this works.

If the producer of your equipment does not provide a Python-specific programming interface to your equipment or its software (if it has software), you may need to interface with your equipment via some communication protocol, like VISA. Some examples of this includes The `pywatlow package <https://pywatlow.readthedocs.io/en/latest/readme.html>`_ and Brendan Sweeny's `write up <http://brendansweeny.com/posts/watlow>`_ on how he created it, the `alicat package <https://github.com/numat/alicat>`_ which uses pySerial to control MFCs, and the `LightLab <https://lightlab.readthedocs.io/en/development/index.html>`_ project which generalizes the development of VISA connections to lab equipment. Often, equipment without software or an existing API will have a programmer manual describing how to use serial/GPIB/VISA communication commands.

Ideally, users that need to develop their own communication interfaces through some read/write commands via pySerial, pyVISA, and the like can write their python driver in a seperate package, publish it, and import it into the catalight package. It is much easier for users to use tools with more human readable commands like alicat.MassFlowController.set_flow() wrapping over the signals communication. Ease of use is exactly why we choose to use packages like alicat and pywatlow in the first place!!

Creating New Experiment Types
-----------------------------
Coming soon

Making Changes to the GUI
-------------------------
Function
^^^^^^^^
To create new static widget, we recommend using the QtDesigner application and opening the :file:`catalight.gui_components.reactorUI.ui` file. Any custom widgets added to the GUI can be inserted to the `catalight.gui_components` folder and promoted within QtDesigner. In the current state, all static widgets were created in this way when used within :mod:`catalight.catalight_GUI` and the code inside of this module connection all of the functionality of the GUI window and its components. Remember, the main purpose of the GUI is to help the user create experiment objects and "run a study". Experimental functionality should be added to the :class:`~catalight.equipment.experiment_control.Experiment` class. New widgets should help fill attributes of the Experiment class or other classes that need to be developed in the future. A second, but major function of the GUI is to directly control hardware. Future development should allow users to choose and utilize any equipment within the GUI.

Style
^^^^^
:mod:`catalight.gui_components.style_guide` is a subpackage accessible when catalight is downloaded as a repository from the GitHub page. Within this folder is two image files and a folder containing QSS templates. The "icon.svg" and "drawing.svg" files can be replaced with the file of your choice, provided your match the filename exactly. This should replace the catalight icon and D-Lab logos within the GUI directly, without any code changes. To use alternate file types, you'll need to utilize QT Designer (or edit the ui file - not recommended) to change the image resource path.
The QSS sheet was downloaded an lightly modified from `the QSS Stock website <https://qss-stock.devsecstudio.com/templates.php>`_. You can edit this file for wide-spread style changes to the GUI appearance, or enter your own QSS style sheet and insert it to the GUI by editting the path inside the :func:`catalight.catalight_GUI.setup_style` function.


.. _future:

Areas for Future Development:
-----------------------------
Design is an iterative process. The catalight project has already been updated several times going into the deployment of v1.0.0, but there is always room for improvement. Below is a laundry list of improvements that can be added to future versions of the package.

The current iteration of the system has been designed with modularity in mind, but additional improvements could be made to enable more seamless use by a variety of groups with different hardware configurations. This will become increasingly important as users develop their own equipment classes.

* Better methods need to be developped to **allow users to configure specific hardware** with minimal coding while maximizing compatibility with the rest of the package.

  * For example, an abstract "GasSystem" class could be created with standardized class method names compatible with the rest of the package, then a specific "AlicatGasSystem" class can be initialized that subclasses the abstract class and decorates the class methods to make them compatible with the specific hardware used by a particular lab. In otherwords, the methods of every gas sytem should behave identically on the surface, while the actual implementation should change for each specific hardware setup. AlicatGasSystem.set_flow() needs to behave the same as a hypothetical BronkhorstGasSystem.set_flow()

  * This would ideally be managed in a single location, such as a configuration file, that a new user could edit once in order to make the system compatible with their hardware. Ideally no other code components would need to be edited. This configuration file could allow the user to change between "AlicatGasSystem" or "BronkhorstGasSystem". If class abstraction is implemented correctly, the rest the code package will continue working as intended.

  * The `LightLab <https://lightlab.readthedocs.io/en/development/index.html>`_ package is an excellent example of flexible lab configuration and could be a very helpful reference for development in this area. In particular, future development should look into their implementation of `"essentialMethods" <https://lightlab.readthedocs.io/en/development/API/lightlab.laboratory.instruments.interfaces.html>`_ attribute for abstract drivers and type checking in their `DriverMeta <https://github.com/lightwave-lab/lightlab/blob/development/lightlab/equipment/visa_bases/visa_driver.py>`_ class. Their tutorial on `creating instrument drivers <https://lightlab.readthedocs.io/en/development/_static/tutorials/drivers/drivers.html>`_ is also a great reference.

* **The Gas_System class needs to support a flexible number of MFCs.** The gas_system class and the related GUI components are currently configured to work with a specific number of mass flow controllers. This could easily be amended by utilizing loops and list for accessing MFC data and controls. For example, the MFC class currently has attributes self.mfc_a, self.mfc_b, etc. This should be replaced by self.mfc_list which contains a list of all mfcs used by the system, allowing flexibility for different system configurations. Ideally this can be managed by a file outside the gas_system class. This also needs to be updated within the GUI code, which currently generates MFC components using QtDesigner. This would need to be done programmatically for flexibility.

* The data analysis sub-package was initially designed with only gas chromatography data in mind. The original authors intend to **implement FTIR data and support for multiple GC detectors** in the near future, but additional consideration for adaptability with other data types needs to be considered to expand usability.

* **Calibration files need to be able to handle components logged on multiple detectors.** This could either be handled by individual calibration files for each detector or by string handling to inteligently interpret slashes, for example

* **The toolbar in the GUI needs to displays realistic values from the actual data shown.** The main GUI creates a matplotlib figure with an interactive toolbar, but the x, y coordinates are set for the underlying sub-plot instead of the two front most half figures.

* **Unit testing** will be an important feature for implementing pull requests on GitHub if new users try contributing to the project. These will be implemented in the future.
* **Formalized error reporting** needs to be handled.
* **Wavelength sweep experiments** will be implemented when NKT support is (soon)
* **Stability test experiments should be implemented more clearly.** The current implementation of stability test is clunky. It looks confusing in the GUI and doesn't have a dedicated time ind_var. Fixing will require some refactoring.
* **Add plot integration option to chromatogram_scanner_gui**
* **Add option to lock scale on chromatogram_scanner_gui**, possibly by getting max value of all files

Writing Documentation
---------------------
Writing documentation is important! You can use the `ReadtheDocs tutorial <https://docs.readthedocs.io/en/stable/tutorial/index.html>`_ to get familiar with how writing documentation works. We used sphinx to build our API automatically from docstrings, and mostly utilized numpy style docstrings. Especially since this package is written by beginners for beginners, its important to note that docstrings require a specific format to be read by automatic documentation tools!!! We didn't appreciate this when starting, and it lead to many hours of rewriting docstrings. If you aren't familiar with docstring (typically enclosed in triple quote ''' under functions/classes/attributes), you should think of them as instruction on how to use a given function, class, or method. They aren't really a step by step of how a piece of code works, but should contain information on what the code takes in, performs, and returns. The end-user shouldn't need to know exactly how the code works! Of course, you should still comment you source code, too! Many science users are probably most familiar with "documentation" in the form of writing comments that the end-user will use as instructions. Likely, you are used to sending a collaborator a .py file and them editting it directly with user inputs and changes. This isn't the "right way" to distribute code. You want to write functions and documentation such that the user doesn't need to know anything about how it works, like when you import numpy for example. The end user may never see you comments and code, only call your function using its docstring!

If you write proper docstrings, the documentation of your code will be automated. This process is done using a tool called "sphinx" which is apparently the standard for documenting Python code. Though it is automated, it is not that intuitive. It is normal to experience many warning and can be difficult to find help resources. Ideally, this process won't be necessary for other developers as we've already handled most of the configuring. The documentation writer should follow the spinx getting started tutorial to get basic familiarity with the process, but you should only need to run the "make clean" and "make html" commands from within catalight/docs once you've installed sphinx (a requirement for the catalight package anyway).

(#) `Using Sphinx's autosummary tool vs sphinx-apidoc provides cleaner documentation <https://stackoverflow.com/questions/53099934/sphinx-apidoc-vs-autosummary>`_
(#) `More information on autosummary vs sphinx-apidoc <https://romanvm.pythonanywhere.com/post/autodocumenting-your-python-code-sphinx-part-ii-6/>`_
(#) `autosummary isn't a complete solution. Custom .rst templates are needed <https://stackoverflow.com/questions/48074094/use-sphinx-autosummary-recursively-to-generate-api-documentation>`_
(#) `Inherited members needed to be removed in the .rst class template so objects inheriting QT objects weren't too many lines <https://stackoverflow.com/questions/43983799/how-to-avoid-inherited-members-using-autosummary-and-custom-templates>`_

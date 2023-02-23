# -*- coding: utf-8 -*-
"""
I don't think i even committed these additions, but i'm a bit of a hoarder.

I ended up creating a more concise work around using dataclasses instead.
Created on Wed Feb  8 18:37:25 2023

@author: brile
"""

@dataclass
class PlotOptions():
    """
    Dataclass containing common plotting options.

    Attributes
    ----------
    reactant : str
        String identity of reactant molecule to track. Must match what exists
        in the calibration file exactly.
    target_molecule : str
        String identity of the target to use when calculating selectivity. Must
        match what exists in the calibration file exacly.
    mole_bal : str, optional
        Code will perform a mole balance for the element provided.
        The default is 'c'. (i.e. carbon balance)
    figsize : tuple, optional
         Desired size of output figure in inches (x,y), Default is (6.5, 4.5).
         figsize suggestions:
         1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);
         1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);
    savedata : bool, optional
        Indicates whether or not to save data. The default is 'True'.
    switch_to_hours : float, optional
        Time in hours when the output should switch units to
        hours instead of minutes. The default is 2.
    """

    reactant: str
    target_molecule: str
    mole_bal: str = 'c'
    figsize: tuple = (6.5, 4.5)
    savedata: bool = True
    switch_to_hours: float = 2

    def __iter__(self):
        return iter(astuple(self))

    def as_dict(self):
        """Return dictionary of attributes"""
        return asdict(self)


class PlotOptionsLayout(QGridLayout):
    """
    Subclass QGridLayout to request standard plot options from user.

    Parameters
    ----------
    Parent : QWidget
        Can provide parent widget to house layout.
    include_mole_bal : bool
        Mark false to remove those widgets from view, Default is True
    include_savedata : bool
        Mark false to remove those widgets from view, Default is True
    """

    def __init__(self, Parent=None, include_mole_bal=True,
                 include_savedata=True, include_switchtohours=True):
        """Init layout."""
        super().__init__(Parent)

        # Create widgets for window
        self.reactant_entry = QLineEdit('c2h2')
        self.target_molecule_entry = QLineEdit('c2h4')
        self.mole_bal_entry = QLineEdit('C')
        self.figsize_entry = QComboBox()
        self.savedata_entry = QComboBox()
        self.switchtohourss_entry = QDoubleSpinBox(2)

        self.reactant_label = QLabel('Reactant')
        self.target_label = QLabel('Target Molecule')
        self.mole_bal_label = QLabel('Mole Balance Element')
        self.figsize_label = QLabel('Figure Size (x, y)')
        self.savedata_label = QLabel('Save Data? (T/F)')
        self.switchtohourss_label = QLabel('Time to switch units to hours (hr)')

        # Edit ComboBox features
        self.figsize_entry.addItems(['(4.35, 3.25)',
                                     '(5, 3.65)',
                                     '(6.5, 4.5)',
                                     '(9, 6.65)'])
        self.figsize_entry.setEditable(True)
        self.savedata_entry.addItems(['True', 'False'])

        reactant_tip = ('String identity of reactant molecule to track.\nMust '
                        'match what exists in the calibration file exactly.')
        target_tip = ('String identity of the target to use when calculating '
                      'selectivity.\nMust match what exists in the calibration '
                      'file exacly.')
        mole_bal_tip = ('Code will perform a mole balance for the element prov'
                        'ided.\nThe default is \'c\'. (i.e. carbon balance)')
        figsize_tip = ('Desired size of output figure in inches (x,y),\n'
                       'figsize suggestions:\n'
                       '1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);\n'
                       '1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);')

        self.reactant_entry.setToolTip(reactant_tip)
        self.target_molecule_entry.setToolTip(target_tip)
        self.mole_bal_entry.setToolTip(mole_bal_tip)

        self.figsize_entry.setToolTip(figsize_tip)
        self.savedata_entry.setToolTip('Save Data? T/F')
        self.switchtohourss_entry.setToolTip('Time in hour to switch x axis unit')

        # Add widgets to window layout
        self.addWidget(self.reactant_label, 0, 0)
        self.addWidget(self.target_label, 1, 0)
        self.addWidget(self.mole_bal_label, 2, 0)
        self.addWidget(self.figsize_label, 3, 0)
        self.addWidget(self.savedata_label, 4, 0)
        self.addWidget(self.switchtohourss_label, 5, 0)
        self.addWidget(self.reactant_entry, 0, 1)
        self.addWidget(self.target_molecule_entry, 1, 1)
        self.addWidget(self.mole_bal_entry, 2, 1)
        self.addWidget(self.figsize_entry, 3, 1)
        self.addWidget(self.savedata_entry, 4, 1)
        self.addWidget(self.switchtohourss_entry, 5, 1)

        if not include_mole_bal:
            self.removeWidget(self.mole_bal_entry)
            self.removeWidget(self.mole_bal_label)
        if not include_savedata:
            self.removeWidget(self.savedata_entry)
            self.removeWidget(self.savedata_label)
        if not include_switchtohours:
            self.removeWidget(self.switchtohours_entry)
            self.removeWidget(self.switchtohours_label)

    def get_inputs(self):
        """
        Call to return the current supplied entries in plot entries layout.

        Returns
        -------
        options : PlotOptions
            PlotOptions instance containing reactant, target, mole_bal,
            figsize, savedata, switch_to_hours as attributes

        """
        reactant = self.reactant_entry.text()
        target_molecule = self.target_molecule_entry.text()
        mole_bal = self.mole_bal_entry.text()
        figsize = eval(self.figsize_entry.currentText())
        savedata = eval(self.savedata_entry.currentText())
        switch_to_hours = self.switchtohours_entry.value()
        options = PlotOptions(reactant, target_molecule, mole_bal,
                              figsize, savedata, switch_to_hours)
        return options

class PlotDialog(QDialog):
    """
    Open a window to asking the user for plotting options for normal plotting.

    Attributes
    ----------
    plot_options : PlotOptions
        PlotOptions instance containing reactant, target, mole_bal,
        figsize, savedata, switch_to_hours as attributes
    overwrite : bool
        User input for whether or not to overwrite existing data.
    """

    def __init__(self):
        """
        Create widgets, add to window, connect accept button.

        Returns
        -------
        None.

        """
        super().__init__()
        self.setWindowTitle('Enter Plotting Instructions')

        # Create widgets for window
        self.layout = QGridLayout(self)
        self.basic_options_layout = PlotOptionsLayout()
        self.overwrite_entry = QComboBox()
        self.overwrite_entry.addItems(['True', 'False'])
        self.overwrite_label = QLabel('Overwrite previous calculations?')
        self.basecorrect_entry = QComboBox()
        self.basecorrect_entry.addItems(['True', 'False'])
        self.basecorrect_label = QLabel('Add baseline correction?')
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                          | QDialogButtonBox.Cancel)

        # Connect accept button to accept function
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Add widgets to window layout
        self.layout.addWidget(self.overwrite_label, 1, 0)
        self.layout.addWidget(self.overwrite_entry, 1, 1)
        self.layout.addLayout(self.basic_options_layout, 2, 0, 1, 2)
        self.layout.addWidget(self.buttonBox, 3, 0, 1, 2, Qt.AlignCenter)

    def accept(self):
        """Record user entries as attributes and close window."""
        self.overwrite = self.overwrite_entry.currentText()
        self.basecorrect = self.basecorrect_entry.currentText()
        self.plot_options = self.basic_options_layout.get_inputs()
        super(PlotDialog, self).accept()
        self.close()


class ChangeXDialog(QDialog):
    """
    Open a window to asking the user for plotting options for normal plotting.

    Attributes
    ----------
    plot_options : PlotOptions
        PlotOptions instance containing reactant, target, mole_bal,
        figsize, savedata, switch_to_hours as attributes
    overwrite : bool
        User input for whether or not to overwrite existing data.
    """

    def __init__(self):
        """
        Create widgets, add to window, connect accept button.

        Returns
        -------
        None.

        """
        super().__init__()
        self.setWindowTitle('Enter Plotting Instructions')

        # Create widgets for window
        self.layout = QGridLayout(self)
        self.basic_options_layout = PlotOptionsLayout()
        self.xdata_entry = QLineEdit('[x1, x2, x3, x4, ...]')
        self.xdata_label = QLabel('Enter array for new X data')
        self.units_entry = QLineEdit('H2/C2H2')
        self.units_label = QLabel('Enter New X Units')
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                          | QDialogButtonBox.Cancel)

        # Connect accept button to accept function
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Add widgets to window layout
        self.layout.addWidget(self.xdata_label, 1, 0)
        self.layout.addWidget(self.xdata_entry, 1, 1)
        self.layout.addLayout(self.basic_options_layout, 2, 0, 1, 2)
        self.layout.addWidget(self.buttonBox, 3, 0, 1, 2, Qt.AlignCenter)

    def accept(self):
        """Record user entries as attributes and close window."""
        self.xdata = self.xdata_entry.currentText()
        self.units = self.units_entry.currentText()
        self.plot_options = self.basic_options_layout.get_inputs()
        super(ChangeXDialog, self).accept()
        self.close()


class MultiplotDialog(QDialog):
    """
    Open a window to asking the user for plotting options for multiplotting.

    Attributes
    ----------
    plot_options : PlotOptions
        PlotOptions instance containing reactant, target, mole_bal,
        figsize, savedata, switch_to_hours as attributes
    XandS : bool
        Radiobutton result. True to plot conversion and selectivity plots.
    XvsS : bool
        RadioButton result. True to plot selectivity as function of conversion.
    """

    def __init__(self):
        """
        Create widgets, add to window, connect accept button.

        Returns
        -------
        None.

        """
        super().__init__()
        self.setWindowTitle('Enter Plotting Instructions')

        # Create widgets for window
        self.layout = QGridLayout(self)
        self.basic_options_layout = PlotOptionsLayout(include_mole_bal=False,
                                                      include_savedata=False,
                                                      include_switchtohours=False)
        self.XandS_button = QRadioButton()
        self.XvsS_button = QRadioButton()
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                          | QDialogButtonBox.Cancel)

        # Connect accept button to accept function
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Add widgets to window layout
        self.layout.addWidget(QLabel('Plot Conversion and Selectivity (2 plots)'), 0, 0)
        self.layout.addWidget(QLabel('Plot Selectivity vs Conversion (1 plot)'), 1, 0)
        self.layout.addWidget(self.XandS_button, 0, 1)
        self.layout.addWidget(self.XvsS_button, 1, 1)
        self.layout.addLayout(self.basic_options_layout, 2, 0, 1, 2)
        self.layout.addWidget(self.buttonBox, 3, 0, 1, 2, Qt.AlignCenter)

    def accept(self):
        """Record user entries as attributes and close window."""
        self.XandS = self.XandS_button.isChecked()
        self.XvsS = self.XvsS_button.isChecked()
        self.plot_options = self.basic_options_layout.get_inputs()
        super(MultiplotDialog, self).accept()
        self.close()


class CalDialog(QDialog):
    """
    Open a window to asking the user for plotting options for normal plotting.

    Attributes
    ----------
    force_zero : bool
        Add point (x=0, y=0) to data set.
     figsize : tuple
         Desired size of output figure in inches (x,y).
    """

    def __init__(self):
        """
        Create widgets, add to window, connect accept button.

        Returns
        -------
        None.

        """
        super().__init__()
        self.setWindowTitle('Enter Plotting Instructions')

        # Create widgets for window
        self.layout = QGridLayout(self)
        self.forcezero_entry = QComboBox()
        self.figsize_entry = QComboBox()
        self.figsize_label = QLabel('Figure Size (x, y)')
        self.forcezero_label = QLabel('Include (0, 0) in fit?')
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                          | QDialogButtonBox.Cancel)

        # Edit ComboBox features
        self.forcezero_entry.addItems(['True', 'False'])
        self.figsize_entry.addItems(['(4.35, 3.25)', '(5, 3.65)',
                                     '(6.5, 4.5)', '(9, 6.65)'])
        self.figsize_entry.setEditable(True)
        figsize_tip = ('Desired size of output figure in inches (x,y),\n'
                       'figsize suggestions:\n'
                       '1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);\n'
                       '1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);')
        self.figsize_entry.setToolTip(figsize_tip)

        # Connect accept button to accept function
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Add widgets to window layout
        self.layout.addWidget(self.forcezero_label, 1, 0)
        self.layout.addWidget(self.forcezero_entry, 1, 1)
        self.layout.addWidget(self.figsize_label, 2, 0)
        self.layout.addWidget(self.figsize_entry, 2, 1)
        self.layout.addWidget(self.buttonBox, 3, 0, 1, 2, Qt.AlignCenter)

    def accept(self):
        """Record user entries as attributes and close window."""
        self.forcezero = eval(self.forcezero_entry.currentText())
        self.figsize = eval(self.figsize_entry.currentText())
        super(CalDialog, self).accept()
        self.close()

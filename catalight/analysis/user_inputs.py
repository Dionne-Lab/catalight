r"""
Graphical user interface classes for helping user input parameters.

This module contains a number of UI classes that prompt the user to select
calibration files, data paths, and enter function parameters.
Created on Thu Jun 23 22:42:55 2022
@author: Briley Bourgeois

References
----------
(1) https://github.com/napari/magicgui/issues/9
(2) https://stackoverflow.com/questions/28544425/pyqt-qfiledialog-multiple-directory-selection
(3) https://stackoverflow.com/questions/38746002/pyqt-qfiledialog-directly-browse-to-a-folder
(4) https://stackoverflow.com/questions/4286036/how-to-have-a-directory-dialog
(5) https://stackoverflow.com/questions/38609516/hide-empty-parent-folders-qtreeview-qfilesystemmodel
(6) https://www.youtube.com/watch?v=dqg0L7Qw3ko
(7) https://stackoverflow.com/questions/52592977/how-to-return-variables-from-pyqt5-ui-to-main-function-python

"""
from __future__ import annotations
import os
import sys
from dataclasses import astuple, asdict, dataclass, fields, is_dataclass


import catalight.analysis.tools as analysis_tools
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialogButtonBox, QItemDelegate, QDialog,
                             QApplication, QTreeWidget, QAbstractItemView,
                             QGridLayout, QListView, QTreeView, QVBoxLayout,
                             QFileDialog, QFileSystemModel, QTreeWidgetItem,
                             QComboBox, QRadioButton, QLineEdit, QLabel,
                             QDoubleSpinBox)

# Not sure this is needed. can likely delete after testing
# you need to run Qapplication before initiating these windows.
app = QApplication(sys.argv)
#app.setApplicationName('Select the data you want to be plotted')


class DirectorySelector(QFileDialog):
    """
    Open a file dialog that allows selection of multiple directories.

    We use this function instead of regular QFileDialog because
    this lets us select multiple folders. Updates selection mode.

    Parameters
    ----------
    starting_dir : str, optional
        Path in which to start search. The default is None.

    """

    def __init__(self, starting_dir=None):
        super().__init__()
        self.setWindowTitle('Choose Directories')
        self.setGeometry(50, 100, 1800, 800)
        self.setViewMode(1)
        self.setOption(QFileDialog.DontUseNativeDialog, True)
        self.setFileMode(QFileDialog.DirectoryOnly)
        if starting_dir is not None:
            self.setDirectory(starting_dir)

        # This loop cycles through dialog and sets multi-item selection
        for view in self.findChildren((QListView, QTreeView)):
            if isinstance(view.model(), QFileSystemModel):
                view.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def get_output(self):
        """Return list of selected directories."""
        return self.selectedFiles()

@dataclass
class Option():
    """
    Generic option to use when building plotting dialogs.
    """
    value: tuple | bool | float | str  #: User supplied value
    include: bool  #: Indicates whether or not to include GUI element
    label: str  #: String for constructing QLabel(label)
    tooltip: str  #: String for widget tooltip
    widget: QComboBox | QDoubleSpinBox | QLineEdit | QRadioButton
    #: Widget used for entering option values


@dataclass
class PlotOptionList():
    """
    Starting list of options to use when building plotting dialogs.

    General purpose label, tooltips, and default values are already included.
    When utilizing this class, you need to "turn on" GUI elements by setting
    individual Option instances to Option.include = True. This is made easier
    with the change_includes() method.
    """

    _reactant_tip = ('String identity of reactant molecule to track.\nMust '
                     'match what exists in the calibration file exactly.')
    _target_tip = ('String identity of the target to use when calculating '
                   'selectivity.\nMust match what exists in the calibration '
                   'file exacly.')
    _mole_bal_tip = ('Code will perform a mole balance for the element prov'
                     'ided.\nThe default is \'c\'. (i.e. carbon balance)')
    _figsize_tip = ('Desired size of output figure in inches (x,y),\n'
                    'figsize suggestions:\n'
                    '1/2 slide = (6.5, 4.5);  1/6 slide = (4.35, 3.25);\n'
                    '1/4 slide =  (5, 3.65); Full slide =    (9, 6.65);')

    reactant: Option = Option('', False, 'Reactant', _reactant_tip, QLineEdit())
    target_molecule: Option = Option('', False, 'Target Molecule', _target_tip,
                                     QLineEdit())
    mole_bal: Option = Option('c', False, 'Mole Balance Element', _mole_bal_tip,
                              QLineEdit())
    figsize: Option = Option((6.5, 4.5), False, 'Figure Size (x, y)',
                             _figsize_tip, QComboBox())
    savedata: Option = Option(True, False, 'Save Data? (T/F)',
                              'Save Data? T/F', QComboBox())
    switch_to_hours: Option = Option(2, False,
                                     'Time to switch units to hours (hr)',
                                     'Time in hour to switch x axis unit',
                                     QDoubleSpinBox())
    overwrite: Option = Option(False, False,
                               'Overwrite previous calculations?',
                               None, QComboBox())
    basecorrect: Option = Option(True, False, 'Add baseline correction?',
                                  None, QComboBox())
    xdata: Option = Option('[x1, x2, x3, ...]', False,
                           'Enter array for new X data', 'Alice', QLineEdit())
    units: Option = Option('H2/C2H2', False, 'Enter New X Units',
                           None, QLineEdit())
    XandS: Option = Option(False, False,
                           'Plot Conversion and Selectivity (2 plots)',
                           'True to plot conversion and selectivity plots.',
                           QRadioButton())
    XvsS: Option = Option(False, False,
                          'Plot Selectivity vs Conversion (1 plot)',
                          'True plots selectivity as function of conversion.',
                          QRadioButton())
    forcezero: Option = Option(True, False, 'Include (0, 0) in fit?',
                               'Add point (x=0, y=0) to data set.',
                               QComboBox())

    def __iter__(self):
        """
        If the user hasn't modified the attributes, unpacks individual Options.

        Raises
        ------
        TypeError
            Raises type error if user somehow changes data type of class.

        Returns
        -------
        iterator?
            Returns iterator of instance attributes like unpacking with *tuple.
            If the user hasn't modified the attributes, this will unpack
            individual Option instances.
        """
        if not is_dataclass(self):
            raise TypeError(f"This mixin is dataclass-only,"
                            f"which {type(self)} isn't.")
        return (getattr(self, field.name) for field in fields(self))

    def change_includes(self, option_toggle_dict):
        """
        Set individual options on/off in one command using a dict.

        Parameters
        ----------
        option_toggle_dict : dict
            {field: bool} Use this to set individual
            Options on/off in one command.

        Returns
        -------
        None.

        """
        for key, value in option_toggle_dict.items():
            getattr(self, key).include = value

    def values_todict(self, get_all=False):
        """
        Return dict of values for active Options.

        Parameters
        ----------
        get_all : bool, optional
            Setting to True returns values for hidden GUI elements.
            The default is False.

        Returns
        -------
        values_dict : dict
            {field: value} User supplied values for fields based on GUI entry.

        """

        values_dict = {}
        for field in fields(self):
            key = field.name
            option = getattr(self, key)
            value = option.value

            if option.include or get_all:
                values_dict[key] = value

        return values_dict


class PlotOptionsDialog(QDialog):
    """
    Dynamic dialog window displaying options based on input parameters.

    Supply an instance of PlotOptionList with .include attr turned on for the
    desired GUI elements. When the user presses ok, the PlotOptionList instance
    will have its values updated based on the GUI values provided.

    Parameters
    ----------
    plot_options: PlotOptionList
        Instance of PlotOptionList for which the Option.include attr has been
        updated to True for all desired GUI elements.
    """

    def __init__(self, plot_options):
        super().__init__()
        self.setWindowTitle('Enter Plotting Instructions')

        # Create widgets for window
        self.layout = QGridLayout(self)
        self.options = plot_options
        row_num = 0
        for option in self.options:
            # Skip when Option.include=False
            if not option.include:
                continue

            # Get widgets from Option instance and update properties
            widget = option.widget
            widget.setToolTip(option.tooltip)
            if isinstance(widget, QComboBox):
                if isinstance(option.value, bool):
                    widget.addItems(['True', 'False'])
                if isinstance(option.value, tuple):
                    widget.addItems(['(4.35, 3.25)', '(5, 3.65)',
                                     '(6.5, 4.5)', '(9, 6.65)'])
                    widget.setEditable(True)
            # Add widgets to layout
            self.layout.addWidget(QLabel(option.label), row_num, 0)
            self.layout.addWidget(widget, row_num, 1)
            row_num += 1

        # Create Dialog buttons, connect, and add to window
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                          | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox, row_num, 0, 1, 2, Qt.AlignCenter)

    def accept(self):
        """
        Update Option.field.value for all GUI components included in instance.

        Returns
        -------
        None.

        """
        for option in self.options:
            if not option.include:
                continue
            widget = option.widget
            if isinstance(widget, QComboBox):
                option.value = eval(widget.currentText())
            elif isinstance(widget, QLineEdit):
                option.value = widget.text()
            elif isinstance(widget, QDoubleSpinBox):
                option.value = eval(widget.value())
            elif isinstance(widget, QRadioButton):
                option.value = widget.isChecked()
            else:
                print('widget changed to something incompatible')
        super(PlotOptionsDialog, self).accept()


class MyDelegate(QItemDelegate):
    """Use for sorting items."""

    def createEditor(self, parent, option, index):
        """Create editor."""
        if index.column() == 1:
            return super(MyDelegate, self).createEditor(parent, option, index)
        return None


class DataExtractor(QDialog):
    """
    User interface for selecting data folders.

    Sweeps the starting directory for matching datafiles, then opens a UI
    showing paths matching data_depth. The user can select which paths they'd
    like, and provide a label for that data set using a table and tree widget.

    Parameters
    ----------
    starting_dir : str, optional
        Main directory to initialize gui in. The default is None.
    target : str, optional
        String to identify as "has data". The default is 'avg_conc'.
    suffix : str, optional
        File type to search for. The default is '.csv'.
    data_depth : int, optional
        Depth between data and path to return. The default is 2.
        For example,

        ==========  ==============================================
        data_depth  path returned
        ==========  ==============================================
        0           user/reactions/experiment/Results/avg_conc.csv
        1           user/reactions/experiment/Results
        2           user/reactions/experiment
        ==========  ==============================================

    Returns
    -------
    None.
    """

    def __init__(self, starting_dir=None, target='avg_conc',
                 suffix='.csv', data_depth=2):
        """Initialize extraction gui."""
        # Can be used if this dialog needs to interact with parent
        # super(DataExtractor, self).__init__(parent)
        super().__init__()

        # Define input parameters as attributes
        self.starting_dir = starting_dir
        # String to find partial match with
        self.target = target
        self.suffix = suffix
        # Seperation between data and folder to display
        self.data_depth = data_depth

        self.initLayout()
        self.get_expt_dirs()

    def initLayout(self):
        """Initialize layout of GUI."""
        self.setWindowTitle('Select data to be plotted')
        self.setGeometry(50, 50, 1200, 600)
        # Create the treeWidget, populated when get_expt_dirs is run
        delegate = MyDelegate()
        self.treeWidget = QTreeWidget(self)
        self.treeWidget.setItemDelegate(delegate)
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setHeaderLabels(['Name', 'Data Label'])

        # create other buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                          | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.cancel)

        # arrange the GUI
        self.gridLayout = QGridLayout()
        self.gridLayout.addWidget(self.buttonBox, 0, 0)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.treeWidget)
        self.layout.addLayout(self.gridLayout)

    def populateTree(self, dataset):
        """
        Display files in a selection gui allowing user to pick relvant files.

        The path shown in the selection tree will be altered by self.data_depth

        Parameters
        ----------
        dataset : list
            list of strings containing paths to data files
        """
        tree_root = (None, {})
        for f in dataset:
            # Append (../*n) to move folder depth desired number of levels
            # Named folder is the folder you want displayed when choosing data
            file_depth_modifier = '/'.join(['..'] * self.data_depth)
            named_folder = os.path.abspath(os.path.join(f, file_depth_modifier))
            sample_str = os.path.relpath(named_folder,
                                         os.path.dirname(self.pathRoot))
            parts = sample_str.split('\\')
            node = tree_root

            for i, p in enumerate(parts):
                if p != '':
                    if p not in node[1]:
                        node[1][p] = (QTreeWidgetItem(node[0]), {})
                        # Changing setText to zero keeps name in 'one' column
                        node[1][p][0].setText(0, p)

                        if i == len(parts) - 1:  # If bottom item
                            node[1][p][0].setCheckState(0, Qt.Unchecked)
                            node[1][p][0].setFlags(node[1][p][0].flags() | Qt.ItemIsEditable)
                    node = node[1][p]

        # Add top level items
        for node in tree_root[1].values():
            self.treeWidget.addTopLevelItem(node[0])
        self.treeWidget.expandAll()
        for n in range(2):
            self.treeWidget.resizeColumnToContents(n)

    def getParentPath(self, item):
        """Get parent path of item."""
        def getParent(item, outstring):
            if item.parent() is None:
                return outstring
            outstring = item.parent().text(0) + '/' + outstring
            return getParent(item.parent(), outstring)
        output = getParent(item, item.text(0))
        return output

    def get_expt_dirs(self):
        """
        Open file dialog and let user select directories to analyze.

        Then finds files matching target and suffix provided and calls
        populateTree() using those filepaths. Updates pathRoot.

        Returns
        -------
        None.

        """
        selector = DirectorySelector(self.starting_dir)
        if selector.exec_() == QDialog.Accepted:
            expt_dirs = selector.get_output()
        print(expt_dirs)
        filepaths = analysis_tools.list_matching_files(expt_dirs, self.target,
                                                       self.suffix)
        print(filepaths)
        self.pathRoot = os.path.dirname(expt_dirs[0])
        # function populates tree items based on matching criteria specified
        self.populateTree(filepaths)

    def accept(self):
        """Redefine accept button."""
        file_list = []
        data_labels = []
        for item in self.treeWidget.findItems("", Qt.MatchContains
                                              | Qt.MatchRecursive):
            if item.checkState(0) == Qt.Checked:
                # drop end of pathRoot, to not have it twice
                file_list.append(os.path.join(os.path.dirname(self.pathRoot),
                                              self.getParentPath(item)))
                data_labels.append((item.text(1)))
        self._output = (file_list, data_labels)
        print(self._output)
        super(DataExtractor, self).accept()

    def cancel(self):
        """Restart init at picking starting directory."""
        self.get_expt_dirs()

    def get_output(self):
        """
        Get GUI input values.

        Returns
        -------
        (file_list, data_labels) : tuple
            Where file_list is the full path to the files specified by input
            parameters and data_labels is the matching strings provided in the
            GUI.
        """
        return self._output


if __name__ == "__main__":

    app = QApplication(sys.argv)
    main = DataExtractor()
    # main.move(app.desktop().screen().rect().center() - main.rect().center())
    main.show()
    sys.exit(app.exec())

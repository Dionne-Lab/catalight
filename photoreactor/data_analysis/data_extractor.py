"""
Open user interface to select data.

Created on Thu Jun 23 22:42:55 2022

@author: Briley Bourgeois

References
----------
[1] https://github.com/napari/magicgui/issues/9
[2] https://stackoverflow.com/questions/28544425
/pyqt-qfiledialog-multiple-directory-selection
[3] https://stackoverflow.com/questions/38746002
/pyqt-qfiledialog-directly-browse-to-a-folder
[4] https://stackoverflow.com/questions/4286036/how-to-have-a-directory-dialog
[5] https://stackoverflow.com/questions/38609516
/hide-empty-parent-folders-qtreeview-qfilesystemmodel
[6] https://www.youtube.com/watch?v=dqg0L7Qw3ko
[7] https://stackoverflow.com/questions/52592977
/how-to-return-variables-from-pyqt5-ui-to-main-function-python
"""
import os
import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem

# Not sure this is needed. can likely delete after testing
# app = QtWidgets.QApplication(sys.argv)
# app.setApplicationName('Select the data you want to be plotted')


class MyDelegate(QtWidgets.QItemDelegate):
    """Use for sorting items."""

    def createEditor(self, parent, option, index):
        """Create editor."""
        if index.column() == 1:
            return super(MyDelegate, self).createEditor(parent, option, index)
        return None


class DataExtractor(QtWidgets.QDialog):
    """File dialog for selecting data folders."""

    def __init__(self, starting_dir=None, target='avg_conc.csv',
                 data_depth=2, parent=None):
        """
        Initialize extraction gui.

        Parameters
        ----------
        starting_dir : str, optional
            Main directory to initialize gui in. The default is None.
        target : str, optional
            string to identify as "hass data". The default is 'avg_conc.csv'.
        data_depth : int, optional
            depth between data and folder to display. The default is 2.
        parent : TYPE, optional
            DESCRIPTION. The default is None.

        Returns
        -------
        None.

        """
        # super(DataExtractor, self).__init__(parent)
        super().__init__()
        self.setWindowTitle('Select data to be plotted')
        # String to find partial match with
        self.target = target
        # Seperation between data and folder to display
        self.data_depth = data_depth
        # I editted this line to bring up file dialog to set start point
        expt_dirs = self.handleChooseDirectories(starting_dir)

        # This is the section that creates the treeWidget and populates
        delegate = MyDelegate()
        self.treeWidget = QTreeWidget(self)
        self.treeWidget.setItemDelegate(delegate)
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setHeaderLabels(['Name', 'Data Label'])

        # function populates tree items based on matching criteria specified
        self.populateTree(self.getMatchingFiles(expt_dirs))
        self.setGeometry(50, 50, 1200, 600)
        self.initLayout()

    def handleChooseDirectories(self, starting_dir=None):
        """
        Set alternate file dialog.

        We use this function instead of regular QFileDialog because
        this lets us select multiple folders. Updates selection mode.

        Parameters
        ----------
        starting_dir : str, optional
            path in which to start search. The default is None.

        Returns
        -------
        expt_dirs : list
            list of strings containing matching paths
        """
        dialog = QtWidgets.QFileDialog(self)
        dialog.setWindowTitle('Choose Directories')
        dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        if starting_dir is not None:
            dialog.setDirectory(starting_dir)
        dialog.setGeometry(50, 100, 1800, 800)
        dialog.setViewMode(1)

        # This loop cycles through dialog and sets multi-item selection
        for view in dialog.findChildren((QtWidgets.QListView,
                                         QtWidgets.QTreeView)):

            if isinstance(view.model(), QtWidgets.QFileSystemModel):
                view.setSelectionMode(
                    QtWidgets.QAbstractItemView.ExtendedSelection)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            expt_dirs = dialog.selectedFiles()
            return expt_dirs

    def getMatchingFiles(self, expt_dirs):
        """
        Get files matching self.target within selected directories.

        Parameters
        ----------
        expt_dirs : list
            list of strings containing paths to directories containing data

        Returns
        -------
        dataset : list
            list of strings containing paths to
            actual data files within expt_dirs
        """
        self.pathRoot = os.path.dirname(expt_dirs[0])
        dataset = []
        for root in expt_dirs:
            for dirpath, dirnames, filenames in os.walk(root):
                for filename in filenames:
                    if self.target in filename:
                        dataset.append(os.path.join(dirpath, filename))
        return dataset

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

    def initLayout(self):
        """Initialize layout of GUI."""
        # create other buttons
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.cancel)

        # arrange the GUI
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.addWidget(self.buttonBox, 0, 0)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.treeWidget)
        self.layout.addLayout(self.gridLayout)

    def getParentPath(self, item):
        """Get parent path of item."""
        def getParent(item, outstring):
            if item.parent() is None:
                return outstring
            outstring = item.parent().text(0) + '/' + outstring
            return getParent(item.parent(), outstring)
        output = getParent(item, item.text(0))
        return output

    def accept(self):
        """Redefine accept button."""
        file_list = []
        data_labels = []
        for item in self.treeWidget.findItems("", Qt.MatchContains | Qt.MatchRecursive):
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
        self.treeWidget.clear()
        expt_dirs = self.handleChooseDirectories()
        # function populates tree items based on matching criteria specified
        self.populateTree(self.getMatchingFiles(expt_dirs))

    def get_output(self):
        """Return output of object."""
        return self._output


if __name__ == "__main__":

    app = QApplication(sys.argv)
    main = DataExtractor()
    # main.move(app.desktop().screen().rect().center() - main.rect().center())
    main.show()
    sys.exit(app.exec())

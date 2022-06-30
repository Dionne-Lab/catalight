# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 22:42:55 2022

@author: brile
https://github.com/napari/magicgui/issues/9
https://stackoverflow.com/questions/28544425/pyqt-qfiledialog-multiple-directory-selection
https://stackoverflow.com/questions/38746002/pyqt-qfiledialog-directly-browse-to-a-folder
https://stackoverflow.com/questions/4286036/how-to-have-a-directory-dialog
https://stackoverflow.com/questions/38609516/hide-empty-parent-folders-qtreeview-qfilesystemmodel
https://www.youtube.com/watch?v=dqg0L7Qw3ko
https://stackoverflow.com/questions/52592977/how-to-return-variables-from-pyqt5-ui-to-main-function-python
"""
import re, os, sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileSystemModel, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import QSortFilterProxyModel, QDir, Qt

app = QtWidgets.QApplication(sys.argv)
app.setApplicationName('Select the data you want to be plotted')

class MyDelegate(QtWidgets.QItemDelegate):

    def createEditor(self, parent, option, index):
        if index.column() == 1:
            return super(MyDelegate, self).createEditor(parent, option, index)
        return None

class DataExtractor(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(DataExtractor, self).__init__(parent)

        # I editted this line to bring up file dialog to set start point
        starting_dir = r"G:\Shared drives\Photocatalysis Projects\AgPd Polyhedra\Ensemble Reactor"
        expt_dirs = self.handleChooseDirectories(starting_dir)

        # This is the section that creates the treeWidget and populates
        delegate = MyDelegate()
        self.treeWidget = QTreeWidget(self)
        self.treeWidget.setItemDelegate(delegate)
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setHeaderLabels(['Name', 'Data Label'])

        # function populates tree items based on matching criteria specified
        self.populateTree(self.getMatchingFiles(expt_dirs))
        self.setGeometry(50, 50, 1800, 800)
        self.initLayout()

    def handleChooseDirectories(self, starting_dir=None):
        '''we use this function instead of regular QFileDialog because
        this lets us select multiple folders'''
        dialog = QtWidgets.QFileDialog(self)
        dialog.setWindowTitle('Choose Directories')
        dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        if starting_dir is not None:
            dialog.setDirectory(starting_dir)
        dialog.setGeometry(50, 100, 1800, 800)
        dialog.setViewMode(1)
        for view in dialog.findChildren(
            (QtWidgets.QListView, QtWidgets.QTreeView)):
            if isinstance(view.model(), QtWidgets.QFileSystemModel):
                view.setSelectionMode(
                    QtWidgets.QAbstractItemView.ExtendedSelection)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            expt_dirs = dialog.selectedFiles()
            return expt_dirs


    def getMatchingFiles(self, expt_dirs):
        self.pathRoot = os.path.dirname(expt_dirs[0])
        dataset = []
        for root in expt_dirs:
            for dirpath, dirnames, filenames in os.walk(root):
                for filename in filenames:
                    if filename == 'avg_conc.csv':
                        dataset.append(os.path.join(dirpath, filename))
        return dataset

    def populateTree(self, dataset):
        tree_root = (None, {})
        for f in dataset:
            gparent = os.path.abspath(os.path.join(f ,"../.."))
            sample_str = os.path.relpath(gparent,
                                         os.path.dirname(self.pathRoot))
            parts = sample_str.split('\\')
            node = tree_root

            for i, p in enumerate(parts):
                if p != '':
                    if p not in node[1]:
                        node[1][p] = (QTreeWidgetItem(node[0]), {})
                        # Changing setText to zero keeps name in 'one' column
                        node[1][p][0].setText(0, p)

                        if i == len(parts)-1: # If bottom item
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
        # create other buttons
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # arrange the GUI
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.addWidget(self.buttonBox, 0, 0)


        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.treeWidget)
        self.layout.addLayout(self.gridLayout)

    def getParentPath(self, item):
        def getParent(item, outstring):
            if item.parent() is None:
                return outstring
            outstring = item.parent().text(0) + '/' + outstring
            return getParent(item.parent(), outstring)
        output = getParent(item, item.text(0))
        return output

    def accept(self):
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

    def reject(self):
        '''restarts init at picking starting directory'''
        self.treeWidget.clear()
        expt_dirs = self.handleChooseDirectories()
        # function populates tree items based on matching criteria specified
        self.populateTree(self.getMatchingFiles(expt_dirs))

    def get_output(self):
        return self._output


if __name__ == "__main__":

    main = DataExtractor()
    main.move(app.desktop().screen().rect().center() - main.rect().center())
    main.show()

    sys.exit(app.exec_())

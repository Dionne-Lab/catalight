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
"""
import re, os, sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileSystemModel, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import QSortFilterProxyModel, QDir, Qt

class MyDelegate(QtWidgets.QItemDelegate):

    def createEditor(self, parent, option, index):
        if index.column() == 1:
            return super(MyDelegate, self).createEditor(parent, option, index)
        return None

class MyWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)

        # This is the section that creates the treeView
        # I editted this line to bring up file dialog to set start point
        #self.pathRoot = self.handleChooseDirectories()
        expt_dirs = self.handleChooseDirectories()
        self.pathRoot = os.path.dirname(expt_dirs[0])
        dataset = []
        for root in expt_dirs:
            for dirpath, dirnames, filenames in os.walk(root):
                for filename in filenames:
                    if filename == 'avg_conc.csv':
                        dataset.append(os.path.join(dirpath, filename))

        delegate = MyDelegate()
        self.treeWidget = QTreeWidget(self)
        self.treeWidget.setItemDelegate(delegate)
        n_columns = np.max([f.count('/') for f in dataset])
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setHeaderLabels(['Name', 'Data Label'])
        tree_root = (None, {})
        for f in dataset:
            #gparent = os.path.dirname(dirpath)
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
        for n in range(n_columns):
            self.treeWidget.resizeColumnToContents(n)

        # # this section is for setting up the text lines at top
        # self.labelFileName = QtWidgets.QLabel(self)
        # self.labelFileName.setText("File Name:")

        # self.lineEditFileName = QtWidgets.QLineEdit(self)

        # self.labelFilePath = QtWidgets.QLabel(self)
        # self.labelFilePath.setText("File Path:")

        # self.lineEditFilePath = QtWidgets.QLineEdit(self)
        self.butFin = QtWidgets.QPushButton('Done')
        self.butFin.clicked.connect(self.finished)

        # # this section arranges the GUI
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.addWidget(self.butFin, 0, 0)
        # self.gridLayout.addWidget(self.labelFileName, 0, 0)
        # self.gridLayout.addWidget(self.lineEditFileName, 0, 1)
        # self.gridLayout.addWidget(self.labelFilePath, 1, 0)
        # self.gridLayout.addWidget(self.lineEditFilePath, 1, 1)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.treeWidget)
        self.layout.addLayout(self.gridLayout)


    def handleChooseDirectories(self):
            dialog = QtWidgets.QFileDialog(self)
            dialog.setWindowTitle('Choose Directories')
            dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
            dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            dialog.setDirectory(r"G:\Shared drives\Photocatalysis Projects\AgPd Polyhedra\Ensemble Reactor")
            dialog.setGeometry(50, 100, 1800, 800)
            dialog.setViewMode(1)
            for view in dialog.findChildren(
                (QtWidgets.QListView, QtWidgets.QTreeView)):
                if isinstance(view.model(), QtWidgets.QFileSystemModel):
                    view.setSelectionMode(
                        QtWidgets.QAbstractItemView.ExtendedSelection)

            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                return dialog.selectedFiles()
            dialog.deleteLater()

    def getParentPath(self, item):
        def getParent(item, outstring):
            if item.parent() is None:
                return outstring
            outstring = item.parent().text(0) + '/' + outstring
            return getParent(item.parent(), outstring)
        output = getParent(item, item.text(0))
        return output

    def finished(self):
        file_list = []
        data_labels = []
        for item in self.treeWidget.findItems("", Qt.MatchContains | Qt.MatchRecursive):
            if item.checkState(0) == Qt.Checked:
                file_list.append(os.path.join(self.pathRoot,
                                              self.getParentPath(item)))
                data_labels.append((item.text(1)))
        print(file_list)
        print(data_labels)
        return file_list, data_labels


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('MyWindow')

    main = MyWindow()
    main.setGeometry(50, 50, 1800, 800)
    main.move(app.desktop().screen().rect().center() - main.rect().center())
    main.show()

    sys.exit(app.exec_())

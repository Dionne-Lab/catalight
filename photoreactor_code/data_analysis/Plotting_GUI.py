# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 19:03:12 2022

https://stackoverflow.com/questions/4286036/how-to-have-a-directory-dialog
https://stackoverflow.com/questions/38609516/hide-empty-parent-folders-qtreeview-qfilesystemmodel


@author: brile
"""

import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtCore import QSortFilterProxyModel, QDir

class DirProxy(QSortFilterProxyModel):
    nameFilters = ''
    def __init__(self):
        super().__init__()
        self.dirModel = QFileSystemModel()
        self.dirModel.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files) # <- added QDir.Files to view all files
        self.setSourceModel(self.dirModel)

    def setNameFilters(self, filters):
        if not isinstance(filters, (tuple, list)):
            filters = [filters]
        self.nameFilters = filters
        self.invalidateFilter()

    def hasChildren(self, parent):
        sourceParent = self.mapToSource(parent)
        if not self.dirModel.hasChildren(sourceParent):
            return False
        qdir = QDir(self.dirModel.filePath(sourceParent))
        return bool(qdir.entryInfoList(qdir.NoDotAndDotDot|qdir.AllEntries|qdir.AllDirs))

    def filterAcceptsRow(self, row, parent):
        source = self.dirModel.index(row, 0, parent)
        if source.isValid():
            if self.dirModel.isDir(source):
                qdir = QDir(self.dirModel.filePath(source))
                if self.nameFilters:
                    qdir.setNameFilters(self.nameFilters)
                return bool(qdir.entryInfoList(qdir.NoDotAndDotDot|qdir.AllEntries|qdir.AllDirs))

            elif self.nameFilters:  # <- index refers to a file
                qdir = QDir(self.dirModel.filePath(source))
                return qdir.match(self.nameFilters, self.dirModel.fileName(source)) # <- returns true if the file matches the nameFilters
        return True

class MyWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)

        # This is the section that creates the treeView
        # I editted this line to bring up file dialog to set start point
        self.pathRoot = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")

        self.model = DirProxy()
        self.model.dirModel.directoryLoaded.connect(lambda : self.treeView.expandAll())
        self.model.dirModel.setRootPath(self.pathRoot)
        self.model.setNameFilters(['*.csv'])  # <- filtering all files and folders with "*.ai"


        #self.model = QtWidgets.QFileSystemModel(self)
        #self.model.setRootPath(self.pathRoot)
        #self.model.setNameFilters(['*.csv'])
        self.indexRoot = self.model.dirModel.index(self.model.dirModel.rootPath())
        # Original
        # self.indexRoot = self.model.index(self.model.rootPath())
        #self.model.setNameFilterDisables(False)

        self.treeView = QtWidgets.QTreeView(self)
        self.treeView.setModel(self.model)
        # self.treeView.setRootIndex(self.indexRoot)
        # root_index = self.dirProxy.dirModel.index(r"<Dir>")
        proxy_index = self.model.mapFromSource(self.indexRoot)
        self.treeView.setRootIndex(proxy_index)
        self.treeView.clicked.connect(self.on_treeView_clicked)

        # this section is for setting up the text lines at top
        self.labelFileName = QtWidgets.QLabel(self)
        self.labelFileName.setText("File Name:")

        self.lineEditFileName = QtWidgets.QLineEdit(self)

        self.labelFilePath = QtWidgets.QLabel(self)
        self.labelFilePath.setText("File Path:")

        self.lineEditFilePath = QtWidgets.QLineEdit(self)

        # this section arranges the GUI
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.addWidget(self.labelFileName, 0, 0)
        self.gridLayout.addWidget(self.lineEditFileName, 0, 1)
        self.gridLayout.addWidget(self.labelFilePath, 1, 0)
        self.gridLayout.addWidget(self.lineEditFilePath, 1, 1)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.gridLayout)
        self.layout.addWidget(self.treeView)

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def on_treeView_clicked(self, index):
        indexItem = self.model.index(index.row(), 0, index.parent())

        fileName = self.model.fileName(indexItem)
        filePath = self.model.filePath(indexItem)

        self.lineEditFileName.setText(fileName)
        self.lineEditFilePath.setText(filePath)

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('MyWindow')

    main = MyWindow()
    main.resize(666, 333)
    main.move(app.desktop().screen().rect().center() - main.rect().center())
    main.show()

    sys.exit(app.exec_())

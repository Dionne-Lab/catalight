# -*- coding: utf-8 -*-
"""
Created on Sun Feb 20 18:45:10 2022

@author: brile
"""
import sys
from experiment_control import Experiment
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QWidget,
    QListWidgetItem)


experiment_list = []
# Subclass QMainWindow to customize your application's main window
class MainWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BruceJr")
        loadUi('reactorUI.ui', self)
        self.butAddExpt.clicked.connect(self.add_expt)
        self.butDelete.clicked.connect(self.delete_expt)
        self.listWidget.currentItemChanged.connect(self.display_expt)

    def add_expt(self):
        print('clicked!')
        item = QListWidgetItem('Bob\'s your uncle', self.listWidget)
        item.setData(Qt.UserRole, Experiment())

    def delete_expt(self):
        item = self.listWidget.currentItem()
        self.listWidget.takeItem(self.listWidget.row(item))

    def display_expt(self):
        item = self.listWidget.currentItem()
        print(item.data(Qt.UserRole).temp)


app = QApplication(sys.argv)
window = MainWindow()
window.show()

sys.exit(app.exec())

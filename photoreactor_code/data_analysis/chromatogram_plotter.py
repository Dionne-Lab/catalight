# -*- coding: utf-8 -*-
"""
Created on Mon Nov  7 13:33:04 2022

@author: brile
"""
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from PyQt5.uic import loadUi
from PyQt5.QtCore import (Qt, QTimer, QDateTime, QThreadPool, QObject, pyqtSignal)
from PyQt5.QtWidgets import (
    QPushButton,
    QLabel,
    QApplication,
    QDialog,
    QWidget,
    QListWidgetItem,
    QFileDialog,
    QDialogButtonBox,
    QAbstractItemView,
    QMainWindow)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi('chromatogram_plotter.ui', self)

        self.init_figs()
        self.file_browser = QFileDialog()

    def init_figs(self): # Initialize figure canvas and add to:
        # This is the Canvas Widget that displays the `figure`
        # It takes the `figure` instance as a parameter to __init__
        self.figure = plt.figure(figsize=(12,8))
        self.canvas = FigureCanvas(self.figure)
        self.verticalLayout.addWidget(self.canvas) # Study Overview

# Main
plt.close('all')
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())

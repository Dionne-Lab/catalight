"""
Graphical User Interface for scanning through chromatograms within a directory.

@authors: Claire Carlin, Briley Bourgeois
"""
import os
import sys

import pyqtgraph as pg
import numpy as np
from catalight.analysis.gcdata import GCData
import catalight.analysis.tools as analysis_tools
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QGridLayout,
                             QCheckBox, QComboBox, QListWidget, QFileDialog,
                             QApplication, QLineEdit, QLabel)

os.environ['QT_MAC_WANTS_LAYER'] = '1'
# function which updates graph based on highlighted list item


class MainWindow(QMainWindow):
    """Subclass QMainWindow to customize your application's main window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Use Arrow Keys to Cycle Chromatograms")

        # Create widgets
        self.layout = QVBoxLayout()
        self.widget = QWidget()  # Main widget
        self.listWidget = QListWidget()
        self.graphWidget = pg.PlotWidget()

        # Create options
        self.options_layout = QGridLayout()
        self.bc_box = QCheckBox("baseline correction?")
        self.int_box = QCheckBox("Plot integration bounds?")
        self.target_entry = QComboBox()
        self.target_entry.addItems(['FID', 'TCD'])
        self.suffix_entry = QLineEdit('.asc')
        self.target_label = QLabel('Data Type:')
        self.suffix_label = QLabel('File Ending:')

        # Assemble options to layout
        self.options_layout.addWidget(self.bc_box, 0, 0)
        self.options_layout.addWidget(self.int_box, 1, 0)
        self.options_layout.addWidget(self.target_label, 0, 1)
        self.options_layout.addWidget(self.target_entry, 1, 1)
        self.options_layout.addWidget(self.suffix_label, 0, 2)
        self.options_layout.addWidget(self.suffix_entry, 1, 2)

        # Add widgets to layout
        self.layout.addWidget(self.listWidget)
        self.layout.addLayout(self.options_layout)
        self.layout.addWidget(self.graphWidget)

        # Add layout to window
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        # Connect Signals/Slots
        # Update which plot shows up to be whichever is highlighted
        self.listWidget.currentItemChanged.connect(self.update_plot)
        self.target_entry.currentTextChanged.connect(self.get_files)
        self.suffix_entry.editingFinished.connect(self.get_files)
        self.bc_box.clicked.connect(self.update_plot)
        self.int_box.clicked.connect(self.update_plot)

        # Get main directory containing data files
        self.folderpath = QFileDialog \
            .getExistingDirectory(None, 'Select folder containing data')
        self.set_graph_style()
        self.get_files()
        self.init_plot()

    def get_files(self):
        """List user's desired files and add to listWidget."""
        # Populate list with all datafiles in selected folder based on options
        filematch_args = ([self.folderpath],
                          self.target_entry.currentText(),
                          self.suffix_entry.text())
        self.filelist = analysis_tools.list_matching_files(*filematch_args)
        if not self.filelist:
            print('No matching files found in folder')
        self.listWidget.clear()  # Make sure widget is empty
        self.listWidget.addItems(self.filelist)

    def init_plot(self):
        """Pull first data file and add to plot."""
        # Make the first file in the list appear as the plot upon opening
        # Get data from filepath
        path = self.listWidget.item(0).text()
        data = GCData(path, basecorrect=False)
        datacorr = GCData(path, basecorrect=True)
        # Plot pulled data
        self.data_line = self.graphWidget.plot(data.time, data.signal,
                                               pen=self.pen1, name="raw")
        self.data_line_corr = self.graphWidget.plot(datacorr.time,
                                                    datacorr.signal,
                                                    pen=self.pen2,
                                                    name="corrected")
        self.data_line_left = self.graphWidget.plot([0],[0],pen=None, symbol='o', name="left indices")
        self.data_line_right = self.graphWidget.plot([0],[0],pen=None, symbol='o', name="right indices")
        self.data_line_apex = self.graphWidget.plot([0],[0],pen=None, symbol='o', name="apex indices")
        self.graphWidget.removeItem(self.data_line_corr)
        self.graphWidget.removeItem(self.data_line_left)
        self.graphWidget.removeItem(self.data_line_right)
        self.graphWidget.removeItem(self.data_line_apex)
        self.graphWidget.setTitle('Run 0:', color="k", size="18pt")

    def set_graph_style(self):
        """Update graph appearance."""
        # graph styling things
        self.graphWidget.addLegend(labelTextColor="k", labelTextSize="14pt")
        self.graphWidget.setBackground('w')
        styles = {'color': 'r', 'font-size': '18px'}
        self.graphWidget.setLabel('left', 'Counts', **styles)
        self.graphWidget.setLabel('bottom', 'Time (min)', **styles)
        self.graphWidget.getAxis('left').setTextPen('k')
        self.graphWidget.getAxis('bottom').setTextPen('k')
        pen = pg.mkPen(color=(0, 0, 0), width=2)
        self.graphWidget.plotItem.getAxis('left').setPen(pen)
        self.graphWidget.plotItem.getAxis('bottom').setPen(pen)
        self.graphWidget.plotItem.getAxis('right').setPen(pen)
        self.graphWidget.plotItem.getAxis('top').setPen(pen)

        # Pens for later plotting
        self.pen1 = pg.mkPen(color=(0, 102, 255), width=2)
        self.pen2 = pg.mkPen(color=(0, 153, 51), width=1)

    def update_plot(self):
        """Update plot with current listWidget item, if present."""
        if not self.listWidget.currentItem():
            print('No Items')
            self.graphWidget.clear()
            return

        path = self.listWidget.currentItem().text()
        data = GCData(path, basecorrect=False)
        datacorr = GCData(path, basecorrect=True)
        num = self.filelist.index(path)

        # Update title of graph
        self.graphWidget.setTitle("run " + str(num) + ":",
                                  color="k", size="18pt")

        # Update data, check if baseline correction is needed
        self.data_line.setData(data.time, data.signal,
                               pen=self.pen1, name="raw")
        if self.int_box.isChecked():
            if self.bc_box.isChecked():
                data_ind = datacorr
            else:
                data_ind = data
            if self.data_line_left not in self.graphWidget.listDataItems():
                self.graphWidget.addItem(self.data_line_left)
                self.graphWidget.addItem(self.data_line_right)
                self.graphWidget.addItem(self.data_line_apex)

            [left_idx, right_idx] = (np.rint(data_ind.lind).astype('int'), np.rint(data_ind.rind).astype('int'))
            apex_idx = data.apex_ind
            self.data_line_left.setData(data_ind.time[left_idx], data_ind.signal[left_idx],
                                        pen=None,symbolBrush=(216,27,96),
                                        symbol='o',symbolSize = 6,
                                        name="left indices")
            self.data_line_right.setData(data_ind.time[right_idx], data_ind.signal[right_idx],
                                        pen=None,symbolBrush=(42,164,56),
                                        symbol='o',symbolSize = 6)
            self.data_line_apex.setData(data_ind.time[apex_idx], data_ind.signal[apex_idx],
                                        pen=None,symbolBrush=(76,206,241),
                                        symbol='o',symbolSize = 6)

        else:
            self.graphWidget.removeItem(self.data_line_left)
            self.graphWidget.removeItem(self.data_line_right)
            self.graphWidget.removeItem(self.data_line_apex)

        if self.bc_box.isChecked():
            if self.data_line_corr not in self.graphWidget.listDataItems() :
                self.graphWidget.addItem(self.data_line_corr)

            self.data_line_corr.setData(datacorr.time, datacorr.signal,
                                        pen=self.pen2, name="corrected")
        else:
            #self.data_line_corr.clear()
            self.graphWidget.removeItem(self.data_line_corr)


if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

import os
import sys  # We need sys so that we can pass argv to QApplication

import pyqtgraph as pg
from photoreactor.data_analysis.gcdata import GCData
from photoreactor.data_analysis import analysis_tools
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QColor, QPalette
from pyqtgraph import PlotWidget, plot

os.environ['QT_MAC_WANTS_LAYER'] = '1'
# function which updates graph based on highlighted list item

class MainWindow(QMainWindow):
    """Subclass QMainWindow to customize your application's main window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Look Briley I did it")
        self.layout = QtWidgets.QVBoxLayout()
        self.bc_box = QtWidgets.QCheckBox("baseline correction?")
        self.listWidget = QtWidgets.QListWidget()
        self.graphWidget = pg.PlotWidget()
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)
        # put layout in the window
        self.layout.addWidget(self.listWidget)
        self.layout.addWidget(self.bc_box)
        self.layout.addWidget(self.graphWidget)
        self.set_graph_style()
        self.get_files()

    def get_files(self):
        # Have user select data folder
        self.folderpath = QtWidgets.QFileDialog \
            .getExistingDirectory(None, 'Select Folder')

        # Populate list with all .asc in selected folder
        # This is where you can specify what kind of files you want plotted
        self.filelist = analysis_tools.list_data_files(self.folderpath, 'FID')
        self.listWidget.addItems(self.filelist)
        # make the first file in the list appear as the plot upon opening
        self.filename = self.listWidget.item(0).text()
        # update which plot shows up to be whichever is highlighted
        # self.listWidget.currentItemChanged.connect(listitem_clicked)
        self.listWidget.currentItemChanged \
            .connect(lambda clickedItem: self.handle_trigger(clickedItem))
        self.init_plot()

    def init_plot(self):
        self.set_graph_style()
        # data we're pulling
        path = os.path.join(self.folderpath, self.filename)
        data = GCData(path, basecorrect=False)
        datacorr = GCData(path, basecorrect=True)
        self.data_line = self.graphWidget.plot(data.time, data.signal,
                                               pen=self.pen1, name="raw")
        self.data_line_corr = self.graphWidget.plot(datacorr.time,
                                                    datacorr.signal,
                                                    pen=self.pen2,
                                                    name="corrected")
        self.data_line_corr.clear()
        self.graphWidget.setTitle(self.filename, color="k", size="18pt")

    def set_graph_style(self):
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

    def handle_trigger(self, clickedItem):
        self.filename = self.listWidget.currentItem().text()
        path = os.path.join(self.folderpath, self.filename)
        data = GCData(path, basecorrect=False)
        datacorr = GCData(path, basecorrect=True)
        # TODO y not use getrunnum in analysis_tools()?
        num = self.filelist.index(self.filename)

        # Update title of graph
        self.graphWidget.setTitle("run " + str(num) + ": " + self.filename,
                                  color="k", size="18pt")

        # Update data, check if baseline correction is needed
        self.data_line.setData(data.time, data.signal,
                               pen=self.pen1, name="raw")
        if self.bc_box.isChecked():
            self.data_line_corr.setData(datacorr.time, datacorr.signal,
                                        pen=self.pen2, name="corrected")
        else:
            self.data_line_corr.clear()

if __name__ == "__main__":
    # make widget, label window, define layout
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

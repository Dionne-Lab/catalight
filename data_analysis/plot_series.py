from PyQt5 import QtWidgets, QtCore
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
from PyQt5.QtGui import QPalette, QColor
import sys  # We need sys so that we can pass argv to QApplication
import os
from gcdata import GCData
os.environ['QT_MAC_WANTS_LAYER'] = '1'

app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QWidget()
window.setWindowTitle("Look Briley I did it")
layout = QtWidgets.QVBoxLayout()

forward = QtWidgets.QPushButton("onward!")
layout.addWidget(forward)

forward.clicked.connect(forward_clicked)

#directory path
directory = "/Users/ccarlin/Documents/calibration/20220418calibration_273K_0.0mW_50sccm/Data/1 1.0CalGas_0.0Ar_0.0H2ppm"
chrom = "20201219_calibration1000ppm_FID04.ASC"
path = os.path.join(directory, chrom)
data = GCData(path, basecorrect=False)

# make graph widget
graphWidget = pg.PlotWidget()
#self.setCentralWidget(self.graphWidget)

# graph styling things
graphWidget.setTitle(chrom, color="k", size="18pt")
graphWidget.setBackground('w')
pen = pg.mkPen(color=(0, 102, 255), width=2)
data_line = graphWidget.plot(data.time, data.signal, pen=pen)
styles = {'color':'r', 'font-size':'18px'}
graphWidget.setLabel('left', 'Counts', **styles)
graphWidget.setLabel('bottom', 'Time (s)', **styles)
pen = pg.mkPen(color=(0, 0, 0), width=2)
graphWidget.plotItem.getAxis('left').setPen(pen)
graphWidget.plotItem.getAxis('bottom').setPen(pen)
graphWidget.plotItem.getAxis('right').setPen(pen)
graphWidget.plotItem.getAxis('top').setPen(pen)
graphWidget.getAxis('left').setTextPen('k')
graphWidget.getAxis('bottom').setTextPen('k')


layout.addWidget(graphWidget)


window.setLayout(layout)
window.show()


sys.exit(app.exec_())

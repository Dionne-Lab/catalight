from PyQt5 import QtWidgets, QtCore
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
from PyQt5.QtGui import QPalette, QColor
import sys  # We need sys so that we can pass argv to QApplication
import os
from gcdata import GCData

os.environ['QT_MAC_WANTS_LAYER'] = '1'
class Color(QtWidgets.QWidget):

    def __init__(self, color):
        super(Color, self).__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("look at this nice thing Claire made")

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        #self.rarrow = QtWidgets.QPushButton('Click me', self)
        #self.rarrow.resize(100,32)
        #self.rarrow.move(50, 50)
        #self.rarrow.clicked.connect(self.clickMethod)


        #directory path
        directory = "/Users/ccarlin/Documents/calibration/20220418calibration_273K_0.0mW_50sccm/Data/1 1.0CalGas_0.0Ar_0.0H2ppm"
        chrom = "20201219_calibration1000ppm_FID04.ASC"
        path = os.path.join(directory, chrom)
        data = GCData(path, basecorrect=False)

        # make graph widget
        self.graphWidget = pg.PlotWidget()
        #self.setCentralWidget(self.graphWidget)

        # graph styling things
        self.graphWidget.setTitle(chrom, color="k", size="18pt")
        self.graphWidget.setBackground('w')
        pen = pg.mkPen(color=(0, 102, 255), width=2)
        self.data_line = self.graphWidget.plot(data.time, data.signal, pen=pen)
        styles = {'color':'r', 'font-size':'18px'}
        self.graphWidget.setLabel('left', 'Counts', **styles)
        self.graphWidget.setLabel('bottom', 'Time (s)', **styles)
        pen = pg.mkPen(color=(0, 0, 0), width=2)
        self.graphWidget.plotItem.getAxis('left').setPen(pen)
        self.graphWidget.plotItem.getAxis('bottom').setPen(pen)
        self.graphWidget.plotItem.getAxis('right').setPen(pen)
        self.graphWidget.plotItem.getAxis('top').setPen(pen)
        self.graphWidget.getAxis('left').setTextPen('k')
        self.graphWidget.getAxis('bottom').setTextPen('k')

        w1 = Color('red')
        layout = QtWidgets.QVBoxLayout(central_widget)
        self.graphWidget.setMinimumWidth(30)

        layout.addWidget(self.graphWidget)
        layout.addWidget(w1)
        layout.addWidget(Color('green'))
        layout.addWidget(Color('blue'))
        layout.addWidget(Color('red'))



    def clickMethod(self):
        print('Clicked Pyqt button.')

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

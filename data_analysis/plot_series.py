from PyQt5 import QtWidgets, QtCore
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
from PyQt5.QtGui import QPalette, QColor
import sys  # We need sys so that we can pass argv to QApplication
import os
from gcdata import GCData
os.environ['QT_MAC_WANTS_LAYER'] = '1'

# function which updates graph based on highlighted list item
def listitem_clicked(clickedItem):
    chrom = clickedItem.text()
    path = os.path.join(folderpath, chrom)
    data = GCData(path, basecorrect = False)
    datacorr = GCData(path, basecorrect = True)
    num = runnumlist.index(chrom)
    graphWidget.setTitle("run "+str(num)+": "+chrom, color="k", size="18pt")
    data_line.setData(data.time, data.signal)

def btnstate(b):
    if b.isChecked() == True:
        pen = pg.mkPen(color=(0, 153, 51), width=2)
        graphWidget.plot(datacorr.time, datacorr.signal, pen=pen)
    else:
        print("not checked")


# make widget, label window, define layout
app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QWidget()
window.setWindowTitle("Look Briley I did it")
layout = QtWidgets.QVBoxLayout()

# have user select data folder
folderpath = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select Folder')

# populate list with all asc in selected folder
# LOOK HERE! This is where you can specify what kind of files you want plotted
listWidget = QtWidgets.QListWidget()
runnumlist = []
for filename in sorted(os.listdir(folderpath)):
    if filename.endswith(".ASC"):
        if "FID" in filename:
            runnumlist.append(filename)
            listWidget.addItem(filename)
layout.addWidget(listWidget)
chrom = listWidget.item(0).text() # make the first file in the list appear as the plot upon opnening
listWidget.currentItemChanged.connect(listitem_clicked) # update which plot shows up to be whichever is highlighted

#data we're pulling
path = os.path.join(folderpath, chrom)
data = GCData(path, basecorrect=False)
datacorr = GCData(path, basecorrect = True)

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

# add graph to layout
layout.addWidget(graphWidget)

bc_box = QtWidgets.QCheckBox("baseline correction?")
bc_box.toggled.connect(lambda:btnstate(bc_box))
layout.addWidget(bc_box)
# put layout in the window
window.setLayout(layout)
window.show()
sys.exit(app.exec_())

# -*- coding: utf-8 -*-
"""
Created on Sun Feb 20 18:45:10 2022

@author: brile
"""
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from experiment_control import Experiment
from equipment.sri_gc.gc_control import GC_Connector
#from equipment.diode_laser.diode_control import Diode_Laser
from equipment.harrick_watlow.heater_control import Heater
from equipment.alicat_MFC.gas_control import Gas_System
from equipment.alicat_MFC import gas_control
from PyQt5.uic import loadUi
from PyQt5.QtCore import (Qt, QTimer, QDateTime)
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QPushButton,
    QLabel,
    QApplication,
    QDialog,
    QWidget,
    QListWidgetItem,
    QFileDialog)


experiment_list = []
update_flag = False

# Subclass QMainWindow to customize your application's main window
class MainWindow(QDialog):
    def __init__(self):
        super().__init__()
        loadUi('reactorUI.ui', self)
        # TODO initialize equipment, print results to window
        # Connect Study Overview Tab Contents
        self.setWindowTitle("BruceJr")
        self.butAddExpt.clicked.connect(self.add_expt)
        self.butDelete.clicked.connect(self.delete_expt)
        self.listWidget.itemClicked.connect(self.display_expt)
        self.findCalFile.clicked.connect(self.select_cal_file)
        self.findCtrlFile.clicked.connect(self.select_ctrl_file)

        # Connect Experiment Design Tab Contents
        self.expt_types.currentIndexChanged.connect(self.update_expt)
        self.setTemp.valueChanged.connect(self.update_expt)
        self.setPower.valueChanged.connect(self.update_expt)
        self.setFlow.valueChanged.connect(self.update_expt)
        self.setSampleRate.valueChanged.connect(self.update_expt)  # This needs to have a min set by ctrl file
        self.setSampleSize.valueChanged.connect(self.update_expt)
        self.setRampRate.valueChanged.connect(self.update_expt)  # get from heater?
        # self.setBuffer.valueChanged.connect(self.update_expt)
        self.setGasAComp.valueChanged.connect(self.update_expt)
        self.setGasAType.currentIndexChanged.connect(self.update_expt)
        self.setGasBComp.valueChanged.connect(self.update_expt)
        self.setGasBType.currentIndexChanged.connect(self.update_expt)
        self.setGasCComp.valueChanged.connect(self.update_expt)
        self.setGasCType.currentIndexChanged.connect(self.update_expt)
        # lineEdit.editingFinished() good one
        self.IndVar_start.valueChanged.connect(self.update_expt)
        self.IndVar_stop.valueChanged.connect(self.update_expt)
        self.IndVar_step.valueChanged.connect(self.update_expt)
        self.setGasAType.insertItems(0, gas_control.factory_gasses)
        self.setGasBType.insertItems(0, gas_control.factory_gasses)
        self.setGasCType.insertItems(0, gas_control.factory_gasses)

        # Connect timer for live feed
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_eqpt_status)

        # This is the Canvas Widget that displays the `figure`
        # It takes the `figure` instance as a parameter to __init__
        # Initialize figure canvas and add to:
        self.figure = plt.figure(figsize=(8,8))
        self.canvas = FigureCanvas(self.figure)
        self.canvas2 = FigureCanvas(self.figure)
        self.horizontalLayout_4.addWidget(self.canvas) # Study Overview
        self.horizontalLayout_5.addWidget(self.canvas2)  # Experiment Design

    def update_eqpt_status(self):
        '''This function updates the live view of the equipment'''
        # TODO replace timeDisplay with real readouts
        time = QDateTime.currentDateTime()
        timeDisplay = time.toString("mm:ss")
        self.current_power_1.display(timeDisplay)
        self.current_temp_1.display(timeDisplay)
        self.current_gasA_comp_1.display(timeDisplay)
        self.current_gasA_type_1.setText(timeDisplay)
        self.current_gasB_comp_1.display(timeDisplay)
        self.current_gasB_type_1.setText(timeDisplay)
        self.current_gasC_comp_1.display(timeDisplay)
        self.current_gasC_type_1.setText(timeDisplay)
        self.current_gasD_flow_1.display(timeDisplay)

    def update_thread(self):
        # Set the time interval and start the timer
        # I'm not sure this does anything....
        self.timer.start(1000)

    def add_expt(self):
        print('clicked!')
        item = QListWidgetItem('Bob\'s your uncle', self.listWidget)
        expt = Experiment()
        item.setData(Qt.UserRole, expt)
        if self.expt_types.count() < len(expt.expt_list['Expt Name']):
            self.expt_types.addItem('Undefined')
            self.expt_types.addItems(expt.expt_list['Expt Name'].to_list())


    def delete_expt(self):
        item = self.listWidget.currentItem()
        self.listWidget.takeItem(self.listWidget.row(item))

    def display_expt(self):
        self.tabWidget.setUpdatesEnabled(False)
        global update_flag
        update_flag = False
        item = self.listWidget.currentItem()
        expt = item.data(Qt.UserRole)
        print(expt.temp)

        self.expt_types.setCurrentText(expt.expt_type)
        self.setTemp.setValue(expt.temp[0])

        self.setPower.setValue(expt.power[0])

        self.setFlow.setValue(expt.tot_flow[0])

        self.setSampleRate.setValue(expt.sample_rate)  # This needs to have a min set by ctrl file
        self.setSampleSize.setValue(expt.sample_set_size)
        self.setRampRate.setValue(expt.heat_rate)  # get from heater?
        self.setBuffer.setValue(99)

        self.setGasAComp.setValue(expt.gas_comp[0][0])
        self.setGasAType.setCurrentText(expt.gas_type[0])
        self.setGasBComp.setValue(expt.gas_comp[0][1])
        self.setGasBType.setCurrentText(expt.gas_type[1])
        self.setGasCComp.setValue(expt.gas_comp[0][2])
        self.setGasCType.setCurrentText(expt.gas_type[2])
        self.tabWidget.setUpdatesEnabled(True)
        update_flag = True

    def update_expt(self):
        item = self.listWidget.currentItem()
        global update_flag
        if (item is not None) & update_flag:
            print('expt updated')
            expt = item.data(Qt.UserRole)

            expt.expt_type = self.expt_types.currentText()

            expt.temp[0] = self.setTemp.value()

            expt.power[0] = self.setPower.value()

            expt.tot_flow[0] = self.setFlow.value()

            expt.sample_rate = self.setSampleRate.value()  # This needs to have a min set by ctrl file
            expt.sample_set_size = self.setSampleSize.value()
            expt.heat_rate = self.setRampRate.value()  # get from heater?
            # self.setBuffer.value(99)

            expt.gas_comp[0][0] = self.setGasAComp.value()
            expt.gas_type[0] = self.setGasAType.currentText()
            expt.gas_comp[0][1] = self.setGasBComp.value()
            expt.gas_type[1] = self.setGasBType.currentText()
            expt.gas_comp[0][2] = self.setGasCComp.value()
            expt.gas_type[2] = self.setGasCType.currentText()
            self.label_IndVar.setText(expt.ind_var)
            sweep_vals = [self.IndVar_start.value(),
                          self.IndVar_stop.value(),
                          self.IndVar_step.value()]
            if (sweep_vals[1] > sweep_vals[0]) & (sweep_vals[2] > 0):
                setattr(expt, expt.ind_var, list(np.arange(*sweep_vals)))
                expt.plot_sweep(self.figure)
                self.canvas.draw()
                self.canvas.show()
                self.canvas2.draw()
                self.canvas2.show()

    def manual_ctrl(self):
        temp = self.manualTemp.value()
        temp = self.manualBuffer.value()
        temp = self.manualPower.value()
        temp = self.manualRamp.value()
        temp = self.manualSampleRate.value()
        temp = self.manualSampleSize.value()
        temp = self.manualGasAComp.value()
        temp = self.manualGasAType.currentText()
        temp = self.manualGasBComp.value()
        temp = self.manualGasBType.currentText()
        temp = self.manualGasCComp.value()
        temp = self.manualGasCType.currentText()
        temp = self.manualFlow.value()

    def update_ctrl_file(self):

        print('update ctrl file')

    def select_ctrl_file(self):
        print('clicked')
        self.cal_path.setText(QFileDialog.getOpenFileName())
        print('step two')
        QFileDialog.show()

    def select_cal_file(self):
        self.ctrl_path.setText(QFileDialog.getOpenFileName())
        QFileDialog.show()


app = QApplication(sys.argv)
window = MainWindow()
window.show()
window.update_thread()
sys.exit(app.exec())

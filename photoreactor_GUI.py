# -*- coding: utf-8 -*-
"""
Created on Sun Feb 20 18:45:10 2022

@author: brile
"""
import sys
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
    QApplication,
    QDialog,
    QWidget,
    QListWidgetItem)


experiment_list = []
# Subclass QMainWindow to customize your application's main window
class MainWindow(QDialog):
    def __init__(self):
        super().__init__()
        loadUi('reactorUI.ui', self)
        # TODO initialize equipment, print results to window
        self.setWindowTitle("BruceJr")
        self.butAddExpt.clicked.connect(self.add_expt)
        self.butDelete.clicked.connect(self.delete_expt)
        self.listWidget.itemClicked.connect(self.display_expt)

        self.expt_types.currentIndexChanged.connect(self.update_expt)
        self.setTemp.valueChanged.connect(self.update_expt)
        self.setPower.valueChanged.connect(self.update_expt)
        self.setFlow.valueChanged.connect(self.update_expt)
        # self.setSampleRate.valueChanged.connect(self.update_expt)  # This needs to have a min set by ctrl file
        # self.setSampleSize.valueChanged.connect(self.update_expt)
        # self.setRampRate.valueChanged.connect(self.update_expt)  # get from heater?
        # self.setBuffer.valueChanged.connect(self.update_expt)
        self.setGasAComp.valueChanged.connect(self.update_expt)
        self.setGasAType.currentIndexChanged.connect(self.update_expt)
        self.setGasBComp.valueChanged.connect(self.update_expt)
        self.setGasBType.currentIndexChanged.connect(self.update_expt)
        self.setGasCComp.valueChanged.connect(self.update_expt)
        self.setGasCType.currentIndexChanged.connect(self.update_expt)
        # lineEdit.editingFinished() good one

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_eqpt_status)

        self.setGasAType.insertItems(0, gas_control.factory_gasses)
        self.setGasBType.insertItems(0, gas_control.factory_gasses)
        self.setGasCType.insertItems(0, gas_control.factory_gasses)

    def update_eqpt_status(self):
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
        self.timer.start(1000)

    def add_expt(self):
        print('clicked!')
        item = QListWidgetItem('Bob\'s your uncle', self.listWidget)
        item.setData(Qt.UserRole, Experiment())

    def delete_expt(self):
        item = self.listWidget.currentItem()
        self.listWidget.takeItem(self.listWidget.row(item))

    def display_expt(self):
        item = self.listWidget.currentItem()
        expt = item.data(Qt.UserRole)
        print(expt.temp)

        self.expt_types.addItems(expt.expt_list['Expt Name'].to_list())
        self.expt_types.setCurrentText(expt.expt_type)
        self.setTemp.setValue(expt.temp[0])

        self.setPower.setValue(expt.power[0])

        self.setFlow.setValue(expt.tot_flow[0])

        self.setSampleRate.setValue(99)  # This needs to have a min set by ctrl file
        self.setSampleSize.setValue(99)
        self.setRampRate.setValue(99)  # get from heater?
        self.setBuffer.setValue(99)

        self.setGasAComp.setValue(expt.gas_comp[0][0])
        self.setGasAType.setCurrentText(expt.gas_type[0])
        self.setGasBComp.setValue(expt.gas_comp[0][1])
        self.setGasBType.setCurrentText(expt.gas_type[1])
        self.setGasCComp.setValue(expt.gas_comp[0][2])
        self.setGasCType.setCurrentText(expt.gas_type[2])

    def update_expt(self):
        item = self.listWidget.currentItem()
        if item:
            print('expt updated')
            expt = item.data(Qt.UserRole)

            expt.expt_type = self.expt_types.currentText()

            expt.temp[0] = self.setTemp.value()

            expt.power[0] = self.setPower.value()

            expt.tot_flow[0] = self.setFlow.value()

            # self.setSampleRate.setValue(99)  # This needs to have a min set by ctrl file
            # self.setSampleSize.setValue(99)
            # self.setRampRate.setValue(99)  # get from heater?
            # self.setBuffer.setValue(99)

            expt.gas_comp[0][0] = self.setGasAComp.value()
            expt.gas_type[0] = self.setGasAType.currentText()
            expt.gas_comp[0][1] = self.setGasBComp.value()
            expt.gas_type[1] = self.setGasBType.currentText()
            expt.gas_comp[0][2] = self.setGasCComp.value()
            expt.gas_type[2] = self.setGasCType.currentText()







app = QApplication(sys.argv)
window = MainWindow()
window.show()
window.update_thread()
sys.exit(app.exec())

# -*- coding: utf-8 -*-
"""
Created on Sun Feb 20 18:45:10 2022

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
import psutil
import subprocess
import time

from experiment_control import Experiment
from equipment.sri_gc.gc_control import GC_Connector
from equipment.diode_laser.diode_control import Diode_Laser
from equipment.harrick_watlow.heater_control import Heater
from equipment.alicat_MFC.gas_control import Gas_System
from equipment.alicat_MFC import gas_control
from PyQt5.uic import loadUi
from PyQt5.QtCore import (Qt, QTimer, QDateTime, QThreadPool, QObject, pyqtSignal)

#from PyQt5 import QtWidgets
#from System.Threading import Thread, ThreadStart, ApartmentState
#from threading import Thread
from PyQt5.QtWidgets import (
    QPushButton,
    QLabel,
    QApplication,
    QDialog,
    QWidget,
    QListWidgetItem,
    QFileDialog,
    QDialogButtonBox,
    QAbstractItemView)

from PyQt5.QtGui import (QIcon, QTextCursor)

# Subclass QMainWindow to customize your application's main window
class MainWindow(QDialog):
    def __init__(self):
        super().__init__()
        loadUi('reactorUI.ui', self)

        # Initilize GUI
        # #peaksimple = self.open_peaksimple(r"C:\Peak489Win10\Peak489Win10.exe")
        self.timer = QTimer(self)

        # Initilize equipment
        self.init_equipment()
        self.init_study_tab()
        self.init_design_tab()
        self.init_manual_ctrl_tab()
        self.connect_manual_ctrl()
        self.init_figs()
        self.update_thread()
        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        # self.file_browser = QFileDialog()

    def normalOutputWritten(self, text):
        """Append console ouput to the QTextEdit."""
        # Maybe QTextEdit.append() works as well, but this is how I do it:
        cursor = self.consoleOutput.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.consoleOutput.setTextCursor(cursor)
        self.consoleOutput.ensureCursorVisible()
        #self.timer = QTimer(self)



    def update_thread(self):
        # Set the time interval and start the timer
        # I'm not sure this does anything....
        self.timer.start(500)


    def thread_starter(self):
        #self.thread_manager.start(self.thread_test)
        ctrl_thread = Thread(target=self.manual_ctrl_update)
        ctrl_thread.start()

    def thread_test(self):
        print('thread started')

    def add_expt(self):
        '''Creates a new experiment object and adds it to GUI'''
        item = QListWidgetItem('Bob\'s your uncle', self.listWidget)
        expt = Experiment()
        item.setData(Qt.UserRole, expt)


    def delete_expt(self):
        '''deletes currently selected item from listWidget'''
        item = self.listWidget.currentItem()
        self.listWidget.takeItem(self.listWidget.row(item))

    def display_expt(self):
        '''Updates GUI when new expt is selected in listWidget'''
        self.tabWidget.setUpdatesEnabled(False)
        global update_flag
        update_flag = False
        item = self.listWidget.currentItem()
        expt = item.data(Qt.UserRole)

        self.expt_types.setCurrentText(expt.expt_type)

        if expt.ind_var != 'Undefined':
            values = getattr(expt, expt.ind_var)
            if len(values) > 1:
                self.IndVar_start.setValue(np.min(values))
                self.IndVar_stop.setValue(np.max(values))
                self.IndVar_step.setValue(np.diff(values)[0])
        else:
            self.IndVar_start.setValue(0)
            self.IndVar_stop.setValue(0)
            self.IndVar_step.setValue(0)

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
        self.setGasDComp.setValue(expt.gas_comp[0][3])
        self.setGasDType.setCurrentText(expt.gas_type[3])
        self.update_plot(expt)
        self.tabWidget.setUpdatesEnabled(True)
        update_flag = True

    def update_expt(self):
        '''
        populates the attributes of currently selected experiment with the values
        displayed in GUI

        Returns
        -------
        None.

        '''
        item = self.listWidget.currentItem()
        global update_flag
        if (item is not None) & update_flag:
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
            expt.gas_comp[0][3] = self.setGasDComp.value()
            expt.gas_type[3] = self.setGasDType.currentText()

            expt._update_expt_name()
            item.setText(expt.expt_type+expt.expt_name)
            units = (expt.expt_list['Units']
                     [expt.expt_list['Active Status']].to_string(index=False))
            self.label_IndVar.setText(expt.ind_var+' ['+units+']')
            self.update_plot(expt)

    def update_plot(self, expt):
        '''Updates the plots in GUI when experiment is changed'''
        sweep_vals = [self.IndVar_start.value(),
                      self.IndVar_stop.value(),
                      self.IndVar_step.value()]
        if (sweep_vals[1] > sweep_vals[0]) & (sweep_vals[2] > 0):
            setattr(expt, expt.ind_var, list(np.arange(*sweep_vals)))
            expt.plot_sweep(self.figure)
            self.figure.tight_layout()
        else:
            self.figure.clear()
        self.canvas.draw()
        self.canvas.show()
        self.canvas2.draw()
        self.canvas2.show()

    def update_eqpt_status(self):
        '''This function updates the live view of the equipment'''
        if self.diode_Status.isChecked():
            self.current_power_1.setText('%.2f' % self.laser_controller.get_output_power())
            self.current_power_2.setText('%.2f' % self.laser_controller.get_output_power())

        if self.heater_Status.isChecked():
            self.current_temp_1.setText('%.2f' % self.heater.read_temp())
            self.current_temp_2.setText('%.2f' % self.heater.read_temp())

        if self.gas_Status.isChecked():
            flow_dict = self.gas_controller.read_flows()
            self.current_gasA_comp_1.setText('%.2f' % flow_dict['mfc_A']['mass_flow'])
            self.current_gasA_type_1.setText(flow_dict['mfc_A']['gas'])
            self.current_gasB_comp_1.setText('%.2f' % flow_dict['mfc_B']['mass_flow'])
            self.current_gasB_type_1.setText(flow_dict['mfc_B']['gas'])
            self.current_gasC_comp_1.setText('%.2f' % flow_dict['mfc_C']['mass_flow'])
            self.current_gasC_type_1.setText(flow_dict['mfc_C']['gas'])
            self.current_gasD_comp_1.setText('%.2f' % flow_dict['mfc_D']['mass_flow'])
            self.current_gasD_type_1.setText(flow_dict['mfc_D']['gas'])
            self.current_gasE_flow_1.setText('%.2f' % flow_dict['mfc_E']['mass_flow'])

            self.current_gasA_comp_2.setText('%.2f' % flow_dict['mfc_A']['mass_flow'])
            self.current_gasA_type_2.setText(flow_dict['mfc_A']['gas'])
            self.current_gasB_comp_2.setText('%.2f' % flow_dict['mfc_B']['mass_flow'])
            self.current_gasB_type_2.setText(flow_dict['mfc_B']['gas'])
            self.current_gasC_comp_2.setText('%.2f' % flow_dict['mfc_C']['mass_flow'])
            self.current_gasC_type_2.setText(flow_dict['mfc_C']['gas'])
            self.current_gasD_comp_2.setText('%.2f' % flow_dict['mfc_D']['mass_flow'])
            self.current_gasD_type_2.setText(flow_dict['mfc_D']['gas'])
            self.current_gasE_flow_2.setText('%.2f' % flow_dict['mfc_E']['mass_flow'])

    def manual_ctrl_update(self):
        '''updates the setpoint of all equipment based on the current manual
        control values entered in the GUI'''
        # TODO this needs to update the gas on mfce somewhere
        # TODO add pressure readout for mfcs
        # TODO add emergency stop
        # Adjust limits in GUI
        comp_list = [self.manualGasAComp.value(),
                     self.manualGasBComp.value(),
                     self.manualGasCComp.value(),
                     self.manualGasDComp.value()]
        gas_list = [self.manualGasAType.currentText(),
                    self.manualGasBType.currentText(),
                    self.manualGasCType.currentText(),
                    self.manualGasDType.currentText()]
        tot_flow = self.manualFlow.value()

        if self.gas_Status.isChecked():
            self.gas_controller.set_gasses(gas_list)
            self.progressBar.setValue(10)
            self.gas_controller.set_flows(comp_list, tot_flow)
        self.progressBar.setValue(20)
        buffer = self.manualBuffer.value()

        if self.diode_Status.isChecked():
            self.laser_controller.set_power(self.manualPower.value())
        self.progressBar.setValue(40)

        if self.heater_Status.isChecked():
            self.heater.ramp_rate = self.manualRamp.value()
            self.heater.ramp(self.manualTemp.value())
        self.progressBar.setValue(80)

        if self.gc_Status.isChecked():
            #sample_rate = self.manualSampleRate.value()
            self.gc_connector.sample_set_size = self.manualSampleSize.value()
        self.progressBar.setValue(100)

    def update_ctrl_file(self):
        print('update ctrl file')

    def select_ctrl_file(self):
        options = self.file_browser.Options()
        options |= self.file_browser.DontUseNativeDialog
        filePath = self.file_browser \
                       .getOpenFileName(self, 'Select Control File',
                                        "C:\\Peak489Win10\\CONTROL_FILE",
                                        "Control files (*.CON)")[0]
        print(filePath)
        self.ctrl_path.setText(filePath)
        self.gc_connector.ctrl_file = filePath
        self.gc_connector.load_ctrl_file()


    def select_cal_file(self):
        print('clicked')
        options = self.file_browser.Options()
        options |= self.file_browser.DontUseNativeDialog
        filePath = self.file_browser \
                       .getOpenFileName(self, 'Select Control File',
                                        "C:\\Peak489Win10\\CONTROL_FILE",
                                        "Control files (*.CON)")[0]
        print(filePath)
        self.cal_path.setText(filePath)

    def open_peaksimple(self, path_name):
        '''closes peaksimple if currently running,
            opens new edition with subprocess'''
        for process in psutil.process_iter():
            if 'Peak489Win10' in process.name():
                process.kill()
                time.sleep(5)
        process = subprocess.Popen(path_name)
        time.sleep(5)
        return process

    def init_equipment(self):
        ## Initialize Equipment
        # Try to connect to each device, mark indicator off on failed connect
        try:
            self.gc_connector = GC_Connector()
            self.gc_Status.setChecked(1)
        except:
            self.gc_Status.setChecked(0)
        try:
            self.gas_controller = Gas_System()
            self.gas_Status.setChecked(1)
        except:
            self.gas_Status.setChecked(0)
        try:
            self.heater = Heater()
            self.heater_Status.setChecked(1)
        except:
            self.heater_Status.setChecked(0)
        try:
            self.laser_controller = Diode_Laser()
            self.diode_Status.setChecked(1)
        except:
            self.diode_Status.setChecked(0)

    def init_study_tab(self): # Connect Study Overview Tab Contents
        self.setWindowTitle("BruceJr")
        self.butAddExpt.clicked.connect(self.add_expt)
        self.butDelete.clicked.connect(self.delete_expt)
        self.listWidget.itemClicked.connect(self.display_expt)
        self.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.findCalFile.clicked.connect(self.select_cal_file)
        self.findCtrlFile.clicked.connect(self.select_ctrl_file)

    def init_design_tab(self): # Connect Experiment Design Tab Contents
        self.expt_types.currentIndexChanged.connect(self.update_expt)
        # On first run, this should populate expt drop down on GUI
        if self.expt_types.count() < len(Experiment().expt_list['Expt Name']):
            self.expt_types.addItem('Undefined')
            self.expt_types.addItems(Experiment().expt_list['Expt Name'].to_list())
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
        self.setGasDComp.valueChanged.connect(self.update_expt)
        self.setGasDType.currentIndexChanged.connect(self.update_expt)
        # lineEdit.editingFinished() good one
        self.IndVar_start.valueChanged.connect(self.update_expt)
        self.IndVar_stop.valueChanged.connect(self.update_expt)
        self.IndVar_step.valueChanged.connect(self.update_expt)
        self.setGasAType.insertItems(0, gas_control.factory_gasses)
        self.setGasBType.insertItems(0, gas_control.factory_gasses)
        self.setGasCType.insertItems(0, gas_control.factory_gasses)
        self.setGasDType.insertItems(0, gas_control.factory_gasses)

    def init_manual_ctrl_tab(self): # Initialize Manual Control Tab
        self.tabWidget.setUpdatesEnabled(False) # Block Signals during update
        # Initialize Values for gas controller
        if self.gas_Status.isChecked():
            flow_dict = self.gas_controller.read_flows()
            tot_flow = (flow_dict['mfc_A']['setpoint'] +
                        flow_dict['mfc_B']['setpoint'] +
                        flow_dict['mfc_C']['setpoint'] +
                        flow_dict['mfc_D']['setpoint'])
            if tot_flow == 0:
                self.manualGasAComp.setValue(0)
                self.manualGasBComp.setValue(0)
                self.manualGasCComp.setValue(0)
                self.manualGasDComp.setValue(0)
            else:
               self.manualGasAComp.setValue(flow_dict['mfc_A']['setpoint']/tot_flow)
               self.manualGasBComp.setValue(flow_dict['mfc_B']['setpoint']/tot_flow)
               self.manualGasCComp.setValue(flow_dict['mfc_C']['setpoint']/tot_flow)
               self.manualGasDComp.setValue(flow_dict['mfc_D']['setpoint']/tot_flow)

            self.manualGasAType.insertItems(0, gas_control.factory_gasses)
            self.manualGasBType.insertItems(0, gas_control.factory_gasses)
            self.manualGasCType.insertItems(0, gas_control.factory_gasses)
            self.manualGasDType.insertItems(0, gas_control.factory_gasses)
            self.manualGasAType.setCurrentText(flow_dict['mfc_A']['gas'])
            self.manualGasBType.setCurrentText(flow_dict['mfc_B']['gas'])
            self.manualGasCType.setCurrentText(flow_dict['mfc_C']['gas'])
            self.manualGasDType.setCurrentText(flow_dict['mfc_D']['gas'])
            self.manualFlow.setValue(tot_flow)

        if self.heater_Status.isChecked():  # Initialize Values for Heater
            self.manualTemp.setValue(self.heater.read_setpoint())
            self.manualRamp.setValue(self.heater.ramp_rate)

        if self.diode_Status.isChecked():  # Initialize Values for Laser
            self.manualPower.setValue(self.laser_controller.get_output_power())

        if self.gc_Status.isChecked():  # Initialize Values for GC
            self.manualSampleRate.setValue(self.gc_connector.sample_rate)
            self.manualSampleSize.setValue(self.gc_connector.sample_set_size)
            #self.manualBuffer.setValue()
        self.tabWidget.setUpdatesEnabled(True)  # Allow signals again

    def connect_manual_ctrl(self): # Connect Manual Control
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.manual_ctrl_update)
        self.buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.init_manual_ctrl_tab)

        # Connect timer for live feed
        self.timer.timeout.connect(self.update_eqpt_status)

    def init_figs(self): # Initialize figure canvas and add to:
        # This is the Canvas Widget that displays the `figure`
        # It takes the `figure` instance as a parameter to __init__
        self.figure = plt.figure(figsize=(12,8))
        self.canvas = FigureCanvas(self.figure)
        self.canvas2 = FigureCanvas(self.figure)
        self.verticalLayout_7.addWidget(self.canvas) # Study Overview
        self.verticalLayout_8.addWidget(self.canvas2)  # Experiment Design

    def closeEvent(self, *args, **kwargs):
        super(QDialog, self).closeEvent(*args, **kwargs)
        #self.shut_down() # add shutdown process when window closed

    def shut_down(self):
        '''runs shutdown method on each connected piece of equipment.
        normally this just sets to zero'''
        print('Shutting Down Equipment')
        if self.gas_Status.isChecked():
            self.gas_controller.shut_down()

        if self.heater_Status.isChecked():
            self.heater.shut_down()

        if self.diode_Status.isChecked():
            self.laser_controller.shut_down()

    def disconnect(self):
        '''first runs shutdown sequence (normally sets all to zero)
        then disconnects which should sever digital connection too'''
        self.shut_down()
        if self.gas_Status.isChecked():
            self.gas_controller.disconnect()

        if self.heater_Status.isChecked():
            self.heater.disconnect()

        if self.gc_Status.isChecked():
           self.gc_connector.disconnect()

    #def start_study(self):
        '''something like this'''
        # dialogButton.button(QDialogButton.Accepted).block
        # for expt in expt_list:
        #     expt.run()
        # self.eqpt_list.shutdown()
        # dialogButton.button(QDialogButton.Accepted).unblock

# def check_state():
#     current_state = Thread.CurrentThread.GetApartmentState()
#     if current_state == ApartmentState.STA:
#         print('Current state: STA')
#     elif current_state == ApartmentState.MTA:
#         print('Current state: MTA')

class EmittingStream(QObject):
    '''
    Using this to capture console print statements and broadcast within the GUI
    https://stackoverflow.com/questions/8356336/how-to-capture-output-of-pythons-interpreter-and-show-in-a-text-widget
    '''
    textWritten = pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

def setup_style(app):
    script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    rel_path = r"gui_style_guides\Adaptic\Adaptic_v2.qss"
    abs_file_path = os.path.join(script_dir, rel_path)
    file = open(abs_file_path,'r')
    with file:
        qss = file.read()
        app.setStyleSheet(qss)

# Main
plt.close('all')
update_flag = False
app = QApplication(sys.argv)
window = MainWindow()
window.show()
setup_style(app)
sys.exit(app.exec())

# -*- coding: utf-8 -*-
"""
Created on Sun Feb 20 18:45:10 2022

@author: brile
"""
import os
import subprocess
import sys
import time

import matplotlib
import numpy as np
import pandas as pd
import psutil
from alicat import FlowController
from equipment.alicat_MFC import gas_control
from equipment.alicat_MFC.gas_control import Gas_System
from equipment.diode_laser.diode_control import Diode_Laser
from equipment.harrick_watlow.heater_control import Heater
from equipment.sri_gc.gc_control import GC_Connector
from experiment_control import Experiment

matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import \
    NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtCore import (QObject, QRunnable, Qt, QThreadPool, QTimer,
                          pyqtSignal, pyqtSlot)
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QComboBox,
                             QDialogButtonBox, QDoubleSpinBox, QFileDialog,
                             QLabel, QListWidgetItem, QMainWindow, QMessageBox,
                             QPushButton, QSpinBox)
from PyQt5.uic import loadUi


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi('.\gui_components\\reactorUI.ui', self)

        # Initilize GUI
        try:
            peaksimple = self.open_peaksimple(r"C:\Peak489Win10\Peak489Win10.exe")
        except FileNotFoundError:
            print('Peaksimple.exe not found')

        self.timer = QTimer(self)
        self.threadpool = QThreadPool()
        # Pass the function to execute
        # Any other args, kwargs are passed to the run function
        self.run_study_thread = Worker(self.start_study)
        self.eqpt_status_thread = Worker(self.update_eqpt_status)
        self.manual_ctrl_thread = Worker(self.manual_ctrl_eqpt)
        self.run_study_thread.setAutoDelete(False)
        self.eqpt_status_thread.setAutoDelete(False)
        self.manual_ctrl_thread.setAutoDelete(False)
        # TODO : Timer has weird definition in tab init

        # Initilize equipment
        self.init_equipment()
        self.init_study_tab()
        self.init_design_tab()
        self.init_manual_ctrl_tab()
        self.connect_manual_ctrl()
        self.init_figs()
        self.set_form_limits()

        self.timer.start(500) # timer connected to update in init_manual_ctrl
        #sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        self.file_browser = QFileDialog()
        self.emergencyStop.clicked.connect(self.emergency_stop)


    def normalOutputWritten(self, text):
        """Append console ouput to the QTextEdit."""
        # Maybe QTextEdit.append() works as well, but this is how I do it:
        cursor = self.consoleOutput.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.consoleOutput.setTextCursor(cursor)
        self.consoleOutput.ensureCursorVisible()

    ## Button Definitions:
    def add_expt(self):
        '''Creates a new experiment object and adds it to GUI'''
        item = QListWidgetItem('Bob\'s your uncle', self.listWidget)
        expt = Experiment()
        item.setData(Qt.UserRole, expt)

    def delete_expt(self):
        '''deletes currently selected item from listWidget'''
        item = self.listWidget.currentItem()
        self.listWidget.takeItem(self.listWidget.row(item))

    def start_study(self):
        '''Takes experiment objects in listWidget, assigns eqpt, generates
        experiment name and save path, then call expt.run_experiment().
        Shuts down at end.'''
        self.toggle_controls(True)
        expt_list = [self.listWidget.item(x).data(Qt.UserRole)
                     for x in range(self.listWidget.count())]
        eqpt_list = [self.gc_connector, self.laser_controller,
                      self.gas_controller, self.heater]
        sample_name = (self.sample_name.text()
                       + str(self.sample_mass.value()))
        main_fol = os.path.join('C:\Peak489Win10\GCDATA', sample_name)
        os.makedirs(main_fol, exist_ok=True)

        for expt in expt_list:

            expt.sample_name = sample_name
            expt.create_dirs(main_fol)
            expt.update_eqpt_list(eqpt_list)
            print(expt.expt_name)
            print(expt.sample_name)
            expt.run_experiment()
        self.shut_down()
        self.toggle_controls(False)

    def select_ctrl_file(self):
        '''Prompts user to selector GC control file if gc is connected'''
        if self.gc_Status.isChecked():
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
            self.set_form_limits()
        else: print('GC Not Connected')

    def select_cal_file(self):
        '''Prompts user to select calibration file
        is gas system is connected, runs "set_calibration()" method on each mfc
        Adds 'CalGas' option to mfc gas type drop downs'''
        options = self.file_browser.Options()
        options |= self.file_browser.DontUseNativeDialog
        filePath = self.file_browser \
                       .getOpenFileName(self, 'Select Control File',
                                        "C:\\Peak489Win10\\CONTROL_FILE",
                                        "Control files (*.CON)")[0]
        print(filePath)
        self.cal_path.setText(filePath)
        calDF = pd.read_csv(filePath, delimiter=',', index_col='Chem ID')
        if self.gas_Status.isChecked():
            attribute_list = vars(self.gas_controller)
            for key in attribute_list:
                if isinstance(attribute_list[key], FlowController):
                    self.gas_controller.set_calibration(calDF, fill_gas='Ar')

            self.setGasAType.insertItems(0, 'CalGas')
            self.setGasBType.insertItems(0, 'CalGas')
            self.setGasCType.insertItems(0, 'CalGas')
            self.setGasDType.insertItems(0, 'CalGas')
            self.manualGasAType.insertItems(0, 'CalGas')
            self.manualGasBType.insertItems(0, 'CalGas')
            self.manualGasCType.insertItems(0, 'CalGas')
            self.manualGasDType.insertItems(0, 'CalGas')

    def reset_eqpt(self):
        '''Disconnects from equipment and attempts to reconnect'''
        print('Resetting Equipment Connections')
        self.disconnect()
        self.init_equipment()
        self.init_manual_ctrl_tab()
        self.set_form_limits()

    ## Initializing Tabs:
    def init_equipment(self):
        '''Tries to connect to each piece of equipment, adjusts
        (object)_status.setChecked if successful.
        Calls set_form_limits() at end'''
        ## Initialize Equipment
        # Try to connect to each device, mark indicator off on failed connect
        try:
            self.gc_connector = GC_Connector()
            self.gc_Status.setChecked(1)
        except Exception as e:
            print(e)
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
            # Check if output is supported by DAQ
            if self.laser_controller._ao_info.is_supported:
                self.diode_Status.setChecked(1)
            else: self.diode_Status.setChecked(0)
        except:
            self.diode_Status.setChecked(0)
        self.set_form_limits()

    def init_study_tab(self):
        '''Connect Study Overview Tab Contents (signals/slots)'''

        self.setWindowTitle("BruceJr")
        self.butAddExpt.clicked.connect(self.add_expt)
        self.butDelete.clicked.connect(self.delete_expt)
        self.butStart.clicked.connect(lambda: self.threadpool.start(self.run_study_thread))
        self.listWidget.itemClicked.connect(self.display_expt)
        self.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.findCalFile.clicked.connect(self.select_cal_file)
        self.findCtrlFile.clicked.connect(self.select_ctrl_file)

    def init_design_tab(self):
        '''Connect Experiment Design Tab Contents (signals/slots).
        On first call, populates expt_type drop down on GUI.
        Insert possible gasses to combo boxes.
        Initializes widgets used for defining comp_sweep experiments.'''
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
        self.setTSteady.valueChanged.connect(self.update_expt)
        self.setBuffer.valueChanged.connect(self.update_expt)
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
        if self.gas_Status.isChecked(): # sets gas type to last used
            flow_dict = self.gas_controller.read_flows()
            self.setGasAType.setCurrentText(flow_dict['mfc_A']['gas'])
            self.setGasBType.setCurrentText(flow_dict['mfc_B']['gas'])
            self.setGasCType.setCurrentText(flow_dict['mfc_C']['gas'])
            self.setGasDType.setCurrentText(flow_dict['mfc_D']['gas'])

        self.default_grid_widgets = [[self.label_78, self.label_79, self.label_80],
                                     [self.IndVar_start, self.IndVar_stop, self.IndVar_step]]

        # create initial list of buttons to be added into grid layout when
        # comp sweep is selected
        self.comp_sweep_widgets = [[QLabel('-'), QLabel('Multiplier'),
                                    QLabel('Status'), QLabel('Start'),
                                    QLabel('Stop'), QLabel('Step')]]

        combobox_options = ['-', 'Fixed','Fill', 'Ind. Variable', 'Multiple']
        for i in range(1, 5):
            self.comp_sweep_widgets.append([QLabel(('Gas %i' % i)),
                                            QDoubleSpinBox(),
                                            QComboBox(),
                                            QDoubleSpinBox(),
                                            QDoubleSpinBox(),
                                            QDoubleSpinBox()])

            # Add drop down items to combo box that was just added to list
            self.comp_sweep_widgets[i][2].addItems(combobox_options)
            self.comp_sweep_widgets[i][2].currentIndexChanged.connect(self.update_expt)
            for j in [1, 3, 4, 5]:
                self.comp_sweep_widgets[i][j].valueChanged.connect(self.update_expt)
                self.comp_sweep_widgets[i][j].setMaximum(100)


    def init_manual_ctrl_tab(self):
        '''Initialize Manual Control Tab
        Blocks tabWidget updates, puts intial values in manual tab widgets.
        Insert possible gasses to combo boxes'''
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
               self.manualGasAComp.setValue(flow_dict['mfc_A']['setpoint']/tot_flow*100)
               self.manualGasBComp.setValue(flow_dict['mfc_B']['setpoint']/tot_flow*100)
               self.manualGasCComp.setValue(flow_dict['mfc_C']['setpoint']/tot_flow*100)
               self.manualGasDComp.setValue(flow_dict['mfc_D']['setpoint']/tot_flow*100)

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

        self.tabWidget.setUpdatesEnabled(True)  # Allow signals again

    def sum_spinboxes(self, spinboxes, qlabel):
        '''take list of spinboxes, get values, write sum to qlabel'''
        values = self.values_from_spinboxes(spinboxes)
        qlabel.setText('%.2f' % sum(values))

    def values_from_spinboxes(self, spinboxes):
        '''
        give list of spinboxes, return list of values

        Parameters
        ----------
        spinboxes : list
            list of spinboxes you'd like to get values from

        Returns
        -------
        gas_comp : list
            list of the values from the spinboxes supplied

        '''
        values = []
        for entry in spinboxes:
            values.append(entry.value())
        return values

    def connect_manual_ctrl(self):
        '''Connect Manual Control (signals/slots)
        Connects to eqpt status and manual ctrl threads'''
        self.buttonBox.button(QDialogButtonBox.Apply) \
            .clicked.connect(lambda:
                             self.threadpool.start(self.manual_ctrl_thread))
        self.buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.init_manual_ctrl_tab)
        self.eqpt_ReconnectBut.clicked.connect(self.reset_eqpt)
        # Connect timer for live feed
        self.timer.timeout \
            .connect(lambda: self.threadpool.start(self.eqpt_status_thread))

        gas_spinboxes = [self.manualGasAComp, self.manualGasBComp,
                         self.manualGasCComp, self.manualGasDComp]
        func = lambda: self.sum_spinboxes(gas_spinboxes, self.manualCompSum)
        self.manualGasAComp.valueChanged.connect(func)
        self.manualGasBComp.valueChanged.connect(func)
        self.manualGasCComp.valueChanged.connect(func)
        self.manualGasDComp.valueChanged.connect(func)

    def init_figs(self):
        '''Initialize figure canvas:
            creates figure objects, adds to gui, adds navigation bar'''

        self.figure = plt.figure() # Create New figure to share
        self.plotWidgetStudy.canvas.figure = self.figure # Reset fig in canvases
        self.plotWidgetDesign.canvas.figure = self.figure
        # Add navigation bar beneath each figure widget
        self.verticalLayoutStudyFig.addWidget(NavigationToolbar(self.plotWidgetStudy.canvas, self))
        self.verticalLayoutDesignFig.addWidget(NavigationToolbar(self.plotWidgetDesign.canvas, self))


    def set_form_limits(self):
        '''Use this function to set widget min/max values. These can either be
        pulled from eqpt objects to have equipment specific limits, or hard
        coded. Alternativly, many limits are set using QtDesigner'''
        if self.gc_Status.isChecked():
            self.setSampleRate.setMinimum(self.gc_connector.min_sample_rate)

        if self.heater_Status.isChecked():
            self.manualTemp.setMaximum(450)

        if self.gas_Status.isChecked():
            self.manualFlow.setMaximum(350)

    ## Updating Tabs/Objects:
    def display_expt(self):
        '''Updates GUI display when new expt is selected in listWidget'''
        self.tabWidget.setUpdatesEnabled(False)
        global update_flag
        update_flag = False
        item = self.listWidget.currentItem()
        expt = item.data(Qt.UserRole)

        self.expt_types.setCurrentText(expt.expt_type)

        if expt.ind_var != 'Undefined':
            values = getattr(expt, expt.ind_var)
            has_data = len(values) > 1
            if has_data and (expt.expt_type in ['comp_sweep', 'calibration']):

                for i in range(1, len(self.comp_sweep_widgets)):
                    # display only version of composition values
                    self.comp_sweep_widgets[i][1].setValue(0)
                    self.comp_sweep_widgets[i][2].setCurrentText('-')
                    self.comp_sweep_widgets[i][3].setValue(min(values[i]))
                    self.comp_sweep_widgets[i][4].setValue(max(values[i]))
                    self.comp_sweep_widgets[i][5].setValue(values[i][1]-values[i][0])

            elif has_data:
                self.IndVar_start.setValue(np.min(values))
                self.IndVar_stop.setValue(np.max(values))
                self.IndVar_step.setValue(values[1]-values[0])
            self.update_plot(expt)

        else:
            self.IndVar_start.setValue(0)
            self.IndVar_stop.setValue(0)
            self.IndVar_step.setValue(0)
            self.update_plot()

        self.setTemp.setValue(expt.temp[0])
        self.setPower.setValue(expt.power[0])
        self.setFlow.setValue(expt.tot_flow[0])

        self.setSampleRate.setValue(expt.sample_rate)  # This needs to have a min set by ctrl file
        self.setSampleSize.setValue(expt.sample_set_size)
        self.setRampRate.setValue(expt.heat_rate)  # get from heater?
        self.setBuffer.setValue(expt.t_buffer)
        self.setTSteady.setValue(expt.t_steady_state)
        self.setGasAComp.setValue(expt.gas_comp[0][0])
        self.setGasAType.setCurrentText(expt.gas_type[0])
        self.setGasBComp.setValue(expt.gas_comp[0][1])
        self.setGasBType.setCurrentText(expt.gas_type[1])
        self.setGasCComp.setValue(expt.gas_comp[0][2])
        self.setGasCType.setCurrentText(expt.gas_type[2])
        self.setGasDComp.setValue(expt.gas_comp[0][3])
        self.setGasDType.setCurrentText(expt.gas_type[3])
        self.update_ind_var_grid()
        comp_total = sum(expt.gas_comp[0]) # Calculate gas comp total
        self.designCompSum.setText('%.2f' % comp_total)
        self.tabWidget.setUpdatesEnabled(True)
        update_flag = True

    def update_expt(self):
        '''
        populates the attributes of currently selected experiment with the values
        displayed in GUI. If valid independent variable is set, updates plot.
        Clears plot for invalid experiment.

        Returns
        -------
        None.
        '''
        # grab the data associated with selected listWidget item
        item = self.listWidget.currentItem()
        global update_flag
        # If there is data in listWidget item and now in the middle of updating
        if (item is not None) & update_flag:
            expt = item.data(Qt.UserRole) # pull listWidgetItem data out
            # set the attributes of expt object based on GUI entries
            expt.expt_type = self.expt_types.currentText()
            expt.temp[0] = self.setTemp.value()
            expt.power[0] = self.setPower.value()
            expt.tot_flow[0] = self.setFlow.value()
            expt.sample_rate = self.setSampleRate.value()  # This needs to have a min set by ctrl file
            expt.sample_set_size = self.setSampleSize.value()
            expt.heat_rate = self.setRampRate.value()  # get from heater?
            expt.t_buffer = self.setBuffer.value()
            expt.t_steady_state = self.setTSteady.value()
            expt.gas_comp[0][0] = self.setGasAComp.value()
            expt.gas_type[0] = self.setGasAType.currentText()
            expt.gas_comp[0][1] = self.setGasBComp.value()
            expt.gas_type[1] = self.setGasBType.currentText()
            expt.gas_comp[0][2] = self.setGasCComp.value()
            expt.gas_type[2] = self.setGasCType.currentText()
            expt.gas_comp[0][3] = self.setGasDComp.value()
            expt.gas_type[3] = self.setGasDType.currentText()
            comp_total = sum(expt.gas_comp[0]) # Calculate gas comp total
            self.designCompSum.setText('%.2f' % comp_total)

            expt._update_expt_name() # autoname experiment
            item.setText(expt.expt_type+expt.expt_name) # add name to listWidget

            # pull units based on expt class definitions, label in GUI
            units = (expt.expt_list['Units']
                     [expt.expt_list['Active Status']].to_string(index=False))
            self.label_IndVar.setText(expt.ind_var+' ['+units+']')

            self.update_ind_var_grid() # why is this here??
            self.update_ind_var(expt)  # Checks for logical values before plot
            #self.update_plot(expt)

    def update_ind_var(self, expt):
        '''Checks for valid independent variable and updates the experiment
        object accordingly. Returns if invalid variable is supplied'''
        # only actually updates ind var if number check out
        if expt.expt_type in ['comp_sweep', 'calibration']:
            widget_grid = self.comp_sweep_widgets
            row_types = ['null'] # first row of grid is QLabel
            num_rows = len(widget_grid)
            comp_list = [[]]*(num_rows-1) # preallocate comp_list size

            for i in range(1, num_rows): # sweep rows of grid
                # ['null', combobox1, combobox2, etc]
                row_types.append(widget_grid[i][2].currentText())

            # Cases to Reject!!
            if '-' in row_types:
                return
            if ((row_types.count('Fill') != 1)
                or (row_types.count('Ind. Variable') != 1)):
                self.update_plot()
                return

            row_types = np.array(row_types) # to allow np.where()

            # This should execute 0 or 1 times if TODO double updating blocked
            for i in np.where(row_types=='Ind. Variable')[0].tolist():
                ind_var_row = int(np.where(row_types=='Ind. Variable')[0])

                # This block determines if sensible values are in ind_var
                start = widget_grid[ind_var_row][3].value()
                stop = widget_grid[ind_var_row][4].value()+1
                step = widget_grid[ind_var_row][5].value()
                if (stop>start) and (step>0):
                    ind_var = np.arange(start, stop, step)
                else:
                    return(False)

                ind_var = ind_var/100 # convert from % to frac
                comp_list[ind_var_row-1] = ind_var.tolist()

                #fill_vals = np.ones(len(ind_var)) # Fill values = 1 (100%)
                fill_vals = 1 - ind_var

            for i in np.where(row_types=='Multiple')[0].tolist():
                comp_vals = ind_var*widget_grid[i][1].value()
                comp_list[i-1] = comp_vals.tolist()
                fill_vals = fill_vals - comp_vals

            for i in np.where(row_types=='Fixed')[0].tolist():
                comp_vals = np.ones(len(ind_var)) * widget_grid[i][3].value()
                comp_vals = comp_vals/100 # convert from % to frac
                comp_list[i-1] = comp_vals.tolist()
                fill_vals = fill_vals - comp_vals

            for i in np.where(row_types=='Fill')[0].tolist():
                comp_list[i-1] = fill_vals.tolist()

            if (fill_vals<0).any():
                self.update_plot() # Clears plot
                return # Cancels update

            comp_list = np.array(comp_list).T # Transpose comp_list
            comp_list = comp_list.tolist() # return to list of lists
            setattr(expt, expt.ind_var, comp_list)

        elif ((self.IndVar_stop.value() > self.IndVar_start.value())
              & (self.IndVar_step.value() > 0)
              & (expt.expt_type != 'stability_test')):
            setattr(expt, expt.ind_var,
                    list(np.arange(self.IndVar_start.value(),
                                   self.IndVar_stop.value()+1,
                                   self.IndVar_step.value())))
        else:
            self.update_plot() # clear plot
            return # reject update
        self.update_plot(expt) # if either if statement was true



    def update_ind_var_grid(self):
        '''Chooses the correct widgets to display based on the experiment type
        currently selected in the GUI.'''
        def clear_grid():
            # Remove and hide currently present widgets
            for i in range(self.gridLayout_9.rowCount()):
                for j in range(self.gridLayout_9.columnCount()):
                    item = self.gridLayout_9.itemAtPosition(i, j)
                    if item is not None:
                        widget = item.widget()
                        self.gridLayout_9.removeWidget(widget)
                        widget.setHidden(True)

        item = self.listWidget.currentItem()
        global update_flag
        # If there is data in listWidget item and now in the middle of updating
        if (item is not None) & update_flag:
            expt = item.data(Qt.UserRole) # pull listWidgetItem data out
        else: return

        # if comp sweep and grid isn't set up for it
        if ((expt.expt_type in ['comp_sweep', 'calibration'])
            & (self.comp_sweep_widgets[0][0].isHidden())):

            clear_grid()
            # Add comp sweep specific widgets to layout
            for i in range(len(self.comp_sweep_widgets)): # sweep items to add
                for j in range(len(self.comp_sweep_widgets[0])):
                    self.gridLayout_9.addWidget(self.comp_sweep_widgets[i][j], i, j)
                    self.comp_sweep_widgets[i][j].setHidden(False)

            if (expt.expt_type == 'calibration'
                and not os.path.isfile(self.cal_path.text())):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText('Warning: You must enter appropriate calibration '
                            'data file path on overview tab to run calibration!!!')
                msg.setWindowTitle('Calibration Data Path Warning')
                msg.exec()


        # if not comp sweep but grid is still set up
        elif ((expt.expt_type != 'comp_sweep')
              & (self.default_grid_widgets[0][0].isHidden())):

            clear_grid()
            # Add default widgets to layout
            for i in range(len(self.default_grid_widgets)): # sweep items to add
                for j in range(len(self.default_grid_widgets[0])):
                    self.gridLayout_9.addWidget(self.default_grid_widgets[i][j], i, j)
                    self.default_grid_widgets[i][j].setHidden(False)

        # update active elements if comp_sweep is set up
        if ((expt.expt_type == 'comp_sweep')
            & (self.default_grid_widgets[0][0].isHidden())):

            for i in range(1, len(self.comp_sweep_widgets)): # sweep rows of grid

                if self.comp_sweep_widgets[i][2].currentText() == 'Fill':
                    selection_rule = [False, False, False, False]

                elif self.comp_sweep_widgets[i][2].currentText() == 'Fixed':
                    selection_rule = [False, True, False, False]

                elif self.comp_sweep_widgets[i][2].currentText() == 'Multiple':
                    selection_rule = [True, False, False, False]

                elif self.comp_sweep_widgets[i][2].currentText() == 'Ind. Variable':
                    selection_rule = [False, True, True, True]

                else: # This is likely currentText == '-'
                    selection_rule = [False, False, False, False]
                    self.comp_sweep_widgets[i][1].setValue(0)
                    self.comp_sweep_widgets[i][3].setValue(0)
                    self.comp_sweep_widgets[i][4].setValue(0)
                    self.comp_sweep_widgets[i][5].setValue(0)

                # Disable widgets based on selection rules
                self.comp_sweep_widgets[i][1].setEnabled(selection_rule[0])
                self.comp_sweep_widgets[i][3].setEnabled(selection_rule[1])
                self.comp_sweep_widgets[i][4].setEnabled(selection_rule[2])
                self.comp_sweep_widgets[i][5].setEnabled(selection_rule[3])

        self.gridLayout_9.update()

    def update_plot(self, expt=None):
        '''Updates the plots in GUI when experiment is changed'''

        if not expt:
            self.figure.clear()
        elif expt.ind_var:
            expt.plot_sweep(self.figure)
            self.figure.tight_layout()

        else:
            self.figure.clear()

        self.plotWidgetStudy.canvas.draw()
        self.plotWidgetStudy.canvas.show()
        self.plotWidgetDesign.canvas.draw()
        self.plotWidgetDesign.canvas.show()

    def update_eqpt_status(self):
        '''This function updates the live view of the equipment in both the
        manual control (1) and the live view (2) tabs'''
        if self.diode_Status.isChecked():
            self.current_power_1.setText('%.2f' % self.laser_controller.get_output_power())
            self.current_power_2.setText('%.2f' % self.laser_controller.get_output_power())
            self.current_power_setpoint1.setText('%.2f' % self.laser_controller.P_set)
            self.current_power_setpoint2.setText('%.2f' % self.laser_controller.P_set)

        if self.heater_Status.isChecked():
            self.current_temp_1.setText('%.2f' % self.heater.read_temp())
            self.current_temp_2.setText('%.2f' % self.heater.read_temp())
            self.current_temp_setpoint1.setText('%.2f' % self.heater.read_setpoint())
            self.current_temp_setpoint2.setText('%.2f' % self.heater.read_setpoint())

        if self.gas_Status.isChecked():
            flow_dict = self.gas_controller.read_flows()
            self.current_gasA_comp_1.setText('%.2f' % flow_dict['mfc_A']['mass_flow'])
            self.current_gasA_pressure_1.setText('%.2f' % flow_dict['mfc_A']['pressure'])
            self.current_gasA_type_1.setText(flow_dict['mfc_A']['gas'])
            self.current_gasB_comp_1.setText('%.2f' % flow_dict['mfc_B']['mass_flow'])
            self.current_gasB_pressure_1.setText('%.2f' % flow_dict['mfc_B']['pressure'])
            self.current_gasB_type_1.setText(flow_dict['mfc_B']['gas'])
            self.current_gasC_comp_1.setText('%.2f' % flow_dict['mfc_C']['mass_flow'])
            self.current_gasC_pressure_1.setText('%.2f' % flow_dict['mfc_C']['pressure'])
            self.current_gasC_type_1.setText(flow_dict['mfc_C']['gas'])
            self.current_gasD_comp_1.setText('%.2f' % flow_dict['mfc_D']['mass_flow'])
            self.current_gasD_pressure_1.setText('%.2f' % flow_dict['mfc_D']['pressure'])
            self.current_gasD_type_1.setText(flow_dict['mfc_D']['gas'])
            self.current_gasE_flow_1.setText('%.2f' % flow_dict['mfc_E']['mass_flow'])
            self.current_gasE_pressure_1.setText('%.2f' % flow_dict['mfc_E']['pressure'])

            self.current_gasA_comp_2.setText('%.2f' % flow_dict['mfc_A']['mass_flow'])
            self.current_gasA_pressure_2.setText('%.2f' % flow_dict['mfc_A']['pressure'])
            self.current_gasA_type_2.setText(flow_dict['mfc_A']['gas'])
            self.current_gasB_comp_2.setText('%.2f' % flow_dict['mfc_B']['mass_flow'])
            self.current_gasB_pressure_2.setText('%.2f' % flow_dict['mfc_B']['pressure'])
            self.current_gasB_type_2.setText(flow_dict['mfc_B']['gas'])
            self.current_gasC_comp_2.setText('%.2f' % flow_dict['mfc_C']['mass_flow'])
            self.current_gasC_pressure_2.setText('%.2f' % flow_dict['mfc_C']['pressure'])
            self.current_gasC_type_2.setText(flow_dict['mfc_C']['gas'])
            self.current_gasD_comp_2.setText('%.2f' % flow_dict['mfc_D']['mass_flow'])
            self.current_gasD_pressure_2.setText('%.2f' % flow_dict['mfc_D']['pressure'])
            self.current_gasD_type_2.setText(flow_dict['mfc_D']['gas'])
            self.current_gasE_flow_2.setText('%.2f' % flow_dict['mfc_E']['mass_flow'])
            self.current_gasE_pressure_2.setText('%.2f' % flow_dict['mfc_E']['pressure'])

    def manual_ctrl_eqpt(self):
        '''updates the setpoint of all equipment based on the current manual
        control values entered in the GUI'''
        self.toggle_controls(True)
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
            self.progressBar.setValue(25)
            self.gas_controller.set_flows(comp_list, tot_flow)
        self.progressBar.setValue(50)

        if self.diode_Status.isChecked():
            #self.current_power_setpoint1.setStyleSheet('Color: Red')
            #self.current_power_setpoint2.setStyleSheet('Color: Red')
            self.laser_controller.set_power(self.manualPower.value())
            #self.current_power_setpoint1.setStyleSheet('Color: White')
            #self.current_power_setpoint2.setStyleSheet('Color: White')
        self.progressBar.setValue(75)
        print('before heater')
        if self.heater_Status.isChecked():
            print('inside heater')
            #self.current_temp_setpoint1.setStyleSheet('Color: Red')
            #self.current_temp_setpoint2.setStyleSheet('Color: Red')
            self.heater.ramp_rate = self.manualRamp.value()
            self.heater.ramp(self.manualTemp.value())
            #self.current_temp_setpoint1.setStyleSheet('Color: White')
            #self.current_temp_setpoint2.setStyleSheet('Color: White')
        print('after heater')
        self.progressBar.setValue(100)
        self.toggle_controls(False)

    def toggle_controls(self, value):
        '''True disables all widgets in tabWidget (not emergency stop)
        Fals enables all'''
        group = [*self.tabWidget.findChildren(QDialogButtonBox),
                 *self.tabWidget.findChildren(QDoubleSpinBox),
                 *self.tabWidget.findChildren(QPushButton),
                 *self.tabWidget.findChildren(QComboBox),
                 *self.tabWidget.findChildren(QSpinBox)]

        for item in group:
            item.setDisabled(value)


    def open_peaksimple(self, path_name):
        '''closes peaksimple if currently running,
            opens new edition with subprocess'''
        for process in psutil.process_iter():
            if 'Peak489Win10' in process.name():
                #process.kill()
                print('please close peaksimple and reconnect')
                time.sleep(5)
                return

        process = subprocess.Popen(path_name)
        time.sleep(5)
        return process

    def closeEvent(self, *args, **kwargs):
        super(QMainWindow, self).closeEvent(*args, **kwargs)
        self.timer.stop()
        self.timer.disconnect()
        self.disconnect() # add shutdown process when window closed

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

    def emergency_stop(self):

        #self.threadpool.clear()
        #self.threadpool.cancel()
        self.threadpool.cancel(self.run_study_thread)
        self.threadpool.cancel(self.manual_ctrl_thread)
        #self.threadpool.disconnect()
        self.shut_down()



class EmittingStream(QObject):
    '''
    Using this to capture console print statements and broadcast within the GUI
    https://stackoverflow.com/questions/8356336/how-to-capture-output-of-pythons-interpreter-and-show-in-a-text-widget
    '''
    textWritten = pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    See: https://www.pythonguis.com/tutorials/multithreading-pyqt-applications-qthreadpool/

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        self.fn(*self.args, **self.kwargs)

def setup_style(app):
    script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    rel_path = r"gui_components\style_guide\Adaptic\Adaptic_v3.qss"
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

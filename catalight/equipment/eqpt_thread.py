import time

from alicat import FlowController
from catalight.equipment.gas_control.alicat import Gas_System
from catalight.equipment.light_sources.diode_control import Diode_Laser
from catalight.equipment.light_sources.nkt_system import NKT_System
from catalight.equipment.heating.watlow import Heater
from catalight.equipment.gc_control.sri_gc import GC_Connector
from catalight.equipment.experiment_control import Experiment
import catalight.config as cfg

from PyQt5.QtCore import (QObject, QRunnable, Qt, QThreadPool, QTimer,
                          pyqtSignal, pyqtSlot, QThread)


class Eqpt_Controller(QObject):
    """
    Worker thread.

    Inherits from QRunnable to handle
    worker thread setup, signals and wrap-up.

    Parameters
    ----------
    callback : `function`
        The function callback to run on this worker thread. Supplied args and
        kwargs will be passed through to the runner.

    args:
        Arguments to pass to the callback function
    kwargs:
        Keywords to pass to the callback function

    References
    ----------
    [1] (https://www.pythonguis.com/tutorials/
         multithreading-pyqt-applications-qthreadpool/)

    """
    eqpt_status_signal = pyqtSignal(dict)
    connection_status = pyqtSignal(str)
    connection_progress = pyqtSignal(int)
    initialized = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.start(500)
        self.timer.timeout.connect(self.update_eqpt_status)
        # Create signal for each piece of equipment
        # TODO connects these with equivilant GUI elements for LEDs

        # TODO i could turn these into a dict so that i always know the status
        # self.gc_status = pyqtSignal()
        # self.gas_status = pyqtSignal()
        # self.heater_status = pyqtSignal()
        # self.diode_status = pyqtSignal()
        # self.nkt_status = pyqtSignal()


        #TODO hold over
        # Pass the function to execute
        # Any other args, kwargs are passed to the run function
        # self.threadpool = QThreadPool()
        # self.run_study_thread = Worker(self.start_study)
        # self.manual_ctrl_thread = Worker(self.manual_ctrl_eqpt)
        # self.run_study_thread.setAutoDelete(False)
        # self.manual_ctrl_thread.setAutoDelete(False)

        self.eqpt_status = {
            'gc connected': False,
            'gas connected': False,
            'heater connected': False,
            'diode connected': False,
            'nkt connected': False,
        }

        # self.eqpt_status = {
        #     'gc connected': False,
        #     'gas connected': False,
        #     'heater connected': False,
        #     'diode connected': False,
        #     'nkt connected': False,
        #     'flows': flow_dict,
        #     'total flow': tot_flow,
        #     'current_power': laser_controller.get_output_power,
        #     'current power setpoint': laser_controller.P_set,
        #     'bandwidth': (self.laser_controller.bandwidth),
        #     'center': (self.laser_controller.central_wavelength),
        #     'current_center_setpoint': self.laser_controller.central_wavelength,
        #     'current_bandwidth_setpoint': self.laser_controller.bandwidth,
        #     'current_temp': heater.read_temp(),
        #     'current_temp_setpoint': heater.setpoint(),
        #     'max_constant_power': laser_controller.max_constant_power(bandwidth, centers),
        #     'minimum gc sample time': self.gc_connector.min_sample_rate,
        #     'maximum heater temp': 450,
        #     'maximum flow rate': 350,
        #     'wavelength range': self.laser_controller.wavelength_range,
        #     'bandwidth range': self.laser_controller.bandwidth_range,
        #     'tunable laser': False,
        # }

        # eqpt_setpoint = {
        #     'gas comp': comp_list,
        #     'gas list': gas_list,
        #     'total flow': tot_flow,
        #     'power': self.manualPower.value(),
        #     'center': self.manualCenter.value(),
        #     'bandwidth': self.manualBandwidth.value(),
        #     'ramp rate': self.manualRamp.value(),
        #     'temperature': self.manualTemp.value(),
        # }

    @pyqtSlot()
    def init_equipment(self):
        """
        Try to connect to each piece of equipment.

        Adjusts (object)_Status.setChecked if successful.
        If Exception is thrown, setChecked(0) and print Exception
        Calls set_form_limits() at end
        """
        # Initialize Equipment
        # Try to connect to each device, mark indicator off on failed connect
        self.connection_status.emit('Initializing Equipment...')
        self.connection_progress.emit(20)

        self.connection_status.emit('Connecting to GC...')
        self.connection_progress.emit(35)
        try:
            #self.gc_connector = GC_Connector()
            self.eqpt_status['gc connected'] = True
        except Exception as e:
            print(e)
            self.eqpt_status['gc connected'] = False

        time.sleep(1) # delete me

        self.connection_status.emit('Connecting to gas system...')
        self.connection_progress.emit(50)
        time.sleep(0.2)
        try:
            #self.gas_controller = Gas_System()
            self.eqpt_status['gas connected'] = True
        except Exception as e:
            print(e)
            self.eqpt_status['gas connected'] = False

        time.sleep(1) # delete me

        self.connection_status.emit('Connecting to heater...')
        self.connection_progress.emit(60)
        time.sleep(0.2)
        try:
            #self.heater = Heater()
            self.eqpt_status['gc connected'] = True
        except Exception as e:
            print(e)
            self.eqpt_status['gc connected'] = False

        time.sleep(1) # delete me

        self.connection_status.emit('Connecting to lasers...')
        self.connection_progress.emit(70)
        time.sleep(0.2)


        # #TODO what about this stuff??
        # # Make sure combobox is empty (in case restarting equipment)
        # self.laser_selection_box.clear()
        # # Create combo box options for diode and nkt lasers, connect signal
        # self.laser_selection_box.addItem("Diode Laser")
        # self.laser_selection_box.addItem("NKT Laser")
        # self.laser_selection_box.currentIndexChanged.connect(self.change_laser)

        # Try to connect with diode laser
        # try:
        #     laser = Diode_Laser()
        #     # Check if output is supported by DAQ
        #     if laser._ao_info.is_supported:
        #         # Assign diode laser to first item in combobox
        #         self.laser_selection_box.setItemData(0, laser)
        #         # Make sure diode is selected in box and change active laser
        #         self.laser_selection_box.setCurrentIndex(0)
        #         self.change_laser()
        # except Exception as e:
        #     print(e)
        #     self.laser_Status.setChecked(0)

        # self.connection_progress.emit(80)
        # # Try to connect with NKT laser
        # try:
        #     laser = NKT_System()
        #     # Assign nkt laser to first item in combobox
        #     self.laser_selection_box.setItemData(1, laser)
        #     # If previous laser didn't connect, set the nkt as active
        #     if not self.laser_Status.isChecked():
        #         self.laser_selection_box.setCurrentIndex(1)
        #         self.change_laser()
        # except Exception as e:
        #     print(e)

        self.connection_progress.emit(85)
        self.update_eqpt_status()
        self.initialized.emit()
        #TODO what bout this?
        # self.set_form_limits()

    @pyqtSlot()
    def manual_ctrl_eqpt(self):

        # wavelength = gui.widget_dict["wavelength"]["setpoint"].value()
        # bandwidth = gui.widget_dict["bandwidth"]["setpoint"].value()
        # power = gui.widget_dict["power"]["setpoint"].value()
        # print("Wavelength = %3.0f nm | Bandwidth = %3.0f nm | Power = %3.0f mW"
        #       % (wavelength, bandwidth, power))
        # wavelength = self.laser_controller.central_wavelength
        # bandwidth = self.laser_controller.bandwidth
        # power = self.laser_controller.get_output_power()
        # print("Wavelength = %3.0f nm | Bandwidth = %3.0f nm | Power = %3.0f mW"
        #       % (wavelength, bandwidth, power))
        # short = self.laser_controller.short_setpoint
        # long = self.laser_controller.long_setpoint
        # print("Bandpass %4.1f nm - %4.1f nm" % (short, long))
        #breakpoint()
        # print("laser power is " + str(self.laser_controller.power_level))

        # I can create an NKT_busy flag that stops two threads from dealing w/ NKT?
        print('manual control activated')
        time.sleep(1)

    def update_eqpt_status(self):
        # self.eqpt_status = {
        #     'gc connected': False,
        #     'gas connected': False,
        #     'heater connected': False,
        #     'diode connected': False,
        #     'nkt connected': False,
        #     'flows': flow_dict,
        #     'total flow': tot_flow,
        #     'current_power': laser_controller.get_output_power,
        #     'current power setpoint': laser_controller.P_set,
        #     'bandwidth': (self.laser_controller.bandwidth),
        #     'center': (self.laser_controller.central_wavelength),
        #     'current_center_setpoint': self.laser_controller.central_wavelength,
        #     'current_bandwidth_setpoint': self.laser_controller.bandwidth,
        #     'current_temp': heater.read_temp(),
        #     'current_temp_setpoint': heater.setpoint(),
        #     'max_constant_power': laser_controller.max_constant_power(bandwidth, centers),
        #     'minimum gc sample time': self.gc_connector.min_sample_rate,
        #     'maximum heater temp': 450,
        #     'maximum flow rate': 350,
        #     'wavelength range': self.laser_controller.wavelength_range,
        #     'bandwidth range': self.laser_controller.bandwidth_range,
        #     'tunable laser': False,
        # }
        self.eqpt_status.update({
            'flows': {'mfc_A': {'mass_flow': 10, 'pressure': 10,
                                'setpoint': 10, 'gas': 'Ar'},
                      'mfc_B': {'mass_flow': 10, 'pressure': 10,
                                'setpoint': 10, 'gas': 'Ar'},
                      'mfc_C': {'mass_flow': 10, 'pressure': 10,
                                'setpoint': 10, 'gas': 'Ar'},
                      'mfc_D': {'mass_flow': 10, 'pressure': 10,
                                'setpoint': 10, 'gas': 'Ar'},
                      'mfc_E': {'mass_flow': 10, 'pressure': 10,
                                'setpoint': 10, 'gas': 'Ar'}},
            'total flow': 50,
            'power': 100,
            'power setpoint': 100,
            'bandwidth': 100,
            'center': 100,
            'center_setpoint': 100,
            'bandwidth_setpoint': 100,
            'temp': 27,
            'temp_setpoint': 27,
            'heater_ramp_rate': 15,
            'max_constant_power': 234,
            'minimum gc sample time': 10,
            'maximum heater temp': 450,
            'maximum flow rate': 350,
            'wavelength range': [350, 450],
            'bandwidth range': [10, 50],
            'tunable laser': False
        })
        self.eqpt_status_signal.emit(self.eqpt_status)

    @pyqtSlot()
    def calculate_max_constant_power(self, bandwidth, centers):
        power = self.laser_controller.max_constant_power(bandwidth, centers)
        self.max_power_update.emit(power)


    @pyqtSlot("QString")
    def load_ctrl_file(self, filepath):
        print(filepath)
        print(type(filepath))
        # self.gc_connector.ctrl_file = filepath
        # self.gc_connector.load_ctrl_file()
        # self.update_limits()

    @pyqtSlot("PyQt_PyObject")
    def load_cal_file(self, calibration_DF):
        print(calibration_DF)
        print(type(calibration_DF))
        # attribute_list = vars(self.gas_controller)
        # for key in attribute_list:
        #     attr = attribute_list[key]
        #     if isinstance(attr, FlowController):
        #         self.gas_controller.set_calibration_gas(attr, calibration_DF,
        #                                                 fill_gas='Ar')

    @pyqtSlot("PyQt_PyObject")
    def begin_study(self, expt_list):
        # eqpt_list = [self.gc_connector, self.laser_controller,
        #              self.gas_controller, self.heater]
        # for expt in expt_list:
        #     expt.update_eqpt_list(eqpt_list)
        #     try:
        #         expt.run_experiment()
        #     except Exception as e:
        #         print(e)
        #         self.shut_down()
        #         raise
        # self.shut_down()
        # TODO emit when study is finished. Connect to toggle controls
        pass

    def change_laser(self):
        """
        Set the active laser to the one currently selected in combobox.

        Will also adjust the laser_Status icon if a laser exists
        """
        self.laser_controller = self.laser_selection_box.currentData()
        """Currently active laser system"""

        self.update_flag = False
        self.set_form_limits()
        if self.laser_controller:
            self.laser_Status.setChecked(1)
            self.manualBandwidth.setValue(self.laser_controller.bandwidth)
            self.manualCenter.setValue(self.laser_controller.central_wavelength)
            self.setBandwidth.setValue(self.laser_controller.bandwidth)
            self.setCenter.setValue(self.laser_controller.central_wavelength)

        else:
            self.laser_Status.setChecked(0)
        self.update_flag = True
        self.update_power_estimate()

    @pyqtSlot()
    def disconnect(self):
        """Run shutdown sequence then disconnect communications."""
        self.shut_down()
        if self.gas_Status.isChecked():
            self.gas_controller.disconnect()

        if self.heater_Status.isChecked():
            self.heater.disconnect()

        if self.gc_Status.isChecked():
            self.gc_connector.disconnect()

    @pyqtSlot()
    def shut_down(self):
        """Run shutdown method on each connected piece of equipment."""
        print('Shutting Down Equipment')
        if self.gas_Status.isChecked():
            self.gas_controller.shut_down()

        if self.heater_Status.isChecked():
            self.heater.shut_down()

        # Iterate over each laser in the laser_selection_box and turn it off
        for index in range(self.laser_selection_box.count()):
            laser = self.laser_selection_box.itemData(index)
            if laser is not None:
                # Perform the shutdown operation on the associated object
                laser.shut_down()

    def reset_eqpt(self):
        """Disconnects from equipment and attempts to reconnect."""
        print('Resetting Equipment Connections')
        self.disconnect()
        self.init_equipment()
        self.init_manual_ctrl_tab()
        self.set_form_limits()

    def emergency_stop(self):
        """Cancel active threads, call self.shut_down()."""
        # self.threadpool.clear()
        # self.threadpool.cancel()
        self.threadpool.cancel(self.run_study_thread)
        self.threadpool.cancel(self.manual_ctrl_thread)
        self.threadpool.clear()
        self.threadpool.disconnect()
        self.shut_down()


class WorkerSignal(QObject):
    """Provide signals for interacting w/ worker threads."""
    finished = pyqtSignal()
    """
    Basic pyqtSignal indicating worker thread called by worker thread to
    indicate when the process is finished.
    """


class Worker(QRunnable):
    """
    Worker thread.

    Inherits from QRunnable to handle
    worker thread setup, signals and wrap-up.

    Parameters
    ----------
    callback : `function`
        The function callback to run on this worker thread. Supplied args and
        kwargs will be passed through to the runner.

    args:
        Arguments to pass to the callback function
    kwargs:
        Keywords to pass to the callback function

    References
    ----------
    [1] (https://www.pythonguis.com/tutorials/
         multithreading-pyqt-applications-qthreadpool/)

    """

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signal = WorkerSignal()

    @pyqtSlot()
    def run(self):
        """Initialise the runner function with passed args, kwargs."""
        self.fn(*self.args, **self.kwargs)
        self.signal.finished.emit()

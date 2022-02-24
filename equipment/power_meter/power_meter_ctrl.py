# Use of Ophir COM object. 
# Works with python 3.5.1 & 2.7.11
# Uses pywin32

import win32com.client
import time

class NewportMeter:
    def __init__(self):
        # Ophir COM Object is main tool for this class
        self.OphirCOM = win32com.client.Dispatch("OphirLMMeasurement.CoLMMeasurement")
        # Stop & Close all devices
        self.OphirCOM.StopAllStreams() 
        self.OphirCOM.CloseAll()
        # Scan for connected Devices
        DeviceList = self.OphirCOM.ScanUSB()
        if len(DeviceList) > 1:
            raise ValueError('Multiple Devices Found')
        elif len(DeviceList) == 0:
            raise ValueError('No Devices Found')
        else:
            self.Device = DeviceList[0]
            
        
        self.DeviceHandle = self.OphirCOM.OpenUSBDevice(self.Device)  # open device
        exists = self.OphirCOM.IsSensorExists(self.DeviceHandle, 0)
        if exists:
            print('Connected to S/N {0}'.format(self.Device))
            
        else:
            print('No Sensor attached to {0} !!!'.format(self.Device))
    
    def change_wavelength(self, wavelength):
        # Changes to desired wavelength, modifies slot 4 if wavelength DNE
        wavelengths = self.OphirCOM.GetWavelengths(self.DeviceHandle, 0)[1]
        wavelength = str(wavelength)
        if wavelength not in wavelengths:
            self.OphirCOM.ModifyWavelength(self.DeviceHandle, 0, 4, wavelength)
        idx = wavelengths.index(wavelength)
        self.OphirCOM.SetWavelength(self.DeviceHandle, 0, idx)
    
    def read(self, averaging_time=0.5):
        # Reads out averaged power in mW
        self.OphirCOM.SetRange(self.DeviceHandle, 0, 0)  # set range to auto
        self.OphirCOM.StartStream(self.DeviceHandle, 0)  # start measuring
        time.sleep(averaging_time)  # wait a little for data
        data = self.OphirCOM.GetData(self.DeviceHandle, 0)
        reading = sum(list(data[0]))/len(data[0])*1000 # average the readout
        timestamp = time.time()  # get time
        self.OphirCOM.StopAllStreams() # stop measuring
        return(timestamp, reading)
    
    def shut_down(self):
        # Stop & Close all devices
        self.OphirCOM.StopAllStreams()
        self.OphirCOM.CloseAll()
        # Release the object
        self.OphirCOM = None

if __name__ == "__main__":
    power_meter = NewportMeter()
    print(power_meter.read())
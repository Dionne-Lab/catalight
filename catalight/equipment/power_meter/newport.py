"""
Access Newport power meter through Use of Ophir COM object.

You should need to PMManager installed on your computer to use this.
"""
import time

import win32com.client


class NewportMeter:
    """NewportMeter."""

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

        # Open device
        self.DeviceHandle = self.OphirCOM.OpenUSBDevice(self.Device)
        exists = self.OphirCOM.IsSensorExists(self.DeviceHandle, 0)
        if exists:
            print('Connected to S/N {0}'.format(self.Device))
        else:
            print('No Sensor attached to {0} !!!'.format(self.Device))

    def change_wavelength(self, wavelength):
        """Change to desired wavelength, modifies slot 4 if wavelength DNE."""
        wavelengths = self.OphirCOM.GetWavelengths(self.DeviceHandle, 0)[1]
        wavelength = str(wavelength)
        if wavelength not in wavelengths:
            self.OphirCOM.ModifyWavelength(self.DeviceHandle, 0, 4, wavelength)
        idx = wavelengths.index(wavelength)
        self.OphirCOM.SetWavelength(self.DeviceHandle, 0, idx)

    def read(self, averaging_time=0.5):
        """
         Read average powermeter output in mW over averaging_time.

        Parameters
        ----------
        averaging_time : float or int, optional
            Time to collect dataset in seconds. The default is 0.5.

        Returns
        -------
        timestamp : float
            Time since epoch from time.time() of recording
        reading : float
            Power reading in mW
        """
        self.OphirCOM.SetRange(self.DeviceHandle, 0, 0)  # set range to auto
        self.OphirCOM.StartStream(self.DeviceHandle, 0)  # start measuring
        time.sleep(averaging_time)  # collect data during pause
        data = self.OphirCOM.GetData(self.DeviceHandle, 0)
        # average the readout, convert units to mW
        reading = sum(list(data[0])) / len(data[0]) * 1000
        timestamp = time.time()  # get time
        self.OphirCOM.StopAllStreams()  # stop measuring
        return(timestamp, reading)

    def shut_down(self):
        """Stop & Close all devices."""
        self.OphirCOM.StopAllStreams()
        self.OphirCOM.CloseAll()
        # Release the object
        self.OphirCOM = None


if __name__ == "__main__":
    power_meter = NewportMeter()
    print(power_meter.read())

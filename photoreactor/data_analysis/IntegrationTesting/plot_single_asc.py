import os
import sys

import numpy as np

parent = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent)
from gcdata import GCData

filepath = "/Users/ccarlin/Documents/calibration/20220418calibration_273K_0.0mW_50sccm/Data/1 1.0CalGas_0.0Ar_0.0H2ppm/20201219_calibration1000ppm_FID06.ASC"
# filepath = "/Users/ccarlin/Desktop/20201219_calibration1000ppm_FID04.ASC"
data = GCData(filepath, basecorrect=True)
datauncor = GCData(filepath, basecorrect=False)
#data.plot_integration()
datauncor.plot_integration()
print("I'm done :)")

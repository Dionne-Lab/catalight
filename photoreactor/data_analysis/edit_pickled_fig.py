"""
Created on Tue Jul  5 10:53:29 2022

@author: brile
"""
import pickle
import sys

import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QFileDialog

if __name__ == "__main__":

    plt.close('all')
    plt.rcParams['svg.fonttype'] = 'none'
    fig_path = QFileDialog.getOpenFileName(None, "Pick figure to open", "",
                                           "pickle files (*.pickle)")[0]
    fig = pickle.load(open(fig_path, 'rb'))
    ax = fig.get_axes()[0]
    ax.set_xlim([-15, 315])
    fig.show()  # Show the figure, edit it, etc.!

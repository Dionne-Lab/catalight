# -*- coding: utf-8 -*-
"""
Created on Tue Jul  5 10:53:29 2022

@author: brile
"""
import sys
import pickle
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QFileDialog, QApplication, QWidget


if __name__ == "__main__":

    plt.close('all')
    fig_path = QFileDialog.getOpenFileName(None, "Pick figure to open", "",
                                           "pickle files (*.pickle)")[0]
    figx = pickle.load(open(fig_path, 'rb'))
    figx.show() # Show the figure, edit it, etc.!

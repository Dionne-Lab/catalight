# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 17:17:20 2022

@author: brile
"""
from alicat import FlowController
from PyQt5.QtCore import (QObject, QRunnable, Qt, QThreadPool, QTimer,
                          pyqtSignal, pyqtSlot)


class MFC_Holder():
    def __init__(self):
        self.mfc = FlowController(port='COM6', address='A')
        self.threadpool = QThreadPool()
        self.manual_ctrl_thread = Worker(self.ping_mfc)
        self.manual_ctrl_thread.setAutoDelete(False)

    def ping_mfc(self):
        print('inside thread')
        print(self.mfc.connection)

    def start_thread(self):
        self.threadpool.start(self.manual_ctrl_thread)

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

if __name__ == "__main__":
    tester = MFC_Holder()
    print('outside thread')
    print(tester.mfc.connection)
    tester.start_thread()

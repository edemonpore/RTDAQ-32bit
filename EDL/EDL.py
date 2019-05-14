""" EDL.p2
Class for Elements 4-Channel PCA
Acquires PCA data:  Current
Sets:    stuff...
E.Yafuso
May 2019
"""

import edl_py
import numpy as np
import pyqtgraph
from PyQt5 import QtWidgets, uic
import collections, struct
import threading, time
import gc

class EDL(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_EDL = uic.loadUiType("EDLui.ui")[0]
        pyqtgraph.setConfigOption('background', 'k')
        self.ui = Ui_EDL()
        self.ui.setupUi(self)
        self.bAcquiring = False

        # if :
        #     bReply = QtWidgets.QMessageBox.information(self,
        #                                             'Elements ERROR',
        #                                             "e4 PCA Disconnected.")
        # else:
        #     self.bAcquiring = True

        #Signals to slots
        self.ui.showCh1.stateChanged.connect(self.ToggleChannelView)
        self.ui.showCh2.stateChanged.connect(self.ToggleChannelView)
        self.ui.showCh3.stateChanged.connect(self.ToggleChannelView)
        self.ui.showCh4.stateChanged.connect(self.ToggleChannelView)

        # Class attributes
        self.maxLen = 1000
        self.ch1data = collections.deque([0], self.maxLen)
        self.ch2data = collections.deque([0], self.maxLen)
        self.ch3data = collections.deque([0], self.maxLen)
        self.ch4data = collections.deque([0], self.maxLen)
        self.t = collections.deque([0], self.maxLen)

        self.yLimit = 200
        self.p1 = self.ui.Ch1Data.addPlot()
        self.p1.setRange(yRange=[0, self.yLimit])
        self.p1.showGrid(x=True, y=True, alpha=.8)
        self.p1.setLabel('left', 'Current', 'nA')
        self.p1.setLabel('bottom', 'Time (s)')
        self.p1.addLegend()

        self.p2 = self.ui.Ch2Data.addPlot()
        self.p2.setRange(yRange=[0, self.yLimit])
        self.p2.showGrid(x=True, y=True, alpha=.8)
        self.p2.setLabel('left', 'Current', 'nA')
        self.p2.setLabel('bottom', 'Time (s)')
        self.p2.addLegend()

        self.p3 = self.ui.Ch3Data.addPlot()
        self.p3.setRange(yRange=[0, self.yLimit])
        self.p3.showGrid(x=True, y=True, alpha=.8)
        self.p3.setLabel('left', 'Current', 'nA')
        self.p3.setLabel('bottom', 'Time (s)')
        self.p3.addLegend()
        
        self.p4 = self.ui.Ch4Data.addPlot()
        self.p4.setRange(yRange=[0, self.yLimit])
        self.p4.showGrid(x=True, y=True, alpha=.8)
        self.p4.setLabel('left', 'Current', 'nA')
        self.p4.setLabel('bottom', 'Time (s)')
        self.p4.addLegend()

        self.ch1plot = self.p1.plot([], pen=(0, 0, 255), linewidth=.5, name='Ch1')
        self.ch2plot = self.p2.plot([], pen=(0, 255, 0), linewidth=.5, name='Ch2')
        self.ch3plot = self.p3.plot([], pen=(255, 0, 0), linewidth=.5, name='Ch3')
        self.ch4plot = self.p4.plot([], pen=(255, 0, 255), linewidth=.5, name='Ch4')

        # self.DAQThread = threading.Thread(target=self.DataAcquisitionThread)
        # self.DAQThread.start()

        self.ui.Ch1Data.show()
        self.ui.Ch2Data.hide()
        self.ui.lCh2.hide()
        self.ui.Ch3Data.hide()
        self.ui.lCh3.hide()
        self.ui.Ch4Data.hide()
        self.ui.lCh4.hide()
        self.bShow = True
        self.bCanClose = False
        self.MoveToStart()

    def MoveToStart(self):
        ag = QtWidgets.QDesktopWidget().availableGeometry()
        sg = QtWidgets.QDesktopWidget().screenGeometry()
        wingeo = self.geometry()
        x = 100  # ag.width() - wingeo.width()
        y = 100  # 2 * ag.height() - sg.height() - wingeo.height()
        self.move(x, y)

    def ToggleChannelView(self):
        if self.ui.showCh1.isChecked() == True:
            self.ui.Ch1Data.show()
            self.ui.lCh1.show()
        else:
            self.ui.Ch1Data.hide()
            self.ui.lCh1.hide()
        if self.ui.showCh2.isChecked() == True:
            self.ui.Ch2Data.show()
            self.ui.lCh2.show()
        else:
            self.ui.Ch2Data.hide()
            self.ui.lCh2.hide()
        if self.ui.showCh3.isChecked() == True:
            self.ui.Ch3Data.show()
            self.ui.lCh3.show()
        else:
            self.ui.Ch3Data.hide()
            self.ui.lCh3.hide()
        if self.ui.showCh4.isChecked() == True:
            self.ui.Ch4Data.show()
            self.ui.lCh4.show()
        else:
            self.ui.Ch4Data.hide()
            self.ui.lCh4.hide()

    # def DataAcquisitionThread(self):
    #     data_in =
    #     self.t0 = time.time()
    #     count = 0
    #     while (self.bAcquiring):
    #         time.sleep(0.01)
    #         self.t.append(time.time()-self.t0)
    #         if self.AIOUSB.ADC_GetChannelV(-3, 0, ctypes.byref(data_in)) is 0:
    #             self.ch1data.append(float(data_in.value)/5*100)
    #         else: self.ch1data.append(0)
    #         if self.AIOUSB.ADC_GetChannelV(-3, 1, ctypes.byref(data_in)) is 0:
    #             self.ch2data.append(float(data_in.value)/5*100)
    #         else: self.ch2data.append(0)
    #         count += 1
    #         if count > 3:
    #             self.DataPlot()
    #             count = 0

    def DataPlot(self):
        self.ch1plot.setData(self.t, self.ch1data)
        self.ch2plot.setData(self.t, self.ch2data)
        self.ch3plot.setData(self.t, self.ch3data)
        self.ch4plot.setData(self.t, self.ch4data)
        gc.collect()

    def closeEvent(self, event):
        if self.bCanClose:
            self.bAcquiring = False
            if self.DAQThread != None:
                self.DAQThread.join()
            event.accept()
        else:
            self.bShow = False
            self.hide()
            event.ignore()
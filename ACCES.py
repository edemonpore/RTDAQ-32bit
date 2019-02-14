""" ACCES.py
Class for USB-AO16-16A
Acquires USB data:
    ACCES       USB-AO16-16A (x-y analog position feedback)
Sets USB data:
    ACCES      USB-AO16-16A (x-y-z position settings into PI E-664 LVPZT Servo)
E.Yafuso
Feb 2019
"""

import ctypes
import sys
import pyqtgraph
from PyQt5 import QtWidgets, uic
import collections, struct
import threading, time

class ACCES(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_ACCES = uic.loadUiType("ACCES.ui")[0]
        pyqtgraph.setConfigOption('background', 'k')
        self.ui = Ui_ACCES()
        self.ui.setupUi(self)
        self.AIOUSB = ctypes.CDLL("AIOUSB")
        self.bAcquiring = False

        if self.AIOUSB.DACSetBoardRange(-3, 2):  #2 = 0-10V
            bReply = QtWidgets.QMessageBox.question(self,
                                                    'AIOUSB ERROR',
                                                    "USB-AO16-16A Disconnected. Exit?",
                                                    QtWidgets.QMessageBox.Yes |
                                                    QtWidgets.QMessageBox.No,
                                                    QtWidgets.QMessageBox.No)
            if bReply == QtWidgets.QMessageBox.Yes:
                sys.exit(0)
        else:
            self.bAcquiring = True

        # Class attributes
        self.maxLen = 100

        self.xset = 0
        self.xsetdata = collections.deque([0], self.maxLen)
        self.yset = 0
        self.ysetdata = collections.deque([0], self.maxLen)
        self.zset = 0
        self.zsetdata = collections.deque([0], self.maxLen)

        self.fData  = bytearray(2)  # 16-bit data from USB-AO16-16A
        self.xdata  = collections.deque([0], self.maxLen)
        self.ydata  = collections.deque([0], self.maxLen)
        self.t      = collections.deque([0], self.maxLen)
        self.DAQThread = threading.Thread(target=self.DataAcquisitionThread)
        self.DAQThread.start()
        self.PlotThread = threading.Thread(target=self.DataPlotThread)
        self.PlotThread.start()
        self.setPI()

        self.ui.XData.setYRange(0, 100)
        self.ui.YData.setYRange(0, 100)
        self.ui.ZData.setYRange(0, 100)
        self.ui.vsX.setMinimum(0)
        self.ui.vsX.setMaximum(100)
        self.ui.vsX.setValue(self.xset/65535*100)
        self.ui.vsY.setMinimum(0)
        self.ui.vsY.setMaximum(100)
        self.ui.vsY.setValue(self.xset / 65535 * 100)
        self.ui.vsZ.setMinimum(0)
        self.ui.vsZ.setMaximum(100)
        self.ui.vsZ.setValue(self.xset / 65535 * 100)

        #Signals to slots
        self.ui.vsX.valueChanged.connect(self.setPI)
        self.ui.vsY.valueChanged.connect(self.setPI)
        self.ui.vsZ.valueChanged.connect(self.setPI)

        self.show()

    def setPI(self):
        DAQin = ctypes.c_int16()
        temp = self.ui.vsX.value()
        self.xset = int(temp*65535/100)
        self.ui.lxset.setText(str(temp))
        temp = self.ui.vsY.value()
        self.yset = int(temp * 65535 / 100)
        self.ui.lyset.setText(str(temp))
        temp = self.ui.vsZ.value()
        self.zset = int(temp * 65535 / 100)
        self.ui.lzset.setText(str(temp))

        DAQin.value = self.xset
        result = self.AIOUSB.DACDirect(-3, 0, DAQin)
        DAQin.value = self.yset
        result = self.AIOUSB.DACDirect(-3, 1, DAQin)
        DAQin.value = self.zset
        result = self.AIOUSB.DACDirect(-3, 2, DAQin)

    def DataAcquisitionThread(self):
        data_in = ctypes.c_float()
        while (self.bAcquiring):
            time.sleep(0.1)
            self.t.append(float(time.time()))
            if self.AIOUSB.ADC_GetChannelV(-3, 0, ctypes.byref(data_in)) is 0:
                self.fData = bytearray(struct.pack("f", data_in.value))
                value, = struct.unpack('f', self.fData)
                self.xdata.append(value)
            if self.AIOUSB.ADC_GetChannelV(-3, 1, ctypes.byref(data_in)) is 0:
                self.fData = bytearray(struct.pack("f", data_in.value))
                value, = struct.unpack('f', self.fData)
                self.ydata.append(value)
            self.xsetdata.append(self.xset)
            self.xsetdata.append(self.yset)
            self.xsetdata.append(self.zset)

    def DataPlotThread(self):
        penx = pyqtgraph.mkPen(color='b', width=1)
        penset = pyqtgraph.mkPen(color='r', width=1)
        peny = pyqtgraph.mkPen(color='g', width=1)
        while (self.bAcquiring):
            time.sleep(0.33)
            self.ui.XData.plot(self.xdata, pen=penx, clear=True)
            self.ui.YData.plot(self.ydata, pen=peny, clear=True)
            self.ui.XData.plot(self.xset, pen=penset, clear=True)
            self.ui.YData.plot(self.yset, pen=penset, clear=True)
            self.ui.ZData.plot(self.zset, pen=penset, clear=True)

    def Close(self):
        self.bAcquiring = False
        if self.DAQThread != None:
            self.DAQThread.join()
        sys.exit()

    def closeEvent(self, event):
        self.bAcquiring = False
        self.Close()
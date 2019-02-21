""" ACCES.py
Class for USB-AO16-16A
Acquires USB data:  x-y analog position feedback
Sets USB data:      x-y-z position settings into PI E-664 LVPZT Servo
E.Yafuso
Feb 2019
"""

import ctypes
import pandas
import numpy as np
import pyqtgraph
from PyQt5 import QtWidgets, uic
import collections
import threading, time

class ACCES(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_ACCES = uic.loadUiType("ACCESui.ui")[0]
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
        self.maxLen = 10

        self.xset = 0 #setpoints are in microns
        self.xsetdata = collections.deque([0], self.maxLen)
        self.yset = 0
        self.ysetdata = collections.deque([0], self.maxLen)
        self.zset = 0
        self.zsetdata = collections.deque([0], self.maxLen)

        self.fData  = bytearray(2)  # 16-bit data from USB-AO16-16A
        self.xdata  = collections.deque([0], self.maxLen)
        self.ydata  = collections.deque([0], self.maxLen)
        self.t      = collections.deque([0], self.maxLen)
        self.setPI()

        self.px = self.ui.XData.plot()
        self.py = self.ui.YData.plot()
        self.pz = self.ui.ZData.plot()
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
        self.ui.actionOpen.triggered.connect(self.OpenScriptDialog)

        # Set up plotting widgets
        self.show()

        self.ui.vsX.valueChanged.connect(self.setPI)
        self.ui.vsY.valueChanged.connect(self.setPI)
        self.ui.vsZ.valueChanged.connect(self.setPI)

        self.DAQThread = threading.Thread(target=self.DataAcquisitionThread)
        self.DAQThread.start()
        time.sleep(2)
        self.PlotThread = threading.Thread(target=self.DataPlotThread)
        self.PlotThread.start()
        self.show()

    def OpenScriptDialog(self):
        self.filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                              'Open file',
                                                              'C:\\Users\\User\\Desktop\\Demonpore\\Data',
                                                              "Demonpore Script (*.csv)")[0]
        if self.filename:
            temp = pandas.read_csv(self.filename, names=None, header = None)
            self.scriptfile = temp.replace(np.nan, '', regex=True)
            self.ExecuteScript()

    def ExecuteScript(self):
        rows = self.scriptfile.shape[0]
        self.script = self.scriptfile.as_matrix()
        print(self.script)
        for i in range(rows):
            cmd = self.script[i][0]
            if cmd != 'loop':
                self.ExecuteCmd(cmd, 0, i)
            else:
                nRepeat = int(self.script[i][1])
                start = i + 1
                for j in range(nRepeat):
                    k = 0
                    while str(self.script[start+k][0]) == '' and self.script[start+k][1]:
                        cmd = self.script[start+k][1]
                        self.ExecuteCmd(cmd, 1, start+k)
                        k += 1
                i = i + k

    def ExecuteCmd(self, cmd, nIndent, i):
        if cmd == 'wait':
            pause = float(self.script[i][1+nIndent]) / 1000 #wait in milliseconds
            time.sleep(pause)
        elif cmd == 'absolute':
            axis = self.script[i][1+nIndent]
            temp = float(self.script[i][2+nIndent])/1000 #script distances in nanometers
            if axis == 'x':
                self.xset = temp
            elif axis == 'y':
                self.yset = temp
            else:
                self.zset = temp
            self.setPI()
        elif cmd == 'relative':
            axis = self.script[i][1+nIndent]
            temp = float(self.script[i][2+nIndent]) / 1000
            if axis == 'x':
                self.xset = self.xset + temp
            elif axis == 'y':
                self.yset = self.yset + temp
            else:
                self.zset = self.zset + temp
            self.setPI()


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
        self.t0 = time.time()
        while (self.bAcquiring):
            time.sleep(0.01)
            self.t.append(time.time()-self.t0)
            self.xdata.append(value)
            self.ydata.append(value)
            if self.AIOUSB.ADC_GetChannelV(-3, 0, ctypes.byref(data_in)) is 0:
                self.fData = bytearray(struct.pack("f", data_in.value))
                value, = struct.unpack('f', self.fData)
                self.xdata.append(value)
            if self.AIOUSB.ADC_GetChannelV(-3, 1, ctypes.byref(data_in)) is 0:
                self.fData = bytearray(struct.pack("f", data_in.value))
                value, = struct.unpack('f', self.fData)
                self.ydata.append(value)
            self.xsetdata.append(self.xset)
            self.ysetdata.append(self.yset)
            self.zsetdata.append(self.zset)

    def DataPlotThread(self):
        while (self.bAcquiring):
            time.sleep(0.33)
            self.px.setData(self.t, self.xdata, pen=(0, 0, 255))
            #self.pxset = self.ui.XData.addItem(self.t, self.xsetdata)
            self.py.setData(self.t, self.ydata, pen=(0, 255, 0))
            self.pz.setData(self.t, self.zsetdata, pen=(127, 127, 127))

    def closeEvent(self, event):
        self.bAcquiring = False
        if self.DAQThread != None:
            self.DAQThread.join()
        event.accept()
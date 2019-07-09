
""" ACCES.py
Class for USB-AO16-16A
Acquires USB data:  x-y analog position feedback
Sets USB data:      x-y-z position settings into PI E-664 LVPZT Servo
E.Yafuso
March 2019
"""

import os
import ctypes
import pandas
import numpy as np
import pyqtgraph
from PyQt5 import QtWidgets, uic
import threading, time
# import collections, struct
# import gc
# import cProfile, pstats

class ACCES(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        path = os.path.abspath("") + '\\ACCES\\ACCESui.ui'
        try:
            Ui_ACCES = uic.loadUiType(path)[0]
        except:
            Ui_ACCES = uic.loadUiType('ACCESui.ui')[0]
        pyqtgraph.setConfigOption('background', 'k')
        self.ui = Ui_ACCES()
        self.ui.setupUi(self)
        self.AIOUSB = ctypes.CDLL("AIOUSB")
        self.AIOUSB.ADC_GetChannelV.argtypes = (ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.c_double))
        self.AIOUSB.ADC_GetChannelV.restype = ctypes.c_ulong
        self.DAQThread = 0

        # Class attributes
        self.bAcquiring = False
        self.bManual = True
        self.maxLen = 1000
        self.xsetdata = np.zeros(1, dtype=float)
        self.ysetdata = np.zeros(1, dtype=float)
        self.zsetdata = np.zeros(1, dtype=float)
        self.xdata = np.zeros(1, dtype=float)
        self.ydata = np.zeros(1, dtype=float)
        self.t = np.zeros(1, dtype=float)

        # Set stage at zero position
        self.xset = 0.0
        self.yset = 0.0
        self.zset = 0.0
        self.setPI()

        self.px = self.ui.XData.addPlot()
        self.px.setRange(yRange=[0, 100])
        self.px.showGrid(x=True, y=True, alpha=.8)
        self.px.setLabel('left', 'Position', 'microns')
        self.px.setLabel('bottom', 'Time (s)')
        self.px.addLegend()

        self.py = self.ui.YData.addPlot()
        self.py.setRange(yRange=[0, 100])
        self.py.showGrid(x=True, y=True, alpha=.8)
        self.py.setLabel('left', 'Position', 'microns')
        self.py.setLabel('bottom', 'Time (s)')
        self.py.addLegend()

        self.pz = self.ui.ZData.addPlot()
        self.pz.setRange(yRange=[0, 100])
        self.pz.showGrid(x=True, y=True, alpha=.8)
        self.pz.setLabel('left', 'Position', 'microns')
        self.pz.setLabel('bottom', 'Time (s)')
        self.pz.addLegend()

        self.xplot = self.px.plot([], pen=(0, 0, 255), linewidth=.5, name='x-pos')
        self.xsetplot = self.px.plot([], pen=(255, 0, 0), linewidth=.5, name='x-set')
        self.yplot = self.py.plot([], pen=(0, 255, 0), linewidth=.5, name='y-pos')
        self.ysetplot = self.py.plot([], pen=(255, 0, 0), linewidth=.5, name='y-set')
        self.zsetplot = self.pz.plot([], pen=(255, 0, 0), linewidth=.5, name='z-set')

        self.ui.vsX.setMinimum(0)
        self.ui.vsX.setMaximum(100)
        self.ui.vsX.setValue(self.xset)
        self.ui.vsY.setMinimum(0)
        self.ui.vsY.setMaximum(100)
        self.ui.vsY.setValue(self.yset)
        self.ui.vsZ.setMinimum(0)
        self.ui.vsZ.setMaximum(100)
        self.ui.vsZ.setValue(self.zset)

        #Signals to slots
        self.ui.actionOpen.triggered.connect(self.OpenScriptDialog)
        self.ui.vsX.valueChanged.connect(self.setPI)
        self.ui.vsY.valueChanged.connect(self.setPI)
        self.ui.vsZ.valueChanged.connect(self.setPI)

        #Start data acquisition thread
        if self.AIOUSB.DACSetBoardRange(-3, 2):  #2 = 0-10V
            bReply = QtWidgets.QMessageBox.information(self,
                                                    'AIOUSB ERROR',
                                                    "USB-AO16-16A Disconnected.")
        else:
            self.bAcquiring = True

        self.bShow = True
        self.MoveToStart()

    def MoveToStart(self):
        ag = QtWidgets.QDesktopWidget().availableGeometry()
        sg = QtWidgets.QDesktopWidget().screenGeometry()
        wingeo = self.geometry()
        x = 100  # ag.width() - wingeo.width()
        y = 100  # 2 * ag.height() - sg.height() - wingeo.height()
        self.move(x, y)

    def setPI(self):
        if self.bManual:
            self.xset = self.ui.vsX.value()
            self.ui.lxset.setText(str(self.xset))
            self.yset = self.ui.vsY.value()
            self.ui.lyset.setText(str(self.yset))
            self.zset = self.ui.vsZ.value()
            self.ui.lzset.setText(str(self.zset))
        else:
            self.ui.vsX.setValue(self.xset)
            self.ui.lxset.setText(str(self.xset))
            self.ui.vsY.setValue(self.yset)
            self.ui.lyset.setText(str(self.yset))
            self.ui.vsZ.setValue(self.zset)
            self.ui.lzset.setText(str(self.zset))
            self.bManual = True

        if self.bAcquiring:
            DAQin = ctypes.c_int16()
            DAQin.value = int(self.xset * 65535 / 100)
            result = self.AIOUSB.DACDirect(-3, 0, DAQin)
            DAQin.value = int(self.yset * 65535 / 100)
            result = self.AIOUSB.DACDirect(-3, 1, DAQin)
            DAQin.value = int(self.zset * 65535 / 100)
            result = self.AIOUSB.DACDirect(-3, 2, DAQin)

    def moveAxes(self, dx, dy, dz):
        self.bManual = False

        self.xset = self.xset + dx
        if self.xset > 100.0: self.xset = 100.0
        if self.xset < 0.0: self.xset = 0.0

        self.yset = self.yset + dy
        if self.yset > 100.0: self.yset = 100.0
        if self.yset < 0.0: self.yset = 0.0

        self.zset = self.zset + dz
        if self.zset > 100.0: self.zset = 100.0
        if self.zset < 0.0: self.zset = 0.0

        self.setPI()

    def UpdateData(self):
        data_in = ctypes.c_longdouble()  # double-precision IEEE floating point data from ADC
        if self.AIOUSB.ADC_GetChannelV(-3, 0, ctypes.byref(data_in)) is 0:
            self.xdata = np.append(self.xdata, float(data_in.value) * 20)  # Convert 0-5V to 0-100nm
        else:
            self.xdata = np.append(self.xdata, 0)
        if self.AIOUSB.ADC_GetChannelV(-3, 1, ctypes.byref(data_in)) is 0:
            self.ydata = np.append(self.ydata, float(data_in.value) * 20)
        else:
            self.ydata = np.append(self.ydata, 0)
        self.xsetdata = np.append(self.xsetdata, self.xset)
        self.ysetdata = np.append(self.ysetdata, self.yset)
        self.zsetdata = np.append(self.zsetdata, self.zset)

        if __debug__ and not self.bAcquiring:
            self.t = np.append(self.t, time.time())
            self.xdata = np.append(self.xdata, (np.sin(self.t[-1])+1)*50)
            self.ydata = np.append(self.ydata, (np.sin(self.t[-1] + 1)+1)*50)
            self.xsetdata = np.append(self.xsetdata, self.xset)
            self.ysetdata = np.append(self.ysetdata, self.yset)
            self.zsetdata = np.append(self.zsetdata, self.zset)

    def DataAcquisitionThread(self):
        self.t0 = time.time()

        while (self.bAcquiring):
            time.sleep(0.01)
            self.t = np.append(self.t, time.time()-self.t0)
            self.UpdateData()
            self.DataPlot()

        if __debug__ and not self.bAcquiring:
            while True:
                time.sleep(.01)
                self.t = np.append(self.t, time.time() - self.t0)
                self.xdata = np.append(self.xdata, (np.sin(self.t[-1])+1)*50)
                self.ydata = np.append(self.ydata, (np.sin(self.t[-1] + 1)+1)*50)
                self.xsetdata = np.append(self.xsetdata, self.xset)
                self.ysetdata = np.append(self.ysetdata, self.yset)
                self.zsetdata = np.append(self.zsetdata, self.zset)
                self.DataPlot()

    def DataPlot(self):
        self.xplot.setData(self.t[-self.maxLen:], self.xdata[-self.maxLen:])
        self.xsetplot.setData(self.t[-self.maxLen:], self.xsetdata[-self.maxLen:])
        self.yplot.setData(self.t[-self.maxLen:], self.ydata[-self.maxLen:])
        self.ysetplot.setData(self.t[-self.maxLen:], self.ysetdata[-self.maxLen:])
        self.zsetplot.setData(self.t[-self.maxLen:], self.zsetdata[-self.maxLen:])

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

    def closeEvent(self, event):
        self.bAcquiring = False
        if self.DAQThread and self.DAQThread != None:
            self.DAQThread.join()
        event.accept()
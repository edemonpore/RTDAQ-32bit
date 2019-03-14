""" ACCES.py
Class for USB-AO16-16A
Acquires USB data:  x-y analog position feedback
Sets USB data:      x-y-z position settings into PI E-664 LVPZT Servo
E.Yafuso
March 2019
"""

import ctypes
import pandas
import numpy as np
import pyqtgraph
from PyQt5 import QtWidgets, uic
import collections, struct
import threading, time

class ACCES(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_ACCES = uic.loadUiType("ACCESui.ui")[0]
        pyqtgraph.setConfigOption('background', 'k')
        self.ui = Ui_ACCES()
        self.ui.setupUi(self)
        self.AIOUSB = ctypes.CDLL("AIOUSB")
        self.AIOUSB.ADC_GetChannelV.argtypes = (ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.c_double))
        self.AIOUSB.ADC_GetChannelV.restype = ctypes.c_ulong

        self.bAcquiring = False

        if self.AIOUSB.DACSetBoardRange(-3, 2):  #2 = 0-10V
            bReply = QtWidgets.QMessageBox.information(self,
                                                    'AIOUSB ERROR',
                                                    "USB-AO16-16A Disconnected.")
        else:
            self.bAcquiring = True

        # Class attributes
        self.maxLen = 1000
        self.xsetdata = collections.deque([0], self.maxLen)
        self.ysetdata = collections.deque([0], self.maxLen)
        self.zsetdata = collections.deque([0], self.maxLen)
        self.xdata  = collections.deque([0], self.maxLen)
        self.ydata  = collections.deque([0], self.maxLen)
        self.t      = collections.deque([0], self.maxLen)

        self.xset = 0
        self.yset = 0
        self.zset = 0
        self.setPI()

        self.px = self.ui.XData.addPlot()
        self.px.setRange(yRange=[0, 100])
        self.px.showGrid(x=True, y=True, alpha=.8)
        self.px.setLabel('left', 'Position', 'microns')
        self.px.setLabel('bottom', 'Time (s)')
        self.py = self.ui.YData.addPlot()
        self.py.setRange(yRange=[0, 100])
        self.py.showGrid(x=True, y=True, alpha=.8)
        self.py.setLabel('left', 'Position', 'microns')
        self.py.setLabel('bottom', 'Time (s)')
        self.pz = self.ui.ZData.addPlot()
        self.pz.setRange(yRange=[0, 100])
        self.pz.showGrid(x=True, y=True, alpha=.8)
        self.pz.setLabel('left', 'Position', 'microns')
        self.pz.setLabel('bottom', 'Time (s)')

        self.px.addLegend()
        self.py.addLegend()
        self.pz.addLegend()
        self.xplot = self.px.plot([], pen=(0, 0, 255), linewidth=.5, name='x-pos')
        self.xsetplot = self.px.plot([], pen=(255, 0, 0), linewidth=.5, name='x-set')
        self.yplot = self.py.plot([], pen=(0, 255, 0), linewidth=.5, name='y-pos')
        self.ysetplot = self.py.plot([], pen=(255, 0, 0), linewidth=.5, name='y-set')
        self.zsetplot = self.pz.plot([], pen=(255, 0, 0), linewidth=.5, name='z-set')

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
        self.ui.vsX.valueChanged.connect(self.setPI)
        self.ui.vsY.valueChanged.connect(self.setPI)
        self.ui.vsZ.valueChanged.connect(self.setPI)

        self.DAQThread = threading.Thread(target=self.DataAcquisitionThread)
        self.DAQThread.start()

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


    def setPI(self):
        temp = self.ui.vsX.value()
        self.xset = int(temp*65535/100)
        self.ui.lxset.setText(str(temp))
        temp = self.ui.vsY.value()
        self.yset = int(temp * 65535 / 100)
        self.ui.lyset.setText(str(temp))
        temp = self.ui.vsZ.value()
        self.zset = int(temp * 65535 / 100)
        self.ui.lzset.setText(str(temp))

        DAQin = ctypes.c_int16()
        DAQin.value = self.xset
        result = self.AIOUSB.DACDirect(-3, 0, DAQin)
        DAQin.value = self.yset
        result = self.AIOUSB.DACDirect(-3, 1, DAQin)
        DAQin.value = self.zset
        result = self.AIOUSB.DACDirect(-3, 2, DAQin)

    def DataAcquisitionThread(self):
        data_in = ctypes.c_longdouble() # double-precision IEEE floating point data from ADC
        self.t0 = time.time()
        count = 0
        while (self.bAcquiring):
            time.sleep(0.01)
            self.t.append(time.time()-self.t0)
            if self.AIOUSB.ADC_GetChannelV(-3, 0, ctypes.byref(data_in)) is 0:
                self.xdata.append(float(data_in.value)/5*100)
            else: self.xdata.append(0)
            if self.AIOUSB.ADC_GetChannelV(-3, 1, ctypes.byref(data_in)) is 0:
                self.ydata.append(float(data_in.value)/5*100)
            else: self.ydata.append(0)
            self.xsetdata.append(self.xset*100/65535)
            self.ysetdata.append(self.yset*100/65535)
            self.zsetdata.append(self.zset*100/65535)
            count += 1
            if count > 3:
                self.DataPlot()
                count = 0

    def DataPlot(self):
        self.xplot.setData(self.t, self.xdata)
        self.xsetplot.setData(self.t, self.xsetdata)
        self.yplot.setData(self.t, self.ydata)
        self.ysetplot.setData(self.t, self.ysetdata)
        self.zsetplot.setData(self.t, self.zsetdata)

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
        if self.bCanClose:
            self.bAcquiring = False
            if self.DAQThread != None:
                self.DAQThread.join()
            event.accept()
        else:
            self.bShow = False
            self.hide()
            event.ignore()
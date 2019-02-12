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
import numpy as np
import sys
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import collections, struct
import threading, time

class ACCES(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_ACCES = uic.loadUiType("ACCES.ui")[0]
        self.ui = Ui_ACCES()
        self.ui.setupUi(self)
        AIOUSB = ctypes.CDLL("AIOUSB")
        self.bAcquiring = False

        if AIOUSB.DACSetBoardRange(-3, 2):  # 2 = 0-10V
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
        # Set up plotting widgets
        self.xset  = 0
        self.xdata = self.ui.XData.addPlot()
        self.yset  = 0
        self.ydata = self.ui.YData.addPlot()
        self.zset  = 0
        #self.zdata = self.ui.ZData.addPlot()

        # Class attributes
        self.maxLen = 100
        self.fData = bytearray(2) #16-bit data from USB-AO16-16A
        self.data = collections.deque([0] * 100, maxlen=100)
        self.DAQThread = None
        self.bRx = False
        self.t0 = 0

        self.show()

#        result = AIOUSB.DACDirect(-3, 0, 0)

    def bPlot(self):
        if self.bAcquiring is False:
            return
        maxPlotLength = 100
        self.ReadData()

        # Data Plotting...
        pltInterval = 33 #30 fps for general screen updates
        xmin = 0
        xmax = maxPlotLength
        ymin = -1
        ymax = 1
        ax = plt.axes(xlim=(xmin, xmax), ylim=(float(ymin-(ymax-ymin)/10), float(ymax+(ymax-ymin)/10)))
        ax.set_title('Analog Data')
        ax.set_xlabel("Time")
        ax.set_ylabel("mV")

        #Raw Data and Set Potential
        for i in range(1): #ED.Channels):
            self.rawdata.plot(t, self.ED.current[:,i], pen='c', linewidth=.05)
        self.xset.plot(t, self.x-set, pen='r', linewidth=.5, name='X-Setpoint')
        self.xset.plot(t, self.xdata, pen='b', linewidth=.5, name='X-Feedback')
        self.xset.showGrid(x=True, y=True, alpha=.8)
        self.xset.addLegend()
        self.xset.setLabel('left', 'Position', 'nm')
        self.xset.setLabel('bottom', 'Time (s)')

    def ReadData(self):
        if self.DAQThread == None:
            self.DAQThread = threading.Thread(target=self.AnalogDataThread)
            self.DAQThread.start()
            self.bAcuiring = True
            # Block till we start receiving values
            while self.bRx != True:
                time.sleep(0.1)

    def AnalogDataThread(self):    # retrieve data
        time.sleep(1.0)  # give some buffer time for retrieving data
        data_in = c_float()
        while (self.bAcquiring):
            if AIOUSB.ADC_GetChannelV(-3, 0, byref(data_in)) is 0:
                data_in.value = np.sin(float(time.time()))
                self.fData = bytearray(struct.pack("f", data_in.value))
                self.bRx = True
            else:
                self.fData.append(1)

    def DatataPlot(self, frame, lines, lineValueText, lineLabel, timeText):
        t1 = time.perf_counter()
        self.plotTimer = int((t1 - self.t0) * 1000)  # the first reading will be erroneous
        self.t0 = t1
        timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')
        value, = struct.unpack('f', self.fData)
        self.data.append(value)
        lines.set_data(range(self.maxLen), self.data)
        lineValueText.set_text('[' + lineLabel + '] = ' + str(value))

    def Close(self):
        self.bAcquiring = False
        if self.DAQThread != None:
            self.DAQThread.join()
        sys.exit()

    def closeEvent(self,event):
        self.bAcquiring = False
        self.Close()
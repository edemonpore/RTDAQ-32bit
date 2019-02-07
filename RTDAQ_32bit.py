""" RTDAQ_32bit.py
Acquire USB data from:
    Elements    PCA (current)
    ACCES       USB-AO16-16A (x-y analog position feedback)
Set USB data to:
    Elements    PCA (Potential, sample rate, etc.)
    ACCESS      USB-AO16-16A (x-y-z position settings into PI E-664 LVPZT Servo)
E.Yafuso
Feb 2019
"""

from ctypes import *
import numpy as np
import sys, glob
import string
from matplotlib import pyplot as plt
from matplotlib import animation as animation
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import collections, struct
import threading, time

WINDOWS = False
if sys.platform.startswith('win'):
    from winreg import *
    WINDOWS = True
    ports = ['COM%s' % (i + 1) for i in range(256)]
elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
    ports = glob.glob('/dev/tty[A-Za-z]*')
elif sys.platform.startswith('darwin'):
    ports = glob.glob('/dev/tty.*')
else:
    raise EnvironmentError('Unsupported platform')

# Establish access to libraries:
# Elements
libMPSSE = CDLL("libMPSSE")
edl = CDLL("edl")

# ACCES-IO
AIOUSB = CDLL("AIOUSB")


##########################################################
################# Main Dialog Window #####################
##########################################################

Ui_RTDAQ = uic.loadUiType("RTDAQ_32bit.ui")[0]

class RTDAQApp(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_RTDAQ()
        self.ui.setupUi(self)
        if AIOUSB.DACSetBoardRange(-3, 2):  # 2 = 0-10V
            self.bAcuiring = False
            print("DAQ Error:")
        else:
            self.bAcquiring = True

        # Class attributes
        self.maxLen = 100
        self.fData = bytearray(2) #16-bit data from USB-AO16-16A
        self.data = collections.deque([0] * 100, maxlen=100)
        self.DAQThread = None
        self.bRx = False
        self.t0 = 0

        # Signals to slots
        self.ui.bGetPorts.clicked.connect(self.GetPorts)
        self.ui.bAcquire.clicked.connect(self.bPlot)
        self.ui.bQuit.clicked.connect(self.Done)

    # Find port
    def GetPorts(self):

        if WINDOWS:
            bitmask = windll.kernel32.GetLogicalDrives()

            # Alphabetic list of uppercase letters
            self.ui.lPorts.clear()
            AIOUSB.AIOUSB_ReloadDeviceLinks()
            self.ui.lPorts.addItem('--Drives:--')
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    self.ui.lPorts.addItem(letter)
                bitmask >>= 1
            self.ui.lPorts.addItem('')
            print("devices", AIOUSB.GetDevices())
            if AIOUSB.GetDevices() != 0:
                self.ui.lPorts.addItem('--Devices:--')
                sn = c_longlong()
                AIOUSB.GetDeviceSerialNumber(-3, byref(sn))
                self.ui.lPorts.addItem("ACCES USB-AO16-16A  Serial: "+str(sn.value))

#        result = AIOUSB.DACDirect(-3, 0, 0)

    def bPlot(self):

        maxPlotLength = 100
        dataNumBytes = 2
        self.ReadData()

        # Data Plotting...
        pltInterval = 33 #30 fps for general screen updates
        xmin = 0
        xmax = maxPlotLength
        ymin = -1
        ymax = 1
        self.fig = plt.figure('DAQ Position Feedback', figsize=(30,10))
        ax = plt.axes(xlim=(xmin, xmax), ylim=(float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10)))
        ax.set_title('Analog Data')
        ax.set_xlabel("Time")
        ax.set_ylabel("mV")

        lineLabel = 'Analog Value'
        timeText = ax.text(0.50, 0.95, '', transform=ax.transAxes)
        lines = ax.plot([], [], label=lineLabel)[0]
        lineValueText = ax.text(0.50, 0.90, '', transform=ax.transAxes)
        self.FuncAnim = animation.FuncAnimation(self.fig,
                                self.DatataPlot,
                                fargs=(lines, lineValueText, lineLabel, timeText),
                                interval=pltInterval)
        plt.legend(loc="upper left")
        plt.show()

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

    def Done(self):
        self.bAcquiring = False
        if self.DAQThread != None:
            self.DAQThread.join()
        plt.close('DAQ Position Feedback')
        self.close()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = RTDAQApp()
    window.show()
    sys.exit(app.exec_())

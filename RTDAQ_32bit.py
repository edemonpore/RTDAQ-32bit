""" RTDAQ_32bit.py
Acquire USB data from:
    Elements    PCA (current)
    ACCES       USB-AO16-16A (x-y analog position feedback)
Set USB data to:
    Elements    PCA (Potential, sample rate, etc.)
    ACCESS      USB-AO16-16A (x-y-z position settings into PI E-664 LVPZT Servo)
E.Yafuso
Jan 2019
"""

from ctypes import *
import usb.core
import sys, glob, serial.tools.list_ports
import string
from collections import deque
from matplotlib import pyplot as plt
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import _thread, time

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

        # Signals to slots
        self.ui.bGetPorts.clicked.connect(self.get_ports)
        self.ui.bQuit.clicked.connect(self.close)

        # Class attributes
        AIOUSB.DACSetBoardRange(-3, 2) # 2 = 0-10V
        self.bPlot()

    # Find port
    def get_ports(self):
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

        data = c_float()
        analogData = AnalogData(100)
        analogPlot = AnalogPlot(analogData)

        while True:
            try:
                AIOUSB.ADC_GetChannelV(-3, 0, byref(data))
                if (len(data) == 1):
                    analogData.add(float(data.value))
                    analogPlot.update(analogData)
            except KeyboardInterrupt:
                print('Keyboard interrupt. Exiting')
                break

# class that holds analog data for N samples
class AnalogData:

    def __init__(self, maxLen):
        self.ax = deque([0.0] * maxLen)
        self.maxLen = maxLen

    # Ring buffer
    def addToBuf(self, buf, val):
        if len(buf) < self.maxLen:
            buf.append(val)
        else:
            buf.pop()
            buf.appendleft(val)

    # Add data
    def add(self, data):
        assert (len(data) == 1)
        self.addToBuf(self.ax, data[0])

# plot class
class AnalogPlot:

    def __init__(self, analogData):
        # set plot to animated
        plt.ion()
        self.axline, = plt.plot(analogData.ax)
        plt.ylim([0, 400])

    def update(self, analogData):
        self.axline.set_ydata(analogData.ax)
        plt.draw()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = RTDAQApp()
    window.show()
    sys.exit(app.exec_())

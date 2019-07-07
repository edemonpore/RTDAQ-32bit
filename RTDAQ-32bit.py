""" RTDAQ_32bit.py
Acquire USB data:
    Elements    PCA (current)
    ACCES       USB-AO16-16A (x-y analog position feedback)
Set USB data:
    Elements    PCA (Potential, sample rate, etc.)
    ACCES       USB-AO16-16A (x-y-z position settings into PI E-664 LVPZT Servo)
E.Yafuso
Feb 2019
"""

import sys, glob
import numpy as np
import string
import ctypes
from PyQt5 import QtWidgets, uic

import threading, time
import Video
import ACCES
import EDL
import uF

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


##########################################################
################# Main Dialog Window #####################
##########################################################

class RTDAQApp(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        Ui_RTDAQ = uic.loadUiType("RTDAQ-32bitui.ui")[0]
        self.ui = Ui_RTDAQ()
        self.ui.setupUi(self)
        self.bAcquiring = False

        # Signals to slots
        self.ui.bGetPorts.clicked.connect(self.GetPorts)
        self.ui.bVideo.clicked.connect(self.VideoShow)
        self.ui.bNanoControl.clicked.connect(self.NanoWindowShow)
        self.ui.bElements.clicked.connect(self.ElementsShow)

        # Real-time data...
        self.t = np.zeros(1, dtype=float)

        self.show()

        # Externally developed classes
        self.VidWin = Video.VidWin()
        self.VidWin.show()
        self.NanoControl = ACCES.ACCES()
        self.NanoControl.show()
        self.Elements = EDL.EDL()
        self.Elements.show()
        self.uF = uF.uF()
        self.uF.show()

        # Start real-time data acquisition thread
        self.DAQThread = threading.Thread(target=self.DataAcquisitionThread, daemon=True)
        self.DAQThread.start()

    def DataAcquisitionThread(self):
        self.t0 = time.time()

        while True:
            time.sleep(0.01)
            self.t = np.append(self.t, time.time() - self.t0)
            self.UpdateData()
            self.DataPlot()

    def UpdateData(self):
        self.NanoControl.UpdateData()

    def DataPlot(self):
        pass

    def GetPorts(self):
        if WINDOWS:
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()

            # Alphabetic list of uppercase letters
            self.ui.lPorts.clear()
            self.NanoControl.AIOUSB.AIOUSB_ReloadDeviceLinks()
            self.ui.lPorts.addItem('--Drives:--')
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    self.ui.lPorts.addItem(letter)
                bitmask >>= 1
            self.ui.lPorts.addItem('')
            if self.NanoControl.AIOUSB.GetDevices() != 0:
                self.ui.lPorts.addItem('--Devices:--')
                sn = ctypes.c_longlong()
                self.NanoControl.AIOUSB.GetDeviceSerialNumber(-3, ctypes.byref(sn))
                self.ui.lPorts.addItem("ACCES USB-AO16-16A  Serial: "+str(sn.value))

    def VideoShow(self):
        if self.VidWin.bShow:
            self.VidWin.hide()
            self.VidWin.bShow = False
        else:
            self.VidWin.show()
            self.VidWin.bShow = True

    def NanoWindowShow(self):
        if self.NanoControl.bShow:
            self.NanoControl.hide()
            self.NanoControl.bShow = False
        else:
            self.NanoControl.show()
            self.NanoControl.bShow = True

    def ElementsShow(self):
        if self.Elements.bShow:
            self.Elements.hide()
            self.Elements.bShow = False
        else:
            self.Elements.show()
            self.Elements.bShow = True

    def Close(self):
        self.VidWin.bCanClose = self.NanoControl.bCanClose = True
        self.VidWin.close()
        self.NanoControl.close()
        self.Elements.close()

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self,
                                           'RTDAQ Quit all',
                                           "Quit?",
                                           QtWidgets.QMessageBox.Yes,
                                           QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.Close()
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    AppWindow = RTDAQApp()
    sys.exit(app.exec_())

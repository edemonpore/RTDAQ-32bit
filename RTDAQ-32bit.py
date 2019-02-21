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
import string
import ctypes
from PyQt5 import QtCore, QtGui, QtWidgets, uic

import Video
import ACCES

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
        Ui_RTDAQ = uic.loadUiType("RTDAQ-32bit.ui")[0]
        self.ui = Ui_RTDAQ()
        self.ui.setupUi(self)
        self.bAcquiring = False

        # Externally developed classes
        self.VidWin = Video.VidWin()
        self.NanoControl = ACCES.ACCES()

        # Signals to slots
        self.ui.bGetPorts.clicked.connect(self.GetPorts)

        self.show()

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
                sn = c_longlong()
                self.NanoControl.AIOUSB.GetDeviceSerialNumber(-3, byref(sn))
                self.ui.lPorts.addItem("ACCES USB-AO16-16A  Serial: "+str(sn.value))

    def Close(self):
        self.VidWin.close()
        self.NanoControl.close()
        sys.exit()

    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self,
                                           'RTDAQ Quit Received',
                                           "Quit?",
                                           QtGui.QMessageBox.Yes,
                                           QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.Close()
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    AppWindow = RTDAQApp()
    sys.exit(app.exec_())

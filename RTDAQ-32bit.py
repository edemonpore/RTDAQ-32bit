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
#import Video
import ACCES
import EDL
#import uF

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
        self.ui.pbREC.setStyleSheet("background-color:rgb(255,0,0)")
        self.ui.pbREC.clicked.connect(self.ToggleRecording)
        self.ui.bGetPorts.clicked.connect(self.GetPorts)
       # self.ui.bVideo.clicked.connect(self.VideoShow)
        self.ui.bNanoControl.clicked.connect(self.NanoWindowShow)
        self.ui.bElements.clicked.connect(self.ElementsShow)
        #self.ui.buF.clicked.connect(self.uFluidicsShow)

        # Class attributes
        self.bRecord = False

        # Real-time data...
        self.t = np.zeros(1, dtype=float)

        self.show()

        # Externally developed classes
        #self.VidWin = Video.VidWin()
        #self.VidWin.show()
        self.NanoControl = ACCES.ACCES()
        self.NanoControl.show()
        #self.uF = uF.uF()
        #self.uF.show()
        self.Elements = EDL.EDL()
        self.Elements.show()

        # Start real-time data acquisition thread
        self.DAQProcess = threading.Thread(target=self.DataAcquisitionProcess)
        self.DAQProcess.start()

    def DataAcquisitionProcess(self):
        self.InitDataArrays()
        self.t0 = self.t = time.time()
        while True:
            time.sleep(0.01)
            self.UpdateData(self.t)
            self.DataPlot()

    def UpdateData(self, t):
        self.t = np.append(self.t, time.time()-self.t0)
        self.NanoControl.UpdateData(self.t)
        self.Elements.UpdateData()
        #self.uF.UpdateData(self.t)
        if self.bRecord:
            self.ui.pbREC.setText("RECORDING: ", self.t[-1])

    def DataPlot(self):
        self.NanoControl.DataPlot(self.t)
        self.Elements.DataPlot()
        #self.uF.DataPlot(self.t)

    def ToggleRecording(self):
        if self.bRecord == False:
            self.bRecord = True
            self.ui.pbREC.setStyleSheet("background-color:rgb(0,255,0)")
            self.ui.pbREC.setText("RECORDING")
            self.InitDataArrays()
        else:
            self.bRecord = False
            self.ui.pbREC.setStyleSheet("background-color:rgb(255,0,0)")
            self.ui.pbREC.setText("RECORDING STOPPED")
            if QtWidgets.QMessageBox.question(self, 'Save data run?', "Save last run to file?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
                savefilename = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                      'Save data to file',
                                                                      'C:\\',
                                                                      "Demonpore Data Files (*.csv)")[0]
                self.SaveData(savefilename)

    def InitDataArrays(self):
        self.NanoControl.xsetdata = np.zeros(1, dtype=float)
        self.NanoControl.ysetdata = np.zeros(1, dtype=float)
        self.NanoControl.zsetdata = np.zeros(1, dtype=float)
        self.NanoControl.xdata = np.zeros(1, dtype=float)
        self.NanoControl.ydata = np.zeros(1, dtype=float)

        self.Elements.InitDataArrays()

        # self.uF.Psetdata = np.zeros(1, dtype=float)
        # self.uF.Pdata = np.zeros(1, dtype=float)
        # self.uF.Flowdata = np.zeros(1, dtype=float)

        self.t[0] = self.Elements.t[0] = time.time()

    def SaveData(self, savefilename):
        DataToSave = np.column_stack((self.t,
                                      self.Elements.t,
                                      self.Elements.vHolddata,
                                      self.Elements.ch1data,
                                      self.Elements.ch2data,
                                      self.Elements.ch3data,
                                      self.Elements.ch4data,
                                      self.NanoControl.xsetdata,
                                      self.NanoControl.ysetdata,
                                      self.NanoControl.zsetdata,
                                      self.NanoControl.xdata,
                                      self.NanoControl.ydata))
                                      # self.uF.Psetdata,
                                      # self.uF.Pdata,
                                      # self.uF.Flowdata))

        np.savetxt(savefilename,
                   DataToSave,
                   delimiter=',',
                   header='Time,PCATime,VHold,PCA1,PCA2,PCA3,PCA4,XSET,YSET,ZSET,XPOS,YPOS,PSET,PDAT,FLOW',
                   comments='')


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

    # def VideoShow(self):
    #     if self.VidWin.bShow:
    #         self.VidWin.hide()
    #         self.VidWin.bShow = False
    #     else:
    #         self.VidWin.show()
    #         self.VidWin.bShow = True

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

    # def uFluidicsShow(self):
    #     if self.uF.bShow:
    #         self.uF.hide()
    #         self.uF.bShow = False
    #     else:
    #         self.uF.show()
    #         self.uF.bShow = True

    def Close(self):
        self.VidWin.close()
        self.NanoControl.close()
        self.Elements.close()
        #self.uF.close()

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self,
                                           'RTDAQ Quit all',
                                           "Quit?",
                                           QtWidgets.QMessageBox.Yes,
                                           QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            if self.DAQProcess != None:
                self.DAQProcess.join()
            self.Close()
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    AppWindow = RTDAQApp()
    sys.exit(app.exec_())

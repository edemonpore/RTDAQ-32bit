""" EDL.py
Class for Elements 4-Channel PCA
Acquires PCA data:  Current
Sets: Current sensing range, potential, polarity, sampling rate, sample filter,
E.Yafuso
Latest revision, June 2019
"""

import os
import edl_py
import edl_py_constants as epc
from localtools import ElementsData
import pyqtgraph as pg
import numpy as np
from PyQt5 import QtWidgets, uic
import threading, time

class EDL(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        path = os.path.abspath("") + '\\EDL\\EDLui.ui'
        try:
            Ui_EDL = uic.loadUiType(path)[0]
        except:
            Ui_EDL = uic.loadUiType('EDLui.ui')[0]
        pg.setConfigOption('background', 'k')
        self.ui = Ui_EDL()
        self.ui.setupUi(self)
        self.bRun = True
        self.bAcquiring = False
        self.DAQThread = None


        # Class attributes
        self.maxLen = 1000
        self.InitDataArrays()
        self.DetectionThreshold = 0
        self.LatestPackets = 0

        # Initialize EDL class object
        self.edl = edl_py.EDL_PY()

        # String list to collect detected devices
        self.devices = [""] * 0

        # User settings, initialized to defaults from CC (May 2019)
        self.bVoltagePositive = True
        self.ui.sbVhold.setRange(-500, 500)
        self.ui.sbVhold.setValue(0)
        self.Range = epc.EDL_PY_RADIO_RANGE_200_NA
        self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_1_25_KHZ
        self.t_step = 1 / 100
        self.BandwidthDivisor = epc.EDL_PY_RADIO_FINAL_BANDWIDTH_SR_2
        self.UpdateSettings()
        self.SetPotential()

        # User settings, threshold for event detection
        self.DetectionThreshold = 0
        self.bThresholdPositive = True
        self.ui.sbThreshold.setRange(-500, 500)
        self.ui.sbThreshold.setValue(0)

        # User settings, preset nanoposition response to event detection
        self.XMove = 0
        self.YMove = 0
        self.ZMove = 0
        self.ui.sbMoveX.setRange(-100, 100)
        self.ui.sbMoveX.setValue(0)
        self.ui.sbMoveY.setRange(-100, 100)
        self.ui.sbMoveY.setValue(0)
        self.ui.sbMoveZ.setRange(-100, 100)
        self.ui.sbMoveZ.setValue(0)

        #Signals to slots (Tab 1)
        self.ui.pbCompensateDigitalOffset.clicked.connect(self.CompensateDigitalOffset)
        self.ui.showVhold.stateChanged.connect(self.ToggleChannelView)
        self.ui.showCh1.stateChanged.connect(self.ToggleChannelView)
        self.ui.showCh2.stateChanged.connect(self.ToggleChannelView)
        self.ui.showCh3.stateChanged.connect(self.ToggleChannelView)
        self.ui.showCh4.stateChanged.connect(self.ToggleChannelView)
        #Signals to slots (Tab 2)
        self.ui.sbVhold.valueChanged.connect(self.SetPotential)
        self.ui.pbPolarity.clicked.connect(self.ToggleVoltagePolarity)
        self.ui.pbPolarity.setToolTip('Toggle Voltage Polarity')
        self.ui.rb200pA.clicked.connect(self.UpdateSettings)
        self.ui.rb2nA.clicked.connect(self.UpdateSettings)
        self.ui.rb20nA.clicked.connect(self.UpdateSettings)
        self.ui.rb200nA.clicked.connect(self.UpdateSettings)
        self.ui.rb1_25KHz.clicked.connect(self.UpdateSettings)
        self.ui.rb5KHz.clicked.connect(self.UpdateSettings)
        self.ui.rb10KHz.clicked.connect(self.UpdateSettings)
        self.ui.rb20KHz.clicked.connect(self.UpdateSettings)
        self.ui.rb50KHz.clicked.connect(self.UpdateSettings)
        self.ui.rb100KHz.clicked.connect(self.UpdateSettings)
        self.ui.rb200KHz.clicked.connect(self.UpdateSettings)
        self.ui.rbSRby2.clicked.connect(self.UpdateSettings)
        self.ui.rbSRby8.clicked.connect(self.UpdateSettings)
        self.ui.rbSRby10.clicked.connect(self.UpdateSettings)
        self.ui.rbSRby20.clicked.connect(self.UpdateSettings)
        self.ui.sbThreshold.valueChanged.connect(self.SetThreshold)
        self.ui.pbThresholdPolarity.clicked.connect(self.ToggleThresholdPolarity)
        self.ui.sbMoveX.valueChanged.connect(self.SetNano)
        self.ui.sbMoveY.valueChanged.connect(self.SetNano)
        self.ui.sbMoveZ.valueChanged.connect(self.SetNano)
        #Signals to slots (Tab 3)
        self.ui.actionOpen_Data_File_to_View.triggered.connect(self.FileDialog)

        # Plot setups
        self.VhLimit = 500
        self.p0 = self.ui.VhData.pg.PlotItem()
        self.p0._setProxyOptions(deferGetattr=True)
        self.ui.VhData.setCentralItem(self.p0)
        self.p0.setRange(yRange=[-self.VhLimit, self.VhLimit], padding=0)
        self.p0.showGrid(x=True, y=True, alpha=.8)
        self.p0.setLabel('left', 'Volts', 'mV')
        self.p0.setLabel('bottom', 'Time (s)')
        #self.p0.addLegend()

        self.yLimit = 201
        self.p1 = self.ui.Ch1Data.pg.PlotItem()
        self.ui.Ch1Data.setCentralItem(self.p1)
        self.p1.setRange(yRange=[-self.yLimit, self.yLimit], padding=0)
        self.p1.showGrid(x=True, y=True, alpha=.8)
        self.p1.setLabel('left', 'Current', 'nA')
        self.p1.setLabel('bottom', 'Time (s)')
        #self.p1.addLegend()

        self.p2 = self.ui.Ch2Data.pg.PlotItem()
        self.ui.Ch2Data.setCentralItem(self.p2)
        self.p2.setRange(yRange=[-self.yLimit, self.yLimit], padding=0)
        self.p2.showGrid(x=True, y=True, alpha=.8)
        self.p2.setLabel('left', 'Current', 'nA')
        self.p2.setLabel('bottom', 'Time (s)')
        #self.p2.addLegend()

        self.p3 = self.ui.Ch3Data.pg.PlotItem()
        self.ui.Ch3Data.setCentralItem(self.p3)
        self.p3.setRange(yRange=[-self.yLimit, self.yLimit], padding=0)
        self.p3.showGrid(x=True, y=True, alpha=.8)
        self.p3.setLabel('left', 'Current', 'nA')
        self.p3.setLabel('bottom', 'Time (s)')
        #self.p3.addLegend()

        self.p4 = self.ui.Ch4Data.pg.PlotItem()
        self.ui.Ch4Data.setCentralItem(self.p4)
        self.p4.setRange(yRange=[-self.yLimit, self.yLimit], padding=0)
        self.p4.showGrid(x=True, y=True, alpha=.8)
        self.p4.setLabel('left', 'Current', 'nA')
        self.p4.setLabel('bottom', 'Time (s)')
        #self.p4.addLegend()


        # Detect devices and set acquisition flag accordingly
        self.DetectandConnectDevices()

        if self.bAcquiring == False:
            QtWidgets.QMessageBox.information(self,
                                              'Data Acquisition Notice',
                                              "e4 acquisition thread not initiated. Must restart to capture data.")

        # Initial graph tab should only have Ch1 data graph showing.
        self.ui.VhData.hide()
        self.ui.lVhold.hide()
        self.ui.Ch2Data.hide()
        self.ui.lCh2.hide()
        self.ui.Ch3Data.hide()
        self.ui.lCh3.hide()
        self.ui.Ch4Data.hide()
        self.ui.lCh4.hide()

        self.bShow = True
        self.MoveToStart()

    def InitDataArrays(self):
        self.vHolddata = np.zeros(1, dtype=float)
        self.ch1data = np.zeros(1, dtype=float)
        self.ch2data = np.zeros(1, dtype=float)
        self.ch3data = np.zeros(1, dtype=float)
        self.ch4data = np.zeros(1, dtype=float)
        self.t = np.zeros(1, dtype=float)

    def SetFiducials(self, t):
        self.t[0] = t

    def UpdateData(self):
        if __debug__ and not self.bAcquiring:
            readPacketsNum = 10

            start = self.t[-1] + self.t_step
            span = (readPacketsNum + 1) * self.t_step
            stop = self.t[-1] + span
            step = self.t_step
            self.t = np.append(self.t,
                               np.arange(start, stop, step))
            self.vHolddata = np.sin(self.t) * 100
            self.ch1data = np.sin(self.t + 1) * 100
            self.ch2data = np.sin(self.t + 2) * 100
            self.ch3data = np.sin(self.t + 3) * 100
            self.ch4data = np.sin(self.t + 4) * 100

        if self.bAcquiring:
            status = edl_py.EdlDeviceStatus_t()
            readPacketsNum = [0]
            res = self.edl.purgeData()
            # if self.edl.purgeData() != epc.EdlPySuccess and not self.bAcquiring and not __debug__:
            #     print('Elements Old Data purge error. Result = ', res)

            # Get number of available data packets EdlDeviceStatus_t::availableDataPackets.
            res = self.edl.getDeviceStatus(status)
            if res != epc.EdlPySuccess:
                QtWidgets.QMessageBox.information(self,
                                                  'Elements Connection Error',
                                                  "Error getting device status")
                return res
            if status.bufferOverflowFlag or status.lostDataFlag:
                print('Elements Buffer overflow, data loss. Result = ', res)
            if status.availableDataPackets >= 10:
                data = [0.0] * 0
                self.edl.readData(status.availableDataPackets, readPacketsNum, data)
                self.LatestPackets = readPacketsNum[0]

                self.vHolddata = np.append(self.vHolddata, data[0::5])
                self.ch1data = np.append(self.ch1data, data[1::5])
                self.ch2data = np.append(self.ch2data, data[2::5])
                self.ch3data = np.append(self.ch3data, data[3::5])
                self.ch4data = np.append(self.ch4data, data[4::5])

                start = self.t[-1] + self.t_step
                span = (readPacketsNum[0] + 1) * self.t_step
                stop = self.t[-1] + span
                step = self.t_step
                self.t = np.append(self.t, np.arange(start, stop, step))
            else:
                # If no read, wait 1 ms and retry.
                time.sleep(0.001)

        self.DataPlot(self.t[-self.maxLen:],
                      self.vHolddata[-self.maxLen:],
                      self.ch1data[-self.maxLen:],
                      self.ch2data[-self.maxLen:],
                      self.ch3data[-self.maxLen:],
                      self.ch4data[-self.maxLen:])

    def DataAcquisitionThread(self):
        while self.bRun:
            self.UpdateData()

    def DataPlot(self, t, data0, data1, data2, data3, data4):
        if len(self.t) > self.maxLen:
            if self.ui.showVhold.isChecked() == True:
                self.p0.plot(x=t, y=data0, pen=(127, 127, 127), linewidth=.5, clear=True, _callSync='off')
            if self.ui.showCh1.isChecked() == True:
                self.p1.plot(x=t, y=data1, pen=(0, 0, 255), linewidth=.5, clear=True, _callSync='off')
            if self.ui.showCh2.isChecked() == True:
                self.p2.plot(x=t, y=data2, pen=(0, 255, 0), linewidth=.5, clear=True, _callSync='off')
            if self.ui.showCh3.isChecked() == True:
                self.p3.plot(x=t, y=data3, pen=(255, 0, 0), linewidth=.5, clear=True, _callSync='off')
            if self.ui.showCh4.isChecked() == True:
                self.p4.plot(x=t, y=data4, pen=(255, 0, 255), linewidth=.5, clear=True, _callSync='off')


    def DetectandConnectDevices(self):
        res = 1
        count = 0
        while res != epc.EdlPySuccess:
            count = count + 1
            if count > 5:
                break
            res = self.edl.detectDevices(self.devices)
            time.sleep(.1)

        if res != epc.EdlPySuccess or self.devices[0] is '':
            QtWidgets.QMessageBox.information(self,
                                              'Elements Error',
                                              "No Elements e4 PCA device found.")
            self.bAcquiring = False
        else:
            QtWidgets.QMessageBox.information(self,
                                              'Elements Success',
                                              "Device found: " + self.devices[0])
            self.bAcquiring = True

            # Connect Device
            if self.edl.connectDevice(self.devices[0]) != epc.EdlPySuccess:
                QtWidgets.QMessageBox.information(self,
                                                  'Elements Connection Error',
                                                  "Error connecting to: " + self.devices[0])
        return res

    def ToggleVoltagePolarity(self):
        if self.bVoltagePositive == True:
            self.bVoltagePositive = False
            self.ui.pbPolarity.setText("-")
        else:
            self.bVoltagePositive = True
            self.ui.pbPolarity.setText("+")
        self.SetPotential()

    def SetPotential(self):
        commandStruct = edl_py.EdlCommandStruct_t()
        Vhold = self.ui.sbVhold.value()
        if self.bVoltagePositive:
            commandStruct.value = Vhold
        else:
            commandStruct.value = -Vhold
        self.edl.setCommand(epc.EdlPyCommandVhold, commandStruct, True)

    def ToggleThresholdPolarity(self):
        if self.bThresholdPositive == True:
            self.bThresholdPositive = False
            self.ui.pbThresholdPolarity.setText("-")
        else:

            self.bThresholdPositive = True
            self.ui.pbThresholdPolarity.setText("+")
        self.SetThreshold()

    def SetThreshold(self):
        if self.bThresholdPositive:
            self.DetectionThreshold = self.ui.sbThreshold.value()
        else:
            self.DetectionThreshold = -self.ui.sbThreshold.value()

    def SetNano(self):
        self.XMove = self.ui.sbMoveX.value()
        self.YMove = self.ui.sbMoveY.value()
        self.ZMove = self.ui.sbMoveZ.value()

    def UpdateSettings(self):
        if self.ui.rb200pA.isChecked == True: self.Range = epc.EDL_PY_RADIO_RANGE_200_PA
        if self.ui.rb2nA.isChecked == True: self.Range = epc.EDL_PY_RADIO_RANGE_2_NA
        if self.ui.rb20nA.isChecked == True: self.Range = epc.EDL_PY_RADIO_RANGE_20_NA
        if self.ui.rb200nA.isChecked == True: self.Range = epc.EDL_PY_RADIO_RANGE_200_NA
        if self.ui.rb1_25KHz.isChecked == True:
            self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_1_25_KHZ
            self.t_step = 1024/1250000    #1.25MHz sampling rate downsampled
        if self.ui.rb5KHz.isChecked == True:
            self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_5_KHZ
            self.t_step = 256/1250
        if self.ui.rb10KHz.isChecked == True:
            self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_10_KHZ
            self.t_step = 128/1250
        if self.ui.rb20KHz.isChecked == True:
            self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_20_KHZ
            self.t_step = 64/1250
        if self.ui.rb50KHz.isChecked == True:
            self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_50_KHZ
            self.t_step = 1/50
        if self.ui.rb100KHz.isChecked == True:
            self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_100_KHZ
            self.t_step = 1/100
        if self.ui.rb200KHz.isChecked == True:
            self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_200_KHZ
            self.t_step = 1/200
        if self.ui.rbSRby2.isChecked == True: self.BandwidthDivisor = epc.EDL_PY_RADIO_FINAL_BANDWIDTH_SR_2
        if self.ui.rbSRby8.isChecked == True: self.BandwidthDivisor = epc.EDL_PY_RADIO_FINAL_BANDWIDTH_SR_8
        if self.ui.rbSRby10.isChecked == True: self.BandwidthDivisor = epc.EDL_PY_RADIO_FINAL_BANDWIDTH_SR_10
        if self.ui.rbSRby20.isChecked == True: self.BandwidthDivisor = epc.EDL_PY_RADIO_FINAL_BANDWIDTH_SR_20
        self.ConfigureEDL()

    def ConfigureEDL(self):
        self.bAcquiring = False
        commandStruct = edl_py.EdlCommandStruct_t()
        commandStruct.radioId = self.SR
        self.edl.setCommand(epc.EdlPyCommandSamplingRate, commandStruct, False)
        commandStruct.radioId = self.Range
        self.edl.setCommand(epc.EdlPyCommandRange, commandStruct, False)
        commandStruct.radioId = self.BandwidthDivisor
        self.edl.setCommand(epc.EdlPyCommandFinalBandwidth, commandStruct, True)
        self.bAcquiring = True

    def CompensateDigitalOffset(self):
        commandStruct = edl_py.EdlCommandStruct_t()
        commandStruct.value = 0.0
        self.edl.setCommand(epc.EdlPyCommandMainTrial, commandStruct, False)
        commandStruct.value = 0.0
        self.edl.setCommand(epc.EdlPyCommandVhold, commandStruct, False)
        self.edl.setCommand(epc.EdlPyCommandApplyProtocol, commandStruct, True)

        #Digital compensation...
        commandStruct.checkboxChecked = epc.EDL_PY_CHECKBOX_CHECKED
        self.edl.setCommand(epc.EdlPyCommandCompensateAllChannels, commandStruct, True)
        time.sleep(5)

        #End digital compensation.
        commandStruct.checkboxChecked = epc.EDL_PY_CHECKBOX_UNCHECKED
        self.edl.setCommand(epc.EdlPyCommandCompensateAllChannels, commandStruct, True)

    def ToggleChannelView(self):
        if self.ui.showVhold.isChecked() == True:
            self.ui.VhData.show()
            self.ui.lVhold.show()
        else:
            self.ui.VhData.hide()
            self.ui.lVhold.hide()
        if self.ui.showCh1.isChecked() == True:
            self.ui.Ch1Data.show()
            self.ui.lCh1.show()
        else:
            self.ui.Ch1Data.hide()
            self.ui.lCh1.hide()
        if self.ui.showCh2.isChecked() == True:
            self.ui.Ch2Data.show()
            self.ui.lCh2.show()
        else:
            self.ui.Ch2Data.hide()
            self.ui.lCh2.hide()
        if self.ui.showCh3.isChecked() == True:
            self.ui.Ch3Data.show()
            self.ui.lCh3.show()
        else:
            self.ui.Ch3Data.hide()
            self.ui.lCh3.hide()
        if self.ui.showCh4.isChecked() == True:
            self.ui.Ch4Data.show()
            self.ui.lCh4.show()
        else:
            self.ui.Ch4Data.hide()
            self.ui.lCh4.hide()

    def SaveData(self, savefilename):
        savefilename = 1

    #Open File Dialog
    def FileDialog(self):
        self.filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                               'Open file',
                                               'C:\\',
                                               "Elements Header Files (*.edh)")[0]
        self.ED = ElementsData(self.filename)

    def DetectSignal(self, channel, high = True):
        # if high:
        #     threshold = channel.mean() + self.DetectionThreshold
        #     if channel > threshold:
        #         return True
        # else:
        #     threshold = channel.mean() - self.DetectionThreshold
        #     if channel < threshold:
        #         return True
        return False

    def MoveToStart(self):
        ag = QtWidgets.QDesktopWidget().availableGeometry()
        sg = QtWidgets.QDesktopWidget().screenGeometry()
        wingeo = self.geometry()
        x = 200  # ag.width() - wingeo.width()
        y = 200  # 2 * ag.height() - sg.height() - wingeo.height()
        self.move(x, y)

    def closeEvent(self, event):
        self.bAcquiring = False
        self.bRun = False
        if self.DAQThread != None:
            self.DAQThread.join()
        # At end of acquisition, close remote processes
        self.ui.VhData.close()
        self.ui.Ch1Data.close()
        self.ui.Ch2Data.close()
        self.ui.Ch3Data.close()
        self.ui.Ch4Data.close()
        event.accept()
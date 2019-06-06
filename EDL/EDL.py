""" EDL.py
Class for Elements 4-Channel PCA
Acquires PCA data:  Current
Sets: Current sensing range, potential, polarity, sampling rate, sample filter,
E.Yafuso
June 2019
"""

import edl_py
import edl_py_constants as epc
from localtools import ElementsData
import pyqtgraph
import numpy as np
from PyQt5 import QtWidgets, QtWidgets, uic
import collections, struct
import threading, time
import gc

class EDL(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_EDL = uic.loadUiType("EDLui.ui")[0]
        pyqtgraph.setConfigOption('background', 'k')
        self.ui = Ui_EDL()
        self.ui.setupUi(self)
        self.bAcquiring = False
        self.DAQThread = None

        # Class attributes
        self.maxLen = 1000
        self.InitDataArrays()

        self.bRecord = False

        # Initialize EDL class object
        self.edl = edl_py.EDL_PY()

        # String list to collect detected devices
        self.devices = [""] * 0

        # User settings, initialized to defaults from CC (May 2019)
        self.bVoltagePositive = True
        self.ui.sbVhold.setRange(-500, 500)
        self.ui.sbVhold.setValue(0)
        self.Range = epc.EDL_PY_RADIO_RANGE_200_NA
        self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_100_KHZ
        self.t_step = 1 / 100
        self.BandwidthDivisor = epc.EDL_PY_RADIO_FINAL_BANDWIDTH_SR_2
        self.UpdateSettings()
        self.SetPotential()

        #Signals to slots (Tab 1)
        self.ui.pbREC.setStyleSheet("background-color:rgb(255,0,0)")
        self.ui.pbREC.clicked.connect(self.ToggleRecording)
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
        #Signals to slots (Tab 3)
        self.ui.actionOpen_Data_File_to_View.triggered.connect(self.FileDialog)

        # Plot setups
        self.VhLimit = 500
        self.p0 = self.ui.VhData.addPlot()
        self.p0.setRange(yRange=[-self.VhLimit, self.VhLimit])
        self.p0.showGrid(x=True, y=True, alpha=.8)
        self.p0.setLabel('left', 'Volts', 'mV')
        self.p0.setLabel('bottom', 'Time (s)')
        self.p0.addLegend()

        self.yLimit = 200
        self.p1 = self.ui.Ch1Data.addPlot()
        self.p1.setRange(yRange=[-self.yLimit, self.yLimit])

        self.p1.showGrid(x=True, y=True, alpha=.8)
        self.p1.setLabel('left', 'Current', 'nA')
        self.p1.setLabel('bottom', 'Time (s)')
        self.p1.addLegend()

        self.p2 = self.ui.Ch2Data.addPlot()
        self.p2.setRange(yRange=[-self.yLimit, self.yLimit])
        self.p2.showGrid(x=True, y=True, alpha=.8)
        self.p2.setLabel('left', 'Current', 'nA')
        self.p2.setLabel('bottom', 'Time (s)')
        self.p2.addLegend()

        self.p3 = self.ui.Ch3Data.addPlot()
        self.p3.setRange(yRange=[-self.yLimit, self.yLimit])
        self.p3.showGrid(x=True, y=True, alpha=.8)
        self.p3.setLabel('left', 'Current', 'nA')
        self.p3.setLabel('bottom', 'Time (s)')
        self.p3.addLegend()
        
        self.p4 = self.ui.Ch4Data.addPlot()
        self.p4.setRange(yRange=[0, self.yLimit])
        self.p4.showGrid(x=True, y=True, alpha=.8)
        self.p4.setLabel('left', 'Current', 'nA')
        self.p4.setLabel('bottom', 'Time (s)')
        self.p4.addLegend()

        self.Vhplot = self.p0.plot([], pen=(127, 127, 127), linewidth=.5, name='VHold')
        self.ch1plot = self.p1.plot([], pen=(0, 0, 255), linewidth=.5, name='Ch1')
        self.ch2plot = self.p2.plot([], pen=(0, 255, 0), linewidth=.5, name='Ch2')
        self.ch3plot = self.p3.plot([], pen=(255, 0, 0), linewidth=.5, name='Ch3')
        self.ch4plot = self.p4.plot([], pen=(255, 0, 255), linewidth=.5, name='Ch4')

        # Detect devices and set acquisition flag accordingly
        self.DetectandConnectDevices()


        if self.bAcquiring:
            self.DAQThread = threading.Thread(target=self.DataAcquisitionThread)
            self.DAQThread.start()
        else:
            QtWidgets.QMessageBox.information(self,
                                              'Data Acquisition Notice',
                                              "e4 acquisition thread not initiated. Must restart to capture data.")

        # InitiaL graph tab should only have Ch1 data graph showing.
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

    def DetectandConnectDevices(self):
        res = 1
        count = 0
        while res != epc.EdlPySuccess:
            count = count + 1
            if count > 50:
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
        commandStruct = edl_py.EdlCommandStruct_t()
        commandStruct.radioId = self.SR
        self.edl.setCommand(epc.EdlPyCommandSamplingRate, commandStruct, False)
        commandStruct.radioId = self.Range
        self.edl.setCommand(epc.EdlPyCommandRange, commandStruct, False)
        commandStruct.radioId = self.BandwidthDivisor
        self.edl.setCommand(epc.EdlPyCommandFinalBandwidth, commandStruct, True)

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

    def ToggleRecording(self):
        if self.bRecord == False:
            self.bRecord = True
            self.ui.pbREC.setStyleSheet("background-color:rgb(0,255,0)")
            self.ui.pbREC.setText("||")
        else:
            self.bRecord = False
            self.ui.pbREC.setStyleSheet("background-color:rgb(255,0,0)")
            self.ui.pbREC.setText("REC")
            if QtWidgets.QMessageBox.question(self, 'Save data run?', "Save last run to file?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
                savefilename = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                      'Save data to file',
                                                                      'C:\\',
                                                                      "Elements Header Files (*.edh)")[0]
                self.SaveData(savefilename)
            else: self.InitDataArrays()

    def InitDataArrays(self):
        self.vHolddata = np.zeros(1, dtype=float)
        self.ch1data = np.zeros(1, dtype=float)
        self.ch2data = np.zeros(1, dtype=float)
        self.ch3data = np.zeros(1, dtype=float)
        self.ch4data = np.zeros(1, dtype=float)
        self.t = np.zeros(1, dtype=float)

    def SaveData(self, savefilename):
        savefilename = 1

    #Open File Dialog
    def FileDialog(self):
        self.filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                               'Open file',
                                               'C:\\',
                                               "Elements Header Files (*.edh)")[0]
        self.ED = ElementsData(self.filename)

    def DataAcquisitionThread(self):
        status = edl_py.EdlDeviceStatus_t()
        readPacketsNum = [0]
        time.sleep(0.5)
        res = self.edl.purgeData()
        if self.edl.purgeData() != epc.EdlPySuccess:
            QtWidgets.QMessageBox.information(self,
                                              'Elements Connection Error',
                                              "Old Data purge error")
            return res
        self.t0 = time.time()
        while self.bAcquiring:
            # Get number of available data packets EdlDeviceStatus_t::availableDataPackets.
            res = self.edl.getDeviceStatus(status)
            if res != epc.EdlPySuccess:
                QtWidgets.QMessageBox.information(self,
                                                  'Elements Connection Error',
                                                  "Error getting device status")
                return res
            if status.bufferOverflowFlag or status.lostDataFlag:
                QtWidgets.QMessageBox.information(self,
                                                  'Elements Connection Error',
                                                  "Buffer overflow, data loss.")
            if status.availableDataPackets >= 10:
                data = [0.0] * 0
                res = self.edl.readData(status.availableDataPackets, readPacketsNum, data)

                self.vHolddata = np.append(self.vHolddata, data[0::5])
                self.ch1data = np.append(self.ch1data, data[1::5])
                self.ch2data = np.append(self.ch2data, data[2::5])
                self.ch3data = np.append(self.ch3data, data[3::5])
                self.ch4data = np.append(self.ch4data, data[4::5])

                start = self.t[-1]+self.t_step
                stop = self.t[-1]+((readPacketsNum+1)*self.t_step)
                step = self.t_step
                self.t = np.append(self.t,
                                   np.arange(start, stop, step))
                self.DataPlot()
            else:
                # If the read not performed wait 1 ms before trying to read again.
                time.sleep(0.001)

    def DataPlot(self):
        if len(self.Vhplot) > self.maxLen:
            self.Vhplot.setData(self.t[-self.maxLen:], self.vHolddata[-self.maxLen:])
            self.ch1plot.setData(self.t[-self.maxLen:], self.ch1data[-self.maxLen:])
            self.ch2plot.setData(self.t[-self.maxLen:], self.ch2data[-self.maxLen:])
            self.ch3plot.setData(self.t[-self.maxLen:], self.ch3data[-self.maxLen:])
            self.ch4plot.setData(self.t[-self.maxLen:], self.ch4data[-self.maxLen:])
            gc.collect()

    def MoveToStart(self):
        ag = QtWidgets.QDesktopWidget().availableGeometry()
        sg = QtWidgets.QDesktopWidget().screenGeometry()
        wingeo = self.geometry()
        x = 100  # ag.width() - wingeo.width()
        y = 100  # 2 * ag.height() - sg.height() - wingeo.height()
        self.move(x, y)

    def closeEvent(self, event):
        self.bAcquiring = False
        if self.DAQThread != None:
            self.DAQThread.join()
        event.accept()
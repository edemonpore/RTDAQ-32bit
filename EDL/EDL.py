""" EDL.py
Class for Elements 4-Channel PCA
Acquires PCA data:  Current
Sets:    stuff...
E.Yafuso
May 2019
"""

import edl_py
import edl_py_constants as epc
import pyqtgraph
from PyQt5 import QtWidgets, uic
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

        # Initialize EDL class object
        self.edl = edl_py.EDL_PY()

        # String list to collect detected devices
        self.devices = [""] * 0

        # Detect devices and set acquisition flag accordingly
        self.DetectandConnectDevices()

        # User settings, initialized to defaults from CC (May 2019)
        self.bVoltagePositive = True
        self.ui.sbVhold.setRange(-500, 500)
        self.Range = epc.EDL_PY_RADIO_RANGE_200_NA
        self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_100_KHZ
        self.BandwidthDivisor = epc.EDL_PY_RADIO_FINAL_BANDWIDTH_SR_2
        self.UpdateSettings()

        #Signals to slots (Tab 1)
        self.ui.showCh1.stateChanged.connect(self.ToggleChannelView)
        self.ui.showCh2.stateChanged.connect(self.ToggleChannelView)
        self.ui.showCh3.stateChanged.connect(self.ToggleChannelView)
        self.ui.showCh4.stateChanged.connect(self.ToggleChannelView)
        #Signals to slots (Tab 2)
        self.ui.pbCompensateDigitalOffset.clicked.connect(self.CompensateDigitalOffset)
        self.ui.pbPolarity.clicked.connect(self.ToggleVoltagePolarity)
        self.ui.pbPolarity.setToolTip('Toggle Voltage Polarity')
        self.ui.rb200pA.toggled.connect(self.UpdateSettings)
        self.ui.rb2nA.toggled.connect(self.UpdateSettings)
        self.ui.rb20nA.toggled.connect(self.UpdateSettings)
        self.ui.rb200nA.toggled.connect(self.UpdateSettings)
        self.ui.rb1_25KHz.toggled.connect(self.UpdateSettings)
        self.ui.rb5KHz.toggled.connect(self.UpdateSettings)
        self.ui.rb10KHz.toggled.connect(self.UpdateSettings)
        self.ui.rb20KHz.toggled.connect(self.UpdateSettings)
        self.ui.rb50KHz.toggled.connect(self.UpdateSettings)
        self.ui.rb100KHz.toggled.connect(self.UpdateSettings)
        self.ui.rb200KHz.toggled.connect(self.UpdateSettings)
        self.ui.rbSRby2.toggled.connect(self.UpdateSettings)
        self.ui.rbSRby8.toggled.connect(self.UpdateSettings)
        self.ui.rbSRby10.toggled.connect(self.UpdateSettings)
        self.ui.rbSRby20.toggled.connect(self.UpdateSettings)

        # Class attributes
        self.maxLen = 1000
        self.ch1data = collections.deque([0], self.maxLen)
        self.ch2data = collections.deque([0], self.maxLen)
        self.ch3data = collections.deque([0], self.maxLen)
        self.ch4data = collections.deque([0], self.maxLen)
        self.t = collections.deque([0], self.maxLen)

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

        self.ch1plot = self.p1.plot([], pen=(0, 0, 255), linewidth=.5, name='Ch1')
        self.ch2plot = self.p2.plot([], pen=(0, 255, 0), linewidth=.5, name='Ch2')
        self.ch3plot = self.p3.plot([], pen=(255, 0, 0), linewidth=.5, name='Ch3')
        self.ch4plot = self.p4.plot([], pen=(255, 0, 255), linewidth=.5, name='Ch4')

        self.DAQThread = threading.Thread(target=self.DataAcquisitionThread)
        self.DAQThread.start()

        self.ui.Ch1Data.show()
        self.ui.Ch2Data.hide()
        self.ui.lCh2.hide()
        self.ui.Ch3Data.hide()
        self.ui.lCh3.hide()
        self.ui.Ch4Data.hide()
        self.ui.lCh4.hide()
        self.bShow = True
        self.MoveToStart()

    def UpdateSettings(self):
        if self.ui.rb200pA.isChecked == True: self.Range = epc.EDL_PY_RADIO_RANGE_200_PA
        if self.ui.rb2nA.isChecked == True: self.Range = epc.EDL_PY_RADIO_RANGE_2_NA
        if self.ui.rb20nA.isChecked == True: self.Range = epc.EDL_PY_RADIO_RANGE_20_NA
        if self.ui.rb200nA.isChecked == True: self.Range = epc.EDL_PY_RADIO_RANGE_200_NA
        if self.ui.rb1_25KHz.isChecked == True: self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_1_25_KHZ
        if self.ui.rb5KHz.isChecked == True: self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_5_KHZ
        if self.ui.rb10KHz.isChecked == True: self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_10_KHZ
        if self.ui.rb20KHz.isChecked == True: self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_20_KHZ
        if self.ui.rb50KHz.isChecked == True: self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_50_KHZ
        if self.ui.rb100KHz.isChecked == True: self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_100_KHZ
        if self.ui.rb200KHz.isChecked == True: self.SR = epc.EDL_PY_RADIO_SAMPLING_RATE_200_KHZ
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

    def ToggleVoltagePolarity(self):
        if self.bVoltagePositive == True:
            self.bVoltagePositive = False
            self.ui.pbPolarity.setText("-")
        else:
            self.bVoltagePositive = True
            self.ui.pbPolarity.setText("+")

    def DetectandConnectDevices(self):
        res = self.edl.detectDevices(self.devices)

        if res != epc.EdlPySuccess:
            QtWidgets.QMessageBox.information(self,
                                              'Elements Error',
                                              "No Elements e4 PCA device found.")
            self.bAcquiring = False
        else:
            QtWidgets.QMessageBox.information(self,
                                              'Elements Success',
                                              "Device found:" + self.devices[0])
            self.bAcquiring = True

            # Connect Devices
            for device in self.devices:
                if edl.connectDevice(device) != epc.EdlPySuccess:
                    QtWidgets.QMessageBox.information(self,
                                                      'Elements Connection Error',
                                                      "Error connecting to:" + device)
                break
        return res

    def MoveToStart(self):
        ag = QtWidgets.QDesktopWidget().availableGeometry()
        sg = QtWidgets.QDesktopWidget().screenGeometry()
        wingeo = self.geometry()
        x = 100  # ag.width() - wingeo.width()
        y = 100  # 2 * ag.height() - sg.height() - wingeo.height()
        self.move(x, y)

    def ToggleChannelView(self):
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

    def DataAcquisitionThread(self):
        # data_in =
        self.t0 = time.time()
        # count = 0
        # while (self.bAcquiring):
        #     time.sleep(0.01)
        #     self.t.append(time.time()-self.t0)
        #     if self.AIOUSB.ADC_GetChannelV(-3, 0, ctypes.byref(data_in)) is 0:
        #         self.ch1data.append(float(data_in.value)/5*100)
        #     else: self.ch1data.append(0)
        #     if self.AIOUSB.ADC_GetChannelV(-3, 1, ctypes.byref(data_in)) is 0:
        #         self.ch2data.append(float(data_in.value)/5*100)
        #     else: self.ch2data.append(0)
        #     count += 1
        #     if count > 3:
        #         self.DataPlot()
        #         count = 0
    def readAndSaveSomeData(self):
        status = edl_py.EdlDeviceStatus_t()
        readPacketsNum = [0]
        time.sleep(0.5)
        if self.edl.purgeData != epc.EdlPySuccess:
            QtWidgets.QMessageBox.information(self,
                                              'Elements Connection Error',
                                              "Old Data purge error")
            return res
        c = 0
        while c < 1000:
            c = c + 1
            #Get umber of available data packets EdlDeviceStatus_t::availableDataPackets.
            res = edl.getDeviceStatus(status)
            #If EDL::getDeviceStatus returns error code output code and return.
            if res != epc.EdlPySuccess:
                QtWidgets.QMessageBox.information(self,
                                                  'Elements Connection Error',
                                                  "Error getting device status")
                return res;
            if status.bufferOverflowFlag or status.lostDataFlag:
                QtWidgets.QMessageBox.information(self,
                                                  'Elements Connection Error',
                                                  "Buffer overflow, data loss.")
            if status.availableDataPackets >= MINIMUM_DATA_PACKETS_TO_READ:
                data = [0.0] * 0
                res = edl.readData(status.availableDataPackets, readPacketsNum, data)
                voltageData.extend(data[0::epc.EDL_PY_CHANNEL_NUM])
                for currentIdx in range(epc.EDL_PY_CHANNEL_NUM - 1):
                    currentData[currentIdx].extend(data[currentIdx + 1::epc.EDL_PY_CHANNEL_NUM])
            else:
                #If the read was not performed wait 1 ms before trying to read again.
                time.sleep(0.001)
        return res;

    def DataPlot(self):
        self.ch1plot.setData(self.t, self.ch1data)
        self.ch2plot.setData(self.t, self.ch2data)
        self.ch3plot.setData(self.t, self.ch3data)
        self.ch4plot.setData(self.t, self.ch4data)
        gc.collect()

    def closeEvent(self, event):
        self.bAcquiring = False
        if self.DAQThread != None:
            self.DAQThread.join()
            event.accept()
        else:
            self.bShow = False
            self.hide()
            event.ignore()
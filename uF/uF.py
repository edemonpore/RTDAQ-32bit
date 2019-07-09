""" uF.py
Class for Elveflow Controller
Provides initialization over USB:
    Caliabration: default, new, save, load
    Add sensor
Acquires USB data:
    get pressure
    get sensor data
Sets USB data:
    set pressure: all channels or one at a time
    event trigger
E.Yafuso
June 2019
"""

import os
from ctypes import *
import pandas
import numpy as np
import pyqtgraph
from PyQt5 import QtWidgets, uic
import threading, time


class uF(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        path = os.path.abspath("") + '\\uF\\uFui.ui'
        try:
            Ui_uF = uic.loadUiType(path)[0]
        except:
            Ui_uF = uic.loadUiType('uFui.ui')[0]
        pyqtgraph.setConfigOption('background', 'k')
        self.ui = Ui_uF()
        self.ui.setupUi(self)
        path = os.path.abspath("") + '\\uF\\Python_32\\DLL32\\Elveflow32.dll'
        self.Elveflow = CDLL(path)
        self.bAcquiring = False
        self.DAQThread = 0

        # Initialize OB1 (Kenobi)
        self.Instr_ID = c_int32()
        # Error code = 0 if initialization successful
        error = self.OB1_Initialization('01C9D9C3'.encode('ascii'), 1, 2, 4, 3, byref(self.Instr_ID))
        if error:
            QtWidgets.QMessageBox.information(self, 'Elveflow ERROR', "Device initialization failure.")
            print(error)
        else:
            print(self.Instr_ID.value)
            self.bAcquiring = True

        # Add digital flow sensor with water calibration
        error = self.OB1_Add_Sens(self.Instr_ID, 1, 1, 1, 0, 7)
        if error:
            QtWidgets.QMessageBox.information(self, 'Elveflow ERROR', "Digital flow sensor failure.")
            self.bAcquiring = False
            print('Error adding digital flow sensor: %d' % error)

        self.Cal = (c_double * 1000)()  # calibration should have 1000 elements
        error = self.Elveflow_Calibration_Default(byref(self.Cal), 1000)
        if error:
            QtWidgets.QMessageBox.information(self, 'Elveflow ERROR', "Calibration failure.")
            self.bAcquiring = False
        # else:
        #     for i in range(0,1000): print('[',i,']: ',self.Cal[i])

        # Class attributes
        self.maxLen = 1000
        self.Psetdata = np.zeros(1, dtype=float)
        self.Pdata = np.zeros(1, dtype=float)
        self.Flowdata = np.zeros(1, dtype=float)
        self.t = np.zeros(1, dtype=float)

        self.p = self.ui.PData.addPlot()
        self.p.setRange(yRange=[-900, 6000])
        self.p.showGrid(x=True, y=True, alpha=.8)
        self.p.setLabel('left', 'Pressure (mbar)')
        self.p.setLabel('bottom', 'Time (s)')
        self.p.addLegend()

        self.f = self.ui.FlowData.addPlot()
        self.f.setRange(yRange=[0, 7])
        self.f.showGrid(x=True, y=True, alpha=.8)
        self.f.setLabel('left', 'Flow', 'uL')
        self.f.setLabel('bottom', 'Time (s)')
        self.f.addLegend()

        self.pplot = self.p.plot([], pen=(0, 0, 255), linewidth=.5, name='P')
        self.psetplot = self.p.plot([], pen=(127, 127, 127), linewidth=.5, name='P-set')
        self.flowplot = self.f.plot([], pen=(0, 255, 0), linewidth=.5, name='Flow')

        self.pset = 0
        self.ui.vsP.setMinimum(-900)
        self.ui.vsP.setMaximum(6000)
        self.ui.vsP.setValue(self.pset)

        #Signals to slots
        self.ui.actionOpen.triggered.connect(self.OpenScriptDialog)
        self.ui.vsP.valueChanged.connect(self.setPressure)

        self.bShow = True
        self.MoveToStart()

    def MoveToStart(self):
        ag = QtWidgets.QDesktopWidget().availableGeometry()
        sg = QtWidgets.QDesktopWidget().screenGeometry()
        wingeo = self.geometry()
        x = 200  # ag.width() - wingeo.width()
        y = 200  # 2 * ag.height() - sg.height() - wingeo.height()
        self.move(x, y)

    def setPressure(self):
        temp = self.ui.vsP.value()
        self.pset = int(temp)
        self.ui.lsetPressure.setText(str(temp))

        # Set actual pressure on OB-1...
        set_channel = 1 #assume using channel 1 for now
        set_channel = c_int32(set_channel)  # convert to c_int32
        set_pressure = float(temp)
        set_pressure = c_double(set_pressure)  # convert to c_double
        error = self.OB1_Set_Press(self.Instr_ID.value, set_channel, set_pressure, byref(self.Cal), 1000)

    def UpdateData(self):
        data_in = c_double()
        if self.OB1_Get_Press(self.Instr_ID.value, c_int32(1), 1, self.Cal, byref(data_in), 1000):
            self.Pdata = np.append(self.Pdata, 0)
        else:
            self.Pdata = np.append(self.Pdata, float(data_in.value))
        if self.OB1_Get_Sens_Data(self.Instr_ID.value, c_int32(1), 1, byref(data_in)):
            self.Flowdata = np.append(self.Flowdata, 0)
        else:
            self.Flowdata = np.append(self.Flowdata, float(data_in.value))
        self.Psetdata = np.append(self.Psetdata, self.pset)

        if __debug__ and not self.bAcquiring:
            self.t = np.append(self.t, time.time())
            self.Pdata = np.append(self.Pdata, (np.sin(self.t[-1])+1)*3000)
            self.Flowdata = np.append(self.Flowdata, (np.sin(self.t[-1] + 1)+1))
            self.Psetdata = np.append(self.Psetdata, self.pset)
            self.DataPlot()

    def DataAcquisitionThread(self):
        self.t0 = time.time()
        while (self.bAcquiring):
            time.sleep(0.01)
            self.t = np.append(self.t, time.time() - self.t0)
            self.UpdateData()
            self.DataPlot()

        if __debug__ and not self.bAcquiring:
            while True:
                time.sleep(.01)
                self.t = np.append(self.t, time.time() - self.t0)
                self.Pdata = np.append(self.Pdata, (np.sin(self.t[-1])+1)*3000)
                self.Flowdata = np.append(self.Flowdata, (np.sin(self.t[-1] + 1)+1))
                self.Psetdata = np.append(self.Psetdata, self.pset)
                self.DataPlot()

    def DataPlot(self):
        self.pplot.setData(self.t, self.Pdata)
        self.psetplot.setData(self.t, self.Psetdata)
        self.flowplot.setData(self.t, self.Flowdata)

    def OB1_Initialization(self, Device_Name, Reg_Ch_1, Reg_Ch_2, Reg_Ch_3, Reg_Ch_4, OB1_ID_out):
        X_OB1_Initialization = self.Elveflow.OB1_Initialization
        X_OB1_Initialization.argtypes = [c_char_p, c_uint16, c_uint16, c_uint16, c_uint16, POINTER(c_int32)]
        return X_OB1_Initialization(Device_Name, Reg_Ch_1, Reg_Ch_2, Reg_Ch_3, Reg_Ch_4, OB1_ID_out)

    # Set default Cal in Cal cluster, len is the Cal_Array_out array length
    # use ctypes c_double*1000 for calibration array
    def Elveflow_Calibration_Default(self, Calib_Array_out, len):
        X_Elveflow_Calibration_Default = self.Elveflow.Elveflow_Calibration_Default
        X_Elveflow_Calibration_Default.argtypes = [POINTER(c_double * 1000), c_int32]
        return X_Elveflow_Calibration_Default(Calib_Array_out, len)

    def Elveflow_Calibration_Load(self, Path, Calib_Array_out, len):
        X_Elveflow_Calibration_Load = self.Elveflow.Elveflow_Calibration_Load
        X_Elveflow_Calibration_Load.argtypes = [c_char_p, POINTER(c_double * 1000), c_int32]
        return X_Elveflow_Calibration_Load(Path, Calib_Array_out, len)

    def Elveflow_Calibration_Save(self, Path, Calib_Array_in, len):
        X_Elveflow_Calibration_Save = self.Elveflow.Elveflow_Calibration_Save
        X_Elveflow_Calibration_Save.argtypes = [c_char_p, POINTER(c_double * 1000), c_int32]
        return X_Elveflow_Calibration_Save(Path, Calib_Array_in, len)

    def OB1_Calib(self, OB1_ID_in, Calib_array_out, len):
        X_OB1_Calib = self.Elveflow.OB1_Calib
        X_OB1_Calib.argtypes = [c_int32, POINTER(c_double * 1000), c_int32]
        return X_OB1_Calib(OB1_ID_in, Calib_array_out, len)

    def OB1_Get_Press(self, OB1_ID, Channel_1_to_4, Acquire_Data1True0False, Calib_array_in, Pressure, Calib_Array_len):
        X_OB1_Get_Press = self.Elveflow.OB1_Get_Press
        X_OB1_Get_Press.argtypes = [c_int32, c_int32, c_int32, POINTER(c_double * 1000), POINTER(c_double), c_int32]
        return X_OB1_Get_Press(OB1_ID, Channel_1_to_4, Acquire_Data1True0False, Calib_array_in, Pressure,
                               Calib_Array_len)

    def OB1_Get_Sens_Data(self, OB1_ID, Channel_1_to_4, Acquire_Data1True0False, Sens_Data):
        X_OB1_Get_Sens_Data = self.Elveflow.OB1_Get_Sens_Data
        X_OB1_Get_Sens_Data.argtypes = [c_int32, c_int32, c_int32, POINTER(c_double)]
        return X_OB1_Get_Sens_Data(OB1_ID, Channel_1_to_4, Acquire_Data1True0False, Sens_Data)

    def OB1_Get_Trig(self, OB1_ID, Trigger):
        X_OB1_Get_Trig = self.Elveflow.OB1_Get_Trig
        X_OB1_Get_Trig.argtypes = [c_int32, POINTER(c_int32)]
        return X_OB1_Get_Trig(OB1_ID, Trigger)

    # Set the trigger of the OB1 (0 = 0V, 1 = 3.3V)
    def OB1_Set_Trig(self, OB1_ID, trigger):
        X_OB1_Set_Trig = self.Elveflow.OB1_Set_Trig
        X_OB1_Set_Trig.argtypes = [c_int32, c_int32]
        return X_OB1_Set_Trig(OB1_ID, trigger)

    def OB1_Add_Sens(self, OB1_ID, Channel_1_to_4, SensorType, DigitalAnalog, FSens_Digit_Calib,
                     FSens_Digit_Resolution):
        X_OB1_Add_Sens = self.Elveflow.OB1_Add_Sens
        X_OB1_Add_Sens.argtypes = [c_int32, c_int32, c_uint16, c_uint16, c_uint16, ]
        return X_OB1_Add_Sens(OB1_ID, Channel_1_to_4, SensorType, DigitalAnalog, FSens_Digit_Calib,
                              FSens_Digit_Resolution)

    def OB1_Set_Press(self, OB1_ID, Channel_1_to_4, Pressure, Calib_array_in, Calib_Array_len):
        X_OB1_Set_Press = self.Elveflow.OB1_Set_Press
        X_OB1_Set_Press.argtypes = [c_int32, c_int32, c_double, POINTER(c_double * 1000), c_int32]
        return X_OB1_Set_Press(OB1_ID, Channel_1_to_4, Pressure, Calib_array_in, Calib_Array_len)

    def OB1_Set_All_Press(self, OB1_ID, Pressure_array_in, Calib_array_in, Pressure_Array_Len, Calib_Array_Len):
        X_OB1_Set_All_Press = self.Elveflow.OB1_Set_All_Press
        X_OB1_Set_All_Press.argtypes = [c_int32, POINTER(c_double), POINTER(c_double), c_int32, c_int32]
        return X_OB1_Set_All_Press(OB1_ID, Pressure_array_in, Calib_array_in, Pressure_Array_Len, Calib_Array_Len)

    def OB1_Reset_Instr(self, OB1_ID):
        X_OB1_Reset_Instr = self.Elveflow.OB1_Reset_Instr
        X_OB1_Reset_Instr.argtypes = [c_int32]
        return X_OB1_Reset_Instr(OB1_ID)

    def OB1_Reset_Digit_Sens(self, OB1_ID, Channel_1_to_4):
        X_OB1_Reset_Digit_Sens = self.Elveflow.OB1_Reset_Digit_Sens
        X_OB1_Reset_Digit_Sens.argtypes = [c_int32, c_int32]
        return X_OB1_Reset_Digit_Sens(OB1_ID, Channel_1_to_4)

    # For illustration: feedback loop idea
    def Elveflow_EXAMPLE_PID(self, PID_ID_in, actualValue, Reset, P, I, PID_ID_out, value):
        X_Elveflow_EXAMPLE_PID = self.Elveflow.Elveflow_EXAMPLE_PID
        X_Elveflow_EXAMPLE_PID.argtypes = [c_int32, c_double, c_int32, c_double, c_double, POINTER(c_int32),
                                           POINTER(c_double)]
        return X_Elveflow_EXAMPLE_PID(PID_ID_in, actualValue, Reset, P, I, PID_ID_out, value)

    def OB1_Destructor(self, OB1_ID):
        X_OB1_Destructor = self.Elveflow.OB1_Destructor
        X_OB1_Destructor.argtypes = [c_int32]
        return X_OB1_Destructor(OB1_ID)

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
        self.bAcquiring = False
        if self.DAQThread and self.DAQThread != None:
            self.DAQThread.join()

            event.accept()
        else:
            self.bShow = False
            self.hide()
            event.ignore()
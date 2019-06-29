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

import ctypes
import pandas
import numpy as np
import pyqtgraph
from PyQt5 import QtWidgets, uic
import threading, time
import gc

class uF(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_uF = uic.loadUiType("uFui.ui")[0]
        pyqtgraph.setConfigOption('background', 'k')
        self.ui = Ui_uF()
        self.ui.setupUi(self)
        self.Elveflow = ctypes.CDLL("Elveflow32")

        self.bAcquiring = False

        # Initialize OB1 (Kenobi)
        self.Instr_ID = c_int32()
        # Error code = 0 if initialization successful
        error = self.OB1_Initialization('01C9D9C3'.encode('ascii'), 1, 2, 4, 3, ctypes.byref(self.Instr_ID))
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
            print('error adding digit flow sensor:%d' % error)

        self.Cal = (c_double * 1000)()  # calibration should have 1000 elements
        error = self.Elveflow_Calibration_Default(byref(Cal), 1000)
        if error:
            QtWidgets.QMessageBox.information(self, 'Elveflow ERROR', "Calibration failure.")
            self.bAcquiring = False
        else:
            for i in range(0,1000): print('[',i,']: ',self.Cal[i])

        # Class attributes
        self.maxLen = 1000
        self.Psetdata = np.zeros(1, dtype=float)
        self.Pdata = np.zeros(1, dtype=float)
        self.Flowdata = np.zeros(1, dtype=float)
        self.t = np.zeros(1, dtype=float)

        self.p = self.ui.PData.addPlot()
        self.p.setRange(yRange=[-900, 6000])
        self.p.showGrid(x=True, y=True, alpha=.8)
        self.p.setLabel('left', 'Pressure', 'mbar')
        self.p.setLabel('bottom', 'Time (s)')
        self.p.addLegend()

        self.f = self.ui.FlowData.addPlot()
        self.f.setRange(yRange=[0, 7])
        self.f.showGrid(x=True, y=True, alpha=.8)
        self.f.setLabel('left', 'Flow', 'uL')
        self.f.setLabel('bottom', 'Time (m)')
        self.f.addLegend()

        self.pplot = self.p.plot([], pen=(0, 0, 255), linewidth=.5, name='P')
        self.psetplot = self.p.plot([], pen=(127, 127, 127), linewidth=.5, name='P-set')
        self.flowplot = self.f.plot([], pen=(0, 255, 0), linewidth=.5, name='Flow')

        self.ui.vsP.setMinimum(0)
        self.ui.vsP.setMaximum(100)
        self.ui.vsP.setValue(self.pset)

        #Signals to slots
        self.ui.actionOpen.triggered.connect(self.OpenScriptDialog)
        self.ui.vsP.valueChanged.connect(self.setPressure)

        self.DAQThread = threading.Thread(target=self.DataAcquisitionThread)
        self.DAQThread.start()

        self.bShow = True
        self.bCanClose = False
        self.MoveToStart()

    def MoveToStart(self):
        ag = QtWidgets.QDesktopWidget().availableGeometry()
        sg = QtWidgets.QDesktopWidget().screenGeometry()
        wingeo = self.geometry()
        x = 200  # ag.width() - wingeo.width()
        y = 200  # 2 * ag.height() - sg.height() - wingeo.height()
        self.move(x, y)

    def OB1_Initialization(self, Device_Name, Reg_Ch_1, Reg_Ch_2, Reg_Ch_3, Reg_Ch_4, OB1_ID_out):
        X_OB1_Initialization = Elveflow.OB1_Initialization
        X_OB1_Initialization.argtypes = [c_char_p, c_uint16, c_uint16, c_uint16, c_uint16, POINTER(c_int32)]
        return X_OB1_Initialization(Device_Name, Reg_Ch_1, Reg_Ch_2, Reg_Ch_3, Reg_Ch_4, OB1_ID_out)

        # Set default Calib in Calib cluster, len is the Calib_Array_out array length
        # use ctypes c_double*1000 for calibration array

    def Elveflow_Calibration_Default(self, Calib_Array_out, len):
        X_Elveflow_Calibration_Default = Elveflow.Elveflow_Calibration_Default
        X_Elveflow_Calibration_Default.argtypes = [POINTER(c_double * 1000), c_int32]
        return X_Elveflow_Calibration_Default(Calib_Array_out, len)

        # Elveflow Library
        # OB1-AF1 Device
        #
        # Load the calibration file located at Path and returns the calibration
        # parameters in the Calib_Array_out. len is the Calib_Array_out array length.
        # The function asks the user to choose the path if Path is not valid, empty
        # or not a path. The function indicate if the file was found.
        #
        # use ctypes c_double*1000 for calibration array

    def Elveflow_Calibration_Load(self, Path, Calib_Array_out, len):
        X_Elveflow_Calibration_Load = Elveflow.Elveflow_Calibration_Load
        X_Elveflow_Calibration_Load.argtypes = [c_char_p, POINTER(c_double * 1000), c_int32]
        return X_Elveflow_Calibration_Load(Path, Calib_Array_out, len)

        # Elveflow Library
        # OB1-AF1 Device
        #
        # Save the Calibration cluster in the file located at Path. len is the
        # Calib_Array_in array length. The function prompt the user to choose the
        # path if Path is not valid, empty or not a path.
        #
        # use ctypes c_double*1000 for calibration array

    def Elveflow_Calibration_Save(self, Path, Calib_Array_in, len):
        X_Elveflow_Calibration_Save = Elveflow.Elveflow_Calibration_Save
        X_Elveflow_Calibration_Save.argtypes = [c_char_p, POINTER(c_double * 1000), c_int32]
        return X_Elveflow_Calibration_Save(Path, Calib_Array_in, len)

        # Elveflow Library
        # OB1 Device
        #
        # Launch OB1 calibration and return the calibration array. Before
        # Calibration, ensure that ALL channels are proprely closed with adequate
        # caps.
        # Len correspond to the Calib_array_out length.
        #
        # use ctypes c_double*1000 for calibration array

    def OB1_Calib(self, OB1_ID_in, Calib_array_out, len):
        X_OB1_Calib = Elveflow.OB1_Calib
        X_OB1_Calib.argtypes = [c_int32, POINTER(c_double * 1000), c_int32]
        return X_OB1_Calib(OB1_ID_in, Calib_array_out, len)

        # Elveflow Library
        # OB1 Device
        #
        #
        # Get the pressure of an OB1 channel.
        #
        # Calibration array is required (use Set_Default_Calib if required) and
        # return a double . Len correspond to the Calib_array_in length.
        #
        # If Acquire_data is true, the OB1 acquires ALL regulator AND ALL analog
        # sensor value. They are stored in the computer memory. Therefore, if several
        # regulator values (OB1_Get_Press) and/or sensor values (OB1_Get_Sens_Data)
        # have to be acquired simultaneously, set the Acquire_Data to true only for
        # the First function. All the other can used the values stored in memory and
        # are almost instantaneous.
        #
        # use ctypes c_double*1000 for calibration array
        # use ctype c_double*4 for pressure array

    def OB1_Get_Press(self, OB1_ID, Channel_1_to_4, Acquire_Data1True0False, Calib_array_in, Pressure, Calib_Array_len):
        X_OB1_Get_Press = Elveflow.OB1_Get_Press
        X_OB1_Get_Press.argtypes = [c_int32, c_int32, c_int32, POINTER(c_double * 1000), POINTER(c_double), c_int32]
        return X_OB1_Get_Press(OB1_ID, Channel_1_to_4, Acquire_Data1True0False, Calib_array_in, Pressure,
                               Calib_Array_len)

    def OB1_Destructor(self, OB1_ID):
        X_OB1_Destructor = Elveflow.OB1_Destructor
        X_OB1_Destructor.argtypes = [c_int32]
        return X_OB1_Destructor(OB1_ID)

        # Read the sensor of the requested channel acquired in OB1_Acquire_data
        # Units : Flow sensor �l/min
        # Pressure : mbar
        #
        # If Acquire_data is true, the OB1 acquires ALL regulator AND ALL analog
        # sensor value. They are stored in the computer memory. Therefore, if several
        # regulator values (OB1_Get_Press) and/or sensor values (OB1_Get_Sens_Data)
        # have to be acquired simultaneously, set the Acquire_Data to true only for
        # the First function. All the other can used the values stored in memory and
        # are almost instantaneous. For Digital Sensor, that required another
        # communication protocol, this parameter have no impact
        #
        # NB: For Digital Flow Senor, If the connection is lots, OB1 will be reset
        # and the return value will be zero

    def OB1_Get_Sens_Data(self, OB1_ID, Channel_1_to_4, Acquire_Data1True0False, Sens_Data):
        X_OB1_Get_Sens_Data = Elveflow.OB1_Get_Sens_Data
        X_OB1_Get_Sens_Data.argtypes = [c_int32, c_int32, c_int32, POINTER(c_double)]
        return X_OB1_Get_Sens_Data(OB1_ID, Channel_1_to_4, Acquire_Data1True0False, Sens_Data)

        # Get the trigger of the OB1 (0 = 0V, 1 =3,3V)

    def OB1_Get_Trig(self, OB1_ID, Trigger):
        X_OB1_Get_Trig = Elveflow.OB1_Get_Trig
        X_OB1_Get_Trig.argtypes = [c_int32, POINTER(c_int32)]
        return X_OB1_Get_Trig(OB1_ID, Trigger)

        # Set the trigger of the OB1 (0 = 0V, 1 =3,3V)

    def OB1_Set_Trig(self, OB1_ID, trigger):
        X_OB1_Set_Trig = Elveflow.OB1_Set_Trig
        X_OB1_Set_Trig.argtypes = [c_int32, c_int32]
        return X_OB1_Set_Trig(OB1_ID, trigger)

    def OB1_Add_Sens(self, OB1_ID, Channel_1_to_4, SensorType, DigitalAnalog, FSens_Digit_Calib,
                     FSens_Digit_Resolution):
        X_OB1_Add_Sens = Elveflow.OB1_Add_Sens
        X_OB1_Add_Sens.argtypes = [c_int32, c_int32, c_uint16, c_uint16, c_uint16, ]
        return X_OB1_Add_Sens(OB1_ID, Channel_1_to_4, SensorType, DigitalAnalog, FSens_Digit_Calib,
                              FSens_Digit_Resolution)

    def OB1_Set_All_Press(self, OB1_ID, Pressure_array_in, Calib_array_in, Pressure_Array_Len, Calib_Array_Len):
        X_OB1_Set_All_Press = Elveflow.OB1_Set_All_Press
        X_OB1_Set_All_Press.argtypes = [c_int32, POINTER(c_double), POINTER(c_double), c_int32, c_int32]
        return X_OB1_Set_All_Press(OB1_ID, Pressure_array_in, Calib_array_in, Pressure_Array_Len, Calib_Array_Len)

    def OB1_Reset_Instr(self, OB1_ID):
        X_OB1_Reset_Instr = Elveflow.OB1_Reset_Instr
        X_OB1_Reset_Instr.argtypes = [c_int32]
        return X_OB1_Reset_Instr(OB1_ID)

    def OB1_Reset_Digit_Sens(self, OB1_ID, Channel_1_to_4):
        X_OB1_Reset_Digit_Sens = Elveflow.OB1_Reset_Digit_Sens
        X_OB1_Reset_Digit_Sens.argtypes = [c_int32, c_int32]
        return X_OB1_Reset_Digit_Sens(OB1_ID, Channel_1_to_4)

        # For illustration: feedback loop idea

    def Elveflow_EXAMPLE_PID(self, PID_ID_in, actualValue, Reset, P, I, PID_ID_out, value):
        X_Elveflow_EXAMPLE_PID = Elveflow.Elveflow_EXAMPLE_PID
        X_Elveflow_EXAMPLE_PID.argtypes = [c_int32, c_double, c_int32, c_double, c_double, POINTER(c_int32),
                                           POINTER(c_double)]
        return X_Elveflow_EXAMPLE_PID(PID_ID_in, actualValue, Reset, P, I, PID_ID_out, value)

    def setPressure(self):
        temp = self.ui.vsP.value()
        self.pset = int(temp)
        self.ui.lsetPressure.setText(str(temp))

        # Set actual pressure on OB-1...
        set_channel = 1 #assume using channel 1 for now
        set_channel = c_int32(set_channel)  # convert to c_int32
        set_pressure = float(temp)
        set_pressure = c_double(set_pressure)  # convert to c_double
        error = self.OB1_Set_Press(self.Instr_ID.value, set_channel, set_pressure, ctypes.byref(self.Cal), 1000)

    def DataAcquisitionThread(self):
        data_in = ctypes.c_double()
        self.t0 = time.time()
        while (self.bAcquiring):
            time.sleep(0.01)
            self.t.append(time.time()-self.t0)
            if self.OB1_Get_Press(self.Instr_ID.value, c_int32(1), 1, self.Cal, ctypes.byref(data_in), 1000):
                self.Pdata.append(0)
            else: self.Pdata.append(float(data_in.value))
            if self.OB1_Get_Sens_Data(self.Instr_ID.value, c_int32(1), 1, ctypes.byref(data_in)):
                self.Flowdata.append(0)
            else: self.Flowdata.append(float(data_in.value))
            self.Psetdata.append(self.pset)
            self.DataPlot()

    def DataPlot(self):
        self.pplot.setData(self.t, self.Pdata)
        self.psetplot.setData(self.t, self.Psetdata)
        self.flowplot.setData(self.t, self.Flowdata)
        gc.collect()

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
        if self.bCanClose:
            self.bAcquiring = False
            if self.DAQThread != None:
                self.DAQThread.join()
            event.accept()
        else:
            self.bShow = False
            self.hide()
            event.ignore()
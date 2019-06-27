#Tested with Python 3.5.1 (IDE Eclipse V4.5.2 + Pydev V5.0.0)
#add python_xx and python_xx/DLL to the project path 

import sys
from _ast import Load
sys.path.append('D:/dev/SDK/DLL32/DLL32') #add the path of the library here
sys.path.append('D:/dev/SDK/Python_32')#add the path of the LoadElveflow.py

from ctypes import *

from array import array

from Elveflow32 import *


#
# Initialization of AF1 ( ! ! ! REMEMBER TO USE .encode('ascii')
#
Instr_ID=c_int32()
print("Instrument name and regulator type and sensor type  hardcoded in the python script")
#see User guide to determine regulator type NI MAX to determine the instrument name 
error=AF1_Initialization('My_AF1'.encode('ascii'),4,1,byref(Instr_ID)) 
# all functions will return error code to help you to debug your code, for further information see user guide
print('error:%d' % error)
print("AF1 ID: %d" % Instr_ID.value)


#
#Set the calibration type
#

Calib=(c_double*1000)() # always define array that way, calibration should have 1000 elements
repeat=True
while repeat==True:
    answer=input('select calibration type (default, load, new ) : ')
    #answer='load'#test purpose only
    Calib_path='C:\\Users\\Marchand\\Desktop\\Calibration\\CalibAF1_python.txt'
    if answer=='default':
        error=Elveflow_Calibration_Default (byref(Calib),1000)
        #for i in range (0,1000):
            #print('[',i,']: ',Calib[i])
        repeat=False
    if answer=='load':
        error=Elveflow_Calibration_Load (Calib_path.encode('ascii'), byref(Calib), 1000)
        for i in range (0,1000):
            print('[',i,']: ',Calib[i])
        repeat=False
        
    if answer=='new':
        AF1_Calib (Instr_ID.value, Calib, 1000)
        #for i in range (0,1000):
            #print('[',i,']: ',Calib[i])
        error=Elveflow_Calibration_Save(Calib_path.encode('ascii'), byref(Calib), 1000)
        print ('calib saved in %s' % Calib_path.encode('ascii'))
        repeat=False


#
#Main loops 
#
    
repeat=True
while repeat:
    answer=input('what to do (set_p, get_p, get_sens, get_trig, set_trig or exit) : ')
    if answer=='set_p':
        set_pressure=input("select pressure (-1000 to 8000 mbars) : ")
        set_pressure=float(set_pressure) 
        set_pressure=c_double(set_pressure)
        error=AF1_Set_Press(Instr_ID.value, set_pressure, byref(Calib),1000) 
        
        
    if answer=='get_p':
        get_pressure=c_double(0)
        error=AF1_Get_Press(Instr_ID.value, 100, byref(Calib),byref(get_pressure), 1000)
        print('Pressure',get_pressure.value)
        #print('ch1: ', get_pressure()[0] , ' mbar\nch2: ', get_pressure()[1] ,' mbar\nch3: ', get_pressure()[2] , ' mbar\nch4: ', get_pressure()[3] ,' mbar')
        
    if answer=="get_sens":
        data_sens=c_double()
        error=AF1_Get_Flow_rate(Instr_ID.value,byref(data_sens))
        print('Flow: ', data_sens.value)
        
    if answer=="get_trig":
        trigger_ext=c_int32()  
        error=AF1_Get_Trig(Instr_ID, byref(trigger_ext))
        if trigger_ext.value==1:
            print('trigger high')
        else: 
            print('trigger low')
            
    if answer=="set_trig":
        trigger_int_val=input("set trigger value (high=1, low=0): ")
        trigger_int_val=int(trigger_int_val) #convert to int
        trigger_int_val=c_int32(trigger_int_val) #convert to c_int32
        error=AF1_Set_Trig(Instr_ID, trigger_int_val)

    if answer=='exit':
        repeat=False
    
    print( 'error :', error)
        

error=AF1_Destructor(Instr_ID.value)



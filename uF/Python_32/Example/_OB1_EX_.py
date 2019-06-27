#Tested with Python 3.5.1 (IDE Eclipse V4.5.2 + Pydev V5.0.0)
#add python_xx and python_xx/DLL to the project path 

import sys
sys.path.append('D:/dev/SDK/DLL32/DLL32') #add the path of the library here
sys.path.append('D:/dev/SDK/Python_32')#add the path of the LoadElveflow.py

from ctypes import *

from array import array

from Elveflow32 import *


#
# Initialization of OB1 ( ! ! ! REMEMBER TO USE .encode('ascii')
#
Instr_ID=c_int32()
print("Instrument name and regulator types hardcoded in the python script")
#see User guide to determine regulator type NI MAX to determine the instrument name 
error=OB1_Initialization('01C9D9C3'.encode('ascii'),1,2,4,3,byref(Instr_ID)) 
# all functions will return error code to help you to debug your code, for further information see user guide
print('error:%d' % error)
print("OB1 ID: %d" % Instr_ID.value)

#add one digital flow sensor with water calibration (OB1 MK3+ only) 
#error=OB1_Add_Sens(Instr_ID, 1, 1, 1, 0, 7)
#print('error add digit flow sensor:%d' % error)


#add one analog flow sensor
#error=OB1_Add_Sens(Instr_ID, 1, 5, 0, 0, 7)
#print('error add analog flow sensor:%d' % error)



#
#Set the calibration type
#

Calib=(c_double*1000)() # always define array that way, calibration should have 1000 elements
repeat=True
while repeat==True:
    answer=input('select calibration type (default, load, new ) : ')
    #answer='default'#test purpose only
    Calib_path='C:\\Users\\Marchand\\Desktop\\Calibration\\Calib.txt'
    if answer=='default':
        error=Elveflow_Calibration_Default (byref(Calib),1000)
        #for i in range (0,1000):
            #print('[',i,']: ',Calib[i])
        repeat=False
    if answer=='load':
        error=Elveflow_Calibration_Load (Calib_path.encode('ascii'), byref(Calib), 1000)
        #for i in range (0,1000):
            #print('[',i,']: ',Calib[i])
        repeat=False
        
    if answer=='new':
        OB1_Calib (Instr_ID.value, Calib, 1000)
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
    answer=input('what to do (set_p, get_p, get_sens, get_all, get_trig, set_trig or exit) : ')
    if answer=='set_p':
        set_channel=input("select channel(1-4) : ")
        set_channel=int(set_channel) #convert to int
        set_channel=c_int32(set_channel) #convert to c_int32
        set_pressure=input("select pressure (-1000 to 8000 mbars) : ")
        set_pressure=float(set_pressure) 
        set_pressure=c_double(set_pressure)#convert to c_double
        error=OB1_Set_Press(Instr_ID.value, set_channel, set_pressure, byref(Calib),1000) 
        
        
    if answer=='get_p':
        set_channel=input("select channel(1-4) : ")
        set_channel=int(set_channel) #convert to int
        set_channel=c_int32(set_channel) #convert to c_int32
        get_pressure=c_double()
        error=OB1_Get_Press(Instr_ID.value, set_channel, 1, byref(Calib),byref(get_pressure), 1000) # Acquire_data =1 -> Read all the analog value
        print('error: ', error)
        print('ch',set_channel,': ',get_pressure.value)
        #print('ch1: ', get_pressure()[0] , ' mbar\nch2: ', get_pressure()[1] ,' mbar\nch3: ', get_pressure()[2] , ' mbar\nch4: ', get_pressure()[3] ,' mbar')
        
    if answer=="get_all":
        data_sens=c_double()
        get_pressure=c_double()
        error=OB1_Get_Press(Instr_ID.value, 1, 1, byref(Calib),byref(get_pressure), 1000) #Ch =1;  Acquire_data =1 -> Read all the analog value 
        print('error: ', error)
        print('Press ch 1: ',get_pressure.value)
        
        for i in range(2,5):
            error=OB1_Get_Press(Instr_ID.value, i, 0, byref(Calib),byref(get_pressure), 1000) #Ch = i;  Acquire_data =0 -> Use the value acquired in OB1_Get_Press
            print('error: ', error)
            print('Press ch ', i,': ',get_pressure.value) 
       
        for i in range(1,5):
            error=OB1_Get_Sens_Data(Instr_ID.value, i, 0, byref(data_sens)) #Ch = i;  Acquire_data =0 -> Use the value acquired in OB1_Get_Press
            print('error: ', error)
            print('Sens ch ', i,': ',data_sens.value) 
       
    if answer=="get_sens":
        data_sens=c_double()
        set_channel=input("select channel(1-4) : ")
        set_channel=int(set_channel) #convert to int
        set_channel=c_int32(set_channel) #convert to c_int32
        error=OB1_Get_Sens_Data(Instr_ID.value,set_channel, 1,byref(data_sens)) # Acquire_data =1 -> Read all the analog value
        print('Press or Flow ch', set_channel.value,': ',data_sens.value)
        
    if answer=="get_trig":
        trigger_ext=c_int32()  
        error=OB1_Get_Trig(Instr_ID, byref(trigger_ext))
        if trigger_ext.value==1:
            print('trigger high')
        else: 
            print('trigger low')
            
    if answer=="set_trig":
        trigger_int_val=input("set trigger value (high=1, low=0): ")
        trigger_int_val=int(trigger_int_val) #convert to int
        trigger_int_val=c_int32(trigger_int_val) #convert to c_int32
        error=OB1_Set_Trig(Instr_ID, trigger_int_val)

    if answer=='exit':
        repeat=False
    
    print( 'error :', error)
        

error=OB1_Destructor(Instr_ID.value)


#OB1_Calib(OB1_ID,Calib,1000)

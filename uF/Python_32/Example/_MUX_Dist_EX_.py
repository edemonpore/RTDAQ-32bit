#Tested with Python 3.5.1 (IDE Eclipse V4.5.2 + Pydev V5.0.0)
#add python_xx and python_xx/DLL to the project path 

import sys
sys.path.append('D:/dev/SDK/DLL32/DLL32') #add the path of the library here
sys.path.append('D:/dev/SDK/Python_32')#add the path of the LoadElveflow.py

from ctypes import *

from array import array

from Elveflow32 import *


#
# Initialization of MUX_Dist ( ! ! ! REMEMBER TO USE .encode('ascii')
#
Instr_ID=c_int32()
print("Instrument name and regulator types hardcoded in the python script")
#see User guide to determine regulator type NI MAX to determine the instrument name 
error=MUX_Dist_Initialization("ASRL4::INSTR".encode('ascii'),byref(Instr_ID)) #Chose the com port, can be ASRLXXX::INSTR (where XXX=port number)
# all functions will return error code to help you to debug your code, for further information see user guide
print('error:%d' % error)
print("MUX Dist ID: %d" % Instr_ID.value)

#
#Main loops 
#
    
repeat=True
while repeat:
    answer=input('what to do (get_valve, set_valve or exit) : ')
    
        
    if answer=="get_valve":
        valve=c_int32(-1)
        error=MUX_Dist_Get_Valve(Instr_ID.value,byref(valve))
        print('selected channel',valve.value)
        
    if answer=="set_valve":
        valve2=c_double()
        Valve2=input("select valve (1-6 or 1-10) : ")
        Valve2=int(Valve2) #convert to int
        Valve2=c_int32(Valve2) #convert to c_int32
        error=MUX_Dist_Set_Valve(Instr_ID.value,Valve2)
            
    
    if answer=='exit':
        repeat=False
    
    print( 'error :', error)
        

error=MUX_Dist_Destructor(Instr_ID.value)

    
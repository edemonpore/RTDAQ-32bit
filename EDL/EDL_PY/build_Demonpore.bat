REM the environmental variables for the build command
REM PYTHON_ROOT C:\ProgramData\Anaconda3_32bit
REM BOOST_ROOT C:\Users\User\Desktop\Demonpore\CPrograms\boost_1_68_0
REM to rebuild the .pyd file
REM
REM NOTE: %BOOST_ROOT%\stage\lib this folder for the Boost built libraries,
REM it contains for example the libboost_python36-mgw53-mt-x32-1_67.dll

g++ -shared edl_pywrapper.cpp
-IC:\ProgramData\Anaconda3_32bit\include
-IC:\Users\User\Desktop\Demonpore\CPrograms\boost_1_68_0
-o edl_py.pyd
-L%BOOST_ROOT%\stage\lib
-lboost_python36-mgw53-mt-x32-1_67
-LC:\ProgramData\Anaconda3_32bit\libs -lpython37
-L. -IEDL -ledl
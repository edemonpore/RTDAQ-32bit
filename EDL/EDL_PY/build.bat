REM the environmental variables used in the build command in my specific case areas follow
REM PYTHON_ROOT C:\Users\FCona\AppData\Local\Programs\Python\Python36-32
REM BOOST_ROOT C:\Program Files\boost\boost_1_67_0
REM you should adapt them to your system if you want to rebuild the .pyd file
REM
REM NOTE: %BOOST_ROOT%\stage\lib this folder is where I installed the Boost built libraries,
REM it contains for example the libboost_python36-mgw53-mt-x32-1_67.dll that is part of the zip

g++ -shared
edl_pywrapper.cpp
-I%PYTHON_ROOT%\include
-I%BOOST_ROOT%
-o edl_py.pyd
-L%BOOST_ROOT%\stage\lib -lboost_python36-mgw53-mt-x32-1_67
-L%PYTHON_ROOT%\libs" -lpython36
-L. -IEDL -ledl
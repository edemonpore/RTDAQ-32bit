REM ctypes approach
REM EYafuso


g++ -shared
edl_pywrapper.cpp
-I%PYTHON_ROOT%\include
-I%BOOST_ROOT%
-o edl_py.pyd
-L%BOOST_ROOT%\stage\lib -lboost_python36-mgw53-mt-x32-1_67
-L%PYTHON_ROOT%\libs" -lpython36
-L. -IEDL -ledl
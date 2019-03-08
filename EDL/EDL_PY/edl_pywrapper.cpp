#ifndef EDL_PYWRAPPER_H
#define EDL_PYWRAPPER_H

#include "edl.h"
#include <boost/python.hpp>
#include <boost/list.hpp>

class EDL_PY : public EDL {
public:
    EDL_PY() : EDL() {
		
	}
	
    unsigned int detectDevices(list &devices_py) {
		std::vector <std::string> devices;
        unsigned int res = (unsigned int)EDL::detectDevices(devices);
		for (unsigned int i = 0; i < devices.size(); i++) {
            devices_py.append(devices.at(i));
		}
		return res;
	}
	
    unsigned int connectDevice(const std::string deviceId_py) {
        unsigned int res = (unsigned int)EDL::connectDevice(deviceId_py);
		return res;
	}

    unsigned int disconnectDevice() {
        unsigned int res = (unsigned int)EDL::disconnectDevice();
        return res;
    }

    unsigned int getDeviceStatus(EdlDeviceStatus_t &status) {
        unsigned int res = (unsigned int)EDL::getDeviceStatus(status);
        return res;
	}

    unsigned int readData(int dataToRead_py, list &dataRead_py, list &buffer_py) {
        unsigned int dataToRead = (unsigned int)dataToRead_py;
        unsigned int dataRead;
        std::vector <float> buffer;
        unsigned int res = (unsigned int)EDL::readData(dataToRead,
                                                       dataRead,
                                                       buffer);
        for (unsigned int i = 0; i < buffer.size(); i++) {
            buffer_py.append(buffer.at(i));
        }
        dataRead_py[0] = (int)dataRead;
        return res;
    }

    unsigned int purgeData() {
        unsigned int res = (unsigned int)EDL::purgeData();
        return res;
    }

    unsigned int setCommand(unsigned int commandId_py,
                            EdlCommandStruct_t &commandStruct_py,
                            bool sendFlag_py) {
        EdlCommandId_t commandId = (EdlCommandId_t)commandId_py;
        unsigned int res = (unsigned int)EDL::setCommand(commandId,
                                                         commandStruct_py,
                                                         sendFlag_py);
        return res;
    }
};

using namespace boost::python;

BOOST_PYTHON_MODULE(edl_py) {
    Py_Initialize();

	class_<EdlDeviceStatus_t>("EdlDeviceStatus_t")
        .def_readwrite("availableDataPackets", &EdlDeviceStatus_t::availableDataPackets)
        .def_readwrite("bufferOverflowFlag", &EdlDeviceStatus_t::bufferOverflowFlag)
        .def_readwrite("lostDataFlag", &EdlDeviceStatus_t::lostDataFlag);
		
	class_<EdlCommandStruct_t>("EdlCommandStruct_t")
        .def_readwrite("radioId", &EdlCommandStruct_t::radioId)
        .def_readwrite("checkboxChecked", &EdlCommandStruct_t::checkboxChecked)
        .def_readwrite("buttonPressed", &EdlCommandStruct_t::buttonPressed)
        .def_readwrite("value", &EdlCommandStruct_t::value);
		
	class_<EDL_PY>("EDL_PY", init<>())
        .def("detectDevices", &EDL_PY::detectDevices)
        .def("connectDevice", &EDL_PY::connectDevice)
        .def("disconnectDevice", &EDL_PY::disconnectDevice)
        .def("getDeviceStatus", &EDL_PY::getDeviceStatus)
        .def("readData", &EDL_PY::readData)
        .def("purgeData", &EDL_PY::purgeData)
        .def("setCommand", &EDL_PY::setCommand);
}

#endif // EDL_PYWRAPPER_H

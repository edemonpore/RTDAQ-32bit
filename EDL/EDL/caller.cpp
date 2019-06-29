/*! \file caller.cpp
 * \brief Sample program to connect to an e4 device, set a working configuration and read some data.
 */
#include <iostream>
#include "windows.h"
#include "edl.h"

/*! \def MINIMUM_DATA_PACKETS_TO_READ
 * \brief Minimum number of available data packets to perform a read.
 * May be increased in case of frequent data loss due to buffer overflow:
 * #EdlDeviceStatus_t::bufferOverflowFlag set true.
 */
#define MINIMUM_DATA_PACKETS_TO_READ 10

/*! \fn configureWorkingModality
 * \brief Configure sampling rate, current range and bandwidth.
 */
void configureWorkingModality(EDL edl) {
	/*! Declare an #EdlCommandStruct_t to be used as configuration for the commands. */
    EdlCommandStruct_t commandStruct;

	/*! Set the sampling rate to 5kHz. Stack the command (do not apply). */
    commandStruct.radioId = EDL_RADIO_SAMPLING_RATE_5_KHZ;
    edl.setCommand(EdlCommandSamplingRate, commandStruct, false);

	/*! Set the current range to 200pA. Stack the command (do not apply). */
    commandStruct.radioId = EDL_RADIO_RANGE_200_PA;
    edl.setCommand(EdlCommandRange, commandStruct, false);

	/*! Disable current filters (final bandwidth equal to half sampling rate). Apply all of the stacked commands. */
    commandStruct.radioId = EDL_RADIO_FINAL_BANDWIDTH_SR_2;
    edl.setCommand(EdlCommandFinalBandwidth, commandStruct, true);
}

/*! \fn compensateDigitalOffset
 * \brief Compensate digital offset due to electrical load.
 */
void compensateDigitalOffset(EDL edl) {
	/*! Declare an #EdlCommandStruct_t to be used as configuration for the commands. */
    EdlCommandStruct_t commandStruct;

	/*! Select the constant protocol: protocol 0. */
    commandStruct.value = 0.0;
    edl.setCommand(EdlCommandMainTrial, commandStruct, false);

	/*! Set the vHold to 0mV. */
    commandStruct.value = 0.0;
    edl.setCommand(EdlCommandVhold, commandStruct, false);

	/*! Apply the protocol. */
    edl.setCommand(EdlCommandApplyProtocol, commandStruct, true);
	
    /*! Start the digital compensation. */
    commandStruct.buttonPressed = EDL_BUTTON_PRESSED;
    edl.setCommand(EdlCommandCompensateAllChannels, commandStruct, true);

    /*! Wait for some seconds. */
    Sleep(5000);

    /*! Stop the digital compensation. */
    commandStruct.buttonPressed = EDL_BUTTON_RELEASED;
    edl.setCommand(EdlCommandCompensateAllChannels, commandStruct, true);
}

/*! \fn setTriangularProtocol
 * \brief Set the parameters and start a triangular protocol.
 */
void setTriangularProtocol(EDL edl) {
    /*! Declare an #EdlCommandStruct_t to be used as configuration for the commands. */
    EdlCommandStruct_t commandStruct;

    /*! Select the triangular protocol: protocol 1. */
    commandStruct.value = 1.0;
    edl.setCommand(EdlCommandMainTrial, commandStruct, false);

    /*! Set the vHold to 0mV. */
    commandStruct.value = 0.0;
    edl.setCommand(EdlCommandVhold, commandStruct, false);

    /*! Set the triangular wave amplitude to 50mV: 100mV positive to negative delta voltage. */
    commandStruct.value = 50.0;
    edl.setCommand(EdlCommandVamp, commandStruct, false);

    /*! Set the triangular period to 100ms. */
    commandStruct.value = 100.0;
    edl.setCommand(EdlCommandTPeriod, commandStruct, false);

    /*! Apply the protocol. */
    edl.setCommand(EdlCommandApplyProtocol, commandStruct, true);
}

/*! \fn readAndSaveSomeData
 * \brief Reads data from the EDL device and writes them on an open file.
 */
EdlErrorCode_t readAndSaveSomeData(EDL edl, FILE * f) {
    /*! Declare an #EdlErrorCode_t to be returned from #EDL methods. */
    EdlErrorCode_t res;
	
	/*! Declare an #EdlDeviceStatus_t variable to collect the device status. */
    EdlDeviceStatus_t status;
	
	/*! Declare a variable to collect the number of read data packets. */
    unsigned int readPacketsNum;
	
	/*! Declare a vector to collect the read data packets. */
    std::vector <float> data;
	
    Sleep(500);

    std::cout << "purge old data" << std::endl;
	/*! Get rid of data acquired during the device configuration */
	res = edl.purgeData();
	
	/*! If the EDL::purgeData returns an error code output an error and return. */
    if (res != EdlSuccess) {
        std::cout << "failed to purge data" << std::endl;
        return res;
    }

	/*! Start collecting data. */
	
    std::cout << "collecting data... ";
	unsigned int c;
    for (c = 0; c < 1e3; c++) {
		/*! Get current status to know the number of available data packets EdlDeviceStatus_t::availableDataPackets. */
        res = edl.getDeviceStatus(status);
        
        /*! If the EDL::getDeviceStatus returns an error code output an error and return. */
        if (res != EdlSuccess) {
            std::cout << "failed to get device status" << std::endl;
            return res;
        }
        
		if (status.bufferOverflowFlag) {
			std::cout << std::endl << "lost some data due to buffer overflow; increase MINIMUM_DATA_PACKETS_TO_READ to improve performance" << std::endl;
		}
		
		if (status.lostDataFlag) {
			std::cout << std::endl << "lost some data from the device; decrease sampling frequency or close unused applications to improve performance" << std::endl;
			std::cout << "data loss may also occur immediately after sending a command to the device" << std::endl;
		}
		
        if (status.availableDataPackets >= MINIMUM_DATA_PACKETS_TO_READ) {
		    /*! If at least MINIMUM_DATA_PACKETS_TO_READ data packet are available read them. */
			res = edl.readData(status.availableDataPackets, readPacketsNum, data);
			
	        /*! If the device is not connected output an error, close the file for data storage and return. */
            if (res == EdlDeviceNotConnectedError) {
				std::cout << "the device is not connected" << std::endl;
                fclose(f);
				return res;
				
			} else {
	            /*! If the number of available data packets is lower than the number of required packets output an error, but the read is performed nonetheless
				 * with the available data. */
				if (res == EdlNotEnoughAvailableDataError) {
					std::cout << "not enough available data, only "  << readPacketsNum << " packets have been read" << std::endl;
				}
				
	            /*! The output vector consists of \a readPacketsNum data packets of #EDL_CHANNEL_NUM floating point data each.
				 * The first item in each data packet is the value voltage channel [mV];
				 * the following items are the values of the current channels either in pA or nA, depending on value assigned to #EdlCommandSamplingRate. */
                for (unsigned int readPacketsIdx = 0; readPacketsIdx < readPacketsNum; readPacketsIdx++) {
                    for (unsigned int channelIdx = 0; channelIdx < EDL_CHANNEL_NUM; channelIdx++) {
                        fwrite((unsigned char *)&data.at(readPacketsIdx*EDL_CHANNEL_NUM+channelIdx), sizeof(float), 1, f);
                    }
                }
				
			}
			
        } else {
		    /*! If the read was not performed wait 1 ms before trying to read again. */
            Sleep(1);
		}
    }
	std::cout << "done" << std::endl;
	
    return res;
}

/*! \fn main
 * \brief Application entry point.
 */
int main() {
	/*! Initialize an #EDL object. */
    EDL edl;
	
	/*! Declare an #EdlErrorCode_t to be returned from #EDL methods. */
    EdlErrorCode_t res;
	
	/*! Initialize a vector of strings to collect the detected devices. */
    std::vector <std::string> devices;

    std::ios::sync_with_stdio(true);
	
	/*! Detect plugged in devices. */
    res = edl.detectDevices(devices);
	
	/*! If none is found output an error and return. */
    if (res != EdlSuccess) {
        std::cout << "could not detect devices" << std::endl;
        return -1;
    }

    std::cout << "first device found " << devices.at(0) << std::endl;
	
	/*! If at list one device is found connect to the first one. */
    res = edl.connectDevice(devices.at(0));
	
    std::cout << "connecting... ";
	/*! If the EDL::connectDevice returns an error code output an error and return. */
    if (res != EdlSuccess) {
        std::cout << "connection error" << std::endl;
        return -1;
    }
	std::cout << "done" << std::endl;

	/*! Configure the device working modality. */
    std::cout << "configuring working modality" << std::endl;
    configureWorkingModality(edl);
	
	/*! Compensate for digital offset. */
	std::cout << "performing digital offset compensation... ";
    compensateDigitalOffset(edl);
	std::cout << "done" << std::endl;
	
    std::cout << "applying triangular test protocol" << std::endl;
    /*! Apply a triangular test protocol. */
    setTriangularProtocol(edl);

	/*! Initialize a file descriptor to store the read data packets. */
    FILE * f;
    f = fopen("data.dat", "wb+");
	
    res = readAndSaveSomeData(edl, f);
    if (res != EdlSuccess) {
        std::cout << "failed to read data" << std::endl;
        return -1;
    }
	
	/*! Close the file for data storage. */
    fclose(f);

	/*! Try to disconnect the device.
	 * \note Data reading is performed in a separate thread started by EDL::connectDevice.
	 * The while loop may be useful in case few operations are performed between before calling EDL::disconnectDevice,
	 * to ensure that the connection is fully established before trying to disconnect. */
	 
	std::cout << "disconnecting... ";
    unsigned int c = 0;
    while (c++ < 1e3) {
		res = edl.disconnectDevice();
		if (res == EdlSuccess) {
            std::cout << "done" << std::endl;
			break;
		}
		
		/*! If the disconnection was unsuccessful wait 1 ms before trying to disconnect again. */
        Sleep(1);
    }

	/*! If the EDL::disconnectDevice returns an error code after trying for 1 second (1e3 * 1ms) output an error and return. */
    if (res != EdlSuccess) {
        std::cout << "disconnection error" << std::endl;
        return -1;
    }

    return 0;
}
/*! [caller_snippet] */

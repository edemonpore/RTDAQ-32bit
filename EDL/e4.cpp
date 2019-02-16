/* caller-e4.cpp
dll to connect e4 device and export functions to Python
EYafuso
*/

#include <iostream>
#include "windows.h"
#include "edl.h"

#define MINIMUM_DATA_PACKETS_TO_READ 10

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
    edl.setCommand(EdlCommandCompAll, commandStruct, true);

    /*! Wait for some seconds. */
    Sleep(5000);

    /*! Stop the digital compensation. */
    commandStruct.buttonPressed = EDL_BUTTON_RELEASED;
    edl.setCommand(EdlCommandCompAll, commandStruct, true);
}


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

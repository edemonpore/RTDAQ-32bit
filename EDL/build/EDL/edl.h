/*! \file edl.h
 * \brief Declares class EDL.
 */
#ifndef EDL_H
#define EDL_H

#include <vector>
#include <string>

#include "edl_global.h"
#include "edl_errorcodes.h"
#include "edl_devicespecs.h"

/*! \struct EdlDeviceStatus_t
 * \brief Struct that contains information on the device status.
 * Returned by EDL::getDeviceStatus.
 */
typedef struct {
    unsigned int availableDataPackets; /*!< Number of data packets available for read.
                                        * Each data packets consists of 1 sample per channel.
                                        * Successful calls to EDL::readData reduce this number. */
    bool bufferOverflowFlag; /*!< This flag is true if the internal buffer has been filled and old data has been overwritten.
                              * This flag is reset after a call to EDL::getDeviceStatus. */
    bool lostDataFlag; /*!< This flag is true if the device has sent too much data and some has been lost.
                        * This flag is reset after a call to EDL::getDeviceStatus. */
} EdlDeviceStatus_t;

/*! \struct EdlCommandStruct_t
 * \brief Struct that contains commands configuration for EDL::setCommand.
 * Up to 1 field is relevant, depending on the #EdlCommandId_t used.
 */
typedef struct {
    unsigned int radioId; /*!< Index of the radio button to select. */
    bool checkboxChecked; /*!< Flag indicating whether to check or not a checkbox. */
    bool buttonPressed; /*!< Flag indicating whether to press or not a checkbutton. */
    double value; /*!< Value to set a numeric field. */
} EdlCommandStruct_t;

/*! \class EDL
 * \brief This class can be used as interface to Elements devices.
 */

class EDLSHARED_EXPORT EDL {
public:
    /*! \brief EDL constructor.
     */
    EDL();

    /*! \brief EDL destructor.
     */
    ~EDL();

    /*! \brief Detects plugged in devices.
     *
     * \param deviceIds [out] List of plugged in devices IDs.
     * \return #EdlErrorCode_t Error code.
     */
    EdlErrorCode_t detectDevices(EDL_OUT std::vector <std::string> &deviceIds);

    /*! \brief Connects to a specific device
     * Calling this method if a device is already connected will return an error code.
     *
     * \param deviceId [in] Device ID of the device to connect to.
     * \return #EdlErrorCode_t Error code.
     */
    EdlErrorCode_t connectDevice(EDL_IN std::string deviceId);

    /*! \brief Disconnects from connected device.
     * Calling this method if no device is connected will return an error code.
     *
     * \return #EdlErrorCode_t Error code.
     */
    EdlErrorCode_t disconnectDevice(EDL_VOID);

    /*! \brief Returns information on the device status.
     * Calling this method if no device is connected will return an error code.
     *
     * \param status [out] Struct containing device information.
     * \return #EdlErrorCode_t Error code.
     */
    EdlErrorCode_t getDeviceStatus(EDL_OUT EdlDeviceStatus_t &status);

    /*! \brief Reads data packets from the device.
     * The returned buffer consists of \a dataRead data packets of #EDL_CHANNEL_NUM samples each.
     * So the vector total size will be \a dataRead * #EDL_CHANNEL_NUM. \n
     * Calling this method with \a dataRead grater than the actual number of available data packets will return an error code,
     * but a vector consisting of all the available data packets will still be returned, and \a dataRead will be smaller than
     * \a dataToRead. \n
     * Calling this method if no device is connected will return an error code.
     *
     * \param dataToRead [in] Number of data packets to read.
     * \param dataRead [out] Number of data packets actually read (may be lower than dataToRead).
     * \param buffer [out] Buffer of data read. Each data packet consists of 1 sample per channel.
     * In each data packet the first sample is the voltage command;
     * the following samples are the measured currents, 1 sample per current channel.
     * \return #EdlErrorCode_t Error code.
     */
    EdlErrorCode_t readData(EDL_IN unsigned int dataToRead,
                            EDL_OUT unsigned int &dataRead,
                            EDL_OUT std::vector <float> &buffer);


    /*! \brief Purges data read from the device.
     * This command is useful to get rid of data acquired during the device configuration (e.g. during setting of sampling rate or digital offset compensation).
     * Calling this method if no device is connected will return an error code.
     *
     * \return #EdlErrorCode_t Error code.
     */
    EdlErrorCode_t purgeData(EDL_VOID);

    /*! \brief Sets a command for the device.
     * The command can either be sent immediately or just stacked and sent together with other commands later.
     * Calling this method if no device is connected will return an error code.
     *
     * \param commandId [in] Index of the command to send.
     * This argument defines WHAT the command will do e.g. changing the sampling rate, rather than setting a protocol parameter.
     * \param commandStruct [in] Configuration of the command to send.
     * This argument defines HOW the command will operate e.g. setting the current range to 200pA, rather than to 20nA.
     * \param sendFlag [in] Flag to send the command immediately.
     * This argument defines IF the command is actually sent or just stacked.
     * All stacked commands are sent on the first call to EDL::setCommand with \a sendFlag set true. \n
     * \note When setting a protocol parameter, \a sendFlag must be false, otherwise an error code will be returned;
     * for a protocol to be applied all protocol parameters must be set silently before and a EdlCommandApplyProtocol must be sent afterwards. \n
     * \note When sending a push button command, \a sendFlag must be true, otherwise an error code will be returned;
     * push buttons cause events, not configuration changes, so they can't be stacked.
     * \return #EdlErrorCode_t Error code.
     */
    EdlErrorCode_t setCommand(EDL_IN EdlCommandId_t commandId,
                              EDL_IN EdlCommandStruct_t &commandStruct,
                              EDL_IN bool sendFlag);
};

#endif // EDL_H

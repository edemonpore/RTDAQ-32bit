/*! \file edl_errorcodes.h
 * \brief Defines error codes returned by EDL methods.
 */
#ifndef EDL_ERRORCODES_H
#define EDL_ERRORCODES_H

/*! \def EDL_CONNECTION_ERRORS_OFFSET
 * \brief Offset of error codes related to connection errors.
 */
#define EDL_CONNECTION_ERRORS_OFFSET 0x0100

/*! \def EDL_COMMANDS_CONFIGURATION_ERRORS_OFFSET
 * \brief Offset of error codes related to bad command configurations.
 */
#define EDL_COMMANDS_CONFIGURATION_ERRORS_OFFSET 0x0200

/*! \def EDL_CONFIG_ERRORS_OFFSET
 * \brief Offset of error codes related to bad dll generation.
 * \note Communicate such kind of errors to Elements s.r.l. info@elements-ic.com.
 */
#define EDL_CONFIG_ERRORS_OFFSET 0x1000

/*! \enum EdlErrorCode_t
 * \brief Enumerates error codes returned by EDL methods.
 */
typedef enum {
    EdlSuccess = 0x0000, /*!< EDL method returns with no errors. */
    EdlNoDevicesError = 0x0001, /*!< Error returned by EDL::detectDevices if no devices are plugged in.
                                 * This error may be due to problems with FTDI driver installation too. */
    EdlDeviceNotConnectedError = 0x002, /*!< Error returned when a EDL method other than EDL::detectDevices or EDL::connectDevice
                                         * is called but no device is connected yet. */
    EdlDeviceExpiredError = 0x0003, /*!< Error returned when calling EDL::connectDevice to connect to an expired device.
                                     * \note Communicate such kind of errors to Elements s.r.l. info@elements-ic.com. */
    EdlWriteToFtdiError = 0x0004, /*!< Error returned when failing to send a command to the device. */
    EdlDeviceConnectionError = EDL_CONNECTION_ERRORS_OFFSET+0x0001, /*!< Error returned when EDL::connectDevice fails to open a
                                                                     * connection channel with the device. */
    EdlDeviceAlreadyConnectedError = EDL_CONNECTION_ERRORS_OFFSET+0x0002, /*!< Error returned if calling EDL::connectDevice when a
                                                                           * device is already connected. */
    EdlDeviceConnectionLatencyError = EDL_CONNECTION_ERRORS_OFFSET+0x0003, /*!< Error returned when EDL::connectDevice fails to set
                                                                            * connection latency. */
    EdlDeviceConnectionSetUSBError = EDL_CONNECTION_ERRORS_OFFSET+0x0004, /*!< Error returned when EDL::connectDevice fails to set
                                                                           * USB connection parameters. */
    EdlDeviceConnectionTransferSizeError = EDL_CONNECTION_ERRORS_OFFSET+0x0005, /*!< Error returned when EDL::connectDevice fails to set
                                                                                 * USB packets size. */
    EdlDeviceConnectionPurgeError = EDL_CONNECTION_ERRORS_OFFSET+0x0006, /*!< Error returned when EDL::connectDevice fails to purge the
                                                                          * USB channel. */
    EdlDeviceConnectionFirstWriteError = EDL_CONNECTION_ERRORS_OFFSET+0x0007, /*!< Error returned when EDL::connectDevice fails the test
                                                                               * write on a newly opened communication channel. */
    EdlDeviceDisconnectionError = EDL_CONNECTION_ERRORS_OFFSET+0x0008, /*!< Error returned when EDL::disconnectDevice fails to close
                                                                        * a communication channel. */
    EdlCommandIdOutOfRangeError = EDL_COMMANDS_CONFIGURATION_ERRORS_OFFSET+0x0001, /*!< Error returned when setting an invalid value to
                                                                                    * EDL::setCommand first argument. */
    EdlTrialValueSendNotDisabledError = EDL_COMMANDS_CONFIGURATION_ERRORS_OFFSET+0x0002, /*!< Error returned when setting EDL::setCommand
                                                                                          * third argument true with a protocol value command
                                                                                          * type. */
    EdlPushButtonSendDisabledError = EDL_COMMANDS_CONFIGURATION_ERRORS_OFFSET+0x0003, /*!< Error returned when setting EDL::setCommand
                                                                                       * third argument false with a push button command
                                                                                       * type. */
    EdlViolatedTrialRuleError = EDL_COMMANDS_CONFIGURATION_ERRORS_OFFSET+0x0004, /*!< Error returned when the protocol parameters set violate
                                                                                  * a rule and EDL::setCommand with EdlCommandApplyProtocol
                                                                                  * as first parameter is called. */
    EdlNotEnoughAvailableDataError = EDL_COMMANDS_CONFIGURATION_ERRORS_OFFSET+0x0005, /*!< Error returned when calling EDL::readData with a
                                                                                       * too high value as first argument. \note To avoid this
                                                                                       * call EDL::getDeviceStatus before any read and check the
                                                                                       * number of available data packets. */
    EdlWrongValueBitsNumSumError = EDL_CONFIG_ERRORS_OFFSET+0x0001, /*!< Error due to bad dll generation.
                                                                     * \note Communicate such kind of errors to Elements s.r.l. info@elements-ic.com. */
    EdlWrongSignBitsNumError = EDL_CONFIG_ERRORS_OFFSET+0x0002, /*!< Error due to bad dll generation.
                                                                 * \note Communicate such kind of errors to Elements s.r.l. info@elements-ic.com. */
    EdlUnknownError = 0xFFFF /*!< Undefined error. */
} EdlErrorCode_t;

#endif // EDL_ERRORCODES_H

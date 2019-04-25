# conversions of values from edl_errorcodes.h
EDL_PY_CONNECTION_ERRORS_OFFSET = 0x0100
EDL_PY_COMMANDS_CONFIGURATION_ERRORS_OFFSET = 0x0200
EDL_PY_CONFIG_ERRORS_OFFSET = 0x1000

EdlPySuccess = 0x0000
EdlPyNoDevicesError = 0x0001
EdlPyDeviceNotConnectedError = 0x002
EdlPyDeviceExpiredError = 0x0003
EdlPyWriteToFtdiError = 0x0004

EdlPyDeviceConnectionError = EDL_PY_CONNECTION_ERRORS_OFFSET+0x0001
EdlPyDeviceAlreadyConnectedError = EDL_PY_CONNECTION_ERRORS_OFFSET+0x0002
EdlPyDeviceConnectionLatencyError = EDL_PY_CONNECTION_ERRORS_OFFSET+0x0003
EdlPyDeviceConnectionSetUSBError = EDL_PY_CONNECTION_ERRORS_OFFSET+0x0004
EdlPyDeviceConnectionTransferSizeError = EDL_PY_CONNECTION_ERRORS_OFFSET+0x0005
EdlPyDeviceConnectionPurgeError = EDL_PY_CONNECTION_ERRORS_OFFSET+0x0006
EdlPyDeviceConnectionFirstWriteError = EDL_PY_CONNECTION_ERRORS_OFFSET+0x0007
EdlPyDeviceDisconnectionError = EDL_PY_CONNECTION_ERRORS_OFFSET+0x0008

EdlPyCommandIdOutOfRangeError = EDL_PY_COMMANDS_CONFIGURATION_ERRORS_OFFSET+0x0001
EdlPyTrialValueSendNotDisabledError = EDL_PY_COMMANDS_CONFIGURATION_ERRORS_OFFSET+0x0002
EdlPyPushButtonSendDisabledError = EDL_PY_COMMANDS_CONFIGURATION_ERRORS_OFFSET+0x0003
EdlPyViolatedTrialRuleError = EDL_PY_COMMANDS_CONFIGURATION_ERRORS_OFFSET+0x0004
EdlPyNotEnoughAvailableDataError = EDL_PY_COMMANDS_CONFIGURATION_ERRORS_OFFSET+0x0005

EdlPyWrongValueBitsNumSumError = EDL_PY_CONFIG_ERRORS_OFFSET+0x0001
EdlPyWrongSignBitsNumError = EDL_PY_CONFIG_ERRORS_OFFSET+0x0002

EdlPyUnknownError = 0xFFFF

# conversions of values from edl_devicespecs.h
EDL_PY_CHANNEL_NUM = 5

EdlPyCommandRange = 0 # Radio type command
EdlPyCommandSamplingRate = 1 # Radio type command
EdlPyCommandFinalBandwidth = 2 # Radio type command
EdlPyCommandZAPAllChannels = 3 # PushButton type command
EdlPyCommandCompensateAllChannels = 4 # CheckButton type command
EdlPyCommandResetOffsetCompensation = 5 # PushButton type command
EdlPyCommandReset = 6 # Checkbox type command
EdlPyCommandPulseAmplitude = 7 # Value type command
EdlPyCommandPulseDuration = 8 # Value type command
EdlPyCommandPulse = 9 # PushButton type command
EdlPyCommandVoffsetCH1 = 10 # Value type command
EdlPyCommandVoffsetCH2 = 11 # Value type command
EdlPyCommandVoffsetCH3 = 12 # Value type command
EdlPyCommandVoffsetCH4 = 13 # Value type command
EdlPyCommandApplyProtocol = 14 # PushButton type command
EdlPyCommandMainTrial = 15 # Value type command
EdlPyCommandVhold = 16 # Value type command
EdlPyCommandVpulse = 17 # Value type command
EdlPyCommandVstep = 18 # Value type command
EdlPyCommandVmax = 19 # Value type command
EdlPyCommandVmin = 20 # Value type command
EdlPyCommandThold = 21 # Value type command
EdlPyCommandTpulse = 22 # Value type command
EdlPyCommandTstep = 23 # Value type command
EdlPyCommandN = 24 # Value type command
EdlPyCommandNR = 25 # Value type command
EdlPyCommandSlope = 26 # Value type command
EdlPyCommandVamp = 27 # Value type command
EdlPyCommandTPeriod = 28 # Value type command

EDL_PY_RADIO_RANGE_200_PA = 0
EDL_PY_RADIO_RANGE_2_NA = 1
EDL_PY_RADIO_RANGE_20_NA = 2
EDL_PY_RADIO_RANGE_200_NA = 3

EDL_PY_RADIO_SAMPLING_RATE_1_25_KHZ = 0
EDL_PY_RADIO_SAMPLING_RATE_5_KHZ = 1
EDL_PY_RADIO_SAMPLING_RATE_10_KHZ = 2
EDL_PY_RADIO_SAMPLING_RATE_20_KHZ = 3
EDL_PY_RADIO_SAMPLING_RATE_50_KHZ = 4
EDL_PY_RADIO_SAMPLING_RATE_100_KHZ = 5
EDL_PY_RADIO_SAMPLING_RATE_200_KHZ = 6

EDL_PY_RADIO_FINAL_BANDWIDTH_SR_2 = 0
EDL_PY_RADIO_FINAL_BANDWIDTH_SR_8 = 1
EDL_PY_RADIO_FINAL_BANDWIDTH_SR_10 = 2
EDL_PY_RADIO_FINAL_BANDWIDTH_SR_20 = 3

EDL_PY_CHECKBOX_CHECKED = True
EDL_PY_CHECKBOX_UNCHECKED = False

EDL_PY_BUTTON_PRESSED = True
EDL_PY_BUTTON_RELEASED = False
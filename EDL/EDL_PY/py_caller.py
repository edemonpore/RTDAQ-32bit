# edl python wrapper imports
import edl_py
import edl_py_constants as epc

# python imports
import numpy as np
import sys
import time
import matplotlib.pyplot as plt

MINIMUM_DATA_PACKETS_TO_READ = 10

currentData = []
voltageData = []

# Configure sampling rate, current range and bandwidth.
def configureWorkingModality(edl):
#	Declare an #EdlCommandStruct_t to be used as configuration for the commands.
	commandStruct = edl_py.EdlCommandStruct_t()

#	Set the sampling rate to 5kHz. Stack the command (do not apply).
	commandStruct.radioId = epc.EDL_PY_RADIO_SAMPLING_RATE_5_KHZ
	edl.setCommand(epc.EdlPyCommandSamplingRate, commandStruct, False)

#	Set the current range to 200pA. Stack the command (do not apply).
	commandStruct.radioId = epc.EDL_PY_RADIO_RANGE_200_PA
	edl.setCommand(epc.EdlPyCommandRange, commandStruct, False)

#	Disable current filters (final bandwidth equal to half sampling rate). Apply all of the stacked commands.
	commandStruct.radioId = epc.EDL_PY_RADIO_FINAL_BANDWIDTH_SR_2
	edl.setCommand(epc.EdlPyCommandFinalBandwidth, commandStruct, True)

# Compensate digital offset due to electrical load.
def compensateDigitalOffset(edl):
#	Declare an #EdlCommandStruct_t to be used as configuration for the commands.
	commandStruct = edl_py.EdlCommandStruct_t()

#	Select the constant protocol: protocol 0.
	commandStruct.value = 0.0
	edl.setCommand(epc.EdlPyCommandMainTrial, commandStruct, False)

#	Set the vHold to 0mV.
	commandStruct.value = 0.0
	edl.setCommand(epc.EdlPyCommandVhold, commandStruct, False)

#	Apply the protocol.
	edl.setCommand(epc.EdlPyCommandApplyProtocol, commandStruct, True)
	
#	Start the digital compensation.
	commandStruct.checkboxChecked = epc.EDL_PY_CHECKBOX_CHECKED
	edl.setCommand(epc.EdlPyCommandOffsetCompensation, commandStruct, True)

#	Wait for some seconds.
	time.sleep(5.0)
	
#	Stop the digital compensation.
	commandStruct.checkboxChecked = epc.EDL_PY_CHECKBOX_UNCHECKED
	edl.setCommand(epc.EdlPyCommandOffsetCompensation, commandStruct, True)

# Set the parameters and start a seal test protocol.
def setSealTestProtocol(edl):
#   Declare an #EdlCommandStruct_t to be used as configuration for the commands.
	commandStruct = edl_py.EdlCommandStruct_t()

#   Select the seal test protocol: protocol 1.
	commandStruct.value = 2.0
	edl.setCommand(epc.EdlPyCommandMainTrial, commandStruct, False)

#   Set the vHold to 0mV.
	commandStruct.value = 0.0
	edl.setCommand(epc.EdlPyCommandVhold, commandStruct, False)

#   Set the pulse amplitude to 50mV: 100mV positive to negative delta voltage.
	commandStruct.value = 50.0
	edl.setCommand(epc.EdlPyCommandVstep, commandStruct, False)

#   Set the pulse period to 20ms.
	commandStruct.value = 20.0;
	edl.setCommand(epc.EdlPyCommandTpu, commandStruct, False)

#   Set the command period to 50ms.
	commandStruct.value = 50.0;
	edl.setCommand(epc.EdlPyCommandTpe, commandStruct, False)

#   Apply the protocol.
	edl.setCommand(epc.EdlPyCommandApplyProtocol, commandStruct, True)

# Reads data from the EDL device and writes them on an open file.
def readAndSaveSomeData(edl):
#	Declare an #EdlDeviceStatus_t variable to collect the device status.
	status = edl_py.EdlDeviceStatus_t()

#	Declare a variable to collect the number of read data packets.
	readPacketsNum = [0]
	
	time.sleep(0.5)

#	Get rid of data acquired during the device configuration.
	print("purge old data")
	res = edl.purgeData();
	
#	If the EDL::purgeData returns an error code output an error and return.
	if res != epc.EdlPySuccess:
		print("failed to purge data")
		return res

#	Start collecting data.
	print("collecting data... ", end="")
	sys.stdout.flush()
	
	c = 0
	while c < 1000:
		c = c+1
		
#		Get current status to know the number of available data packets EdlDeviceStatus_t::availableDataPackets.
		res = edl.getDeviceStatus(status)
			
#	    If the EDL::getDeviceStatus returns an error code output an error and return.
		if res != epc.EdlPySuccess:
			print("failed to get device status")
			return res;
		
		if status.bufferOverflowFlag:
			print("\nlost some data due to buffer overflow; increase MINIMUM_DATA_PACKETS_TO_READ to improve performance")
	
		if status.lostDataFlag:
			print("\nlost some data from the device; decrease sampling frequency or close unused applications to improve performance")
			print("data loss may also occur immediately after sending a command to the device")
	
		if status.availableDataPackets >= MINIMUM_DATA_PACKETS_TO_READ:
#			Declare a vector to collect the read data packets.
			data = [0.0]*0

#			If at least MINIMUM_DATA_PACKETS_TO_READ data packet are available read them.
			res = edl.readData(status.availableDataPackets, readPacketsNum, data)
	
#		    If the device is not connected output an error, close the file for data storage and return.
			if res == epc.EdlPyDeviceNotConnectedError:
				print("the device is not connected")
				return res
				
			else:
#		        If the number of available data packets is lower than the number of required packets output an error, but the read is performed nonetheless
#				with the available data.
				if res == epc.EdlPyNotEnoughAvailableDataError:
					print("not enough available data, only " + readPacketsNum[0] + " packets have been read")
	
#		        The output vector consists of \a readPacketsNum data packets of #EDL_CHANNEL_NUM floating point data each.
#				The first item in each data packet is the value voltage channel [mV];
#				the following items are the values of the current channels either in pA or nA, depending on value assigned to #EdlCommandSamplingRate. */
				voltageData.extend(data[1::2])
				currentData.extend(data[::2])
	
		else:
#			If the read was not performed wait 1 ms before trying to read again.
			time.sleep(0.001)

	print("done");
	
	return res;

# main
# Initialize an #EDL object.
edl = edl_py.EDL_PY();

# Initialize a vector of strings to collect the detected devices.
devices = [""]*0

# Detect plugged in devices.
res = edl.detectDevices(devices);

# If none is found output an error and return.
if res != epc.EdlPySuccess:
    sys.exit("could not detect devices")
else:
	print("first device found " + devices[0])

# If at list one device is found connect to the first one.
res = edl.connectDevice(devices[0])

print("connecting... ", end="")

# If the EDL::connectDevice returns an error code output an error and return.
if res != epc.EdlPySuccess:
    sys.exit("connection error")
else:
	print("done")

# Configure the device working modality.
print("configuring working modality")

configureWorkingModality(edl)
	
# Compensate for digital offset.
print("performing digital offset compensation... ", end="")
sys.stdout.flush()

compensateDigitalOffset(edl)

print("done")

# Apply a seal test protocol.
print("applying seal test protocol")

setSealTestProtocol(edl)

res = readAndSaveSomeData(edl)
if res != epc.EdlPySuccess:
    sys.exit("failed to read data")

timeData = []
dt = 256.0/1.25e6 # Real sampling rate is slightly lower than 5000kHz, the correct formula is 1.25MHz /256
for i in range(0, len(voltageData)):
	timeData.append(i*dt)

plt.subplot(212)
plt.plot(timeData, voltageData)
plt.subplot(211)
plt.plot(timeData, currentData)
plt.show()

# Try to disconnect the device.
# Note: Data reading is performed in a separate thread started by EDL::connectDevice.
#       The while loop may be useful in case few operations are performed between before calling EDL::disconnectDevice,
#       to ensure that the connection is fully established before trying to disconnect. */
print("disconnecting... ", end="")
sys.stdout.flush()

c = 0
while c < 1000:
	c = c+1
	res = edl.disconnectDevice()
	if res == epc.EdlPySuccess:
		print("done")
		break
#	If the disconnection was unsuccessful wait 1 ms before trying to disconnect again.
	time.sleep(0.001)

# If the EDL::disconnectDevice returns an error code after trying for 1 second (1e3 * 1ms) output an error and return.
if res != epc.EdlPySuccess:
    sys.exit("disconnection error")

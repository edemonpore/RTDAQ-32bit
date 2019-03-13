/*! \file edl_devicespecs.h
 * \brief Auto-generated header file with definitions of command types and arguments
 * for a specific device type.
 */
#ifndef EDL_DEVICESPECS_H
#define EDL_DEVICESPECS_H

/*! \def EDL_CHANNEL_NUM
 * \brief Number of channels.
 * Usually there are #EDL_CHANNEL_NUM - 1 current channels and 1 voltage channel.
 */
#define EDL_CHANNEL_NUM 2

/*! \enum EdlCommandId_t
 * \brief Command IDs.
 * The first argument to EDL::setCommand should be selected from this list with the exception of #EdlCommandIdNum.
 */
typedef enum {
    EdlCommandRange = 0, /*!< Radio type command. */
    EdlCommandSamplingRate = 1, /*!< Radio type command. */
    EdlCommandFinalBandwidth = 2, /*!< Radio type command. */
    EdlCommandOffsetCompensation = 3, /*!< Checkbox type command. */
    EdlCommandReset = 4, /*!< Checkbox type command. */
    EdlCommandZAP = 5, /*!< PushButton type command. */
    EdlCommandApplyProtocol = 6, /*!< PushButton type command. */
    EdlCommandMainTrial = 7, /*!< Value type command. */
    EdlCommandVhold = 8, /*!< Value type command. */
    EdlCommandVfp = 9, /*!< Value type command. */
    EdlCommandVstep = 10, /*!< Value type command. */
    EdlCommandTstep = 11, /*!< Value type command. */
    EdlCommandTpu = 12, /*!< Value type command. */
    EdlCommandTpe = 13, /*!< Value type command. */
    EdlCommandN = 14, /*!< Value type command. */
    EdlCommandNe = 15, /*!< Value type command. */
    EdlCommandVmax = 16, /*!< Value type command. */
    EdlCommandVmin = 17, /*!< Value type command. */
    EdlCommandSlope = 18, /*!< Value type command. */
    EdlCommandIdNum /*!< Number of available command IDs. \note This is not a valid command ID. */
} EdlCommandId_t;

/*! Value for EdlCommandStruct_t::radioId field using #EdlCommandRange command */
#define EDL_RADIO_RANGE_200_PA 0

/*! Value for EdlCommandStruct_t::radioId field using #EdlCommandRange command */
#define EDL_RADIO_RANGE_20_NA 1


/*! Value for EdlCommandStruct_t::radioId field using #EdlCommandSamplingRate command */
#define EDL_RADIO_SAMPLING_RATE_1_25_KHZ 0

/*! Value for EdlCommandStruct_t::radioId field using #EdlCommandSamplingRate command */
#define EDL_RADIO_SAMPLING_RATE_5_KHZ 1

/*! Value for EdlCommandStruct_t::radioId field using #EdlCommandSamplingRate command */
#define EDL_RADIO_SAMPLING_RATE_10_KHZ 2

/*! Value for EdlCommandStruct_t::radioId field using #EdlCommandSamplingRate command */
#define EDL_RADIO_SAMPLING_RATE_20_KHZ 3

/*! Value for EdlCommandStruct_t::radioId field using #EdlCommandSamplingRate command */
#define EDL_RADIO_SAMPLING_RATE_50_KHZ 4

/*! Value for EdlCommandStruct_t::radioId field using #EdlCommandSamplingRate command */
#define EDL_RADIO_SAMPLING_RATE_100_KHZ 5

/*! Value for EdlCommandStruct_t::radioId field using #EdlCommandSamplingRate command */
#define EDL_RADIO_SAMPLING_RATE_200_KHZ 6


/*! Value for EdlCommandStruct_t::radioId field using #EdlCommandFinalBandwidth command */
#define EDL_RADIO_FINAL_BANDWIDTH_SR_2 0

/*! Value for EdlCommandStruct_t::radioId field using #EdlCommandFinalBandwidth command */
#define EDL_RADIO_FINAL_BANDWIDTH_SR_8 1

/*! Value for EdlCommandStruct_t::radioId field using #EdlCommandFinalBandwidth command */
#define EDL_RADIO_FINAL_BANDWIDTH_SR_10 2

/*! Value for EdlCommandStruct_t::radioId field using #EdlCommandFinalBandwidth command */
#define EDL_RADIO_FINAL_BANDWIDTH_SR_20 3


/*! Value for EdlCommandStruct_t::checkboxChecked field when using Checkbox command types */
#define EDL_CHECKBOX_CHECKED true

/*! Value for EdlCommandStruct_t::checkboxChecked field when using Checkbox command types */
#define EDL_CHECKBOX_UNCHECKED false


/*! Value for EdlCommandStruct_t::buttonPressed field when using CheckButton command types */
#define EDL_BUTTON_PRESSED true

/*! Value for EdlCommandStruct_t::buttonPressed field when using CheckButton command types */
#define EDL_BUTTON_RELEASED false

#endif // EDL_DEVICESPECS_H

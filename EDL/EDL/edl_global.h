/*! \file edl_global.h
 * \brief Defines some utility global macros.
 */
#ifndef EDL_GLOBAL_H
#define EDL_GLOBAL_H

/*! \def EDLSHARED_EXPORT
 * \brief Macro used to export classes shared by the dll.
 * \note Defining macro \a EDL_LIBRARY will prevent project building.
 */

#if defined(EDL_LIBRARY)
#  define EDLSHARED_EXPORT __declspec(dllexport)
#else
#  define EDLSHARED_EXPORT __declspec(dllimport)
#endif

/*! \def EDL_IN
 * \brief Dummy macro to identify input arguments.
 */
#define EDL_IN

/*! \def EDL_OUT
 * \brief Dummy macro to identify output arguments.
 */
#define EDL_OUT

/*! \def EDL_VOID
 * \brief Dummy macro to identify void arguments.
 */
#define EDL_VOID void

#endif // EDL_GLOBAL_H

#pragma once

#ifdef EMTRACKER_EXPORTS
#define EMTRACKER_API __declspec(dllexport)
#else
#define EMTRACKER_API __declspec(dllimport)
#endif

#include <windows.h>
#include "ATC3DG.h"		// ATC3DG API
#include <stdio.h>		// printf
#include <string>		// string handling
#include <stdlib.h>		// exit() function
#include <stdint.h>

extern "C" EMTRACKER_API int SetUpTracker(int32_t sensorIdx, int32_t msgType, double sensorOffsetX, double sensorOffsetY, double sensorOffsetZ, double angleAz, double angleEl, double angleRoll, double rate);
extern "C" EMTRACKER_API int GetSampleMatrix(int32_t sensorID, double sample[12]);
extern "C" EMTRACKER_API int GetSampleQuater(int32_t sensorID, double sample[7]);
extern "C" EMTRACKER_API int GetSampleEuler(int32_t sensorID, double sample[6]);
extern "C" EMTRACKER_API int ShutDownTracker();
extern "C" EMTRACKER_API void ErrorCodeToString(int32_t error);
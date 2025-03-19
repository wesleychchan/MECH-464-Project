#include "pch.h"
#include "EMTracker.h"

int32_t SetUpTracker(int32_t sensorIdx, int32_t msgType, double sensorOffsetX, double sensorOffsetY, double sensorOffsetZ, double angleAz, double angleEl, double angleRoll, double rate) {
	printf("Initializing ATC3DG system...\n");
	
	SYSTEM_CONFIGURATION ATC3DG;
	SENSOR_CONFIGURATION pSensor;
	TRANSMITTER_CONFIGURATION pXmtr;
	
	// Initialize system
	int32_t errorCode = InitializeBIRDSystem();
	if (errorCode != BIRD_ERROR_SUCCESS) {
		printf("Failed to init BIRD system\n");
		return errorCode;
	}

	// Connect to device
	errorCode = GetBIRDSystemConfiguration(&ATC3DG);
	if (errorCode != BIRD_ERROR_SUCCESS) {
		printf("Failed to get BIRD configuration\n");
		return errorCode;
	}

	// Connect to sensor
	errorCode = GetSensorConfiguration(sensorIdx, &pSensor);
	if (errorCode != BIRD_ERROR_SUCCESS) { 
		printf("Failed to init sensor\n");
		return errorCode; 
	}
	printf(pSensor.attached ? "EM sensor is connected\n" : "EM sensor not connected\n");

	// Set units to millimeters
	BOOL metric = true;
	errorCode = SetSystemParameter(METRIC, &metric, sizeof(metric));
	if (errorCode != BIRD_ERROR_SUCCESS) {
		printf("Failed to set system to millimeters\n");
		return errorCode;
	}

	if (msgType == 0) {
		// Set sensor to send position and matrix
		int format = DOUBLE_POSITION_MATRIX;
		errorCode = SetSensorParameter(sensorIdx, DATA_FORMAT, &format, sizeof(format));
		if (errorCode != BIRD_ERROR_SUCCESS) {
			printf("Failed to set data type\n");
			return errorCode;
		}
	}
	else if (msgType == 2) {
		// Set sensor to send position and euler angles
		int format = DOUBLE_POSITION_ANGLES;
		errorCode = SetSensorParameter(sensorIdx, DATA_FORMAT, &format, sizeof(format));
		if (errorCode != BIRD_ERROR_SUCCESS) {
			printf("Failed to set data type\n");
			return errorCode;
		}
	}
	else if (msgType == 1) {
		// Set sensor to send position, quaternion
		int format = DOUBLE_POSITION_QUATERNION;
		errorCode = SetSensorParameter(sensorIdx, DATA_FORMAT, &format, sizeof(format));
		if (errorCode != BIRD_ERROR_SUCCESS) {
			printf("Failed to set data type\n");
			return errorCode;
		}
	}

	// Set SENSOR_OFFSET
	DOUBLE_POSITION_RECORD rec; 
	rec.x = sensorOffsetX;
	rec.y = sensorOffsetY;
	rec.z = sensorOffsetZ;
	errorCode = SetSensorParameter(sensorIdx, SENSOR_OFFSET, &rec, sizeof(rec));
	if (errorCode != BIRD_ERROR_SUCCESS) {
		printf("Failed to set sensor offset\n");
		return errorCode;
	}

	// Set angle offset
	DOUBLE_ANGLES_RECORD arec;
	arec.a = angleAz;
	arec.e = angleEl;
	arec.r = angleRoll;
	errorCode = SetSensorParameter(sensorIdx, ANGLE_ALIGN, &arec, sizeof(arec));
	if (errorCode != BIRD_ERROR_SUCCESS) {
		printf("Failed to set sensor angle offset\n");
		return errorCode;
	}

	// Set measurement rate
	if (rate < 20) {
		printf("Data rate must be > 20 Hz\n");
		return -1;
	}
	errorCode = SetSystemParameter(MEASUREMENT_RATE, &rate, sizeof(rate));
	if (errorCode != BIRD_ERROR_SUCCESS) {
		printf("Failed to set measurement rate\n");
		return errorCode;
	}

	// Look for the first transmitter
	for (short i = 0; i < ATC3DG.numberTransmitters; i++)
	{
		errorCode = GetTransmitterConfiguration(i, &pXmtr);
		if (errorCode != BIRD_ERROR_SUCCESS) return errorCode;
		if (pXmtr.attached) {
			errorCode = SetSystemParameter(SELECT_TRANSMITTER, &i, sizeof(i));
			if (errorCode != BIRD_ERROR_SUCCESS) {
				printf("Failed to set transmitter\n");
				return errorCode;
			}
			break;
		}
	}
}
int32_t GetSampleMatrix(int32_t sensorID, double sample[12]) {
	try {
		DOUBLE_POSITION_MATRIX_RECORD record, * pRecord = &record;

		// sensor attached so get record
		int32_t errorCode = GetAsynchronousRecord(sensorID, pRecord, sizeof(record));
		if (errorCode != BIRD_ERROR_SUCCESS) {
			printf("Failed to obtain synchronous record\n");
			return errorCode;
		}

		// get the status of the last data record
		// only report the data if everything is okay
		uint32_t status = GetSensorStatus(sensorID);

		if (status == VALID_STATUS)
		{
			sample[0] = record.x;
			sample[1] = record.y;
			sample[2] = record.z;
			sample[3] = record.s[0][0];
			sample[4] = record.s[0][1];
			sample[5] = record.s[0][2];
			sample[6] = record.s[1][0];
			sample[7] = record.s[1][1];
			sample[8] = record.s[1][2];
			sample[9] = record.s[2][0];
			sample[10] = record.s[2][1];
			sample[11] = record.s[2][2];
		}

		return status;
	}
	catch (std::exception e) {
		printf("Failed to obtain sample\n");
		return -1;
	}
}
int32_t GetSampleQuater(int32_t sensorID, double sample[7]) {
	try {
		DOUBLE_POSITION_QUATERNION_RECORD record, * pRecord = &record;

		// sensor attached so get record
		int32_t errorCode = GetAsynchronousRecord(sensorID, pRecord, sizeof(record));
		if (errorCode != BIRD_ERROR_SUCCESS) {
			printf("Failed to obtain synchronous record\n");
			return errorCode;
		}

		// get the status of the last data record
		// only report the data if everything is okay
		uint32_t status = GetSensorStatus(sensorID);

		if (status == VALID_STATUS)
		{
			sample[0] = record.x;
			sample[1] = record.y;
			sample[2] = record.z;
			sample[3] = record.q[0];
			sample[4] = record.q[1];
			sample[5] = record.q[2];
			sample[6] = record.q[3];
		}

		return status;
	}
	catch (std::exception e) {
		printf("Failed to obtain sample\n");
		return -1;
	}
}
int32_t GetSampleEuler(int32_t sensorID, double sample[6]) {
	try {
		DOUBLE_POSITION_ANGLES_RECORD record, * pRecord = &record;

		// sensor attached so get record
		int32_t errorCode = GetAsynchronousRecord(sensorID, pRecord, sizeof(record));
		if (errorCode != BIRD_ERROR_SUCCESS) {
			printf("Failed to obtain synchronous record\n");
			return errorCode;
		}

		// get the status of the last data record
		// only report the data if everything is okay
		uint32_t status = GetSensorStatus(sensorID);

		if (status == VALID_STATUS)
		{
			sample[0] = record.x;
			sample[1] = record.y;
			sample[2] = record.z;
			sample[3] = record.a;
			sample[4] = record.e;
			sample[5] = record.r;
		}

		return status;
	}
	catch (std::exception e) {
		printf("Failed to obtain sample\n");
		return -1;
	}
}

int32_t ShutDownTracker() {
	short id = -1;
	int32_t errorCode = SetSystemParameter(SELECT_TRANSMITTER, &id, sizeof(id));
	if (errorCode != BIRD_ERROR_SUCCESS) {
		printf("Failed to shut down properly\n");
		return errorCode;
	}
}

void ErrorCodeToString(int32_t error)
{
	char buffer[1024];
	char* pBuffer = &buffer[0];
	int	numberBytes;

	GetErrorText(error, pBuffer, sizeof(buffer), SIMPLE_MESSAGE);
	numberBytes = strlen(buffer);
	buffer[numberBytes] = '\n';		// append a newline to buffer
	printf("%s", buffer);
}
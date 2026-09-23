/* Auto-generated from protocol.yaml. Do not edit by hand. */
#pragma once

#include <stdint.h>

#define PROTOCOL_VERSION 1
#define PROTOCOL_HEADER_SIZE 2
#define PROTOCOL_STATUS_OK 0
#define PROTOCOL_STATUS_FRAME_TOO_SHORT -1
#define PROTOCOL_STATUS_UNEXPECTED_ID -2
#define PROTOCOL_STATUS_UNEXPECTED_LENGTH -3

#define PACKET_ID_IMU 0x01
#define IMU_PAYLOAD_SIZE 12
#define IMU_FRAME_SIZE 14

#define COMMAND_ID_OPEN_VALVE 0x10
#define OPEN_VALVE_PAYLOAD_SIZE 1
#define OPEN_VALVE_FRAME_SIZE 3

typedef struct {
    int16_t a_x;
    int16_t a_y;
    int16_t a_z;
    int16_t roll;
    int16_t pitch;
    int16_t yaw;
} IMU_Packet_t;

typedef struct {
    uint8_t valve_id;
} OPEN_VALVE_Command_t;

uint8_t encode_imu_packet(uint8_t *frame, const IMU_Packet_t *value);

int decode_open_valve_command(const uint8_t *frame, uint8_t frame_size, OPEN_VALVE_Command_t *out);

/* Auto-generated from protocol.yaml. Do not edit by hand. */
#include "protocol.h"
#include <stdio.h>

static void protocol_write_u16_le(uint8_t *out, uint16_t value) {
    out[0] = (uint8_t)(value & 0xFFu);
    out[1] = (uint8_t)((value >> 8) & 0xFFu);
}

static uint16_t protocol_read_u16_le(const uint8_t *in) {
    return (uint16_t)(((uint16_t)in[1] << 8) | (uint16_t)in[0]);
}

static void protocol_write_u32_le(uint8_t *out, uint32_t value) {
    out[0] = (uint8_t)(value & 0xFFu);
    out[1] = (uint8_t)((value >> 8) & 0xFFu);
    out[2] = (uint8_t)((value >> 16) & 0xFFu);
    out[3] = (uint8_t)((value >> 24) & 0xFFu);
}

static uint32_t protocol_read_u32_le(const uint8_t *in) {
    return ((uint32_t)in[3] << 24) | ((uint32_t)in[2] << 16) | ((uint32_t)in[1] << 8) | (uint32_t)in[0];
}

int decode_imu_packet(const uint8_t *frame, uint8_t frame_size, IMU_Packet_t *out) {
    if (frame_size < PROTOCOL_HEADER_SIZE) {
        return PROTOCOL_STATUS_FRAME_TOO_SHORT;
    }
    if (frame[0] != PACKET_ID_IMU) {
        return PROTOCOL_STATUS_UNEXPECTED_ID;
    }
    if (frame[1] != IMU_PAYLOAD_SIZE || frame_size != IMU_FRAME_SIZE) {
        return PROTOCOL_STATUS_UNEXPECTED_LENGTH;
    }
    out->a_x = (int16_t)protocol_read_u16_le(frame + PROTOCOL_HEADER_SIZE + 0);
    out->a_y = (int16_t)protocol_read_u16_le(frame + PROTOCOL_HEADER_SIZE + 2);
    out->a_z = (int16_t)protocol_read_u16_le(frame + PROTOCOL_HEADER_SIZE + 4);
    out->roll = (int16_t)protocol_read_u16_le(frame + PROTOCOL_HEADER_SIZE + 6);
    out->pitch = (int16_t)protocol_read_u16_le(frame + PROTOCOL_HEADER_SIZE + 8);
    out->yaw = (int16_t)protocol_read_u16_le(frame + PROTOCOL_HEADER_SIZE + 10);
    return PROTOCOL_STATUS_OK;
}

size_t imu_packet_to_json(const IMU_Packet_t *value, char *out, size_t out_size) {
    int written = snprintf(out, out_size, "{\"a_x\":%d,\"a_y\":%d,\"a_z\":%d,\"roll\":%d,\"pitch\":%d,\"yaw\":%d}", (int)value->a_x, (int)value->a_y, (int)value->a_z, (int)value->roll, (int)value->pitch, (int)value->yaw);
    if (written < 0) {
        return 0;
    }
    return (size_t)written;
}

uint8_t encode_open_valve_command(uint8_t *frame, const OPEN_VALVE_Command_t *value) {
    frame[0] = COMMAND_ID_OPEN_VALVE;
    frame[1] = OPEN_VALVE_PAYLOAD_SIZE;
    (frame + PROTOCOL_HEADER_SIZE + 0)[0] = value->valve_id;
    return OPEN_VALVE_FRAME_SIZE;
}

int protocol_handle_telemetry_frame(const uint8_t *frame, uint8_t frame_size) {
    if (frame_size < PROTOCOL_HEADER_SIZE) {
        return PROTOCOL_STATUS_FRAME_TOO_SHORT;
    }

    char json[PROTOCOL_JSON_BUFFER_SIZE];
    size_t json_len = 0;

    switch (frame[0]) {
        case PACKET_ID_IMU: {
            IMU_Packet_t value;
            int status = decode_imu_packet(frame, frame_size, &value);
            if (status != PROTOCOL_STATUS_OK) {
                return status;
            }
            json_len = imu_packet_to_json(&value, json, sizeof(json));
            break;
        }
        default:
            return PROTOCOL_STATUS_UNEXPECTED_ID;
    }

    protocol_serial_write((const uint8_t *)json, (uint16_t)json_len);
    return PROTOCOL_STATUS_OK;
}

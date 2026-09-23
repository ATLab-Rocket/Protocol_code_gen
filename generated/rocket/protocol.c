/* Auto-generated from protocol.yaml. Do not edit by hand. */
#include "protocol.h"

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

uint8_t encode_imu_packet(uint8_t *frame, const IMU_Packet_t *value) {
    frame[0] = PACKET_ID_IMU;
    frame[1] = IMU_PAYLOAD_SIZE;
    protocol_write_u16_le(frame + PROTOCOL_HEADER_SIZE + 0, (uint16_t)value->a_x);
    protocol_write_u16_le(frame + PROTOCOL_HEADER_SIZE + 2, (uint16_t)value->a_y);
    protocol_write_u16_le(frame + PROTOCOL_HEADER_SIZE + 4, (uint16_t)value->a_z);
    protocol_write_u16_le(frame + PROTOCOL_HEADER_SIZE + 6, (uint16_t)value->roll);
    protocol_write_u16_le(frame + PROTOCOL_HEADER_SIZE + 8, (uint16_t)value->pitch);
    protocol_write_u16_le(frame + PROTOCOL_HEADER_SIZE + 10, (uint16_t)value->yaw);
    return IMU_FRAME_SIZE;
}

int decode_open_valve_command(const uint8_t *frame, uint8_t frame_size, OPEN_VALVE_Command_t *out) {
    if (frame_size < PROTOCOL_HEADER_SIZE) {
        return PROTOCOL_STATUS_FRAME_TOO_SHORT;
    }
    if (frame[0] != COMMAND_ID_OPEN_VALVE) {
        return PROTOCOL_STATUS_UNEXPECTED_ID;
    }
    if (frame[1] != OPEN_VALVE_PAYLOAD_SIZE || frame_size != OPEN_VALVE_FRAME_SIZE) {
        return PROTOCOL_STATUS_UNEXPECTED_LENGTH;
    }
    out->valve_id = (frame + PROTOCOL_HEADER_SIZE + 0)[0];
    return PROTOCOL_STATUS_OK;
}

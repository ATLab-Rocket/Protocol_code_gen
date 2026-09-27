#include "../generated/rocket/protocol.h"
#include <stdio.h>

int main(void) {
    IMU_Packet_t value = {
        .a_x = 100,
        .a_y = 200,
        .a_z = -50,
        .roll = 10,
        .pitch = 20,
        .yaw = 30,
    };
    uint8_t frame[IMU_FRAME_SIZE] = {0};
    uint8_t size = encode_imu_packet(frame, &value);

    printf("Encoded IMU frame (%u bytes): ", (unsigned int)size);
    for (uint8_t index = 0; index < size; index++) {
        printf("%02X", (unsigned int)frame[index]);
    }
    printf("\n");
    return 0;
}
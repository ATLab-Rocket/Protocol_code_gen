#include "../generated/ground/protocol.h"
#include <ctype.h>
#include <stdio.h>

void protocol_serial_write(const uint8_t *data, uint16_t length) {
	fwrite(data, 1, length, stdout);
	putchar('\n');
}

static int hex_value(char character) {
	if (character >= '0' && character <= '9') {
		return character - '0';
	}
	if (character >= 'a' && character <= 'f') {
		return character - 'a' + 10;
	}
	if (character >= 'A' && character <= 'F') {
		return character - 'A' + 10;
	}
	return -1;
}

int main(void) {
	char input[256];
	uint8_t frame[IMU_FRAME_SIZE];
	size_t frame_size = 0;
	int high_nibble = -1;

	printf("Enter hex frame (example: 010C6400C800CEFF0A0014001E00): ");
	if (fgets(input, sizeof(input), stdin) == NULL) {
		fprintf(stderr, "Failed to read input\n");
		return 1;
	}

	for (size_t index = 0; input[index] != '\0'; index++) {
		if (isspace((unsigned char)input[index])) {
			continue;
		}

		int value = hex_value(input[index]);
		if (value < 0) {
			fprintf(stderr, "Input contains a non-hex character\n");
			return 1;
		}
		if (high_nibble < 0) {
			high_nibble = value;
			continue;
		}
		if (frame_size >= sizeof(frame)) {
			fprintf(stderr, "Frame exceeds maximum length\n");
			return 1;
		}

		frame[frame_size++] = (uint8_t)((high_nibble << 4) | value);
		high_nibble = -1;
	}

	if (frame_size == 0 || high_nibble >= 0) {
		fprintf(stderr, "Input must contain complete hexadecimal bytes\n");
		return 1;
	}

	int status = protocol_handle_telemetry_frame(frame, (uint8_t)frame_size);
	if (status != PROTOCOL_STATUS_OK) {
		fprintf(stderr, "Decode failed, protocol status: %d\n", status);
		return 2;
	}

	return 0;
}

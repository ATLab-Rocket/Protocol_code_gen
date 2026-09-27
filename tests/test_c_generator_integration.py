from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from generators.c_generator import (
    generate_c_header,
    generate_c_source,
    generate_ground_c_header,
    generate_ground_c_source,
)

GCC_AVAILABLE = shutil.which("gcc") is not None
pytestmark = pytest.mark.skipif(not GCC_AVAILABLE, reason="gcc not available on this machine")


ROCKET_ENCODE_MAIN = """
#include "protocol.h"
#include <stdio.h>

int main(void) {
    SensorData_Packet_t value;
    value.status = 7;
    value.altitude_cm = -1234;
    value.battery_mv = 3700;
    value.temperature_c = 21.5f;

    uint8_t frame[SENSORDATA_FRAME_SIZE];
    uint8_t size = encode_sensordata_packet(frame, &value);

    for (uint8_t i = 0; i < size; i++) {
        printf("%02x", frame[i]);
    }
    printf("\\n");
    return 0;
}
"""

GROUND_DECODE_MAIN = """
#include "protocol.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void protocol_serial_write(const uint8_t *data, uint16_t length) {
    fwrite(data, 1, length, stdout);
    printf("\\n");
}

int main(int argc, char **argv) {
    if (argc != 2) {
        return 1;
    }
    const char *hex = argv[1];
    size_t hex_len = strlen(hex);
    uint8_t frame[64];
    uint8_t frame_size = (uint8_t)(hex_len / 2);
    for (uint8_t i = 0; i < frame_size; i++) {
        char byte_str[3] = { hex[i * 2], hex[i * 2 + 1], '\\0' };
        frame[i] = (uint8_t)strtol(byte_str, NULL, 16);
    }
    int status = protocol_handle_telemetry_frame(frame, frame_size);
    return status == PROTOCOL_STATUS_OK ? 0 : 2;
}
"""

GROUND_ENCODE_COMMAND_MAIN = """
#include "protocol.h"
#include <stdio.h>

/* protocol.c also defines protocol_handle_telemetry_frame(), which references
 * this hook even though this particular program never calls it. */
void protocol_serial_write(const uint8_t *data, uint16_t length) {
    (void)data;
    (void)length;
}

int main(void) {
    SetState_Command_t value;
    value.target_state = 2;
    value.delay_ms = 500;

    uint8_t frame[SETSTATE_FRAME_SIZE];
    uint8_t size = encode_setstate_command(frame, &value);

    for (uint8_t i = 0; i < size; i++) {
        printf("%02x", frame[i]);
    }
    printf("\\n");
    return 0;
}
"""

ROCKET_DECODE_COMMAND_MAIN = """
#include "protocol.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        return 1;
    }
    const char *hex = argv[1];
    size_t hex_len = strlen(hex);
    uint8_t frame[64];
    uint8_t frame_size = (uint8_t)(hex_len / 2);
    for (uint8_t i = 0; i < frame_size; i++) {
        char byte_str[3] = { hex[i * 2], hex[i * 2 + 1], '\\0' };
        frame[i] = (uint8_t)strtol(byte_str, NULL, 16);
    }

    SetState_Command_t out;
    int status = decode_setstate_command(frame, frame_size, &out);
    if (status != PROTOCOL_STATUS_OK) {
        return 2;
    }
    printf("%u %u\\n", out.target_state, out.delay_ms);
    return 0;
}
"""


def _compile(tmp_path: Path, name: str, main_source: str, header_text: str, source_text: str) -> Path:
    work_dir = tmp_path / name
    work_dir.mkdir()
    (work_dir / "protocol.h").write_text(header_text, encoding="utf-8")
    (work_dir / "protocol.c").write_text(source_text, encoding="utf-8")
    (work_dir / "main.c").write_text(main_source, encoding="utf-8")

    binary = work_dir / name
    result = subprocess.run(
        ["gcc", "-std=c11", "-Wall", "-Wextra", "-I", str(work_dir),
         str(work_dir / "main.c"), str(work_dir / "protocol.c"), "-o", str(binary)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"compile failed for {name}:\n{result.stderr}"
    return binary


def test_telemetry_round_trip_rocket_encode_to_ground_json(tmp_path, sample_protocol):
    """Rocket encodes a telemetry packet -> ground decodes it and prints JSON -> values match."""
    rocket_binary = _compile(
        tmp_path, "rocket_encode", ROCKET_ENCODE_MAIN,
        generate_c_header(sample_protocol), generate_c_source(sample_protocol),
    )
    ground_binary = _compile(
        tmp_path, "ground_decode", GROUND_DECODE_MAIN,
        generate_ground_c_header(sample_protocol), generate_ground_c_source(sample_protocol),
    )

    frame_hex = subprocess.run([str(rocket_binary)], capture_output=True, text=True, check=True).stdout.strip()
    assert frame_hex  # rocket side actually produced a frame

    decode_result = subprocess.run([str(ground_binary), frame_hex], capture_output=True, text=True)
    assert decode_result.returncode == 0, decode_result.stderr

    payload = json.loads(decode_result.stdout.strip())
    assert payload["status"] == 7
    assert payload["altitude_cm"] == -1234
    assert payload["battery_mv"] == 3700
    assert payload["temperature_c"] == pytest.approx(21.5, abs=1e-4)


def test_command_round_trip_ground_encode_to_rocket_decode(tmp_path, sample_protocol):
    """Ground encodes a command -> rocket decodes it -> argument values match."""
    ground_binary = _compile(
        tmp_path, "ground_encode_cmd", GROUND_ENCODE_COMMAND_MAIN,
        generate_ground_c_header(sample_protocol), generate_ground_c_source(sample_protocol),
    )
    rocket_binary = _compile(
        tmp_path, "rocket_decode_cmd", ROCKET_DECODE_COMMAND_MAIN,
        generate_c_header(sample_protocol), generate_c_source(sample_protocol),
    )

    frame_hex = subprocess.run([str(ground_binary)], capture_output=True, text=True, check=True).stdout.strip()
    assert frame_hex

    decode_result = subprocess.run([str(rocket_binary), frame_hex], capture_output=True, text=True)
    assert decode_result.returncode == 0, decode_result.stderr

    target_state, delay_ms = decode_result.stdout.strip().split()
    assert int(target_state) == 2
    assert int(delay_ms) == 500


def test_ground_decode_rejects_wrong_packet_id(tmp_path, sample_protocol):
    """A frame with an unknown packet ID must be rejected, not silently decoded."""
    ground_binary = _compile(
        tmp_path, "ground_decode_bad_id", GROUND_DECODE_MAIN,
        generate_ground_c_header(sample_protocol), generate_ground_c_source(sample_protocol),
    )

    # Byte 0 is the packet ID; 0xFF does not match any known telemetry packet.
    bad_frame_hex = "ff0b0000000000000000000000"
    result = subprocess.run([str(ground_binary), bad_frame_hex], capture_output=True, text=True)
    assert result.returncode == 2

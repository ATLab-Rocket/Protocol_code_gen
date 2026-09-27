from __future__ import annotations

import pytest

from generators.c_generator import (
    _format_c_read_field,
    _format_c_write_field,
    _json_field_format,
    generate_c_header,
    generate_c_source,
    generate_ground_c_header,
    generate_ground_c_source,
)


# ---------------------------------------------------------------------------
# Rocket side (encode telemetry, decode commands)
# ---------------------------------------------------------------------------

def test_rocket_header_declares_encode_packet_and_decode_command_only(sample_protocol):
    header = generate_c_header(sample_protocol)

    assert "uint8_t encode_sensordata_packet(uint8_t *frame, const SensorData_Packet_t *value);" in header
    assert (
        "int decode_setstate_command(const uint8_t *frame, uint8_t frame_size, SetState_Command_t *out);"
        in header
    )

    # Rocket side must not expose the ground-side directions.
    assert "decode_sensordata_packet" not in header
    assert "encode_setstate_command" not in header


def test_rocket_header_defines_macros_and_structs(sample_protocol):
    header = generate_c_header(sample_protocol)

    assert "#define PACKET_ID_SENSORDATA 0x01" in header
    assert "#define SENSORDATA_PAYLOAD_SIZE 11" in header
    assert "#define SENSORDATA_FRAME_SIZE 13" in header
    assert "#define COMMAND_ID_SETSTATE 0x10" in header
    assert "float temperature_c;" in header
    assert "} SensorData_Packet_t;" in header
    assert "} SetState_Command_t;" in header


def test_rocket_source_has_encode_body_and_decode_validation(sample_protocol):
    source = generate_c_source(sample_protocol)

    assert "uint8_t encode_sensordata_packet(uint8_t *frame, const SensorData_Packet_t *value) {" in source
    assert "int decode_setstate_command(" in source
    assert "PROTOCOL_STATUS_FRAME_TOO_SHORT" in source
    assert "PROTOCOL_STATUS_UNEXPECTED_ID" in source
    assert "PROTOCOL_STATUS_UNEXPECTED_LENGTH" in source


# ---------------------------------------------------------------------------
# Ground station side (decode telemetry -> JSON, encode commands)
# ---------------------------------------------------------------------------

def test_ground_header_declares_decode_packet_json_and_encode_command_only(sample_protocol):
    header = generate_ground_c_header(sample_protocol)

    assert (
        "int decode_sensordata_packet(const uint8_t *frame, uint8_t frame_size, SensorData_Packet_t *out);"
        in header
    )
    assert (
        "size_t sensordata_packet_to_json(const SensorData_Packet_t *value, char *out, size_t out_size);"
        in header
    )
    assert "uint8_t encode_setstate_command(uint8_t *frame, const SetState_Command_t *value);" in header

    # Ground side must not expose the rocket-side directions.
    assert "encode_sensordata_packet" not in header
    assert "decode_setstate_command" not in header


def test_ground_header_declares_serial_hook_and_dispatcher(sample_protocol):
    header = generate_ground_c_header(sample_protocol)

    assert "extern void protocol_serial_write(const uint8_t *data, uint16_t length);" in header
    assert "int protocol_handle_telemetry_frame(const uint8_t *frame, uint8_t frame_size);" in header
    assert "#define PROTOCOL_JSON_BUFFER_SIZE 256" in header


def test_ground_source_json_uses_correct_format_per_type(sample_protocol):
    source = generate_ground_c_source(sample_protocol)

    assert '\\"status\\":%u' in source
    assert '\\"altitude_cm\\":%ld' in source
    assert '\\"battery_mv\\":%u' in source
    assert '\\"temperature_c\\":%.6f' in source
    assert "(long)value->altitude_cm" in source
    assert "(double)value->temperature_c" in source


def test_ground_source_dispatch_switches_on_packet_id(sample_protocol):
    source = generate_ground_c_source(sample_protocol)

    assert "switch (frame[0]) {" in source
    assert "case PACKET_ID_SENSORDATA: {" in source
    assert "decode_sensordata_packet(frame, frame_size, &value);" in source
    assert "sensordata_packet_to_json(&value, json, sizeof(json));" in source
    assert "protocol_serial_write((const uint8_t *)json, (uint16_t)json_len);" in source


# ---------------------------------------------------------------------------
# Shared type-system edges
# ---------------------------------------------------------------------------

def test_unsupported_data_type_raises_value_error():
    with pytest.raises(ValueError):
        _format_c_write_field("value->x", "double64", "frame")
    with pytest.raises(ValueError):
        _format_c_read_field("out->x", "double64", "frame")
    with pytest.raises(ValueError):
        _json_field_format("double64")


def test_empty_protocol_produces_no_dispatcher(sample_protocol):
    sample_protocol.telemetry = []
    sample_protocol.commands = []

    header = generate_ground_c_header(sample_protocol)
    source = generate_ground_c_source(sample_protocol)

    # No telemetry means no serial hook / dispatcher should be emitted at all.
    assert "protocol_serial_write" not in header
    assert "protocol_handle_telemetry_frame" not in source

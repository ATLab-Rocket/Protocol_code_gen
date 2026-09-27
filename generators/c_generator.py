from __future__ import annotations

from protocol.model import Protocol


# ---------------------------------------------------------------------------
# Shared building blocks (identical for both rocket-side and ground-side code)
# ---------------------------------------------------------------------------

def _format_macros_and_structs(protocol: Protocol) -> list[str]:
    lines = [
        f"#define PROTOCOL_VERSION {protocol.version}",
        "#define PROTOCOL_HEADER_SIZE 2",
        "#define PROTOCOL_STATUS_OK 0",
        "#define PROTOCOL_STATUS_FRAME_TOO_SHORT -1",
        "#define PROTOCOL_STATUS_UNEXPECTED_ID -2",
        "#define PROTOCOL_STATUS_UNEXPECTED_LENGTH -3",
        "",
    ]

    for packet in protocol.telemetry:
        lines.append(f"#define {_macro_name('PACKET_ID', packet.name)} 0x{packet.packet_id:02X}")
        lines.append(f"#define {_macro_name(packet.name, 'PAYLOAD_SIZE')} {packet.payload_size}")
        lines.append(f"#define {_macro_name(packet.name, 'FRAME_SIZE')} {packet.packet_size}")

    if protocol.telemetry:
        lines.append("")

    for command in protocol.commands:
        lines.append(f"#define {_macro_name('COMMAND_ID', command.name)} 0x{command.command_id:02X}")
        lines.append(f"#define {_macro_name(command.name, 'PAYLOAD_SIZE')} {command.payload_size}")
        lines.append(f"#define {_macro_name(command.name, 'FRAME_SIZE')} {command.packet_size}")

    if protocol.commands:
        lines.append("")

    for packet in protocol.telemetry:
        lines.extend(_format_struct(packet.name, packet.fields, "Packet"))
        lines.append("")

    for command in protocol.commands:
        lines.extend(_format_struct(command.name, command.arguments, "Command"))
        lines.append("")

    return lines


def _format_struct(name: str, fields, suffix: str) -> list[str]:
    lines = [
        "typedef struct {",
    ]
    for field in fields:
        lines.append(f"    {field.data_type.c_name} {field.name};")
    lines.append(f"}} {name}_{suffix}_t;")
    return lines


def _format_helpers() -> list[str]:
    return [
        "static void protocol_write_u16_le(uint8_t *out, uint16_t value) {",
        "    out[0] = (uint8_t)(value & 0xFFu);",
        "    out[1] = (uint8_t)((value >> 8) & 0xFFu);",
        "}",
        "",
        "static uint16_t protocol_read_u16_le(const uint8_t *in) {",
        "    return (uint16_t)(((uint16_t)in[1] << 8) | (uint16_t)in[0]);",
        "}",
        "",
        "static void protocol_write_u32_le(uint8_t *out, uint32_t value) {",
        "    out[0] = (uint8_t)(value & 0xFFu);",
        "    out[1] = (uint8_t)((value >> 8) & 0xFFu);",
        "    out[2] = (uint8_t)((value >> 16) & 0xFFu);",
        "    out[3] = (uint8_t)((value >> 24) & 0xFFu);",
        "}",
        "",
        "static uint32_t protocol_read_u32_le(const uint8_t *in) {",
        "    return ((uint32_t)in[3] << 24) | ((uint32_t)in[2] << 16) | ((uint32_t)in[1] << 8) | (uint32_t)in[0];",
        "}",
    ]


def _format_c_write_field(value_expression: str, data_type_name: str, output_expression: str) -> list[str]:
    if data_type_name == "uint8":
        return [f"    ({output_expression})[0] = {value_expression};"]
    if data_type_name in {"int16", "uint16"}:
        return [f"    protocol_write_u16_le({output_expression}, (uint16_t){value_expression});"]
    if data_type_name in {"int32", "uint32"}:
        return [f"    protocol_write_u32_le({output_expression}, (uint32_t){value_expression});"]
    if data_type_name == "float32":
        return [
            "    {",
            f"        union {{ float f; uint32_t u; }} converted = {{ .f = {value_expression} }};",
            f"        protocol_write_u32_le({output_expression}, converted.u);",
            "    }",
        ]
    raise ValueError(f"unsupported C write type: {data_type_name}")


def _format_c_read_field(target_expression: str, data_type_name: str, input_expression: str) -> list[str]:
    if data_type_name == "uint8":
        return [f"    {target_expression} = ({input_expression})[0];"]
    if data_type_name == "int16":
        return [f"    {target_expression} = (int16_t)protocol_read_u16_le({input_expression});"]
    if data_type_name == "uint16":
        return [f"    {target_expression} = protocol_read_u16_le({input_expression});"]
    if data_type_name == "int32":
        return [f"    {target_expression} = (int32_t)protocol_read_u32_le({input_expression});"]
    if data_type_name == "uint32":
        return [f"    {target_expression} = protocol_read_u32_le({input_expression});"]
    if data_type_name == "float32":
        return [
            "    {",
            f"        union {{ uint32_t u; float f; }} converted = {{ .u = protocol_read_u32_le({input_expression}) }};",
            f"        {target_expression} = converted.f;",
            "    }",
        ]
    raise ValueError(f"unsupported C read type: {data_type_name}")


def _macro_name(prefix: str, name: str) -> str:
    return f"{prefix}_{name}".upper()


def _function_name(name: str) -> str:
    return name.lower()


# ---------------------------------------------------------------------------
# Rocket / STM32 side (unchanged behavior): encode telemetry, decode commands
# ---------------------------------------------------------------------------

def generate_c_header(protocol: Protocol) -> str:
    lines = [
        "/* Auto-generated from protocol.yaml. Do not edit by hand. */",
        "#pragma once",
        "",
        "#include <stdint.h>",
        "",
    ]
    lines.extend(_format_macros_and_structs(protocol))

    for packet in protocol.telemetry:
        lines.append(f"uint8_t encode_{_function_name(packet.name)}_packet(uint8_t *frame, const {packet.name}_Packet_t *value);")

    if protocol.telemetry and protocol.commands:
        lines.append("")

    for command in protocol.commands:
        lines.append(
            (
                f"int decode_{_function_name(command.name)}_command("
                f"const uint8_t *frame, uint8_t frame_size, {command.name}_Command_t *out);"
            )
        )

    return "\n".join(lines).rstrip() + "\n"


def generate_c_source(protocol: Protocol) -> str:
    lines = [
        "/* Auto-generated from protocol.yaml. Do not edit by hand. */",
        '#include "protocol.h"',
        "",
    ]

    lines.extend(_format_helpers())
    lines.append("")

    for packet in protocol.telemetry:
        lines.extend(_format_encode_telemetry(packet))
        lines.append("")

    for command in protocol.commands:
        lines.extend(_format_decode_command(command))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _format_encode_telemetry(packet) -> list[str]:
    lines = [
        f"uint8_t encode_{_function_name(packet.name)}_packet(uint8_t *frame, const {packet.name}_Packet_t *value) {{",
        f"    frame[0] = {_macro_name('PACKET_ID', packet.name)};",
        f"    frame[1] = {_macro_name(packet.name, 'PAYLOAD_SIZE')};",
    ]

    for field in packet.fields:
        lines.extend(_format_c_write_field(f"value->{field.name}", field.data_type.name, f"frame + PROTOCOL_HEADER_SIZE + {field.offset}"))

    lines.append(f"    return {_macro_name(packet.name, 'FRAME_SIZE')};")
    lines.append("}")
    return lines


def _format_decode_command(command) -> list[str]:
    lines = [
        (
            f"int decode_{_function_name(command.name)}_command("
            f"const uint8_t *frame, uint8_t frame_size, {command.name}_Command_t *out) {{"
        ),
        "    if (frame_size < PROTOCOL_HEADER_SIZE) {",
        "        return PROTOCOL_STATUS_FRAME_TOO_SHORT;",
        "    }",
        f"    if (frame[0] != {_macro_name('COMMAND_ID', command.name)}) {{",
        "        return PROTOCOL_STATUS_UNEXPECTED_ID;",
        "    }",
        f"    if (frame[1] != {_macro_name(command.name, 'PAYLOAD_SIZE')} || frame_size != {_macro_name(command.name, 'FRAME_SIZE')}) {{",
        "        return PROTOCOL_STATUS_UNEXPECTED_LENGTH;",
        "    }",
    ]

    for argument in command.arguments:
        lines.extend(_format_c_read_field(f"out->{argument.name}", argument.data_type.name, f"frame + PROTOCOL_HEADER_SIZE + {argument.offset}"))

    lines.append("    return PROTOCOL_STATUS_OK;")
    lines.append("}")
    return lines


# ---------------------------------------------------------------------------
# Ground station side (new): decode telemetry -> JSON -> serial, encode commands
# ---------------------------------------------------------------------------

def generate_ground_c_header(protocol: Protocol) -> str:
    lines = [
        "/* Auto-generated from protocol.yaml. Do not edit by hand. */",
        "#pragma once",
        "",
        "#include <stdint.h>",
        "#include <stddef.h>",
        "",
        "#ifndef PROTOCOL_JSON_BUFFER_SIZE",
        "#define PROTOCOL_JSON_BUFFER_SIZE 256",
        "#endif",
        "",
    ]
    lines.extend(_format_macros_and_structs(protocol))

    for packet in protocol.telemetry:
        fname = _function_name(packet.name)
        lines.append(
            f"int decode_{fname}_packet(const uint8_t *frame, uint8_t frame_size, {packet.name}_Packet_t *out);"
        )
        lines.append(
            f"size_t {fname}_packet_to_json(const {packet.name}_Packet_t *value, char *out, size_t out_size);"
        )

    if protocol.telemetry and protocol.commands:
        lines.append("")

    for command in protocol.commands:
        lines.append(
            f"uint8_t encode_{_function_name(command.name)}_command(uint8_t *frame, const {command.name}_Command_t *value);"
        )

    if protocol.telemetry:
        lines.append("")
        lines.append("/* Implement this yourself for your platform's UART/USB/etc. Receives one JSON-encoded telemetry packet at a time. */")
        lines.append("extern void protocol_serial_write(const uint8_t *data, uint16_t length);")
        lines.append("")
        lines.append("/* Looks up the incoming frame by packet ID, decodes it, converts it to JSON, and sends it via protocol_serial_write(). */")
        lines.append("int protocol_handle_telemetry_frame(const uint8_t *frame, uint8_t frame_size);")

    return "\n".join(lines).rstrip() + "\n"


def generate_ground_c_source(protocol: Protocol) -> str:
    lines = [
        "/* Auto-generated from protocol.yaml. Do not edit by hand. */",
        '#include "protocol.h"',
        "#include <stdio.h>",
        "",
    ]

    lines.extend(_format_helpers())
    lines.append("")

    for packet in protocol.telemetry:
        lines.extend(_format_decode_telemetry(packet))
        lines.append("")
        lines.extend(_format_json_telemetry(packet))
        lines.append("")

    for command in protocol.commands:
        lines.extend(_format_encode_command(command))
        lines.append("")

    if protocol.telemetry:
        lines.extend(_format_dispatch(protocol.telemetry))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _format_decode_telemetry(packet) -> list[str]:
    lines = [
        (
            f"int decode_{_function_name(packet.name)}_packet("
            f"const uint8_t *frame, uint8_t frame_size, {packet.name}_Packet_t *out) {{"
        ),
        "    if (frame_size < PROTOCOL_HEADER_SIZE) {",
        "        return PROTOCOL_STATUS_FRAME_TOO_SHORT;",
        "    }",
        f"    if (frame[0] != {_macro_name('PACKET_ID', packet.name)}) {{",
        "        return PROTOCOL_STATUS_UNEXPECTED_ID;",
        "    }",
        f"    if (frame[1] != {_macro_name(packet.name, 'PAYLOAD_SIZE')} || frame_size != {_macro_name(packet.name, 'FRAME_SIZE')}) {{",
        "        return PROTOCOL_STATUS_UNEXPECTED_LENGTH;",
        "    }",
    ]

    for field in packet.fields:
        lines.extend(_format_c_read_field(f"out->{field.name}", field.data_type.name, f"frame + PROTOCOL_HEADER_SIZE + {field.offset}"))

    lines.append("    return PROTOCOL_STATUS_OK;")
    lines.append("}")
    return lines


def _format_encode_command(command) -> list[str]:
    lines = [
        f"uint8_t encode_{_function_name(command.name)}_command(uint8_t *frame, const {command.name}_Command_t *value) {{",
        f"    frame[0] = {_macro_name('COMMAND_ID', command.name)};",
        f"    frame[1] = {_macro_name(command.name, 'PAYLOAD_SIZE')};",
    ]

    for argument in command.arguments:
        lines.extend(_format_c_write_field(f"value->{argument.name}", argument.data_type.name, f"frame + PROTOCOL_HEADER_SIZE + {argument.offset}"))

    lines.append(f"    return {_macro_name(command.name, 'FRAME_SIZE')};")
    lines.append("}")
    return lines


def _json_field_format(data_type_name: str) -> tuple[str, str]:
    """Returns (printf format spec, cast expression prefix) for a field's JSON representation."""
    if data_type_name in {"uint8", "uint16"}:
        return "%u", "(unsigned int)"
    if data_type_name == "int16":
        return "%d", "(int)"
    if data_type_name == "uint32":
        return "%lu", "(unsigned long)"
    if data_type_name == "int32":
        return "%ld", "(long)"
    if data_type_name == "float32":
        return "%.6f", "(double)"
    raise ValueError(f"unsupported JSON type: {data_type_name}")


def _format_json_telemetry(packet) -> list[str]:
    parts = []
    args = []
    for field in packet.fields:
        fmt, cast = _json_field_format(field.data_type.name)
        parts.append(f'\\"{field.name}\\":{fmt}')
        args.append(f"{cast}value->{field.name}")

    format_string = "{" + ",".join(parts) + "}"
    call_args = ", ".join(args)
    snprintf_call = f'    int written = snprintf(out, out_size, "{format_string}"'
    snprintf_call += f", {call_args});" if call_args else ");"

    lines = [
        f"size_t {_function_name(packet.name)}_packet_to_json(const {packet.name}_Packet_t *value, char *out, size_t out_size) {{",
        snprintf_call,
        "    if (written < 0) {",
        "        return 0;",
        "    }",
        "    return (size_t)written;",
        "}",
    ]
    return lines


def _format_dispatch(telemetry_packets) -> list[str]:
    lines = [
        "int protocol_handle_telemetry_frame(const uint8_t *frame, uint8_t frame_size) {",
        "    if (frame_size < PROTOCOL_HEADER_SIZE) {",
        "        return PROTOCOL_STATUS_FRAME_TOO_SHORT;",
        "    }",
        "",
        "    char json[PROTOCOL_JSON_BUFFER_SIZE];",
        "    size_t json_len = 0;",
        "",
        "    switch (frame[0]) {",
    ]

    for packet in telemetry_packets:
        fname = _function_name(packet.name)
        lines.extend([
            f"        case {_macro_name('PACKET_ID', packet.name)}: {{",
            f"            {packet.name}_Packet_t value;",
            f"            int status = decode_{fname}_packet(frame, frame_size, &value);",
            "            if (status != PROTOCOL_STATUS_OK) {",
            "                return status;",
            "            }",
            f"            json_len = {fname}_packet_to_json(&value, json, sizeof(json));",
            "            break;",
            "        }",
        ])

    lines.extend([
        "        default:",
        "            return PROTOCOL_STATUS_UNEXPECTED_ID;",
        "    }",
        "",
        "    protocol_serial_write((const uint8_t *)json, (uint16_t)json_len);",
        "    return PROTOCOL_STATUS_OK;",
        "}",
    ])
    return lines
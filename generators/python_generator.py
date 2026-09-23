from __future__ import annotations

from protocol.model import Protocol


def generate_python_module(protocol: Protocol) -> str:
    lines = [
        '"""Auto-generated from protocol.yaml. Do not edit by hand."""',
        "from __future__ import annotations",
        "",
        "import struct",
        "from dataclasses import dataclass",
        "from typing import Any",
        "",
        f"PROTOCOL_VERSION = {protocol.version}",
        f"ENDIAN = {protocol.endian!r}",
        "HEADER_SIZE = 2",
        "",
    ]

    for packet in protocol.telemetry:
        lines.append(f"{_constant_name('PACKET_ID', packet.name)} = 0x{packet.packet_id:02X}")

    if protocol.telemetry:
        lines.append("")

    for command in protocol.commands:
        lines.append(f"{_constant_name('COMMAND_ID', command.name)} = 0x{command.command_id:02X}")

    if protocol.commands:
        lines.append("")

    for packet in protocol.telemetry:
        lines.extend(_format_dataclass(packet.name, packet.fields, "Packet"))
        lines.append("")
        lines.append(f"{_constant_name(packet.name, 'PAYLOAD_FORMAT')} = {_payload_format(protocol, packet.fields)!r}")
        lines.append(f"{_constant_name(packet.name, 'PAYLOAD_SIZE')} = {packet.payload_size}")
        lines.append("")
        lines.extend(_format_decode_function(packet.name, packet.fields, "packet", f"{_constant_name('PACKET_ID', packet.name)}"))
        lines.append("")

    for command in protocol.commands:
        lines.extend(_format_dataclass(command.name, command.arguments, "Command"))
        lines.append("")
        lines.append(f"{_constant_name(command.name, 'PAYLOAD_FORMAT')} = {_payload_format(protocol, command.arguments)!r}")
        lines.append(f"{_constant_name(command.name, 'PAYLOAD_SIZE')} = {command.payload_size}")
        lines.append("")
        lines.extend(
            _format_encode_function(command.name, command.arguments, "command", f"{_constant_name('COMMAND_ID', command.name)}")
        )
        lines.append("")

    lines.extend(_format_dispatch_function("decode_telemetry", protocol.telemetry, "packet", "PACKET_ID"))
    lines.append("")
    lines.extend(_format_validate_frame_function())

    return "\n".join(lines).rstrip() + "\n"


def _format_dataclass(name: str, fields, suffix: str) -> list[str]:
    class_name = _class_name(name, suffix)
    lines = [
        "@dataclass(frozen=True)",
        f"class {class_name}:",
    ]

    if not fields:
        lines.append("    pass")
        return lines

    for field in fields:
        lines.append(f"    {field.name}: {_python_type(field.data_type.name)}")
    return lines


def _payload_format(protocol: Protocol, fields) -> str:
    endian_prefix = "<" if protocol.endian == "little" else ">"
    return endian_prefix + "".join(field.data_type.python_struct_format for field in fields)


def _format_encode_function(name: str, fields, suffix: str, id_constant: str) -> list[str]:
    class_name = _class_name(name, suffix.capitalize())
    function_name = f"encode_{_function_name(name)}_{suffix}"
    format_constant = _constant_name(name, "PAYLOAD_FORMAT")
    value_list = ", ".join(f"value.{field.name}" for field in fields)
    pack_args = f"{format_constant}, {value_list}" if value_list else format_constant
    return [
        f"def {function_name}(value: {class_name}) -> bytes:",
        f"    payload = struct.pack({pack_args})",
        f"    return bytes(({id_constant}, len(payload))) + payload",
    ]


def _format_decode_function(name: str, fields, suffix: str, id_constant: str) -> list[str]:
    class_name = _class_name(name, suffix.capitalize())
    function_name = f"decode_{_function_name(name)}_{suffix}"
    format_constant = _constant_name(name, "PAYLOAD_FORMAT")
    size_constant = _constant_name(name, "PAYLOAD_SIZE")
    return [
        f"def {function_name}(frame: bytes) -> {class_name}:",
        f"    payload = _payload_from_frame(frame, {id_constant}, {size_constant})",
        f"    values = struct.unpack({format_constant}, payload)",
        f"    return {class_name}(*values)",
    ]


def _format_dispatch_function(function_name: str, items, suffix: str, id_prefix: str) -> list[str]:
    lines = [f"def {function_name}(frame: bytes) -> Any:"]
    if not items:
        lines.append('    raise ValueError("no packet definitions available")')
        return lines

    lines.append("    _ensure_minimum_frame_size(frame)")
    lines.append("    frame_id = frame[0]")
    for index, item in enumerate(items):
        keyword = "if" if index == 0 else "elif"
        id_constant = _constant_name(id_prefix, item.name)
        lines.append(f"    {keyword} frame_id == {id_constant}:")
        lines.append(f"        return decode_{_function_name(item.name)}_{suffix}(frame)")
    lines.append(f'    raise ValueError(f"unknown {suffix} id: 0x{{frame_id:02X}}")')
    return lines


def _format_validate_frame_function() -> list[str]:
    return [
        "def _payload_from_frame(frame: bytes, expected_id: int, expected_payload_size: int) -> bytes:",
        "    _ensure_minimum_frame_size(frame)",
        "    frame_id = frame[0]",
        "    if frame_id != expected_id:",
        '        raise ValueError(f"unexpected frame id: 0x{frame_id:02X}")',
        "    payload_size = frame[1]",
        "    if payload_size != expected_payload_size:",
        '        raise ValueError(f"unexpected payload size: {payload_size}")',
        "    expected_frame_size = HEADER_SIZE + expected_payload_size",
        "    if len(frame) != expected_frame_size:",
        '        raise ValueError(f"unexpected frame size: {len(frame)}")',
        "    return frame[HEADER_SIZE:]",
        "",
        "def _ensure_minimum_frame_size(frame: bytes) -> None:",
        "    if len(frame) < HEADER_SIZE:",
        '        raise ValueError(f"frame is too short: {len(frame)}")',
    ]


def _python_type(data_type_name: str) -> str:
    if data_type_name == "float32":
        return "float"
    return "int"


def _class_name(name: str, suffix: str) -> str:
    return "".join(part.capitalize() for part in name.lower().split("_")) + suffix


def _constant_name(*parts: str) -> str:
    return "_".join(parts).upper()


def _function_name(name: str) -> str:
    return name.lower()

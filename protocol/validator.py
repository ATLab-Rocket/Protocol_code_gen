from __future__ import annotations

from collections.abc import Iterable

from .model import MAX_U8, Protocol


def validate_protocol(protocol: Protocol) -> None:
    _validate_protocol_header(protocol)
    _validate_unique_values("packet_id", (packet.packet_id for packet in protocol.telemetry))
    _validate_unique_values("command_id", (command.command_id for command in protocol.commands))

    for packet in protocol.telemetry:
        _validate_packet(packet)

    for command in protocol.commands:
        _validate_command(command)


def _validate_protocol_header(protocol: Protocol) -> None:
    if protocol.version <= 0:
        raise ValueError("protocol version must be positive")
    if protocol.endian not in {"little", "big"}:
        raise ValueError("endian must be 'little' or 'big'")


def _validate_packet(packet) -> None:
    _validate_name("packet name", packet.name)
    _validate_u8("packet_id", packet.packet_id)
    if packet.rate_hz <= 0:
        raise ValueError(f"packet {packet.name!r} rate_hz must be positive")
    if not packet.fields:
        raise ValueError(f"packet {packet.name!r} must define at least one field")

    _validate_unique_values("field name", (field.name for field in packet.fields))

    expected_offset = 0
    for field in packet.fields:
        _validate_name("field name", field.name)
        if field.offset != expected_offset:
            raise ValueError(
                f"packet {packet.name!r} field {field.name!r} has offset {field.offset}; "
                f"expected {expected_offset}"
            )
        expected_offset += field.size

    _validate_u8("payload size", packet.payload_size)


def _validate_command(command) -> None:
    _validate_name("command name", command.name)
    _validate_u8("command_id", command.command_id)
    _validate_unique_values("argument name", (argument.name for argument in command.arguments))

    expected_offset = 0
    for argument in command.arguments:
        _validate_name("argument name", argument.name)
        if argument.offset != expected_offset:
            raise ValueError(
                f"command {command.name!r} argument {argument.name!r} has offset {argument.offset}; "
                f"expected {expected_offset}"
            )
        expected_offset += argument.size

    _validate_u8("command payload size", command.payload_size)


def _validate_name(label: str, value: str) -> None:
    if not value:
        raise ValueError(f"{label} must not be empty")


def _validate_u8(name: str, value: int) -> None:
    if not 0 <= value <= MAX_U8:
        raise ValueError(f"{name} must fit in one byte")


def _validate_unique_values(kind: str, values: Iterable[object]) -> None:
    seen = set()
    for value in values:
        if value in seen:
            raise ValueError(f"duplicate {kind}: {value!r}")
        seen.add(value)

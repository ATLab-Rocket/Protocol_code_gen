from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .model import Command, Packet, Protocol
from .types import DataType


def load_protocol(path: str | Path) -> Protocol:
    with Path(path).open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream)
    return parse_protocol(raw)


def parse_protocol(raw: dict[str, Any]) -> Protocol:
    if not isinstance(raw, dict):
        raise ValueError("protocol file must contain a YAML mapping")

    protocol_header = _required_mapping(raw, "protocol")
    version = _required_int(protocol_header, "version")
    endian = _required_str(protocol_header, "endian")

    telemetry = tuple(_parse_packet(name, packet) for name, packet in _optional_mapping(raw, "telemetry").items())
    commands = tuple(_parse_command(name, command) for name, command in _optional_mapping(raw, "commands").items())

    return Protocol(version=version, endian=endian, telemetry=telemetry, commands=commands)


def _parse_packet(name: str, raw_packet: Any) -> Packet:
    packet = _ensure_mapping(raw_packet, f"telemetry.{name}")
    fields = []
    for raw_field in _required_list(packet, "data"):
        field = _ensure_mapping(raw_field, f"telemetry.{name}.data")
        fields.append((_required_str(field, "name"), DataType.parse(_required_str(field, "type"))))

    return Packet.create(
        name=name,
        packet_id=_required_int(packet, "packet_id"),
        rate_hz=_required_int(packet, "rate_hz"),
        fields=fields,
    )


def _parse_command(name: str, raw_command: Any) -> Command:
    command = _ensure_mapping(raw_command, f"commands.{name}")
    arguments = []
    for raw_argument in command.get("arguments", []):
        argument = _ensure_mapping(raw_argument, f"commands.{name}.arguments")
        arguments.append((_required_str(argument, "name"), DataType.parse(_required_str(argument, "type"))))

    return Command.create(
        name=name,
        command_id=_required_int(command, "command_id"),
        arguments=arguments,
    )


def _optional_mapping(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key, {})
    return _ensure_mapping(value, key)


def _required_mapping(raw: dict[str, Any], key: str) -> dict[str, Any]:
    if key not in raw:
        raise ValueError(f"missing required key: {key}")
    return _ensure_mapping(raw[key], key)


def _ensure_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def _required_list(raw: dict[str, Any], key: str) -> list[Any]:
    if key not in raw:
        raise ValueError(f"missing required key: {key}")
    value = raw[key]
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _required_str(raw: dict[str, Any], key: str) -> str:
    if key not in raw:
        raise ValueError(f"missing required key: {key}")
    value = raw[key]
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _required_int(raw: dict[str, Any], key: str) -> int:
    if key not in raw:
        raise ValueError(f"missing required key: {key}")
    value = raw[key]
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value

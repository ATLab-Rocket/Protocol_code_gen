from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .types import DataType


HEADER_SIZE = 2
MAX_U8 = 0xFF


@dataclass(frozen=True)
class Field:
    name: str
    data_type: DataType
    offset: int

    @property
    def size(self) -> int:
        return self.data_type.size


@dataclass(frozen=True)
class Argument:
    name: str
    data_type: DataType
    offset: int

    @property
    def size(self) -> int:
        return self.data_type.size


@dataclass(frozen=True)
class Packet:
    name: str
    packet_id: int
    rate_hz: int
    fields: tuple[Field, ...] = field(default_factory=tuple)

    @classmethod
    def create(
        cls,
        name: str,
        packet_id: int,
        rate_hz: int,
        fields: Iterable[tuple[str, DataType]],
    ) -> "Packet":
        _validate_u8("packet_id", packet_id)
        if rate_hz <= 0:
            raise ValueError("rate_hz must be positive")

        offset = 0
        model_fields: list[Field] = []
        for field_name, data_type in fields:
            model_fields.append(Field(field_name, data_type, offset))
            offset += data_type.size

        _validate_unique_names("field", (field.name for field in model_fields))
        _validate_u8("payload size", offset)
        return cls(name=name, packet_id=packet_id, rate_hz=rate_hz, fields=tuple(model_fields))

    @property
    def payload_size(self) -> int:
        return sum(field.size for field in self.fields)

    @property
    def packet_size(self) -> int:
        return HEADER_SIZE + self.payload_size


@dataclass(frozen=True)
class Command:
    name: str
    command_id: int
    arguments: tuple[Argument, ...] = field(default_factory=tuple)

    @classmethod
    def create(
        cls,
        name: str,
        command_id: int,
        arguments: Iterable[tuple[str, DataType]],
    ) -> "Command":
        _validate_u8("command_id", command_id)

        offset = 0
        model_arguments: list[Argument] = []
        for argument_name, data_type in arguments:
            model_arguments.append(Argument(argument_name, data_type, offset))
            offset += data_type.size

        _validate_unique_names("argument", (argument.name for argument in model_arguments))
        _validate_u8("command payload size", offset)
        return cls(name=name, command_id=command_id, arguments=tuple(model_arguments))

    @property
    def payload_size(self) -> int:
        return sum(argument.size for argument in self.arguments)

    @property
    def packet_size(self) -> int:
        return HEADER_SIZE + self.payload_size


@dataclass(frozen=True)
class Protocol:
    version: int
    endian: str
    telemetry: tuple[Packet, ...] = field(default_factory=tuple)
    commands: tuple[Command, ...] = field(default_factory=tuple)


def _validate_u8(name: str, value: int) -> None:
    if not 0 <= value <= MAX_U8:
        raise ValueError(f"{name} must fit in one byte")


def _validate_unique_names(kind: str, names: Iterable[str]) -> None:
    _validate_unique_values(f"{kind} name", names)


def _validate_unique_values(kind: str, values: Iterable[object]) -> None:
    seen = set()
    for value in values:
        if value in seen:
            raise ValueError(f"duplicate {kind}: {value!r}")
        seen.add(value)

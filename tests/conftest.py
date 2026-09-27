from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pytest

# Make the project root importable regardless of where pytest is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ---------------------------------------------------------------------------
# Lightweight stand-ins for protocol.model.
#
# The generator code only ever *reads* attributes off these objects (no
# isinstance checks), so these plain dataclasses are enough to drive it in
# tests without depending on the real parser/validator/model implementation.
# If your real Protocol model differs in field names, adjust here.
# ---------------------------------------------------------------------------

@dataclass
class DataType:
    name: str
    c_name: str


@dataclass
class Field:
    name: str
    data_type: DataType
    offset: int
    size: int


@dataclass
class Packet:
    name: str
    packet_id: int
    payload_size: int
    packet_size: int
    rate_hz: float
    fields: List[Field]


@dataclass
class Command:
    name: str
    command_id: int
    payload_size: int
    packet_size: int
    arguments: List[Field]


@dataclass
class Protocol:
    version: int
    endian: str
    telemetry: List[Packet]
    commands: List[Command]


UINT8 = DataType(name="uint8", c_name="uint8_t")
INT16 = DataType(name="int16", c_name="int16_t")
UINT16 = DataType(name="uint16", c_name="uint16_t")
INT32 = DataType(name="int32", c_name="int32_t")
UINT32 = DataType(name="uint32", c_name="uint32_t")
FLOAT32 = DataType(name="float32", c_name="float")


def make_sample_protocol() -> Protocol:
    """One telemetry packet touching every supported data type, and one command."""
    telemetry_fields = [
        Field(name="status", data_type=UINT8, offset=0, size=1),
        Field(name="altitude_cm", data_type=INT32, offset=1, size=4),
        Field(name="battery_mv", data_type=UINT16, offset=5, size=2),
        Field(name="temperature_c", data_type=FLOAT32, offset=7, size=4),
    ]
    packet = Packet(
        name="SensorData",
        packet_id=0x01,
        payload_size=sum(f.size for f in telemetry_fields),
        packet_size=2 + sum(f.size for f in telemetry_fields),
        rate_hz=10,
        fields=telemetry_fields,
    )

    command_fields = [
        Field(name="target_state", data_type=UINT8, offset=0, size=1),
        Field(name="delay_ms", data_type=UINT16, offset=1, size=2),
    ]
    command = Command(
        name="SetState",
        command_id=0x10,
        payload_size=sum(f.size for f in command_fields),
        packet_size=2 + sum(f.size for f in command_fields),
        arguments=command_fields,
    )

    return Protocol(version=1, endian="little", telemetry=[packet], commands=[command])


@pytest.fixture
def sample_protocol() -> Protocol:
    return make_sample_protocol()

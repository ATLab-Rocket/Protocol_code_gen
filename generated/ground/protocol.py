"""Auto-generated from protocol.yaml. Do not edit by hand."""
from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Any

PROTOCOL_VERSION = 1
ENDIAN = 'little'
HEADER_SIZE = 2

PACKET_ID_IMU = 0x01

COMMAND_ID_OPEN_VALVE = 0x10

@dataclass(frozen=True)
class ImuPacket:
    a_x: int
    a_y: int
    a_z: int
    roll: int
    pitch: int
    yaw: int

IMU_PAYLOAD_FORMAT = '<hhhhhh'
IMU_PAYLOAD_SIZE = 12

def decode_imu_packet(frame: bytes) -> ImuPacket:
    payload = _payload_from_frame(frame, PACKET_ID_IMU, IMU_PAYLOAD_SIZE)
    values = struct.unpack(IMU_PAYLOAD_FORMAT, payload)
    return ImuPacket(*values)

@dataclass(frozen=True)
class OpenValveCommand:
    valve_id: int

OPEN_VALVE_PAYLOAD_FORMAT = '<B'
OPEN_VALVE_PAYLOAD_SIZE = 1

def encode_open_valve_command(value: OpenValveCommand) -> bytes:
    payload = struct.pack(OPEN_VALVE_PAYLOAD_FORMAT, value.valve_id)
    return bytes((COMMAND_ID_OPEN_VALVE, len(payload))) + payload

def decode_telemetry(frame: bytes) -> Any:
    _ensure_minimum_frame_size(frame)
    frame_id = frame[0]
    if frame_id == PACKET_ID_IMU:
        return decode_imu_packet(frame)
    raise ValueError(f"unknown packet id: 0x{frame_id:02X}")

def _payload_from_frame(frame: bytes, expected_id: int, expected_payload_size: int) -> bytes:
    _ensure_minimum_frame_size(frame)
    frame_id = frame[0]
    if frame_id != expected_id:
        raise ValueError(f"unexpected frame id: 0x{frame_id:02X}")
    payload_size = frame[1]
    if payload_size != expected_payload_size:
        raise ValueError(f"unexpected payload size: {payload_size}")
    expected_frame_size = HEADER_SIZE + expected_payload_size
    if len(frame) != expected_frame_size:
        raise ValueError(f"unexpected frame size: {len(frame)}")
    return frame[HEADER_SIZE:]

def _ensure_minimum_frame_size(frame: bytes) -> None:
    if len(frame) < HEADER_SIZE:
        raise ValueError(f"frame is too short: {len(frame)}")

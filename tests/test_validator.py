import unittest

from protocol.model import Argument, Command, Field, Packet, Protocol
from protocol.types import DataType
from protocol.validator import validate_protocol


class ValidatorTests(unittest.TestCase):
    def test_accepts_valid_protocol(self):
        int16 = DataType.parse("int16")
        uint8 = DataType.parse("uint8")

        protocol = Protocol(
            version=1,
            endian="little",
            telemetry=(Packet.create("IMU", 0x01, 50, [("roll", int16)]),),
            commands=(Command.create("OPEN_VALVE", 0x10, [("valve_id", uint8)]),),
        )

        validate_protocol(protocol)

    def test_rejects_invalid_endian(self):
        protocol = Protocol(version=1, endian="middle")

        with self.assertRaisesRegex(ValueError, "endian"):
            validate_protocol(protocol)

    def test_rejects_duplicate_packet_ids(self):
        int16 = DataType.parse("int16")
        packet_a = Packet.create("IMU_A", 0x01, 50, [("roll", int16)])
        packet_b = Packet.create("IMU_B", 0x01, 50, [("roll", int16)])
        protocol = Protocol(version=1, endian="little", telemetry=(packet_a, packet_b))

        with self.assertRaisesRegex(ValueError, "duplicate packet_id"):
            validate_protocol(protocol)

    def test_rejects_duplicate_command_ids(self):
        uint8 = DataType.parse("uint8")
        command_a = Command.create("OPEN_VALVE_A", 0x10, [("valve_id", uint8)])
        command_b = Command.create("OPEN_VALVE_B", 0x10, [("valve_id", uint8)])
        protocol = Protocol(version=1, endian="little", commands=(command_a, command_b))

        with self.assertRaisesRegex(ValueError, "duplicate command_id"):
            validate_protocol(protocol)

    def test_rejects_duplicate_field_names(self):
        int16 = DataType.parse("int16")
        packet = Packet(
            name="IMU",
            packet_id=0x01,
            rate_hz=50,
            fields=(Field("roll", int16, 0), Field("roll", int16, 2)),
        )
        protocol = Protocol(version=1, endian="little", telemetry=(packet,))

        with self.assertRaisesRegex(ValueError, "duplicate field name"):
            validate_protocol(protocol)

    def test_rejects_invalid_packet_layout(self):
        int16 = DataType.parse("int16")
        packet = Packet(
            name="IMU",
            packet_id=0x01,
            rate_hz=50,
            fields=(Field("roll", int16, 2),),
        )
        protocol = Protocol(version=1, endian="little", telemetry=(packet,))

        with self.assertRaisesRegex(ValueError, "expected 0"):
            validate_protocol(protocol)

    def test_rejects_duplicate_argument_names(self):
        uint8 = DataType.parse("uint8")
        command = Command(
            name="OPEN_VALVE",
            command_id=0x10,
            arguments=(Argument("valve_id", uint8, 0), Argument("valve_id", uint8, 1)),
        )
        protocol = Protocol(version=1, endian="little", commands=(command,))

        with self.assertRaisesRegex(ValueError, "duplicate argument name"):
            validate_protocol(protocol)


if __name__ == "__main__":
    unittest.main()

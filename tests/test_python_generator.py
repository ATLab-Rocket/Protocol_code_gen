import unittest

from generators.python_generator import generate_python_module
from protocol.model import Command, Packet, Protocol
from protocol.types import DataType


class PythonGeneratorTests(unittest.TestCase):
    def test_generates_constants_dataclasses_and_formats(self):
        int16 = DataType.parse("int16_t")
        uint8 = DataType.parse("uint8")
        protocol = Protocol(
            version=1,
            endian="little",
            telemetry=(Packet.create("IMU", 0x01, 50, [("a_x", int16), ("a_y", int16)]),),
            commands=(Command.create("OPEN_VALVE", 0x10, [("valve_id", uint8)]),),
        )

        module = generate_python_module(protocol)

        self.assertIn("PROTOCOL_VERSION = 1", module)
        self.assertIn("ENDIAN = 'little'", module)
        self.assertIn("PACKET_ID_IMU = 0x01", module)
        self.assertIn("COMMAND_ID_OPEN_VALVE = 0x10", module)
        self.assertIn("@dataclass(frozen=True)\nclass ImuPacket:\n    a_x: int\n    a_y: int", module)
        self.assertIn("@dataclass(frozen=True)\nclass OpenValveCommand:\n    valve_id: int", module)
        self.assertIn("IMU_PAYLOAD_FORMAT = '<hh'", module)
        self.assertIn("OPEN_VALVE_PAYLOAD_FORMAT = '<B'", module)

    def test_generated_ground_module_decodes_telemetry_and_encodes_commands(self):
        int16 = DataType.parse("int16_t")
        uint8 = DataType.parse("uint8")
        protocol = Protocol(
            version=1,
            endian="little",
            telemetry=(Packet.create("IMU", 0x01, 50, [("a_x", int16), ("a_y", int16)]),),
            commands=(Command.create("OPEN_VALVE", 0x10, [("valve_id", uint8)]),),
        )
        namespace = {}

        exec(generate_python_module(protocol), namespace)

        imu_frame = bytes([0x01, 0x04, 0x64, 0x00, 0xCE, 0xFF])
        imu = namespace["ImuPacket"](a_x=100, a_y=-50)
        self.assertEqual(imu_frame, bytes([0x01, 0x04, 0x64, 0x00, 0xCE, 0xFF]))
        self.assertEqual(namespace["decode_imu_packet"](imu_frame), imu)
        self.assertEqual(namespace["decode_telemetry"](imu_frame), imu)

        command = namespace["OpenValveCommand"](valve_id=3)
        command_frame = namespace["encode_open_valve_command"](command)
        self.assertEqual(command_frame, bytes([0x10, 0x01, 0x03]))
        self.assertNotIn("encode_imu_packet", namespace)
        self.assertNotIn("decode_open_valve_command", namespace)
        self.assertNotIn("decode_command", namespace)

    def test_generated_module_rejects_bad_frame_size(self):
        int16 = DataType.parse("int16_t")
        protocol = Protocol(
            version=1,
            endian="little",
            telemetry=(Packet.create("IMU", 0x01, 50, [("a_x", int16)]),),
        )
        namespace = {}

        exec(generate_python_module(protocol), namespace)

        with self.assertRaisesRegex(ValueError, "unexpected payload size"):
            namespace["decode_imu_packet"](bytes([0x01, 0x03, 0x64, 0x00]))


if __name__ == "__main__":
    unittest.main()

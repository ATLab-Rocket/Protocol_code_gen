import unittest

from protocol.model import Command, Packet
from protocol.types import DataType


class DataTypeTests(unittest.TestCase):
    def test_parses_supported_aliases(self):
        self.assertEqual(DataType.parse("int16_t").size, 2)
        self.assertEqual(DataType.parse("uint8").c_name, "uint8_t")
        self.assertEqual(DataType.parse("float32").python_struct_format, "f")

    def test_rejects_unsupported_type(self):
        with self.assertRaisesRegex(ValueError, "unsupported data type"):
            DataType.parse("double")


class PacketModelTests(unittest.TestCase):
    def test_calculates_field_layout_and_packet_size(self):
        int16 = DataType.parse("int16_t")

        packet = Packet.create(
            name="IMU",
            packet_id=0x01,
            rate_hz=50,
            fields=[
                ("a_x", int16),
                ("a_y", int16),
                ("a_z", int16),
                ("roll", int16),
                ("pitch", int16),
                ("yaw", int16),
            ],
        )

        self.assertEqual(packet.fields[0].offset, 0)
        self.assertEqual(packet.fields[-1].offset, 10)
        self.assertEqual(packet.payload_size, 12)
        self.assertEqual(packet.packet_size, 14)

    def test_rejects_duplicate_field_names(self):
        int16 = DataType.parse("int16")

        with self.assertRaisesRegex(ValueError, "duplicate field name"):
            Packet.create("IMU", 0x01, 50, [("roll", int16), ("roll", int16)])


class CommandModelTests(unittest.TestCase):
    def test_calculates_argument_layout(self):
        command = Command.create(
            name="OPEN_VALVE",
            command_id=0x10,
            arguments=[("valve_id", DataType.parse("uint8"))],
        )

        self.assertEqual(command.arguments[0].offset, 0)
        self.assertEqual(command.payload_size, 1)
        self.assertEqual(command.packet_size, 3)


if __name__ == "__main__":
    unittest.main()

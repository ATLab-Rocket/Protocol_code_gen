import unittest

from generators.c_generator import generate_c_header, generate_c_source
from protocol.model import Command, Packet, Protocol
from protocol.types import DataType


class CGeneratorTests(unittest.TestCase):
    def test_generates_ids_and_structs(self):
        int16 = DataType.parse("int16_t")
        uint8 = DataType.parse("uint8")
        protocol = Protocol(
            version=1,
            endian="little",
            telemetry=(
                Packet.create(
                    "IMU",
                    0x01,
                    50,
                    [
                        ("a_x", int16),
                        ("a_y", int16),
                    ],
                ),
            ),
            commands=(Command.create("OPEN_VALVE", 0x10, [("valve_id", uint8)]),),
        )

        header = generate_c_header(protocol)

        self.assertIn("#define PROTOCOL_VERSION 1", header)
        self.assertIn("#define PACKET_ID_IMU 0x01", header)
        self.assertIn("#define IMU_PAYLOAD_SIZE 4", header)
        self.assertIn("#define IMU_FRAME_SIZE 6", header)
        self.assertIn("#define COMMAND_ID_OPEN_VALVE 0x10", header)
        self.assertIn("#define OPEN_VALVE_PAYLOAD_SIZE 1", header)
        self.assertIn("#define OPEN_VALVE_FRAME_SIZE 3", header)
        self.assertIn("typedef struct {\n    int16_t a_x;\n    int16_t a_y;\n} IMU_Packet_t;", header)
        self.assertIn("typedef struct {\n    uint8_t valve_id;\n} OPEN_VALVE_Command_t;", header)
        self.assertIn("uint8_t encode_imu_packet(uint8_t *frame, const IMU_Packet_t *value);", header)
        self.assertIn(
            "int decode_open_valve_command(const uint8_t *frame, uint8_t frame_size, OPEN_VALVE_Command_t *out);",
            header,
        )
        self.assertNotIn("protocol_write_u16_le", header)

    def test_generates_rocket_direction_only(self):
        int16 = DataType.parse("int16_t")
        uint8 = DataType.parse("uint8")
        protocol = Protocol(
            version=1,
            endian="little",
            telemetry=(Packet.create("IMU", 0x01, 50, [("a_x", int16), ("a_y", int16)]),),
            commands=(Command.create("OPEN_VALVE", 0x10, [("valve_id", uint8)]),),
        )

        header = generate_c_header(protocol)
        source = generate_c_source(protocol)

        self.assertIn("uint8_t encode_imu_packet(", source)
        self.assertIn("frame[0] = PACKET_ID_IMU;", source)
        self.assertIn("frame[1] = IMU_PAYLOAD_SIZE;", source)
        self.assertIn("protocol_write_u16_le(frame + PROTOCOL_HEADER_SIZE + 0, (uint16_t)value->a_x);", source)
        self.assertIn("protocol_write_u16_le(frame + PROTOCOL_HEADER_SIZE + 2, (uint16_t)value->a_y);", source)

        self.assertIn("int decode_open_valve_command(", source)
        self.assertIn("if (frame[0] != COMMAND_ID_OPEN_VALVE)", source)
        self.assertIn("out->valve_id = (frame + PROTOCOL_HEADER_SIZE + 0)[0];", source)
        self.assertNotIn("decode_imu_packet", header)
        self.assertNotIn("encode_open_valve_command", header)
        self.assertNotIn("decode_imu_packet", source)
        self.assertNotIn("encode_open_valve_command", source)


if __name__ == "__main__":
    unittest.main()

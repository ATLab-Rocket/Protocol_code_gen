import unittest

from protocol.parser import parse_protocol


class ParserTests(unittest.TestCase):
    def test_parses_protocol_yaml_shape(self):
        protocol = parse_protocol(
            {
                "protocol": {"version": 1, "endian": "little"},
                "telemetry": {
                    "IMU": {
                        "packet_id": 0x01,
                        "rate_hz": 50,
                        "data": [
                            {"name": "roll", "type": "float32"},
                            {"name": "pitch", "type": "float32"},
                            {"name": "yaw", "type": "float32"},
                        ],
                    }
                },
                "commands": {
                    "OPEN_VALVE": {
                        "command_id": 0x10,
                        "arguments": [{"name": "valve_id", "type": "uint8"}],
                    }
                },
            }
        )

        self.assertEqual(protocol.version, 1)
        self.assertEqual(protocol.telemetry[0].payload_size, 12)
        self.assertEqual(protocol.commands[0].payload_size, 1)

    def test_rejects_invalid_packet_definition(self):
        with self.assertRaisesRegex(ValueError, "missing required key: rate_hz"):
            parse_protocol(
                {
                    "protocol": {"version": 1, "endian": "little"},
                    "telemetry": {
                        "IMU": {
                            "packet_id": 0x01,
                            "data": [{"name": "roll", "type": "float32"}],
                        }
                    },
                }
            )

    def test_rejects_invalid_command_definition(self):
        with self.assertRaisesRegex(ValueError, "missing required key: command_id"):
            parse_protocol(
                {
                    "protocol": {"version": 1, "endian": "little"},
                    "commands": {"OPEN_VALVE": {"arguments": [{"name": "valve_id", "type": "uint8"}]}},
                }
            )


if __name__ == "__main__":
    unittest.main()

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from generators.c_generator import generate_c_header, generate_c_source
from generators.python_generator import generate_python_module
from protocol.parser import load_protocol
from protocol.validator import validate_protocol


class CrossPlatformTests(unittest.TestCase):
    def setUp(self):
        self.gcc = shutil.which("gcc")
        if self.gcc is None:
            self.skipTest("gcc is required for cross-platform C/Python tests")

        self.protocol = load_protocol("protocol.yaml")
        validate_protocol(self.protocol)
        self.ground = _load_generated_ground_module(self.protocol)

    def test_python_encode_command_c_decode_command(self):
        frame = self.ground.encode_open_valve_command(self.ground.OpenValveCommand(valve_id=3))

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            _write_c_files(temp_path, self.protocol)
            test_c = temp_path / "test_command_decode.c"
            test_exe = temp_path / "test_command_decode.exe"
            test_c.write_text(
                textwrap.dedent(
                    f"""
                    #include <stdint.h>
                    #include "protocol.h"

                    int main(void) {{
                        uint8_t frame[] = {{{_c_byte_array(frame)}}};
                        OPEN_VALVE_Command_t command = {{0}};
                        int status = decode_open_valve_command(frame, sizeof(frame), &command);

                        if (status != PROTOCOL_STATUS_OK) {{
                            return 1;
                        }}
                        if (command.valve_id != 3) {{
                            return 2;
                        }}
                        return 0;
                    }}
                    """
                ),
                encoding="utf-8",
            )

            self._compile_c(test_c, test_exe, temp_path)
            completed = subprocess.run([test_exe], check=False)
            self.assertEqual(completed.returncode, 0)

    def test_c_encode_telemetry_python_decode_telemetry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            _write_c_files(temp_path, self.protocol)
            test_c = temp_path / "test_telemetry_encode.c"
            test_exe = temp_path / "test_telemetry_encode.exe"
            test_c.write_text(
                textwrap.dedent(
                    """
                    #include <stdint.h>
                    #include <stdio.h>
                    #include "protocol.h"

                    int main(void) {
                        IMU_Packet_t packet = {
                            .a_x = 100,
                            .a_y = 200,
                            .a_z = -50,
                            .roll = 10,
                            .pitch = 20,
                            .yaw = 30,
                        };
                        uint8_t frame[IMU_FRAME_SIZE] = {0};
                        uint8_t frame_size = encode_imu_packet(frame, &packet);

                        for (uint8_t index = 0; index < frame_size; index++) {
                            printf("%02X", frame[index]);
                        }
                        return 0;
                    }
                    """
                ),
                encoding="utf-8",
            )

            self._compile_c(test_c, test_exe, temp_path)
            completed = subprocess.run([test_exe], check=True, capture_output=True, text=True)

        frame = bytes.fromhex(completed.stdout)
        decoded = self.ground.decode_telemetry(frame)
        self.assertEqual(decoded, self.ground.ImuPacket(100, 200, -50, 10, 20, 30))

    def _compile_c(self, source: Path, output: Path, include_dir: Path) -> None:
        subprocess.run(
            [self.gcc, str(source), str(include_dir / "protocol.c"), "-I", str(include_dir), "-o", str(output)],
            check=True,
            capture_output=True,
            text=True,
        )


def _load_generated_ground_module(protocol):
    module_path = Path(tempfile.mkdtemp()) / "ground_protocol.py"
    module_path.write_text(generate_python_module(protocol), encoding="utf-8")

    spec = importlib.util.spec_from_file_location("ground_protocol_for_cross_platform_test", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_c_files(directory: Path, protocol) -> None:
    (directory / "protocol.h").write_text(generate_c_header(protocol), encoding="utf-8")
    (directory / "protocol.c").write_text(generate_c_source(protocol), encoding="utf-8")


def _c_byte_array(frame: bytes) -> str:
    return ", ".join(f"0x{byte:02X}" for byte in frame)


if __name__ == "__main__":
    unittest.main()

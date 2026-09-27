from __future__ import annotations

import argparse
from pathlib import Path

from generators.c_generator import (
    generate_c_header,
    generate_c_source,
    generate_ground_c_header,
    generate_ground_c_source,
)
from generators.python_generator import generate_python_module
from protocol.model import Protocol
from protocol.parser import load_protocol
from protocol.validator import validate_protocol


def main() -> None:
    parser = argparse.ArgumentParser(description="Load protocol.yaml and print the protocol model layout.")
    parser.add_argument("protocol_yaml", help="Path to protocol.yaml")
    parser.add_argument("--c-output", help="Write a generated rocket-side C header to this path")
    parser.add_argument("--c-output-dir", help="Write generated rocket-side protocol.h and protocol.c to this directory")
    parser.add_argument("--ground-output", help="Write a generated ground-station C header to this path")
    parser.add_argument("--ground-output-dir", help="Write generated ground-station protocol.h and protocol.c to this directory")
    parser.add_argument("--python-output", help="Write a generated Python module to this path")
    args = parser.parse_args()

    protocol = load_protocol(args.protocol_yaml)
    validate_protocol(protocol)

    wrote_something = False

    if args.c_output:
        c_output = Path(args.c_output)
        c_output.parent.mkdir(parents=True, exist_ok=True)
        c_output.write_text(generate_c_header(protocol), encoding="utf-8")
        print(f"Wrote rocket-side C header: {c_output}")
        wrote_something = True

    if args.c_output_dir:
        c_output_dir = Path(args.c_output_dir)
        c_output_dir.mkdir(parents=True, exist_ok=True)
        header_output = c_output_dir / "protocol.h"
        source_output = c_output_dir / "protocol.c"
        header_output.write_text(generate_c_header(protocol), encoding="utf-8")
        source_output.write_text(generate_c_source(protocol), encoding="utf-8")
        print(f"Wrote rocket-side C header: {header_output}")
        print(f"Wrote rocket-side C source: {source_output}")
        wrote_something = True

    if args.ground_output:
        ground_output = Path(args.ground_output)
        ground_output.parent.mkdir(parents=True, exist_ok=True)
        ground_output.write_text(generate_ground_c_header(protocol), encoding="utf-8")
        print(f"Wrote ground-station C header: {ground_output}")
        wrote_something = True

    if args.ground_output_dir:
        ground_output_dir = Path(args.ground_output_dir)
        ground_output_dir.mkdir(parents=True, exist_ok=True)
        header_output = ground_output_dir / "protocol.h"
        source_output = ground_output_dir / "protocol.c"
        header_output.write_text(generate_ground_c_header(protocol), encoding="utf-8")
        source_output.write_text(generate_ground_c_source(protocol), encoding="utf-8")
        print(f"Wrote ground-station C header: {header_output}")
        print(f"Wrote ground-station C source: {source_output}")
        wrote_something = True

    if args.python_output:
        python_output = Path(args.python_output)
        python_output.parent.mkdir(parents=True, exist_ok=True)
        python_output.write_text(generate_python_module(protocol), encoding="utf-8")
        print(f"Wrote Python module: {python_output}")
        wrote_something = True

    if not wrote_something:
        print(format_protocol(protocol))


def format_protocol(protocol: Protocol) -> str:
    lines = [
        f"Protocol version: {protocol.version}",
        f"Endian: {protocol.endian}",
        "",
        "Telemetry:",
    ]

    for packet in protocol.telemetry:
        lines.extend(
            [
                "",
                packet.name,
                f"  Packet ID: 0x{packet.packet_id:02X}",
                f"  Rate: {packet.rate_hz} Hz",
                "",
            ]
        )
        for field in packet.fields:
            lines.extend(
                [
                    f"  {field.name}",
                    f"    type: {field.data_type.name}",
                    f"    offset: {field.offset}",
                    f"    size: {field.size}",
                    "",
                ]
            )
        lines.append(f"  payload size: {packet.payload_size} bytes")
        lines.append(f"  packet size: {packet.packet_size} bytes")

    lines.extend(["", "Commands:"])

    for command in protocol.commands:
        lines.extend(["", command.name, f"  Command ID: 0x{command.command_id:02X}", ""])
        for argument in command.arguments:
            lines.extend(
                [
                    f"  {argument.name}",
                    f"    type: {argument.data_type.name}",
                    f"    offset: {argument.offset}",
                    f"    size: {argument.size}",
                    "",
                ]
            )
        lines.append(f"  payload size: {command.payload_size} bytes")
        lines.append(f"  packet size: {command.packet_size} bytes")

    return "\n".join(lines).rstrip()


if __name__ == "__main__":
    main()
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataType:
    """A fixed-width protocol scalar type."""

    name: str
    c_name: str
    python_struct_format: str
    size: int

    @classmethod
    def parse(cls, raw_type: str) -> "DataType":
        try:
            return _DATA_TYPES[raw_type]
        except KeyError as exc:
            supported = ", ".join(sorted(_DATA_TYPES))
            raise ValueError(f"unsupported data type {raw_type!r}; supported: {supported}") from exc


_DATA_TYPES = {
    "uint8": DataType("uint8", "uint8_t", "B", 1),
    "uint8_t": DataType("uint8", "uint8_t", "B", 1),
    "int16": DataType("int16", "int16_t", "h", 2),
    "int16_t": DataType("int16", "int16_t", "h", 2),
    "uint16": DataType("uint16", "uint16_t", "H", 2),
    "uint16_t": DataType("uint16", "uint16_t", "H", 2),
    "int32": DataType("int32", "int32_t", "i", 4),
    "int32_t": DataType("int32", "int32_t", "i", 4),
    "uint32": DataType("uint32", "uint32_t", "I", 4),
    "uint32_t": DataType("uint32", "uint32_t", "I", 4),
    "float32": DataType("float32", "float", "f", 4),
}

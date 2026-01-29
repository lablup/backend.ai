from __future__ import annotations

import enum
import struct
from collections.abc import Sequence

rgba = struct.Struct("BBBB")


class Color:
    def __init__(self, red: int, green: int, blue: int, alpha: int = 255) -> None:
        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha

    @staticmethod
    def from_hex(value: str) -> Color:
        value = value.replace("#", "")
        r = int(value[0:2], 16)
        g = int(value[2:4], 16)
        b = int(value[4:6], 16)
        a = int(value[6:8], 16)
        return Color(r, g, b, a)

    @staticmethod
    def from_rgba(value: Sequence[int]) -> Color:
        return Color(*value)

    @staticmethod
    def from_bytes(value: bytes) -> Color:
        r, g, b, a = rgba.unpack(value)
        return Color(r, g, b, a)

    def to_hex(self, include_alpha: bool = True) -> str:
        if include_alpha:
            return f"#{self.red:02x}{self.green:02x}{self.blue:02x}{self.alpha:02x}"
        return f"#{self.red:02x}{self.green:02x}{self.blue:02x}"

    def to_bytes(self) -> bytes:
        return rgba.pack(self.red, self.green, self.blue, self.alpha)

    def to_rgba(self) -> str:
        return f"rgba({self.red},{self.green},{self.blue},{self.alpha})"


class Colors(Color, enum.Enum):
    Transparent = (255, 255, 255, 0)
    Black = (0, 0, 0, 255)
    Gray = (128, 128, 128, 255)
    White = (255, 255, 255, 255)
    Red = (255, 0, 0, 255)
    Green = (0, 255, 0, 255)
    Blue = (0, 0, 255, 255)
    Yellow = (255, 255, 0, 255)
    Magenta = (255, 0, 255, 255)
    Cyan = (0, 255, 255, 255)


__all__ = [
    "Color",
    "Colors",
]

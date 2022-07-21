import enum
import struct

rgba = struct.Struct("BBBB")


class Color:
    def __init__(self, red, green, blue, alpha=255):
        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha

    @staticmethod
    def from_hex(value):
        value = value.replace("#", "")
        r = int(value[0:2], 16)
        g = int(value[2:4], 16)
        b = int(value[4:6], 16)
        a = int(value[6:8], 16)
        return Color(r, g, b, a)

    @staticmethod
    def from_rgba(value):
        return Color(*value)

    @staticmethod
    def from_bytes(value):
        r, g, b, a = rgba.unpack(value)
        return Color(r, g, b, a)

    def to_hex(self, include_alpha=True):
        if include_alpha:
            return "#{:02x}{:02x}{:02x}{:02x}".format(self.red, self.green, self.blue, self.alpha)
        else:
            return "#{:02x}{:02x}{:02x}".format(self.red, self.green, self.blue)

    def to_bytes(self):
        return rgba.pack(self.red, self.green, self.blue, self.alpha)

    def to_rgba(self):
        return "rgba({},{},{},{})".format(self.red, self.green, self.blue, self.alpha)


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

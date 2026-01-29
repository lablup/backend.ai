from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .color import Colors

if TYPE_CHECKING:
    from .canvas import Canvas


class Vec2D(tuple):
    """A helper class taken from Python stdlib's Turtle package."""

    def __new__(cls, x: float | int, y: float | int):
        return tuple.__new__(cls, (x, y))

    def __add__(self, other: Vec2D):  # type: ignore[override]
        return Vec2D(self[0] + other[0], self[1] + other[1])

    def __mul__(self, other: Vec2D | float | int):  # type: ignore[override]
        if isinstance(other, Vec2D):
            return self[0] * other[0] + self[1] * other[1]
        return Vec2D(self[0] * other, self[1] * other)

    def __rmul__(self, other: float | int):  # type: ignore[override]
        if isinstance(other, (int, float)):
            return Vec2D(self[0] * other, self[1] * other)
        return None

    def __sub__(self, other: Vec2D):  # type: ignore[override]
        return Vec2D(self[0] - other[0], self[1] - other[1])

    def __neg__(self):
        return Vec2D(-self[0], -self[1])

    def __abs__(self):
        return (self[0] ** 2 + self[1] ** 2) ** 0.5

    def rotate(self, angle: float | int) -> Vec2D:
        """rotate self counterclockwise by angle"""
        perp = Vec2D(-self[1], self[0])
        angle = angle * math.pi / 180.0
        c, s = math.cos(angle), math.sin(angle)
        return Vec2D(self[0] * c + perp[0] * s, self[1] * c + perp[1] * s)

    def __getnewargs__(self):
        return (self[0], self[1])

    def __repr__(self) -> str:
        return "({:.2f},{:.2f})".format(*self)


class Turtle:
    def __init__(self, canvas: Canvas) -> None:
        self.canvas = canvas
        self.points = []
        self.pen = True
        w = self.canvas.width
        h = self.canvas.height
        self.cursor = self.canvas.triangle(
            w / 2,
            h / 2,
            12,
            18,
            border=Colors.Red,
            fill=Colors.from_rgba([255, 200, 200, 255]),
            angle=90,
        )
        self.angle = 90
        self.points.append((w / 2, h / 2))

    def forward(self, amt: float | int) -> None:
        x = self.points[-1][0]
        y = self.points[-1][1]
        x_diff = math.sin(math.radians(self.angle)) * amt
        y_diff = -1 * math.cos(math.radians(self.angle)) * amt
        self.canvas.begin_group()
        if self.pen:
            self.canvas.line(x, y, x + x_diff, y + y_diff, color=Colors.from_rgba([255, 0, 0, 128]))
        self.cursor.set_x(x + x_diff)
        self.cursor.set_y(y + y_diff)
        self.canvas.end_group()
        self.points.append((x + x_diff, y + y_diff))

    def left(self, deg: float | int) -> None:
        self.cursor.rotate(-deg)
        self.angle -= deg  # type: ignore[assignment]

    def right(self, deg: float | int) -> None:
        self.cursor.rotate(deg)
        self.angle += deg  # type: ignore[assignment]

    def pos(self) -> Vec2D:
        base_x, base_y = self.points[0][0], self.points[0][1]
        return Vec2D(self.points[-1][0] - base_x, self.points[-1][1] - base_y)

    def penup(self) -> None:
        self.pen = False

    def pendown(self) -> None:
        self.pen = True

    def setpos(self, x: float | int | Vec2D, y: float | int | None = None) -> None:
        base_x, base_y = self.points[0][0], self.points[0][1]
        if y is None:
            _x = x[0]  # type: ignore[index]
            _y = x[1]  # type: ignore[index]
            x, y = _x, _y
        self.canvas.begin_group()
        if self.pen:
            self.canvas.line(
                self.points[-1][0],
                self.points[-1][1],
                x + base_x,  # type: ignore[operator]
                y + base_y,  # type: ignore[operator]
                color=Colors.from_rgba([255, 0, 0, 128]),
            )
        self.cursor.set_x(x + base_x)  # type: ignore[operator]
        self.cursor.set_y(y + base_y)  # type: ignore[operator]
        self.canvas.end_group()
        self.points.append((x + base_x, y + base_y))  # type: ignore[operator]


__all__ = [
    "Turtle",
    "Vec2D",
]

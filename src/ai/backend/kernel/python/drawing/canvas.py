from __future__ import annotations

from typing import Any

from six.moves import builtins

from ai.backend.kernel.python.types import MediaRecord

from .color import Color, Colors
from .encoding import encode_commands
from .turtle import Turtle

_canvas_id_counter = 0

# Command history can contain various command tuples with different structures
CommandTuple = (
    tuple[int, str]  # 2-element: stop-anim, resume-anim, begin-group, end-group, end-fill
    | tuple[int, str, Any]  # 3-element: begin-fill, bgcolor, fgcolor
    | tuple[int, str, int, tuple[Any, ...]]  # 4-element: obj commands (variable length inner tuple)
    | tuple[int, str, Any, Any, Any, Any]  # 6-element: canvas initialization
    | tuple[int, str, int, Any, Any]  # 5-element: update commands
)


class DrawingObject:
    def __init__(self, canvas: Canvas, id_: int, args: tuple[Any, ...]) -> None:
        self._canvas = canvas
        self._id = id_
        self._type = args[0]

    def set_x(self, x: float | int) -> None:
        if self._type in ("rect", "circle", "triangle"):
            self._canvas._cmd_history.append((self._canvas._id, "update", self._id, "x", x))

    def set_y(self, y: float | int) -> None:
        if self._type in ("rect", "circle", "triangle"):
            self._canvas._cmd_history.append((self._canvas._id, "update", self._id, "y", y))

    def set_x1(self, x: float | int) -> None:
        if self._type == "line":
            self._canvas._cmd_history.append((self._canvas._id, "update", self._id, "x1", x))

    def set_y1(self, y: float | int) -> None:
        if self._type == "line":
            self._canvas._cmd_history.append((self._canvas._id, "update", self._id, "y1", y))

    def set_x2(self, x: float | int) -> None:
        if self._type == "line":
            self._canvas._cmd_history.append((self._canvas._id, "update", self._id, "x2", x))

    def set_y2(self, y: float | int) -> None:
        if self._type == "line":
            self._canvas._cmd_history.append((self._canvas._id, "update", self._id, "y2", y))

    def set_radius(self, r: float | int) -> None:
        if self._type == "circle":
            self._canvas._cmd_history.append((self._canvas._id, "update", self._id, "radius", r))

    def rotate(self, a: float | int) -> None:
        self._canvas._cmd_history.append((self._canvas._id, "update", self._id, "rotate", a))

    def set_angle(self, a: float | int) -> None:
        self._canvas._cmd_history.append((self._canvas._id, "update", self._id, "angle", a))

    def stroke(self, color: Color) -> None:
        color_hex = color.to_hex()
        if self._type == "line":
            self._canvas._cmd_history.append((
                self._canvas._id,
                "update",
                self._id,
                "color",
                color_hex,
            ))
        elif self._type == "circle" or self._type in ("rect", "triangle"):
            self._canvas._cmd_history.append((
                self._canvas._id,
                "update",
                self._id,
                "border",
                color_hex,
            ))

    def fill(self, color: Color) -> None:
        color_hex = color.to_hex()
        if self._type == "circle" or self._type in ("rect", "triangle"):
            self._canvas._cmd_history.append((
                self._canvas._id,
                "update",
                self._id,
                "fill",
                color_hex,
            ))


class Canvas:
    def __init__(
        self,
        width: float | int,
        height: float | int,
        bgcolor: Color = Colors.White,
        fgcolor: Color = Colors.Black,
    ) -> None:
        global _canvas_id_counter
        self._id = _canvas_id_counter
        _canvas_id_counter += 1
        self._cmd_history: list[CommandTuple] = []
        self._next_objid = 0
        self._cmd_history.append((
            self._id,
            "canvas",
            width,
            height,
            bgcolor.to_hex(),
            fgcolor.to_hex(),
        ))
        self.width = width
        self.height = height
        self.bgcolor = bgcolor
        self.fgcolor = fgcolor

    def update(self) -> None:
        builtins._sorna_emit(  # type: ignore[attr-defined]
            MediaRecord(
                "application/x-sorna-drawing",
                encode_commands(self._cmd_history),
            )
        )
        self._cmd_history = []

    def show(self) -> None:  # alias
        self.update()

    def create_turtle(self) -> Turtle:
        return Turtle(self)

    def stop_animation(self) -> None:
        self._cmd_history.append((self._id, "stop-anim"))

    def resume_animation(self) -> None:
        self._cmd_history.append((self._id, "resume-anim"))

    def begin_group(self) -> None:
        self._cmd_history.append((self._id, "begin-group"))

    def end_group(self) -> None:
        self._cmd_history.append((self._id, "end-group"))

    def begin_fill(self, c: Color) -> None:
        self._cmd_history.append((self._id, "begin-fill", c.to_hex()))

    def end_fill(self) -> None:
        self._cmd_history.append((self._id, "end-fill"))

    def background_color(self, c: Color) -> None:
        self.bgcolor = c
        self._cmd_history.append((self._id, "bgcolor", c.to_hex()))

    def stroke_color(self, c: Color) -> None:
        self.fgcolor = c
        self._cmd_history.append((self._id, "fgcolor", c.to_hex()))

    def line(
        self,
        x0: float | int,
        y0: float | int,
        x1: float | int,
        y1: float | int,
        color: Color | None = None,
    ) -> DrawingObject:
        if color is None:
            color = self.fgcolor
        args = (
            "line",
            x0,
            y0,
            x1,
            y1,
            color.to_hex(),
        )
        self._cmd_history.append((self._id, "obj", self._next_objid, args))
        obj = DrawingObject(self, self._next_objid, args)
        self._next_objid += 1
        return obj

    def circle(
        self,
        x: float | int,
        y: float | int,
        radius: float | int,
        border: Color | None = None,
        fill: Color | None = None,
        angle: float | int = 0,
    ) -> DrawingObject:
        if border is None:
            border = self.fgcolor
        if fill is None:
            fill = Colors.Transparent
        args = (
            "circle",
            x,
            y,
            radius,
            border.to_hex(),
            fill.to_hex(),
            angle,
        )
        self._cmd_history.append((self._id, "obj", self._next_objid, args))
        obj = DrawingObject(self, self._next_objid, args)
        self._next_objid += 1
        return obj

    def rectangle(
        self,
        left: float | int,
        top: float | int,
        width: float | int,
        height: float | int,
        border: Color | None = None,
        fill: Color | None = None,
        angle: float | int = 0,
    ) -> DrawingObject:
        if border is None:
            border = self.fgcolor
        if fill is None:
            fill = Colors.Transparent
        args = (
            "rect",
            left,
            top,
            width,
            height,
            border.to_hex(),
            fill.to_hex(),
            angle,
        )
        self._cmd_history.append((self._id, "obj", self._next_objid, args))
        obj = DrawingObject(self, self._next_objid, args)
        self._next_objid += 1
        return obj

    def triangle(
        self,
        left: float | int,
        top: float | int,
        width: float | int,
        height: float | int,
        border: Color | None = None,
        fill: Color | None = None,
        angle: float | int = 0,
    ) -> DrawingObject:
        if border is None:
            border = self.fgcolor
        if fill is None:
            fill = Colors.Transparent
        args = (
            "triangle",
            left,
            top,
            width,
            height,
            border.to_hex(),
            fill.to_hex(),
            angle,
        )
        self._cmd_history.append((self._id, "obj", self._next_objid, args))
        obj = DrawingObject(self, self._next_objid, args)
        self._next_objid += 1
        return obj


__all__ = [
    "Canvas",
]

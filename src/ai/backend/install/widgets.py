from __future__ import annotations

import asyncio
from pathlib import Path

from rich.console import ConsoleRenderable
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.validation import ValidationResult, Validator
from textual.widget import Widget
from textual.widgets import Button, Input, Label, RichLog, Static


class DirectoryPathValidator(Validator):
    def validate(self, value: str) -> ValidationResult:
        if Path(value).is_dir():
            return self.success()
        else:
            return self.failure("The path is not a directory")


class SetupLog(RichLog):
    BINDINGS = [
        Binding("enter", "continue", show=False),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._continue = asyncio.Event()

    async def wait_continue(self) -> None:
        """
        Block until the user concludes the dialog.
        If the user cancels, the result will be None.
        """
        self.write(Text.from_markup("\nPress [bold]Enter[/] to continue...\n"))
        self._continue.clear()
        await self._continue.wait()

    async def action_continue(self) -> None:
        self._continue.set()


class InputDialog(Static):
    DEFAULT_CSS = """
    InputDialog {
        width: auto;
        min-width: 40;
        max-width: 78;
        height: auto;
        max-height: 13;
        background: $panel-lighten-1;
    }

    InputDialog > Label {
        width: 1fr;
        height: auto;
        min-height: 2;
        padding: 0 2;
        margin-top: 1;
        content-align: center middle;
    }

    InputDialog Input {
        width: 1fr;
        height: 3;
        margin: 0 1;
        padding: 1 2;
        border: wide $panel-lighten-1;
    }
    InputDialog Input:focus {
        border: wide $foreground;
    }
    InputDialog Horizontal {
        width: 1fr;
    }
    InputDialog Horizontal Button {
        width: 1fr;
    }
    """

    _value: str | None
    _can_focus_list: list[Widget]

    def __init__(
        self,
        label: str | ConsoleRenderable,
        initial_value: str = "",
        *,
        allow_cancel: bool = True,
        validator: Validator | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._label = label
        self._initial_value = initial_value
        self._concluded = asyncio.Event()
        self._allow_cancel = allow_cancel
        self._can_focus_list = []
        self._focus_save = None
        self._validator = validator

    def compose(self) -> ComposeResult:
        yield Label(self._label)
        yield Input(
            self._initial_value,
            validators=self._validator,
            id="input-text",
        )
        with Horizontal():
            yield Button("OK", id="button-ok", classes="primary")
            if self._allow_cancel:
                yield Button("Cancel", id="button-cancel")

    def on_mount(self, _) -> None:
        self._override_focus()
        self.query_one(Input).focus()

    async def wait(self) -> str | None:
        """
        Block until the user concludes the dialog.
        If the user cancels, the result will be None.
        """
        await self._concluded.wait()
        value = self._value
        self.remove()
        self._restore_focus()
        return value

    @on(Input.Submitted, "#input-text")
    @on(Button.Pressed, "#button-ok")
    def action_ok(self) -> None:
        self._value = self.query_one(Input).value
        self._concluded.set()

    @on(Button.Pressed, "#button-cancel")
    def action_cancel(self) -> None:
        self._value = None
        self._concluded.set()

    def _override_focus(self):
        self._focus_save = self.app.focused
        for widget in self.app.screen.focus_chain:
            self._can_focus_list.append(widget)
            widget.can_focus = False
        self.query_one("#input-text").can_focus = True
        for button in self.query(Button):
            button.can_focus = True

    def _restore_focus(self):
        while len(self._can_focus_list) > 0:
            self._can_focus_list.pop().can_focus = True
        if self._focus_save is not None:
            self.app.set_focus(self._focus_save)

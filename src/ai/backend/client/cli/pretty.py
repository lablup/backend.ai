from __future__ import annotations

import asyncio
import enum
import functools
import json
import sys
import textwrap
import traceback
from collections.abc import Sequence
from types import TracebackType
from typing import Optional, Self

from click import echo, style
from tqdm import tqdm

from ..exceptions import BackendAPIError

__all__ = (
    "PrintStatus",
    "print_pretty",
    "print_info",
    "print_wait",
    "print_done",
    "print_warn",
    "print_fail",
    "print_error",
    "show_warning",
)


class PrintStatus(enum.Enum):
    NONE = 0
    WAITING = 1
    DONE = 2
    FAILED = 3
    WARNING = 4


def bold(text: str) -> str:
    """
    Wraps the given text with bold enable/disable ANSI sequences.
    """
    return style(text, bold=True, reset=False) + style("", bold=False, reset=False)


def underline(text: str) -> str:
    return style(text, underline=True, reset=False) + style("", underline=False, reset=False)


def inverse(text: str) -> str:
    return style(text, reverse=True, reset=False) + style("", reverse=False, reset=False)


def italic(text: str) -> str:
    return "\x1b[3m" + text + "\x1b[23m"


def format_pretty(msg, status=PrintStatus.NONE, colored=True):
    if status == PrintStatus.NONE:
        indicator = style("\u2219", fg="bright_cyan", reset=False)
    elif status == PrintStatus.WAITING:
        indicator = style("\u22ef", fg="bright_yellow", reset=False)
    elif status == PrintStatus.DONE:
        indicator = style("\u2714", fg="bright_green", reset=False)
    elif status == PrintStatus.FAILED:
        indicator = style("\u2718", fg="bright_red", reset=False)
    elif status == PrintStatus.WARNING:
        indicator = style("\u2219", fg="yellow", reset=False)
    else:
        raise ValueError
    return style(indicator + textwrap.indent(msg, "  ")[1:], reset=True)


format_info = functools.partial(format_pretty, status=PrintStatus.NONE)
format_wait = functools.partial(format_pretty, status=PrintStatus.WAITING)
format_done = functools.partial(format_pretty, status=PrintStatus.DONE)
format_fail = functools.partial(format_pretty, status=PrintStatus.FAILED)
format_warn = functools.partial(format_pretty, status=PrintStatus.WARNING)


def print_pretty(msg, *, status=PrintStatus.NONE, file=None):
    if file is None:
        file = sys.stderr
    if status == PrintStatus.NONE:
        indicator = style("\u2219", fg="bright_cyan", reset=False)
    elif status == PrintStatus.WAITING:
        assert "\n" not in msg, "Waiting message must be a single line."
        indicator = style("\u22ef", fg="bright_yellow", reset=False)
    elif status == PrintStatus.DONE:
        indicator = style("\u2713", fg="bright_green", reset=False)
    elif status == PrintStatus.FAILED:
        indicator = style("\u2717", fg="bright_red", reset=False)
    elif status == PrintStatus.WARNING:
        indicator = style("\u2219", fg="yellow", reset=False)
    else:
        raise ValueError
    echo("\x1b[2K", nl=False, file=file)
    text = textwrap.indent(msg, "  ")
    text = style(indicator + text[1:], reset=True)
    echo("{0}\r".format(text), nl=False, file=file)
    file.flush()
    if status != PrintStatus.WAITING:
        echo("", file=file)


print_info = functools.partial(print_pretty, status=PrintStatus.NONE)
print_wait = functools.partial(print_pretty, status=PrintStatus.WAITING)
print_done = functools.partial(print_pretty, status=PrintStatus.DONE)
print_fail = functools.partial(print_pretty, status=PrintStatus.FAILED)
print_warn = functools.partial(print_pretty, status=PrintStatus.WARNING)


def _format_gql_path(items: Sequence[str | int]) -> str:
    pieces = []
    for item in items:
        match item:
            case int():
                pieces.append(f"[{item}]")
            case _:
                pieces.append(f".{str(item)}")
    return "".join(pieces)[1:]  # strip first dot


def format_error(exc: Exception):
    if isinstance(exc, BackendAPIError):
        yield "{0}: {1} {2}\n".format(exc.__class__.__name__, exc.status, exc.reason)
        yield "{0[title]}".format(exc.data)
        if exc.data["type"].endswith("/too-many-sessions-matched"):
            matches = exc.data["data"].get("matches", [])
            if matches:
                yield "\nCandidates (up to 10 recent entries):\n"
            for item in matches:
                yield f"- {item['id']} ({item['name']}, {item['status']})\n"
        elif exc.data["type"].endswith("/session-already-exists"):
            existing_session_id = exc.data["data"].get("existingSessionId", None)
            if existing_session_id is not None:
                yield f"\n- Existing session ID: {existing_session_id}"
        elif exc.data["type"].endswith("/invalid-api-params"):
            general_error_msg = exc.data.get("msg", None)
            if general_error_msg is not None:
                yield f"\n- {general_error_msg}"
            per_field_errors = exc.data.get("data", None)
            if per_field_errors:
                yield "\n"
                yield json.dumps(per_field_errors, indent=2)
        else:
            if exc.data["type"].endswith("/graphql-error"):
                yield "\n\u279c Message:\n"
                for err_item in exc.data.get("data", []):
                    yield f"{err_item['message']}"
                    if err_path := err_item.get("path"):
                        yield f" (path: {_format_gql_path(err_path)})"
                    yield "\n"
            else:
                other_details = exc.data.get("msg", None)
                if other_details:
                    yield "\n\u279c Message: "
                    yield str(other_details)
                other_data = exc.data.get("data", None)
                if other_data:
                    yield "\n\u279c Data: "
                    yield repr(other_data)
        agent_details = exc.data.get("agent-details", None)
        if agent_details is not None:
            yield "\n\u279c This is an agent-side error. "
            yield "Check the agent status or ask the administrator for help."
            agent_exc = agent_details.get("exception", None)
            if agent_exc is not None:
                yield "\n\u279c " + str(agent_exc)
            desc = agent_details.get("title", None)
            if desc is not None:
                yield "\n\u279c " + str(desc)
        content = exc.data.get("content", None)
        if content:
            yield "\n" + content
    else:
        args = exc.args if exc.args else [""]
        yield f"{exc.__class__.__name__}: {args[0]}\n"
        yield "\n".join(map(str, args[1:]))
        yield ("*** Traceback ***\n" + "".join(traceback.format_tb(exc.__traceback__)).strip())


def print_error(exc: Exception, *, file=None):
    if file is None:
        file = sys.stderr
    indicator = style("\u2718", fg="bright_red", reset=False)
    if file.isatty():
        echo("\x1b[2K", nl=False, file=file)
    text = "".join(format_error(exc))
    text = textwrap.indent(text, "  ")
    text = style(indicator + text[1:], reset=True)
    echo("{0}\r".format(text), nl=False, file=file)
    echo("", file=file)
    file.flush()


def show_warning(message, category, filename, lineno, file=None, line=None):
    echo(
        "{0}: {1}".format(
            style(str(category.__name__), fg="yellow", bold=True),
            style(str(message), fg="yellow"),
        ),
        file=file,
    )


class ProgressBarWithSpinner(tqdm):
    """
    A simple extension to tqdm adding a spinner.

    .. code-block::

       async with ProgressBarWithSpinner("Waiting...") as pbar:
           # The spinner starts here but no tqdm progress bar is displayed yet.
           await init_work()
           # When the user sets the 'total' attribute, the progress bar gets displayed.
           pbar.total = 10
           for i in range(10):
               await piece_of_work()
               pbar.update(1)
    """

    @staticmethod
    def alt_format_meter(
        n,
        total,
        elapsed,
        ncols=None,
        prefix="",
        ascii=False,
        unit="it",
        unit_scale=False,
        rate=None,
        bar_format=None,
        postfix=None,
        *args,
        **kwargs,
    ) -> str:
        # Return the prefix string only.
        return str(prefix) + str(postfix)

    def __init__(
        self,
        spinner_msg: str = "",
        spinner_delay: float = 0.14,
        unit: str = "it",
    ) -> None:
        self.spinner_msg = spinner_msg
        self.spinner_delay = spinner_delay
        prefix = style("", fg="bright_yellow", reset=False)
        if spinner_msg:
            initial_desc = f"{prefix}  {spinner_msg} "
        else:
            initial_desc = f"{prefix}  "
        self._orig_format_meter = self.format_meter
        super().__init__(
            total=float("inf"),
            unit=unit,
        )
        # Deactivate the progress bar display by default
        self.format_meter = self.alt_format_meter  # type: ignore
        self.set_description_str(initial_desc)
        self.set_postfix_str(style("", reset=True))

    async def spin(self) -> None:
        prefix = style("", fg="bright_yellow", reset=False)
        try:
            while True:
                for char in "|/-\\":
                    if self.spinner_msg:
                        self.set_description_str(f"{prefix}{char} {self.spinner_msg} ")
                    else:
                        self.set_description_str(f"{prefix}{char} ")
                    await asyncio.sleep(self.spinner_delay)
        except asyncio.CancelledError:
            pass

    @property
    def total(self) -> int | float | None:
        return self._total

    @total.setter
    def total(self, value: int | float) -> None:
        self._total = value
        # Reactivate the progress bar display when total is first set
        self.format_meter = self._orig_format_meter  # type: ignore

    async def __aenter__(self) -> Self:
        self.spinner_task = asyncio.create_task(self.spin())
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        if self.spinner_task is not None and not self.spinner_task.done():
            self.spinner_task.cancel()
            await self.spinner_task
        prefix = style("", fg="bright_green", reset=False)
        if self.spinner_msg:
            self.set_description_str(f"{prefix}✓ {self.spinner_msg}")
        else:
            self.set_description_str(f"{prefix}✓ ")
        self.close()
        return None

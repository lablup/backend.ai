import asyncio
import enum
import functools
import sys
import textwrap
import traceback
from typing import Sequence

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
            per_field_errors = exc.data.get("data", {})
            if isinstance(per_field_errors, dict):
                for k, v in per_field_errors.items():
                    yield f'\n- "{k}": {v}'
            else:
                yield f"\n- {per_field_errors}"
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


class Spinner:
    def __init__(self, msg: str, delay: float = 0.3):
        self.msg = msg
        self.task = None
        self.delay = delay

    async def __aenter__(self):
        self.run()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.stop()

    def run(self):
        self.task = asyncio.create_task(self.spin())

    async def spin(self):
        try:
            while True:
                for char in "|/-\\":
                    print_wait("{} {}".format(self.msg, char))
                    await asyncio.sleep(self.delay)
        except asyncio.CancelledError:
            pass

    async def stop(self):
        self.task.cancel()
        await self.task


class ProgressViewer:
    """

    A context manager that displays a spinner and a tqdm progress bar.

    It shows the spinner until it is switched explicitly to the tqdm progress bar.

    Usage:

    ```
    async with ProgressViewer("Waiting...") as viewer:
        for i in range(10):
            await asyncio.sleep(0.2)
        tqdm = await viewer.to_tqdm()
        tqdm.total = 10
        for i in range(10):
            await asyncio.sleep(0.2)
            tqdm.update(1)
    ```
    """

    def __init__(self, spinner_msg: str = "", delay: float = 0.3) -> None:
        self.spinner = Spinner(spinner_msg, delay)
        self.tqdm = None

    async def __aenter__(self):
        self.spinner.run()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.spinner.stop()
        if self.tqdm:
            self.tqdm.close()

    async def to_tqdm(self, unit: str = "it") -> tqdm:
        await self.spinner.stop()
        self.tqdm = tqdm(total=0, unit=unit)
        return self.tqdm

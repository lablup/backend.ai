import warnings
from collections.abc import Callable, Mapping
from functools import update_wrapper
from typing import Any, Concatenate, ParamSpec, TypeVar

import click
from click import get_current_context

from ai.backend.cli.types import CliContextInfo
from ai.backend.client.cli.types import CLIContext, OutputMode
from ai.backend.client.config import APIConfig, set_config
from ai.backend.client.output import get_output_handler


def set_client_config(info: Mapping[str, Any]) -> CLIContext:
    from .announcement import announce

    skip_sslcert_validation = info.get("skip_sslcert_validation", False)
    output = info.get("output", "console")
    config = APIConfig(
        skip_sslcert_validation=skip_sslcert_validation,
        announcement_handler=announce,
    )
    set_config(config)

    output_mode = OutputMode(output)
    cli_ctx = CLIContext(
        api_config=config,
        output_mode=output_mode,
    )
    cli_ctx.output = get_output_handler(cli_ctx, output_mode)

    from .pretty import show_warning

    warnings.showwarning = show_warning
    return cli_ctx


T = TypeVar("T")
P = ParamSpec("P")


def _override_output_mode(
    ctx: click.Context, _param: click.Parameter, value: str | None
) -> str | None:
    """Let a subcommand's own ``--output`` take precedence over the root-level one."""
    if value is not None:
        match ctx.find_root().obj:
            case CliContextInfo(info=info):
                info["output"] = value
    return value


# Accepts `--output` on the command itself, in addition to the root-level `--output`; the
# command-level value wins. Apply it next to `pass_ctx_obj`, which is what supplies the
# `CLIContext` the value is read through -- without that context the option does nothing.
#
# Do NOT apply it to a command that already declares its own `--output` (`admin export
# -o/--output PATH` names a destination file); the two would collide and Click would leave
# one of them dead in its long-option table with no error.
#
# It belongs on commands, never on groups: a group renders no result to format, while the
# root keeps its own `--output` because that one configures the whole invocation.
#
# Wearing it buys formatting of *error* output, which every `pass_ctx_obj` command gets.
# Whether the *result* is formatted depends on the command rendering through
# `ctx.output.print_*` rather than `print()`/`tabulate` -- 71 of the 154 do today, and
# converting the rest is #1925.
output_option = click.option(
    "--output",
    type=click.Choice([OutputMode.JSON.value, OutputMode.CONSOLE.value]),
    default=None,
    expose_value=False,
    callback=_override_output_mode,
    help="Set the output style of this command's result, overriding the root-level one.",
)


def pass_ctx_obj[**P, T](f: Callable[Concatenate[CLIContext, P], T]) -> Callable[P, T]:
    """
    Pass the :class:`CLIContext` as the first argument of the decorated command callback.

    Pair it with :data:`output_option` on commands that should accept ``--output``; that
    option reads the mode through the context this decorator supplies.
    """

    def new_func(*args: P.args, **kwargs: P.kwargs) -> T:
        obj = get_current_context().obj
        match obj:
            case CLIContext():
                inner = f(obj, *args, **kwargs)
            case CliContextInfo(info=info):
                inner = f(set_client_config(info), *args, **kwargs)
            case _:
                raise RuntimeError("Invalid Context from client command")
        return inner

    return update_wrapper(new_func, f)

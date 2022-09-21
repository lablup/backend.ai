import warnings
from functools import update_wrapper
from typing import Any, Callable, Mapping, TypeVar, cast

from click import get_current_context

from ai.backend.cli.types import CliContextInfo
from ai.backend.client.cli.types import CLIContext, OutputMode
from ai.backend.client.config import APIConfig, set_config
from ai.backend.client.output import get_output_handler


def set_client_config(info: Mapping) -> CLIContext:
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


F = TypeVar("F", bound=Callable[..., Any])


def pass_ctx_obj(f: F) -> F:
    def new_func(*args, **kwargs):
        obj = get_current_context().obj
        match obj:
            case CLIContext():
                inner = f(obj, *args, **kwargs)
            case CliContextInfo(info=info):
                inner = f(set_client_config(info), *args, **kwargs)
            case _:
                raise RuntimeError("Invalid Context from client command")
        return inner

    return update_wrapper(cast(F, new_func), f)

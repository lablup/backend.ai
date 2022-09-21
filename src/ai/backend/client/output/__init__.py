from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai.backend.client.cli.types import CLIContext, OutputMode

    from .types import BaseOutputHandler


def get_output_handler(cli_ctx: CLIContext, output_mode: OutputMode) -> BaseOutputHandler:
    from ai.backend.client.cli.types import OutputMode

    if output_mode == OutputMode.JSON:
        from .json import JsonOutputHandler

        return JsonOutputHandler(cli_ctx)
    elif output_mode == OutputMode.CONSOLE:
        from .console import ConsoleOutputHandler

        return ConsoleOutputHandler(cli_ctx)
    raise RuntimeError("Invalid output handler", output_mode)

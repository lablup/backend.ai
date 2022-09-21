from __future__ import annotations

from typing import Optional

import click


class CommaSeparatedChoice(click.Choice):
    def convert(
        self,
        value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> Optional[list[str]]:
        pieces = value.split(",")
        return [super(click.Choice, self).convert(piece, param, ctx) for piece in pieces]


class CustomUsageArgsCommand(click.Command):
    def __init__(self, *args, **kwargs) -> None:
        self._usage_args = kwargs.pop("usage_args")
        super().__init__(*args, **kwargs)

    def format_usage(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        if self._usage_args:
            formatter.write_usage(ctx.command_path, self._usage_args)
        else:
            super().format_usage(ctx, formatter)

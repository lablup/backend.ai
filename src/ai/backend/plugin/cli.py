from __future__ import annotations

import enum
import itertools
import json
import logging
from collections import defaultdict
from typing import Self

import click
import colorama
import tabulate
from colorama import Fore, Style

from ai.backend.common.logging import AbstractLogger, LocalLogger
from ai.backend.common.types import LogSeverity

from .entrypoint import (
    prepare_wheelhouse,
    scan_entrypoint_from_buildscript,
    scan_entrypoint_from_package_metadata,
    scan_entrypoint_from_plugin_checkouts,
)

log = logging.getLogger(__spec__.name)


class FormatOptions(enum.StrEnum):
    CONSOLE = "console"
    JSON = "json"


class CLIContext:
    _logger: AbstractLogger

    def __init__(self, log_level: LogSeverity) -> None:
        self.log_level = log_level

    def __enter__(self) -> Self:
        self._logger = LocalLogger({
            "level": self.log_level,
            "pkg-ns": {
                "": LogSeverity.WARNING,
                "ai.backend": self.log_level,
            },
        })
        self._logger.__enter__()
        return self

    def __exit__(self, *exc_info) -> None:
        self._logger.__exit__()


@click.group()
@click.option(
    "--debug",
    is_flag=True,
    help="Set the logging level to DEBUG",
)
@click.pass_context
def main(
    ctx: click.Context,
    debug: bool,
) -> None:
    """The root entrypoint for unified CLI of the plugin subsystem"""
    log_level = LogSeverity.DEBUG if debug else LogSeverity.INFO
    ctx.obj = ctx.with_resource(CLIContext(log_level))


@main.command()
@click.argument("group_name")
@click.option(
    "--format",
    type=click.Choice([*FormatOptions]),
    default=FormatOptions.CONSOLE,
    show_default=True,
    help="Set the output format.",
)
def scan(
    group_name: str,
    format: FormatOptions,
) -> None:
    sources: dict[str, set[str]] = defaultdict(set)
    rows = []

    prepare_wheelhouse()
    for source, entrypoint in itertools.chain(
        (("buildscript", item) for item in scan_entrypoint_from_buildscript(group_name)),
        (("plugin-checkout", item) for item in scan_entrypoint_from_plugin_checkouts(group_name)),
        (("python-package", item) for item in scan_entrypoint_from_package_metadata(group_name)),
    ):
        sources[entrypoint.name].add(source)
        rows.append((source, entrypoint.name, entrypoint.module))
    rows.sort(key=lambda row: (row[2], row[1], row[0]))

    match format:
        case FormatOptions.CONSOLE:
            if not rows:
                print(f"No plugins found for the entrypoint {group_name!r}")
                return
            colorama.init(autoreset=True)
            ITALIC = colorama.ansi.code_to_chars(3)
            STRIKETHR = colorama.ansi.code_to_chars(9)
            src_style = {
                "buildscript": Fore.LIGHTYELLOW_EX,
                "plugin-checkout": Fore.LIGHTGREEN_EX,
                "python-package": Fore.LIGHTBLUE_EX,
            }
            display_headers = (
                f"{ITALIC}Source{Style.RESET_ALL}",
                f"{ITALIC}Name{Style.RESET_ALL}",
                f"{ITALIC}Module Path{Style.RESET_ALL}",
                f"{ITALIC}Note{Style.RESET_ALL}",
            )
            display_rows = []
            duplicates = set()
            warnings: dict[str, str] = dict()
            for source, name, module_path in rows:
                note = ""
                name_style = Style.BRIGHT
                has_plugin_checkout = "plugin-checkout" in sources[name]
                duplication_threshold = 2 if has_plugin_checkout else 1
                if len(sources[name]) > duplication_threshold:
                    duplicates.add(name)
                    name_style = Fore.RED + Style.BRIGHT
                if source == "plugin-checkout":
                    name_style = Style.DIM + STRIKETHR
                    if "python-package" in sources[name]:
                        note = "Loaded via the python-package source"
                    else:
                        note = "Ignored when loading plugins unless installed as editable"
                display_rows.append((
                    f"{src_style[source]}{source}{Style.RESET_ALL}",
                    f"{name_style}{name}{Style.RESET_ALL}",
                    module_path,
                    note,
                ))
            print(tabulate.tabulate(display_rows, display_headers))
            for name, msg in warnings.items():
                print(msg)
            if duplicates:
                duplicate_list = ", ".join(duplicates)
                print(
                    f"\n{Fore.LIGHTRED_EX}\u26a0 Detected duplicated entrypoint(s): {Style.BRIGHT}{duplicate_list}{Style.RESET_ALL}"
                )
                if "accelerator" in group_name:
                    print(
                        f"{Fore.LIGHTRED_EX}  You should check [agent].allow-compute-plugins in "
                        f"agent.toml to activate only one accelerator implementation for each name.{Style.RESET_ALL}"
                    )
        case FormatOptions.JSON:
            output_rows = []
            for source, name, module_path in rows:
                output_rows.append({
                    "source": source,
                    "name": name,
                    "module_path": module_path,
                })
            print(json.dumps(output_rows, indent=2))

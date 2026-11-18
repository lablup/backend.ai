from __future__ import annotations

import enum
import itertools
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

import click
import colorama
import tabulate
from colorama import Fore, Style

if TYPE_CHECKING:
    from ai.backend.logging import AbstractLogger
    from ai.backend.logging.types import LogLevel

log = logging.getLogger(__spec__.name)

# LogLevel values for click.Choice - avoid importing ai.backend.logging at module level
_LOG_LEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE", "NOTSET"]

_DAEMONS_LOADING_WHEELS = ("manager", "agent", "storage-proxy")


class FormatOptions(enum.StrEnum):
    CONSOLE = "console"
    JSON = "json"


class CLIContext:
    _logger: AbstractLogger

    def __init__(self, log_level: LogLevel) -> None:
        self.log_level = log_level

    def __enter__(self) -> Self:
        from ai.backend.logging import LocalLogger

        self._logger = LocalLogger(log_level=self.log_level)
        self._logger.__enter__()
        return self

    def __exit__(self, *exc_info: Any) -> None:
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
    from ai.backend.logging.types import LogLevel

    log_level = LogLevel.DEBUG if debug else LogLevel.NOTSET
    ctx.obj = ctx.with_resource(CLIContext(log_level))


def _find_daemon_config_paths() -> set[Path]:
    from ai.backend.common.config import ConfigurationError, find_config_file

    daemon_config_paths: set[Path] = set()
    for daemon_name in _DAEMONS_LOADING_WHEELS:
        try:
            daemon_config_paths.add(find_config_file(daemon_name))
        except ConfigurationError:
            # A node runs only some of the daemons.
            continue
    return daemon_config_paths


def _find_allowed_wheelhouse_paths(config_paths: set[Path]) -> set[Path]:
    import tomli

    from ai.backend.common.configs.wheelhouse import WheelhouseConfig

    wheelhouse_paths: set[Path] = set()
    for config_path in config_paths:
        try:
            raw_config = tomli.loads(config_path.read_text())
        except (OSError, tomli.TOMLDecodeError) as e:
            click.echo(f"Warning: Could not read [wheelhouse] from {config_path}: {e}", err=True)
            continue
        wheelhouse_config = WheelhouseConfig.model_validate(raw_config.get("wheelhouse", {}))
        if wheelhouse_config.allow:
            wheelhouse_paths.add(wheelhouse_config.path.resolve())
    return wheelhouse_paths


@main.command()
@click.argument("group_name")
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help=(
        "The config file whose [wheelhouse] section to read. "
        "(default: the manager, agent and storage-proxy config files)"
    ),
)
@click.option(
    "--format",
    type=click.Choice([*FormatOptions]),
    default=FormatOptions.CONSOLE,
    show_default=True,
    help="Set the output format.",
)
def scan(
    group_name: str,
    config_path: Path | None,
    format: FormatOptions,
) -> None:
    from .entrypoint import (
        scan_entrypoint_from_buildscript,
        scan_entrypoint_from_package_metadata,
        scan_entrypoint_from_plugin_checkouts,
        scan_entrypoint_from_wheelhouse,
    )

    sources: dict[str, set[str]] = defaultdict(set)
    rows = []
    config_paths_to_read = {config_path} if config_path is not None else _find_daemon_config_paths()

    for source, entrypoint in itertools.chain(
        (("buildscript", item) for item in scan_entrypoint_from_buildscript(group_name)),
        (("plugin-checkout", item) for item in scan_entrypoint_from_plugin_checkouts(group_name)),
        (("python-package", item) for item in scan_entrypoint_from_package_metadata(group_name)),
        (
            ("wheelhouse", item)
            for wheelhouse_path in _find_allowed_wheelhouse_paths(config_paths_to_read)
            for item in scan_entrypoint_from_wheelhouse(group_name, wheelhouse_path)
        ),
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
                "wheelhouse": Fore.LIGHTMAGENTA_EX,
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

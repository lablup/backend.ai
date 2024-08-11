from __future__ import annotations

import enum
import itertools
import json
from collections import defaultdict

import click
import colorama
import tabulate
from colorama import Fore, Style

from .entrypoint import (
    prepare_external_package_entrypoints,
    scan_entrypoint_from_buildscript,
    scan_entrypoint_from_package_metadata,
    scan_entrypoint_from_plugin_checkouts,
)


class FormatOptions(enum.StrEnum):
    CONSOLE = "console"
    JSON = "json"


@click.group()
def main():
    """The root entrypoint for unified CLI of the plugin subsystem"""
    pass


@main.command()
@click.argument("group_name")
@click.option(
    "--format",
    type=click.Choice([*FormatOptions]),
    default=FormatOptions.CONSOLE,
    show_default=True,
    help="Set the output format.",
)
def scan(group_name: str, format: FormatOptions) -> None:
    sources: dict[str, set[str]] = defaultdict(set)
    rows = []

    prepare_external_package_entrypoints(group_name)
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
            )
            display_rows = []
            duplicates = set()
            warnings: dict[str, str] = dict()
            for source, name, module_path in rows:
                name_style = Style.BRIGHT
                if len(sources[name]) > 1:
                    if sources[name] != {"plugin-checkout", "python-package"}:
                        duplicates.add(name)
                        name_style = Fore.RED + Style.BRIGHT
                if "plugin-checkout" in sources[name] and "python-package" in sources[name]:
                    if source == "plugin-checkout":
                        name_style = Style.DIM + STRIKETHR
                elif "plugin-checkout" in sources[name] and "python-package" not in sources[name]:
                    if source == "plugin-checkout":
                        warnings[name] = (
                            f"\n{Fore.LIGHTRED_EX}\u26a0 {Style.BRIGHT}{name}{Style.NORMAL} ({source}) is detected in the plugins directory "
                            f"but will not work until installed as editable.{Style.RESET_ALL}"
                        )
                display_rows.append((
                    f"{src_style[source]}{source}{Style.RESET_ALL}",
                    f"{name_style}{name}{Style.RESET_ALL}",
                    module_path,
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
                        f"agent.toml to activate only one accelerator implementation.{Style.RESET_ALL}"
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

import enum
import itertools
import json
from collections import defaultdict

import click
import colorama
import tabulate
from colorama import Fore, Style

from .entrypoint import (
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
    duplicate_count: dict[str, int] = defaultdict(int)
    rows = []
    for source, entrypoint in itertools.chain(
        (("buildscript", item) for item in scan_entrypoint_from_buildscript(group_name)),
        (("plugin-checkout", item) for item in scan_entrypoint_from_plugin_checkouts(group_name)),
        (("python-package", item) for item in scan_entrypoint_from_package_metadata(group_name)),
    ):
        duplicate_count[entrypoint.name] += 1
        rows.append((source, entrypoint.name, entrypoint.module))
    rows.sort(key=lambda row: (row[2], row[1], row[0]))
    match format:
        case FormatOptions.CONSOLE:
            if not rows:
                print(f"No plugins found for the entrypoint {group_name!r}")
                return
            colorama.init(autoreset=True)
            ITALIC = colorama.ansi.code_to_chars(3)
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
            has_duplicate = False
            for source, name, module_path in rows:
                name_style = Style.BRIGHT
                if duplicate_count[name] > 1:
                    has_duplicate = True
                    name_style = Fore.RED + Style.BRIGHT
                display_rows.append((
                    f"{src_style[source]}{source}{Style.RESET_ALL}",
                    f"{name_style}{name}{Style.RESET_ALL}",
                    module_path,
                ))
            print(tabulate.tabulate(display_rows, display_headers))
            if has_duplicate:
                print(f"\n💥 {Fore.LIGHTRED_EX}Detected duplicated entrypoint(s)!{Style.RESET_ALL}")
        case FormatOptions.JSON:
            output_rows = []
            for source, name, module_path in rows:
                output_rows.append({
                    "source": source,
                    "name": name,
                    "module_path": module_path,
                })
            print(json.dumps(output_rows, indent=2))

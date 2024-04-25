import itertools
from collections import defaultdict

import click
import colorama
import tabulate
from colorama import Fore, Style

from ai.backend.plugin.entrypoint import (
    scan_entrypoint_from_buildscript,
    scan_entrypoint_from_package_metadata,
    scan_entrypoint_from_plugin_checkouts,
)


@click.group()
def main():
    """The root entrypoint for unified CLI of the plugin subsystem"""
    pass


@main.command()
@click.argument("group_name")
def scan(group_name: str) -> None:
    colorama.init(autoreset=True)
    ITALIC = "\x1b[3m"
    duplicate_count: dict[str, int] = defaultdict(int)
    src_style = {
        "buildscript": Fore.LIGHTYELLOW_EX,
        "plugin-checkout": Fore.LIGHTGREEN_EX,
        "python-package": Fore.LIGHTBLUE_EX,
    }
    rows = []
    headers = (
        f"{ITALIC}Source{Style.RESET_ALL}",
        f"{ITALIC}Name{Style.RESET_ALL}",
        f"{ITALIC}Module Path{Style.RESET_ALL}",
    )
    for source, entrypoint in itertools.chain(
        (("buildscript", item) for item in scan_entrypoint_from_buildscript(group_name)),
        (("plugin-checkout", item) for item in scan_entrypoint_from_plugin_checkouts(group_name)),
        (("python-package", item) for item in scan_entrypoint_from_package_metadata(group_name)),
    ):
        duplicate_count[entrypoint.name] += 1
        rows.append((source, entrypoint.name, entrypoint.module))
    if not rows:
        print(f"No plugins found for the entrypoint {group_name!r}")
        return
    rows.sort(key=lambda row: (row[2], row[1], row[0]))
    display_rows = []
    for source, name, module_path in rows:
        name_style = Style.BRIGHT
        if duplicate_count[name] > 1:
            name_style = Fore.RED + Style.BRIGHT
        display_rows.append((
            f"{src_style[source]}{source}{Style.RESET_ALL}",
            f"{name_style}{name}{Style.RESET_ALL}",
            module_path,
        ))
    print(tabulate.tabulate(display_rows, headers))
    if duplicate_count:
        print(f"\n💥 {Fore.LIGHTRED_EX}Detected duplicated entrypoint(s)!{Style.RESET_ALL}")

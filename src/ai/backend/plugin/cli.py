from collections import defaultdict

import click
import tabulate

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
    duplicate_count: dict[str, int] = defaultdict(int)
    rows = []
    headers = ("Source", "Name", "Module Path")
    for entrypoint in scan_entrypoint_from_buildscript(group_name):
        duplicate_count[entrypoint.name] += 1
        rows.append(("buildscript", entrypoint.name, entrypoint.module))
    for entrypoint in scan_entrypoint_from_plugin_checkouts(group_name):
        duplicate_count[entrypoint.name] += 1
        rows.append(("plugin-checkout", entrypoint.name, entrypoint.module))
    for entrypoint in scan_entrypoint_from_package_metadata(group_name):
        duplicate_count[entrypoint.name] += 1
        rows.append(("python-package", entrypoint.name, entrypoint.module))
    if not rows:
        print(f"No plugins found for the entrypoint {group_name!r}")
        return
    rows.sort(key=lambda row: (row[2], row[1], row[0]))
    print(tabulate.tabulate(rows, headers))
    for name, count in duplicate_count.items():
        if count > 1:
            print(f"duplication detected for {name} ({count})")

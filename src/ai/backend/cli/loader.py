import logging

import click

from ai.backend.plugin.entrypoint import scan_entrypoints

from .main import main

log = logging.getLogger(__spec__.name)


def load_entry_points(
    allowlist: set[str] | None = None,
    blocklist: set[str] | None = None,
) -> click.Group:
    """Register every installed command, groups before the subcommands that extend them.
    A subcommand whose group is not installed is skipped instead of failing the whole CLI.
    """
    entry_prefix = "backendai_cli_v10"
    subcommands = []
    for entrypoint in scan_entrypoints(entry_prefix, allowlist=allowlist, blocklist=blocklist):
        if entrypoint.name == "_":
            cmd_group: click.Group = entrypoint.load()
            for name, cmd in cmd_group.commands.items():
                main.add_command(cmd, name=name)
            continue
        prefix, _, subprefix = entrypoint.name.partition(".")
        if subprefix:
            subcommands.append((entrypoint, prefix, subprefix))
            continue
        try:
            main.add_command(entrypoint.load(), name=prefix)
        except ImportError:
            log.exception("Failed to import %r (%s)", entrypoint, prefix)
    for entrypoint, prefix, subprefix in subcommands:
        parent = main.commands.get(prefix)
        if not isinstance(parent, click.Group):
            log.warning("Skipping %r: its command group %r is not installed", entrypoint, prefix)
            continue
        try:
            parent.add_command(entrypoint.load(), name=subprefix)
        except ImportError:
            log.exception("Failed to import %r (%s)", entrypoint, prefix)
    return main

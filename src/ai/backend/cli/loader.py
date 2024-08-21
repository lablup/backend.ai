import logging
from typing import Optional

import click  # noqa: E402

from ai.backend.plugin.entrypoint import scan_entrypoints

from .main import main  # noqa: E402

log = logging.getLogger(__spec__.name)


def load_entry_points(
    allowlist: Optional[set[str]] = None,
    blocklist: Optional[set[str]] = None,
) -> click.Group:
    entry_prefix = "backendai_cli_v10"
    for entrypoint in scan_entrypoints(entry_prefix, allowlist=allowlist, blocklist=blocklist):
        if entrypoint.name == "_":
            cmd_group: click.Group = entrypoint.load()
            for name, cmd in cmd_group.commands.items():
                main.add_command(cmd, name=name)
        else:
            prefix, _, subprefix = entrypoint.name.partition(".")
            try:
                if not subprefix:
                    subcmd = entrypoint.load()
                    main.add_command(subcmd, name=prefix)
                else:
                    subcmd = entrypoint.load()
                    main.commands[prefix].add_command(subcmd, name=subprefix)  # type: ignore
            except ImportError:
                log.warning("Failed to import %r (%s)", entrypoint, prefix)
    return main

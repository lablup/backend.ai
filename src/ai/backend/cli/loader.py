import click            # noqa: E402

from ai.backend.plugin.entrypoint import scan_entrypoints

from .main import main  # noqa: E402


def load_entry_points() -> click.Group:
    entry_prefix = 'backendai_cli_v10'
    for entrypoint in scan_entrypoints(entry_prefix):
        if entrypoint.name == "_":
            cmd_group = entrypoint.load()
            return cmd_group
        else:
            prefix, _, subprefix = entrypoint.name.partition(".")
            if not subprefix:
                subcmd = entrypoint.load()
                main.add_command(subcmd, name=prefix)
            else:
                subcmd = entrypoint.load()
                main.commands[prefix].add_command(subcmd, name=subprefix)  # type: ignore
    return main

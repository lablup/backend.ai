import logging
import os
from pathlib import Path

import click

from ai.backend.common.logging import BraceStyleAdapter, Logger

from .abc import AbstractVolume
from .config import load_local_config

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


def check_latest(volume: AbstractVolume):
    version_path = volume.mount_path / "version.txt"
    if version_path.exists():
        version = int(version_path.read_text())
    else:
        version = 2

    match version:
        case 2:
            # already the latest version
            log.warning("{}: Detected an old vfolder structure (v{})", volume.mount_path, version)
        case 3:
            # already the latest version
            pass


def migrate(volume):
    pass


def upgrade(local_config):
    log.info("TODO: implement")


@click.command()
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=Path,
    default=None,
    help="The config file path. "
    "(default: ./storage-proxy.toml and /etc/backend.ai/storage-proxy.toml)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="This option will soon change to --log-level TEXT option.",
)
def main(config_path: Path, debug: bool) -> None:
    local_config = load_local_config(config_path, debug=debug)
    ipc_base_path = local_config["storage-proxy"]["ipc-base-path"]
    log_sockpath = Path(
        ipc_base_path / f"storage-proxy-logger-{os.getpid()}.sock",
    )
    log_sockpath.parent.mkdir(parents=True, exist_ok=True)
    log_endpoint = f"ipc://{log_sockpath}"
    local_config["logging"]["endpoint"] = log_endpoint
    logger = Logger(
        local_config["logging"],
        is_master=True,
        log_endpoint=log_endpoint,
    )
    with logger:
        upgrade(local_config)


if __name__ == "__main__":
    main()

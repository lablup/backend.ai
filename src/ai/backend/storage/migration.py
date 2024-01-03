import asyncio
import csv
import enum
import logging
import os
import re
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any, AsyncIterator, Iterator, Optional, TypedDict
from uuid import UUID

import aiofiles
import asyncpg
import click
import more_itertools
import tqdm
import yarl

from ai.backend.common.config import redis_config_iv
from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.common.events import (
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.logging import BraceStyleAdapter, Logger

from .abc import CAP_FAST_SIZE, AbstractVolume
from .config import load_local_config, load_shared_config
from .context import EVENT_DISPATCHER_CONSUMER_GROUP, RootContext
from .types import VFolderID

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@dataclass
class VolumeUpgradeInfo:
    orig_version: int
    target_version: int
    volume: AbstractVolume


class MigrationFolderInfo(TypedDict):
    volume_id: str
    folder_id: UUID
    quota_scope_id: str
    src_path: Path
    dst_path: Path
    current_size: Optional[int]
    old_quota: Optional[int]


class VFolderMigrationStatus(enum.StrEnum):
    PENDING = "pending"
    FAILED = "failed"
    COMPLETE = "complete"


async def check_latest(ctx: RootContext) -> list[VolumeUpgradeInfo]:
    volumes_to_upgrade: list[VolumeUpgradeInfo] = []
    volume_infos = ctx.list_volumes()
    for name, info in volume_infos.items():
        async with ctx.get_volume(name) as volume:
            version_path = volume.mount_path / "version.txt"
            if version_path.exists():
                version = int(version_path.read_text().strip())
            else:
                version = 2
            match version:
                case 2:
                    log.warning(
                        "{}: Detected an old vfolder structure (v{})",
                        volume.mount_path,
                        version,
                    )
                    volumes_to_upgrade.append(VolumeUpgradeInfo(2, 3, volume))
                case 3:
                    # already the latest version
                    pass
    return volumes_to_upgrade


def path_to_uuid(p: Path) -> UUID:
    return UUID(f"{p.parent.parent.name}{p.parent.name}{p.name}")


@actxmgr
async def connect_database(dsn: str) -> AsyncIterator[asyncpg.Connection]:
    db_dsn = yarl.URL(dsn).with_scheme("postgres")
    conn = await asyncpg.connect(dsn=str(db_dsn))
    yield conn
    await conn.close()


async def upgrade_2_to_3(
    ctx: RootContext,
    volume: AbstractVolume,
    outfile: str,
    report_path: Optional[Path] = None,
    force_scan_folder_size: bool = False,
) -> None:
    assert ctx.dsn is not None
    rx_two_digits_hex = re.compile(r"^[a-f0-9]{2}$")
    rx_rest_digits_hex = re.compile(r"^[a-f0-9]{28}$")
    log.info("upgrading {} ...", volume.mount_path)
    volume_id = os.fsdecode(volume.mount_path)
    scan_folder_size = force_scan_folder_size or (CAP_FAST_SIZE in await volume.get_capabilities())

    def scan_vfolders(root: Path, *, depth: int = 0) -> Iterator[Path]:
        for p in root.iterdir():
            if depth < 2:
                if p.is_dir() and rx_two_digits_hex.search(p.name):
                    yield from scan_vfolders(p, depth=depth + 1)
            else:
                if p.is_dir() and rx_rest_digits_hex.search(p.name):
                    yield p

    targets = [*scan_vfolders(volume.mount_path)]
    created_quota_scopes: set[str] = set()
    migration_informations: list[MigrationFolderInfo] = []
    with tqdm.tqdm(total=len(targets)) as progbar:
        for target_chunk in more_itertools.ichunked(targets, 10):
            folder_ids: list[UUID] = []
            old_quota_map: dict[UUID, Optional[int]] = {}
            quota_scope_map: dict[UUID, str] = {}
            async with connect_database(ctx.dsn) as conn:
                for target in target_chunk:
                    folder_id = path_to_uuid(target)
                    folder_ids.append(folder_id)
                rows = await conn.fetch(
                    """\
                    SELECT "id", "quota_scope_id", "max_size" FROM vfolders
                    WHERE "id" = ANY($1);
                    """,
                    folder_ids,
                )
                for row in rows:
                    old_quota_map[row["id"]] = (
                        row["max_size"] * (2**20) if row["max_size"] else None
                    )
                    quota_scope_map[row["id"]] = row["quota_scope_id"]

                log.info("checking {} ...".format(", ".join(map(str, folder_ids))))

            for folder_id in folder_ids:
                try:
                    quota_scope_id = quota_scope_map[folder_id]
                except KeyError:
                    continue
                progbar.set_description(
                    "inspecting contents of vfolder {}".format(
                        folder_id,
                    )
                )
                orig_vfid = VFolderID(None, folder_id)
                dst_vfid = VFolderID(quota_scope_id, folder_id)
                try:
                    if scan_folder_size:
                        current_size = int(
                            await volume.fsop_model.scan_tree_size(
                                volume.mangle_vfpath(orig_vfid),
                            )
                        )
                    else:
                        current_size = None
                    if quota_scope_id not in created_quota_scopes:
                        created_quota_scopes.add(quota_scope_id)
                    migration_informations.append({
                        "volume_id": volume_id,
                        "folder_id": folder_id,
                        "quota_scope_id": quota_scope_id,
                        "src_path": volume.mangle_vfpath(orig_vfid),
                        "dst_path": volume.mangle_vfpath(dst_vfid),
                        "current_size": current_size,
                        "old_quota": old_quota_map[folder_id],
                    })
                except Exception:
                    log.exception("error during migration of vfolder {}", folder_id)
                finally:
                    progbar.update(1)

    script = (
        "#! /bin/sh\n",
        *[f"mkdir -p {m['dst_path'].parent}\n" for m in migration_informations],
        *[f"mv {m['src_path']} {m['dst_path']}\n" for m in migration_informations],
        f"echo 3 > {volume_id}/version.txt\n",
    )
    if outfile == "-":
        print("".join(script))
    else:
        file_suffix = str(volume.mount_path).split("/")[-1]
        async with aiofiles.open(f"{outfile}.{file_suffix}", "w") as fw:
            await fw.writelines(script)
    if report_path:
        in_memory_file = StringIO()
        fieldnames = [
            "volume_id",
            "folder_id",
            "quota_scope_id",
            "current_size",
            "old_quota",
            "src_path",
            "dst_path",
        ]
        writer = csv.DictWriter(in_memory_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(migration_informations)

        async with aiofiles.open(report_path, "w") as csvfile:
            await csvfile.write(in_memory_file.getvalue())


upgrade_handlers = {
    3: upgrade_2_to_3,
}


async def check_and_upgrade(
    local_config: dict[str, Any],
    dsn: str,
    outfile: str,
    report_path: Optional[Path] = None,
    force_scan_folder_size: bool = False,
):
    etcd = load_shared_config(local_config)
    redis_config = redis_config_iv.check(
        await etcd.get_prefix("config/redis"),
    )
    event_producer = await EventProducer.new(
        redis_config,
        db=REDIS_STREAM_DB,
        log_events=local_config["debug"]["log-events"],
    )
    event_dispatcher = await EventDispatcher.new(
        redis_config,
        db=REDIS_STREAM_DB,
        log_events=local_config["debug"]["log-events"],
        node_id=local_config["storage-proxy"]["node-id"],
        consumer_group=EVENT_DISPATCHER_CONSUMER_GROUP,
    )
    ctx = RootContext(
        pid=os.getpid(),
        pidx=0,
        node_id=local_config["storage-proxy"]["node-id"],
        local_config=local_config,
        etcd=etcd,
        dsn=dsn,
        event_producer=event_producer,
        event_dispatcher=event_dispatcher,
        watcher=None,
    )

    async with ctx:
        volumes_to_upgrade = await check_latest(ctx)
        for upgrade_info in volumes_to_upgrade:
            handler = upgrade_handlers[upgrade_info.target_version]
            await handler(
                ctx,
                upgrade_info.volume,
                outfile,
                report_path=report_path,
                force_scan_folder_size=force_scan_folder_size,
            )


@click.command()
@click.argument("outfile")
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=Path,
    default=None,
    help=(
        "The config file path. "
        "[default: ./storage-proxy.toml, ~/.config/backend.ai/storage-proxy.toml, "
        "/etc/backend.ai/storage-proxy.toml (uses the first found one)]"
    ),
)
@click.option(
    "--dsn",
    type=str,
    default="postgres://postgres:develove@localhost:8101/backend",
    help="The DSN of the database connection.",
    show_default=True,
)
@click.option(
    "--report-path",
    "--report",
    type=Path,
    default=None,
    help=(
        "If specified, this program creates a text file which contains information about migrated"
        " folders. Generated report file includes ID of the vFolder, along with its current"
        " occupied size and quota set (both in bytes). Calculating size of the folder without any"
        " help from the storage backend takes so much time, and thus disabled by default. Specify"
        " --force-scan-folder-size flag to override this behavior."
    ),
)
@click.option(
    "--force-scan-folder-size",
    is_flag=True,
    help=(
        "Also scan size of the folder residing in FSOp solution without fast folder size scan"
        " (CAP_FAST_SIZE) capability."
        "WARNING: Enabling this option can slow down whole total migration process a lot!"
    ),
)
@click.option(
    "--debug",
    is_flag=True,
    help="This option will soon change to --log-level TEXT option.",
)
def main(
    outfile: str,
    config_path: Optional[Path],
    dsn: str,
    report_path: Optional[Path],
    force_scan_folder_size: bool,
    debug: bool,
) -> None:
    """
    Print migration script to OUTFILE.
    Pass - as OUTFILE to print results to STDOUT.
    """
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
        asyncio.run(
            check_and_upgrade(
                local_config,
                dsn,
                outfile,
                report_path=report_path,
                force_scan_folder_size=force_scan_folder_size,
            )
        )


if __name__ == "__main__":
    main()

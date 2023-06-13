import asyncio
import csv
import enum
import logging
import os
import re
import traceback
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any, AsyncIterator, Iterator, Optional
from uuid import UUID

import aiofiles
import asyncpg
import click
import more_itertools
import tqdm
import yarl

from ai.backend.common.logging import BraceStyleAdapter, Logger

from .abc import CAP_FAST_SIZE, AbstractVolume
from .config import load_local_config, load_shared_config
from .context import Context
from .types import VFolderID

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@dataclass
class VolumeUpgradeInfo:
    orig_version: int
    target_version: int
    volume: AbstractVolume


class VFolderMigrationStatus(enum.StrEnum):
    PENDING = "pending"
    FAILED = "failed"
    COMPLETE = "complete"


async def check_latest(ctx: Context) -> list[VolumeUpgradeInfo]:
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
    ctx: Context,
    volume: AbstractVolume,
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

    async with connect_database(ctx.dsn) as conn:
        await conn.execute("""\
            CREATE TABLE IF NOT EXISTS vfolder_migration_v3 (
                volume_id VARCHAR(1024),
                folder_id UUID,
                status VARCHAR(16),
                current_size INTEGER DEFAULT NULL,
                old_quota INTEGER DEFAULT NULL,
                log TEXT DEFAULT NULL,
                PRIMARY KEY (volume_id, folder_id)
            );
            """)

    targets = [*scan_vfolders(volume.mount_path)]
    created_quota_scopes: set[str] = set()
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
                    old_quota_map[row["id"]] = row["max_size"]
                    quota_scope_map[row["id"]] = row["quota_scope_id"]

                progbar.write("checking {} ...".format(", ".join(map(str, folder_ids))))

                async with conn.transaction():
                    await conn.executemany(
                        """\
                        INSERT INTO vfolder_migration_v3
                        (volume_id, folder_id, status)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (volume_id, folder_id)
                        DO NOTHING;
                        """,
                        [
                            (
                                volume_id,
                                folder_id,
                                VFolderMigrationStatus.PENDING,
                            )
                            for folder_id in folder_ids
                        ],
                    )

                rows = await conn.fetch(
                    """\
                    SELECT folder_id FROM vfolder_migration_v3
                    WHERE volume_id = $1
                      AND folder_id = ANY($2)
                      AND status = $3;
                    """,
                    volume_id,
                    folder_ids,
                    VFolderMigrationStatus.COMPLETE,
                )
                completed_folder_ids = {row["folder_id"] for row in rows}

            for folder_id in folder_ids:
                if folder_id in completed_folder_ids:
                    progbar.update(1)
                    continue
                quota_scope_id = quota_scope_map[folder_id]
                progbar.write(
                    "moving vfolder {} into quota_scope {}".format(
                        folder_id,
                        quota_scope_id,
                    )
                )
                orig_vfid = VFolderID(None, folder_id)
                dst_vfid = VFolderID(quota_scope_id, folder_id)
                try:
                    if scan_folder_size:
                        current_size = await volume.fsop_model.scan_tree_size(
                            volume.mangle_vfpath(orig_vfid),
                        )
                    else:
                        current_size = None
                    if quota_scope_id not in created_quota_scopes:
                        await volume.quota_model.create_quota_scope(quota_scope_id)
                        created_quota_scopes.add(quota_scope_id)
                    await volume.fsop_model.move_tree(
                        volume.mangle_vfpath(orig_vfid),
                        volume.quota_model.mangle_qspath(dst_vfid),
                    )
                except Exception:
                    log.exception("error during migration of vfolder {}", folder_id)
                    async with (
                        connect_database(ctx.dsn) as conn,
                        conn.transaction(),
                    ):
                        await conn.execute(
                            """\
                            INSERT INTO vfolder_migration_v3
                            (volume_id, folder_id, log, status)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (volume_id, folder_id)
                            DO UPDATE SET log = excluded.log, status = excluded.status;
                            """,
                            volume_id,
                            folder_id,
                            traceback.format_exc(),
                            VFolderMigrationStatus.FAILED,
                        )
                else:
                    log.info(
                        "completed migration of vfolder {}",
                        folder_id,
                    )
                    async with (
                        connect_database(ctx.dsn) as conn,
                        conn.transaction(),
                    ):
                        if old_quota := old_quota_map[folder_id]:
                            quota_in_mib = old_quota * (2**20)
                        else:
                            quota_in_mib = None
                        await conn.execute(
                            """\
                            INSERT INTO vfolder_migration_v3
                            (volume_id, folder_id, status, old_quota, current_size)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (volume_id, folder_id)
                            DO UPDATE SET log = NULL, status = excluded.status,
                            old_quota = excluded.old_quota, current_size = excluded.current_size;
                            """,
                            volume_id,
                            folder_id,
                            VFolderMigrationStatus.COMPLETE,
                            quota_in_mib,
                            int(current_size or 0),
                        )
                    await volume.delete_vfolder(orig_vfid)
                finally:
                    progbar.update(1)

    async with connect_database(ctx.dsn) as conn:
        incomplete_count = await conn.fetchval(
            """\
            SELECT COUNT(*) FROM vfolder_migration_v3
            WHERE volume_id = $1
              AND status != $2;
            """,
            volume_id,
            VFolderMigrationStatus.COMPLETE,
        )
        if incomplete_count == 0:
            log.info("successfully upgraded {}", volume.mount_path)
            (volume.mount_path / "version.txt").write_text("3")
        else:
            log.warning(
                (
                    "There were {} failed migrations. "
                    "Check out vfolder_migration_v3 table in the database."
                ),
                incomplete_count,
            )
            log.warning(
                "You may re-run the migration to retry the failed ones and remaining vfolders."
            )
        if report_path:
            complete_count = await conn.fetchval(
                """\
                SELECT COUNT(*) FROM vfolder_migration_v3
                WHERE volume_id = $1
                AND status = $2;
                """,
                volume_id,
                VFolderMigrationStatus.COMPLETE,
            )
            in_memory_file = StringIO()
            fieldnames = ["volume_id", "folder_id", "current_size", "old_quota"]
            writer = csv.DictWriter(in_memory_file, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(0, complete_count, 10):
                rows = await conn.fetch(
                    """\
                    SELECT "volume_id", "folder_id", "current_size", "old_quota" FROM vfolder_migration_v3
                    WHERE volume_id = $1
                    AND "status" = $2
                    ORDER BY "folder_id"
                    LIMIT 10
                    OFFSET $3;
                    """,
                    volume_id,
                    VFolderMigrationStatus.COMPLETE,
                    i,
                )
                writer.writerows([dict(x) for x in rows])

            async with aiofiles.open(report_path, "w") as csvfile:
                await csvfile.write(in_memory_file.getvalue())


upgrade_handlers = {
    3: upgrade_2_to_3,
}


async def check_and_upgrade(
    local_config: dict[str, Any],
    dsn: str,
    report_path: Optional[Path] = None,
    force_scan_folder_size: bool = False,
):
    etcd = load_shared_config(local_config)
    ctx = Context(pid=os.getpid(), local_config=local_config, etcd=etcd, dsn=dsn)
    volumes_to_upgrade = await check_latest(ctx)
    for upgrade_info in volumes_to_upgrade:
        handler = upgrade_handlers[upgrade_info.target_version]
        await handler(
            ctx,
            upgrade_info.volume,
            report_path=report_path,
            force_scan_folder_size=force_scan_folder_size,
        )


@click.command()
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
    config_path: Optional[Path],
    dsn: str,
    report_path: Optional[Path],
    force_scan_folder_size: bool,
    debug: bool,
) -> None:
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
                report_path=report_path,
                force_scan_folder_size=force_scan_folder_size,
            )
        )


if __name__ == "__main__":
    main()

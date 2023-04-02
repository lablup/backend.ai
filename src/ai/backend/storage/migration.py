import asyncio
import enum
import logging
import os
import re
import traceback
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Iterator
from uuid import UUID

import asyncpg
import click
import more_itertools
import yarl

from ai.backend.common.logging import BraceStyleAdapter, Logger

from .abc import AbstractVolume
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


async def upgrade_2_to_3(ctx: Context, volume: AbstractVolume) -> None:
    assert ctx.dsn is not None
    rx_two_digits_hex = re.compile(r"^[a-f0-9]{2}$")
    rx_rest_digits_hex = re.compile(r"^[a-f0-9]{28}$")
    log.info("upgrading {} ...", volume.mount_path)
    volume_id = os.fsdecode(volume.mount_path)

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
                volume_id VARCHAR(64),
                folder_id UUID,
                status VARCHAR(16),
                log TEXT DEFAULT NULL,
                PRIMARY KEY (volume_id, folder_id)
            );
            """)

    targets = scan_vfolders(volume.mount_path)
    for target_chunk in more_itertools.ichunked(targets, 10):
        folder_ids: list[UUID] = []
        quota_scope_map: dict[UUID, str] = {}
        async with connect_database(ctx.dsn) as conn:
            for target in target_chunk:
                folder_id = path_to_uuid(target)
                folder_ids.append(folder_id)
            rows = await conn.fetch(
                """\
                SELECT "id", "quota_scope_id" FROM vfolders
                WHERE "id" = ANY($1);
                """,
                folder_ids,
            )
            for row in rows:
                quota_scope_map[row["id"]] = row["quota_scope_id"]

            log.info("checking {} ...", ", ".join(map(str, folder_ids)))

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
                continue
            log.info(
                "copying vfolder {} into quota_scope {}",
                folder_id,
                quota_scope_map[folder_id],
            )
            orig_vfid = VFolderID(None, folder_id)
            dst_vfid = VFolderID(quota_scope_map[folder_id], folder_id)
            try:
                # TODO: create the target quota scope
                pass
                # await volume.copy_tree(
                #     volume.mangle_vfpath(orig_Vfid),
                #     volume.mangle_vfpath(dst_vfid),
                # )
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
                log.info("completed migration of vfolder {}", folder_id)
                async with (
                    connect_database(ctx.dsn) as conn,
                    conn.transaction(),
                ):
                    await conn.execute(
                        """\
                            INSERT INTO vfolder_migration_v3
                            (volume_id, folder_id, status)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (volume_id, folder_id)
                            DO UPDATE SET log = NULL, status = excluded.status;
                            """,
                        volume_id,
                        folder_id,
                        VFolderMigrationStatus.COMPLETE,
                    )
                # TODO: delete the source folder

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


upgrade_handlers = {
    3: upgrade_2_to_3,
}


async def check_and_upgrade(local_config: dict[str, Any], dsn: str):
    etcd = load_shared_config(local_config)
    ctx = Context(pid=os.getpid(), local_config=local_config, etcd=etcd, dsn=dsn)
    volumes_to_upgrade = await check_latest(ctx)
    for upgrade_info in volumes_to_upgrade:
        handler = upgrade_handlers[upgrade_info.target_version]
        await handler(ctx, upgrade_info.volume)


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
    "--debug",
    is_flag=True,
    help="This option will soon change to --log-level TEXT option.",
)
def main(config_path: Path, dsn: str, debug: bool) -> None:
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
        asyncio.run(check_and_upgrade(local_config, dsn))


if __name__ == "__main__":
    main()

"""create storage table and migrate

Revision ID: a9e4e4a72fa1
Revises: 7c8501cec07b
Create Date: 2024-08-29 12:38:13.941982

"""

import asyncio
import json
import os
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import (
    Any,
    Final,
    cast,
)

import sqlalchemy as sa
from alembic import op

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.manager import config
from ai.backend.manager.models.base import GUID, Base, IDColumn, URLColumn
from ai.backend.manager.models.storage import StorageSessionManager

# revision identifiers, used by Alembic.
revision = "a9e4e4a72fa1"
down_revision = "7c8501cec07b"
branch_labels = None
depends_on = None

VOLUMES_KEY = "volumes"
ETCD_BACKUP_FILENAME_PATTERN: Final = "backup.etcd.storage.{timestamp}.json"


class StorageProxyRow(Base):
    __tablename__ = "storage_proxies"
    __table_args__ = {"extend_existing": True}
    id = IDColumn()
    name = sa.Column("name", sa.String(length=64), nullable=False, unique=True)
    client_api = sa.Column("client_api", URLColumn, nullable=False)
    manager_api = sa.Column("manager_api", URLColumn, nullable=False)
    secret = sa.Column("secret", sa.String(length=64), nullable=False)
    ssl_verify = sa.Column("ssl_verify", sa.Boolean, default=False, server_default=sa.false())


class StorageVolumeRow(Base):
    __tablename__ = "storage_volumes"
    __table_args__ = (
        sa.UniqueConstraint("name", "proxy_name", name="uq_storage_volumes_name_proxy_name"),
        {"extend_existing": True},
    )
    id = IDColumn()
    name = sa.Column("name", sa.String(length=64), nullable=False)
    proxy_name = sa.Column("proxy_name", sa.String(length=64), nullable=False)
    host_name = sa.Column(
        "host_name", sa.String(length=128), sa.Computed("proxy_name || ':' || name")
    )
    backend = sa.Column("backend", sa.String(length=64), nullable=False)


class _AssociationScalingGroupStorageProxyRow(Base):
    __tablename__ = "association_sgroups_storage_proxies"
    id = IDColumn()
    __table_args__ = (
        sa.Index(
            "ix_sgroup_name_storage_proxy_name", "sgroup_name", "storage_proxy_name", unique=True
        ),
        {"extend_existing": True},
    )
    sgroup_name = sa.Column("sgroup_name", sa.String(length=64), nullable=False)
    storage_proxy_name = sa.Column("storage_proxy_name", sa.String(length=64), nullable=False)


class _ScalingGroupRow(Base):
    __tablename__ = "scaling_groups"
    __table_args__ = {"extend_existing": True}
    name = sa.Column("name", sa.String(length=64), primary_key=True)
    is_public = sa.Column(
        "is_public", sa.Boolean, index=True, default=True, server_default=sa.true(), nullable=False
    )


def get_etcd_client() -> AsyncEtcd:
    local_config = config.load()
    etcd_config = local_config.get("etcd", None)
    assert etcd_config is not None, "etcd configuration is not found"
    etcd_credentials = None
    if local_config["etcd"]["user"]:
        etcd_credentials = {
            "user": local_config["etcd"]["user"],
            "password": local_config["etcd"]["password"],
        }
    scope_prefix_map = {
        ConfigScopes.GLOBAL: "",
    }
    return AsyncEtcd(
        local_config["etcd"]["addr"],
        local_config["etcd"]["namespace"],
        scope_prefix_map,
        credentials=etcd_credentials,
    )


def upgrade() -> None:
    connection = op.get_bind()

    # Create tables
    op.create_table(
        "association_sgroups_storage_proxies",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("sgroup_name", sa.String(length=64), nullable=False),
        sa.Column("storage_proxy_name", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_association_sgroups_storage_proxies")),
    )
    op.create_index(
        "ix_sgroup_name_storage_proxy_name",
        "association_sgroups_storage_proxies",
        ["sgroup_name", "storage_proxy_name"],
        unique=True,
    )
    op.create_table(
        "storage_proxies",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("client_api", URLColumn(), nullable=False),
        sa.Column("manager_api", URLColumn(), nullable=False),
        sa.Column("secret", sa.String(length=64), nullable=False),
        sa.Column("ssl_verify", sa.Boolean(), server_default=sa.text("false"), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_storage_proxies")),
        sa.UniqueConstraint("name", name=op.f("uq_storage_proxies_name")),
    )
    op.create_table(
        "storage_volumes",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("proxy_name", sa.String(length=64), nullable=False),
        sa.Column(
            "host_name",
            sa.String(length=128),
            sa.Computed(
                "proxy_name || ':' || name",
            ),
            nullable=True,
        ),
        sa.Column("backend", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_storage_volumes")),
        sa.UniqueConstraint("name", "proxy_name", name="uq_storage_volumes_name_proxy_name"),
    )

    # Get volume data from etcd
    def backup(raw_storage_config: Mapping[str, Any]) -> None:
        backup_path = Path(os.getenv("BACKEND_ETCD_BACKUP_PATH", "."))
        backup_path /= ETCD_BACKUP_FILENAME_PATTERN.format(timestamp=datetime.now().isoformat())
        with open(backup_path, "w") as f:
            json.dump(raw_storage_config, f, indent=4)

    queue: Queue = Queue()
    with ThreadPoolExecutor() as executor:

        def get_volume_data(queue: Queue) -> None:
            async def _get_data() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
                proxies = []
                volumes = []
                etcd = get_etcd_client()
                raw_storage_config = await etcd.get_prefix(VOLUMES_KEY)
                ## schema of `raw_storage_config`
                # {
                #     "_types": {
                #         "group": "",
                #         "user": ""
                #     },
                #     "default_host": "local:volume1",
                #     "exposed_volume_info": "percentage",
                #     "proxies": {
                #         "local": {
                #             "client_api": "http://127.0.0.1:6021",
                #             "manager_api": "https://127.0.0.1:6022",
                #             "secret": "SECRET...",
                #             "ssl_verify": "false"
                #         }
                #     }
                # }
                storage_config = config.volume_config_iv.check(raw_storage_config)
                for proxy_name, proxy_config in storage_config["proxies"].items():
                    proxies.append({
                        "name": proxy_name,
                        "client_api": proxy_config["client_api"],
                        "manager_api": proxy_config["manager_api"],
                        "secret": proxy_config["secret"],
                        "ssl_verify": proxy_config["ssl_verify"],
                        "sftp_scaling_groups": proxy_config["sftp_scaling_groups"] or [],
                    })
                storage_mgr = StorageSessionManager(storage_config)
                for proxy_name, volume_info in await storage_mgr.get_all_volumes():
                    volumes.append({
                        "name": volume_info["name"],
                        "proxy_name": proxy_name,
                        "backend": volume_info["backend"],
                    })
                return proxies, volumes

            queue.put(asyncio.run(_get_data()))

        executor.submit(get_volume_data, queue)

    proxy_data, volume_data = cast(tuple[list[dict[str, Any]], list[dict[str, Any]]], queue.get())

    # Insert Storage proxy data
    sftp_sgroup_mappings = []
    for proxy in proxy_data:
        try:
            sftp_scaling_groups = cast(list[str], proxy.pop("sftp_scaling_groups"))
        except KeyError:
            continue
        for sgroup in sftp_scaling_groups:
            sftp_sgroup_mappings.append({
                "storage_proxy_name": proxy["name"],
                "sgroup_name": sgroup,
            })
    connection.execute(sa.insert(StorageProxyRow).values(proxy_data))
    if sftp_sgroup_mappings:
        connection.execute(sa.insert(_AssociationScalingGroupStorageProxyRow), sftp_sgroup_mappings)

    public_sgroups = connection.scalars(
        sa.select(_ScalingGroupRow.__table__.c.name).where(
            _ScalingGroupRow.__table__.c.is_public == sa.true()
        )
    ).all()
    public_sgroups = cast(list[str], public_sgroups)

    assoc_data = []
    for sgroup in public_sgroups:
        for proxy in proxy_data:
            proxy_name = proxy["name"]
            assoc_data.append({
                "storage_proxy_name": proxy_name,
                "sgroup_name": sgroup,
            })
    connection.execute(sa.insert(_AssociationScalingGroupStorageProxyRow), assoc_data)

    # Insert Storage volume data
    connection.execute(sa.insert(StorageVolumeRow).values(volume_data))


def downgrade() -> None:
    # Drop tables
    op.drop_table("storage_volumes")
    op.drop_table("storage_proxies")
    op.drop_index(
        "ix_sgroup_name_storage_proxy_name", table_name="association_sgroups_storage_proxies"
    )
    op.drop_table("association_sgroups_storage_proxies")

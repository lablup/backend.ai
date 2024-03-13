"""Migrate container registry schema from `etcd` to `postgreSQL`

Revision ID: 1d42c726d8a3
Revises: 75ea2b136830
Create Date: 2024-03-05 10:36:24.197922

"""

import asyncio
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from itertools import groupby
from queue import Queue
from typing import Any, Final, Mapping, cast

import sqlalchemy as sa
import trafaret as t
from alembic import op

from ai.backend.common import validators as tx
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.manager.config import load
from ai.backend.manager.models.base import Base, IDColumn, StrEnumType, convention
from ai.backend.manager.models.container_registry import ContainerRegistryType
from ai.backend.manager.models.image import ImageRow

# revision identifiers, used by Alembic.
revision = "1d42c726d8a3"
down_revision = "75ea2b136830"
branch_labels = None
depends_on = None

etcd_container_registry_iv = t.Dict({
    t.Key(""): tx.URL,
    t.Key("type", default="docker"): t.String,
    t.Key("username", default=None): t.Null | t.String,
    t.Key("password", default=None): t.Null | t.String(allow_blank=True),
    t.Key("project", default=None): (
        t.Null | t.List(t.String) | tx.StringList(empty_str_as_empty_list=True)
    ),
    tx.AliasedKey(["ssl_verify", "ssl-verify"], default=True): t.ToBool,
}).allow_extra("*")

ETCD_CONTAINER_REGISTRY_KEY: Final = "config/docker/registry"

ETCD_CONTAINER_REGISTRIES_BACKUP_FILENAME: Final = "etcd_container_registries_backup.json"


def get_container_registry_row_schema():
    class ContainerRegistryRow(Base):
        __tablename__ = "container_registries"
        __table_args__ = {"extend_existing": True}
        id = IDColumn()
        url = sa.Column("url", sa.String(length=512), index=True)
        registry_name = sa.Column("registry_name", sa.String(length=50), index=True)
        type = sa.Column(
            "type",
            StrEnumType(ContainerRegistryType),
            default=ContainerRegistryType.DOCKER,
            server_default=ContainerRegistryType.DOCKER,
            nullable=False,
            index=True,
        )
        project = sa.Column("project", sa.String(length=255), nullable=True)  # harbor only
        username = sa.Column("username", sa.String(length=255), nullable=True)
        password = sa.Column("password", sa.String(length=255), nullable=True)
        ssl_verify = sa.Column("ssl_verify", sa.Boolean, server_default=sa.text("true"), index=True)
        is_global = sa.Column("is_global", sa.Boolean, server_default=sa.text("true"), index=True)

    return ContainerRegistryRow


def get_async_etcd() -> AsyncEtcd:
    local_config = load()
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


def migrate_data_etcd_to_psql() -> None:
    queue: Queue = Queue()

    with ThreadPoolExecutor() as executor:

        def backup(etcd_container_registries: Mapping[str, Any]):
            backup_path = os.getenv("BACKEND_ETCD_BACKUP_PATH", ".")
            with open(
                os.path.join(backup_path, ETCD_CONTAINER_REGISTRIES_BACKUP_FILENAME), "w"
            ) as f:
                json.dump(dict(etcd_container_registries), f, indent=4)

        # If there are no container registries, it returns an empty list.
        # If an error occurs while saving backup, it returns error.
        def take_etcd_container_registries(queue: Queue):
            async def _take_container_registries():
                etcd = get_async_etcd()
                result = await etcd.get_prefix(ETCD_CONTAINER_REGISTRY_KEY)
                try:
                    backup(result)
                except Exception as e:
                    return e
                await etcd.delete_prefix(ETCD_CONTAINER_REGISTRY_KEY)
                return result

            queue.put(asyncio.run(_take_container_registries()))

        executor.submit(take_etcd_container_registries, queue)

    maybe_registries = queue.get()

    if isinstance(maybe_registries, Exception):
        err_msg = (
            f"Failed to save etcd container registries backup file., Cause: {maybe_registries}"
        )
        print(
            err_msg,
            file=sys.stderr,
        )
        raise RuntimeError(err_msg) from maybe_registries
    else:
        registries = cast(Mapping[str, Any], maybe_registries)

    old_format_container_registries = {
        hostname: etcd_container_registry_iv.check(item)
        for hostname, item in registries.items()
        # type: ignore
    }

    input_configs = []
    for hostname, registry_info in old_format_container_registries.items():
        input_config_template: dict[str, Any] = {
            "registry_name": hostname,  # hostname is changed to registry_name,
            "url": str(registry_info[""]),
            "type": ContainerRegistryType(registry_info["type"]),
            "username": registry_info.get("username", None),
            "password": registry_info.get("password", None),
            "ssl_verify": registry_info.get("ssl_verify", None),
            "is_global": True,
        }

        # Comma-separated projects are divided into multiple ContainerRegistry rows
        if "project" in registry_info:
            for project in registry_info["project"]:
                input_config = input_config_template.copy()
                input_config["project"] = project
                input_configs.append(input_config)
        else:
            input_configs.append(input_config_template)

    if not input_configs:
        print("There is no container registries data to migrate in etcd.")
        return

    ContainerRegistryRow = get_container_registry_row_schema()

    db_connection = op.get_bind()
    db_connection.execute(sa.insert(ContainerRegistryRow).values(input_configs))


def revert_data_psql_to_etcd() -> None:
    ContainerRegistryRow = get_container_registry_row_schema()

    db_connection = op.get_bind()
    rows = db_connection.execute(sa.select(ContainerRegistryRow)).fetchall()
    items = []

    for id, url, registry_name, type, project, username, password, ssl_verify, _is_global in rows:
        item = {
            "": url,
            "type": str(type),
            "hostname": registry_name,  # registry_name should be reverted to hostname,
        }

        if project is not None:
            item["project"] = project
        if username is not None:
            item["username"] = username
        if password is not None:
            item["password"] = password
        if ssl_verify is not None:
            item["ssl_verify"] = ssl_verify

        items.append(item)

    # Records with the same hostname should be grouped together.
    # Note that if there are columns other than the project column that have different values between records,
    # information loss can occur.
    grouped_items = {k: list(v) for k, v in groupby(items, key=lambda x: x["hostname"])}

    def merge_items(items):
        for item in items:
            if "project" not in item:
                return items[0]

        projects = [item["project"] for item in items]
        merged_projects = ",".join(projects)

        merged_item = items[0].copy()
        merged_item["project"] = merged_projects

        return merged_item

    merged_items = [merge_items(items) for items in grouped_items.values()]

    def put_etcd_container_registries(merged_items: list[Any], queue: Queue):
        etcd = get_async_etcd()
        for item in merged_items:
            hostname = item.pop("hostname")
            asyncio.run(etcd.put_prefix(f"{ETCD_CONTAINER_REGISTRY_KEY}/{hostname}", item))

        queue.put(True)

    queue: Queue = Queue()

    with ThreadPoolExecutor() as executor:
        executor.submit(put_etcd_container_registries, merged_items, queue)

    queue.get()


def insert_registry_id_to_images() -> None:
    db_connection = op.get_bind()
    ContainerRegistry = get_container_registry_row_schema()

    image_infos = db_connection.execute(sa.select([ImageRow.id, ImageRow.name])).fetchall()

    for image_info in image_infos:
        image_id, image_name = image_info

        parts = image_name.split("/")
        registry_name = parts[0]
        project = parts[1]

        registry_id = db_connection.execute(
            sa.select(ContainerRegistry.id)
            .where(ContainerRegistry.registry_name == registry_name)
            .where(ContainerRegistry.project == project)
        ).scalar()

        if registry_id is not None:
            db_connection.execute(
                sa.update(ImageRow)
                .values(registry_id=str(registry_id))
                .where(ImageRow.id == image_id)
            )
        else:
            print(f"ContainerRegistry row not found for image {image_name}", file=sys.stderr)


def upgrade():
    metadata = sa.MetaData(naming_convention=convention)
    op.create_table(
        "container_registries",
        metadata,
        IDColumn("id"),
        sa.Column("url", sa.String(length=512), nullable=True, index=True),
        sa.Column("registry_name", sa.String(length=50), nullable=True, index=True),
        sa.Column(
            "type",
            StrEnumType(ContainerRegistryType),
            default=ContainerRegistryType.DOCKER,
            server_default=ContainerRegistryType.DOCKER,
            nullable=False,
            index=True,
        ),
        sa.Column("project", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("password", sa.String(length=255), nullable=True),
        sa.Column(
            "ssl_verify", sa.Boolean(), server_default=sa.text("true"), nullable=True, index=True
        ),
        sa.Column(
            "is_global", sa.Boolean(), server_default=sa.text("true"), nullable=True, index=True
        ),
    )

    migrate_data_etcd_to_psql()

    op.add_column("images", sa.Column("registry_id", sa.String, default=None, nullable=True))

    insert_registry_id_to_images()


def downgrade():
    revert_data_psql_to_etcd()

    op.drop_table("container_registries")
    op.drop_column("images", "registry_id")

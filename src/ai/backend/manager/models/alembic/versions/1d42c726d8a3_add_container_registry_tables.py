"""Migrate container registry schema from `etcd` to `postgreSQL`

Revision ID: 1d42c726d8a3
Revises: 75ea2b136830
Create Date: 2024-03-05 10:36:24.197922

"""

import asyncio
from typing import Any, Final

import asyncpg
import sqlalchemy as sa
import trafaret as t
from alembic import op
from sqlalchemy.sql import text

from ai.backend.common import validators as tx
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.manager.config import load
from ai.backend.manager.models.base import IDColumn, convention
from ai.backend.manager.models.container_registry import ContainerRegistryRow

# revision identifiers, used by Alembic.
revision = "1d42c726d8a3"
down_revision = "75ea2b136830"
branch_labels = None
depends_on = None

container_registry_iv = t.Dict({
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


def migrate_data_etcd_to_psql():
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
    etcd = AsyncEtcd(
        local_config["etcd"]["addr"],
        local_config["etcd"]["namespace"],
        scope_prefix_map,
        credentials=etcd_credentials,
    )

    async def get_prefix_coroutine():
        return await etcd.get_prefix(ETCD_CONTAINER_REGISTRY_KEY)

    loop = asyncio.get_event_loop()
    registries = loop.run_until_complete(get_prefix_coroutine())

    print("registries", registries)
    items = {
        hostname: container_registry_iv.check(item)
        for hostname, item in registries.items()
        # type: ignore
    }

    input_configs = []
    for hostname, registry_info in items.items():
        input_config: dict[str, Any] = {
            "registry_name": hostname,  # hostname to registry_name,
            "url": str(registry_info[""]),
            "type": registry_info["type"],
            "username": registry_info.get("username", None),
            "password": registry_info.get("password", None),
            "ssl_verify": registry_info.get("ssl_verify", None),
            "is_global": True,
        }

        if "project" in registry_info:
            for project in registry_info["project"]:
                input_config_t = input_config.copy()
                input_config_t["project"] = project
                input_configs.append(input_config_t)
        else:
            input_configs.append(input_config)

    try:
        connection = op.get_bind()
        connection.execute(sa.insert(ContainerRegistryRow).values(input_config))

    except (asyncpg.exceptions.CannotConnectNowError, ConnectionError):
        print("ConnectionError")

    except Exception as e:
        print("e", e)
        raise

    except BaseException:
        print("Base Error")
        raise


def upgrade():
    metadata = sa.MetaData(naming_convention=convention)
    op.create_table(
        "container_registries",
        metadata,
        IDColumn("id"),
        sa.Column("url", sa.String(length=255), nullable=True, index=True),
        sa.Column("registry_name", sa.String(length=50), nullable=True, index=True),
        sa.Column(
            "type",
            sa.Enum("docker", "harbor", "harbor2", name="container_registry_type"),
            default="docker",
            index=True,
            nullable=False,
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


def downgrade():
    op.drop_table("container_registries")
    op.execute(text("DROP TYPE container_registry_type"))

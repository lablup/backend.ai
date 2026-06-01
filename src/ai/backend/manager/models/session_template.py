from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from typing import Any, cast

import sqlalchemy as sa
import trafaret as t
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.common import validators as tx
from ai.backend.common.types import SessionTypes
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.exceptions import InvalidArgument

from .base import GUID, EnumType, IDColumn, metadata
from .vfolder import verify_vfolder_name

__all__: Sequence[str] = (
    "TemplateType",
    "session_templates",
)


class TemplateType(enum.StrEnum):
    TASK = "task"
    CLUSTER = "cluster"


session_templates = sa.Table(
    "session_templates",
    metadata,
    IDColumn("id"),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    sa.Column("is_active", sa.Boolean, default=True),
    sa.Column("domain_name", sa.String(length=64), sa.ForeignKey("domains.name"), nullable=False),
    sa.Column("group_id", GUID, sa.ForeignKey("groups.id"), nullable=True),
    sa.Column("user_uuid", GUID, sa.ForeignKey("users.uuid"), index=True, nullable=False),
    sa.Column("type", EnumType(TemplateType), nullable=False, server_default="TASK", index=True),
    sa.Column("name", sa.String(length=128), nullable=True),
    sa.Column("template", pgsql.JSONB(), nullable=False),
)


task_template_v1 = t.Dict({
    tx.AliasedKey(["api_version", "apiVersion"]): t.String,
    t.Key("kind"): t.Enum("taskTemplate", "task_template"),
    t.Key("metadata"): t.Dict({
        t.Key("name"): t.String,
        t.Key("tag", default=None): t.Null | t.String,
    }),
    t.Key("spec"): t.Dict({
        tx.AliasedKey(["type", "session_type", "sessionType"], default="interactive")
        >> "session_type": tx.Enum(SessionTypes),
        t.Key("kernel"): t.Dict({
            t.Key("image"): t.String,
            t.Key("architecture", default="x86_64"): t.Null | t.String,
            t.Key("environ", default={}): t.Null | t.Mapping(t.String, t.String),
            t.Key("run", default=None): t.Null
            | t.Dict({
                t.Key("bootstrap", default=None): t.Null | t.String,
                tx.AliasedKey(["startup", "startup_command", "startupCommand"], default=None)
                >> "startup_command": t.Null | t.String,
            }),
            t.Key("git", default=None): t.Null
            | t.Dict({
                t.Key("repository"): t.String,
                t.Key("commit", default=None): t.Null | t.String,
                t.Key("branch", default=None): t.Null | t.String,
                t.Key("credential", default=None): t.Null
                | t.Dict({
                    t.Key("username"): t.String,
                    t.Key("password"): t.String,
                }),
                tx.AliasedKey(["destination_dir", "destinationDir"], default=None)
                >> "dest_dir": t.Null | t.String,
            }),
        }),
        t.Key("scaling_group", default=None): t.Null | t.String,
        t.Key("mounts", default={}): t.Null | t.Mapping(t.String, t.Any),
        t.Key("resources", default=None): t.Null | t.Mapping(t.String, t.Any),
        tx.AliasedKey(["agent_list", "agentList"], default=None) >> "agent_list": t.Null
        | t.List(t.String),
    }),
}).allow_extra("*")


def check_task_template(raw_data: Mapping[str, Any]) -> Mapping[str, Any]:
    data = task_template_v1.check(raw_data)
    if mounts := data["spec"].get("mounts"):
        for p in mounts.values():
            if p is None:
                continue
            p = p.removeprefix("/home/work/")
            if not verify_vfolder_name(p):
                raise InvalidArgument(f"Path {p} is reserved for internal operations.")
    return cast(Mapping[str, Any], data)


cluster_template_v1 = t.Dict({
    tx.AliasedKey(["api_version", "apiVersion"]): t.String,
    t.Key("kind"): t.Enum("clusterTemplate", "cluster_template"),
    t.Key("mode"): t.Enum("single-node", "multi-node"),
    t.Key("metadata"): t.Dict({
        t.Key("name"): t.String,
    }),
    t.Key("spec"): t.Dict({
        t.Key("environ", default={}): t.Null | t.Mapping(t.String, t.String),
        t.Key("mounts", default={}): t.Null | t.Mapping(t.String, t.Any),
        t.Key("nodes"): t.List(
            t.Dict({
                t.Key("role"): t.String,
                tx.AliasedKey(["session_template", "sessionTemplate"]): tx.UUID,
                t.Key("replicas", default=1): t.Int,
            })
        ),
    }),
}).allow_extra("*")


def check_cluster_template(raw_data: Mapping[str, Any]) -> Mapping[str, Any]:
    data = cluster_template_v1.check(raw_data)
    defined_roles: list[str] = []
    for node in data["spec"]["nodes"]:
        node["session_template"] = str(node["session_template"])
        if node["role"] in defined_roles:
            raise InvalidArgument("Each role can only be defined once")
        if node["role"] == DEFAULT_ROLE and node["replicas"] != 1:
            raise InvalidArgument(
                f"One and only one {DEFAULT_ROLE} node must be created per cluster",
            )
        defined_roles.append(node["role"])
    if DEFAULT_ROLE not in defined_roles:
        raise InvalidArgument(
            f"One and only one {DEFAULT_ROLE} node must be created per cluster",
        )
    return cast(Mapping[str, Any], data)

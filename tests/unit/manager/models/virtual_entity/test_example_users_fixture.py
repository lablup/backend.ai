"""Tests for the graph rows the account seed declares for its projects."""

from __future__ import annotations

import copy
import json
import pathlib
import uuid
from collections.abc import AsyncGenerator
from typing import Any, Final

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.models.base import populate_fixture
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow, association_groups_users
from ai.backend.manager.models.resource_group.row import ResourceGroupRow, sgroups_for_domains
from ai.backend.manager.models.resource_policy.row import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.fixture import provision_fixture_entities
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import with_tables

_FIXTURE: Final = (
    pathlib.Path(__file__).resolve().parents[5] / "fixtures" / "manager" / "example-users.json"
)

#: The tables whose rows an earlier install wrote, and the ones among them the
#: migration gives a graph node.
_MIGRATED_TABLES: Final = (
    "domains",
    "user_resource_policies",
    "project_resource_policies",
    "scaling_groups",
    "users",
    "groups",
)
_MIGRATED_ENTITIES: Final = ("domains", "scaling_groups", "users", "groups")

#: Every table the seed declares.
_ACCOUNT_TABLES: Final = (
    "domains",
    "user_resource_policies",
    "project_resource_policies",
    "scaling_groups",
    "sgroups_for_domains",
    "users",
    "groups",
    "association_groups_users",
    "virtual_entities",
    "entity_memberships",
    "scope_bindings",
    "entity_membership_caps",
)


@pytest.fixture(scope="module")
def seed() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    return loaded


@pytest.fixture(scope="module")
def nodes(seed: dict[str, Any]) -> dict[tuple[str, str], str]:
    """The node each declared entity id holds. A row that names its entity instead of
    its id is resolved against the database when the seed is loaded, not here."""
    return {
        (row["entity_type"], row["entity_id"]): row["id"]
        for row in seed["virtual_entities"]
        if "entity_id" in row
    }


@pytest.fixture(scope="module")
def memberships(seed: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (row["virtual_entity_id"], row["member_entity_id"]) for row in seed["entity_memberships"]
    }


@pytest.fixture(scope="module")
def bindings(seed: dict[str, Any]) -> set[tuple[str, str]]:
    return {(row["virtual_entity_id"], row["scope_entity_id"]) for row in seed["scope_bindings"]}


@pytest.fixture(scope="module")
def entity_types(seed: dict[str, Any]) -> dict[str, str]:
    return {row["id"]: row["entity_type"] for row in seed["virtual_entities"]}


@pytest.fixture(scope="module")
def caps(seed: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in seed["entity_membership_caps"]:
        grouped.setdefault(row["membership_id"], []).append(row)
    return grouped


class TestExampleUsersGraph:
    def _domain_node(self, seed: dict[str, Any]) -> str:
        """The one node of the seed's domain. The row names its domain instead of
        carrying the id, which the loader resolves against the database."""
        return str(
            next(row["id"] for row in seed["virtual_entities"] if row["entity_type"] == "domain")
        )

    def test_every_project_has_a_node(
        self, seed: dict[str, Any], nodes: dict[tuple[str, str], str]
    ) -> None:
        assert all(("project", group["id"]) in nodes for group in seed["groups"])

    def test_every_project_owns_and_governs_itself(
        self,
        seed: dict[str, Any],
        nodes: dict[tuple[str, str], str],
        memberships: set[tuple[str, str]],
        bindings: set[tuple[str, str]],
    ) -> None:
        for group in seed["groups"]:
            node = nodes[("project", group["id"])]
            assert (node, node) in memberships
            assert (node, node) in bindings

    def test_every_project_is_created_in_its_domain(
        self,
        seed: dict[str, Any],
        nodes: dict[tuple[str, str], str],
        memberships: set[tuple[str, str]],
        bindings: set[tuple[str, str]],
    ) -> None:
        for group in seed["groups"]:
            node = nodes[("project", group["id"])]
            domain = self._domain_node(seed)
            assert (domain, node) in memberships
            assert (node, domain) in bindings

    def test_a_personal_project_holds_its_owner(
        self,
        seed: dict[str, Any],
        nodes: dict[tuple[str, str], str],
        memberships: set[tuple[str, str]],
    ) -> None:
        """The roster row `permissions provision` reads to grant the owner the roles of
        their personal project."""
        for group in seed["groups"]:
            if group["type"] != "personal":
                continue
            node = nodes[("project", group["id"])]
            owner = nodes[("user", group["creator_id"])]
            assert (node, owner) in memberships


class TestExampleUsersRoster:
    """A seeded roster row holds the shape `V2RosterWriteOps` writes: a share capped to
    read."""

    def test_every_roster_edge_is_a_read_capped_share(
        self,
        seed: dict[str, Any],
        entity_types: dict[str, str],
        caps: dict[str, list[dict[str, Any]]],
    ) -> None:
        rosters = [
            row
            for row in seed["entity_memberships"]
            if entity_types[row["virtual_entity_id"]] == "project"
            and entity_types[row["member_entity_id"]] == "user"
        ]
        assert rosters
        for row in rosters:
            assert row.get("capped") is True
            assert caps.get(row.get("id")) == [
                {
                    "membership_id": row["id"],
                    "permission": int(Permission.READ),
                    "all_fields": True,
                }
            ]


class TestExampleUsersScalingGroupReference:
    """The seed names the default scaling group, which a database that already holds it
    carries under a UUID of its own. Loading resolves each reference against the row
    that is there, so `sgroups_for_domains` and the group's node point at it either way."""

    @pytest.fixture
    async def db_engine(
        self, global_entity_ids: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            global_entity_ids,
            [
                DomainRow,
                ResourceGroupRow,
                sgroups_for_domains,
                VirtualEntityRow,
                EntityMembershipRow,
                ScopeBindingRow,
            ],
        ):
            yield global_entity_ids

    @pytest.fixture
    def scaling_group_seed(self, seed: dict[str, Any]) -> dict[str, Any]:
        """The seed's rows on the scaling group path, read from the file the installer
        loads. Its own copy: loading resolves a row's aliases in place."""
        return copy.deepcopy({
            **{key: seed[key] for key in ("domains", "scaling_groups", "sgroups_for_domains")},
            "virtual_entities": [
                row for row in seed["virtual_entities"] if row["entity_type"] == "resource_group"
            ],
        })

    async def _read_references(
        self, db_engine: ExtendedAsyncSAEngine
    ) -> tuple[uuid.UUID, uuid.UUID | None, list[VirtualEntityRow]]:
        """The `default` scaling group's id, the id `sgroups_for_domains` points at (if
        the association is there), and the resource group's graph nodes."""
        async with db_engine.begin_session() as db_sess:
            group_id = await db_sess.scalar(
                sa.select(ResourceGroupRow.id).where(ResourceGroupRow.name == "default")
            )
            link_id = await db_sess.scalar(sa.select(sgroups_for_domains.c.resource_group_id))
            nodes = list(
                (
                    await db_sess.scalars(
                        sa.select(VirtualEntityRow).where(
                            VirtualEntityRow.entity_type == ResourceGroupEntityType()
                        )
                    )
                ).all()
            )
        assert group_id is not None
        return group_id, link_id, nodes

    async def test_resolves_in_an_empty_database(
        self,
        db_engine: ExtendedAsyncSAEngine,
        scaling_group_seed: dict[str, Any],
    ) -> None:
        await populate_fixture(db_engine, scaling_group_seed)

        group_id, link_id, nodes = await self._read_references(db_engine)

        assert group_id == uuid.UUID("4d1e9b32-90c7-5b32-8f0e-6f470b8ed24a")
        assert link_id == group_id
        assert len(nodes) == 1
        assert nodes[0].id == uuid.UUID("7a0f4c2e-3b91-5d6a-9e84-1c5f2b7d9a63")
        assert nodes[0].entity_id == group_id

    async def test_reuses_an_existing_default_scaling_group(
        self,
        db_engine: ExtendedAsyncSAEngine,
        scaling_group_seed: dict[str, Any],
    ) -> None:
        """A database migrated from an older release already holds the `default`
        scaling group, under a UUID its own row minted."""
        existing = dict(scaling_group_seed["scaling_groups"][0])
        existing.pop("id")
        await populate_fixture(db_engine, {"scaling_groups": [existing]})
        preexisting_id, preexisting_link_id, _ = await self._read_references(db_engine)
        assert preexisting_link_id is None

        await populate_fixture(db_engine, scaling_group_seed)

        group_id, link_id, nodes = await self._read_references(db_engine)
        assert group_id == preexisting_id
        assert link_id == preexisting_id
        assert [node.entity_id for node in nodes] == [preexisting_id]


class TestExampleUsersGraphOnAMigratedDatabase:
    """A database an earlier install seeded holds its accounts, its projects and the
    graph the migration built for them, the rows the migration made under ids of its own.
    The seed declares all of them under pinned ids."""

    @pytest.fixture
    async def db_engine(
        self, global_entity_ids: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            global_entity_ids,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                ResourceGroupRow,
                sgroups_for_domains,
                UserRow,
                ProjectRow,
                association_groups_users,
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                ScopeBindingRow,
            ],
        ):
            yield global_entity_ids

    @pytest.fixture
    async def migrated(
        self, db_engine: ExtendedAsyncSAEngine, seed: dict[str, Any]
    ) -> dict[str, Any]:
        """The seed's rows on this path, over a database an earlier install made."""
        return copy.deepcopy({key: seed[key] for key in _ACCOUNT_TABLES})

    @pytest.fixture
    async def migrated_database(
        self, db_engine: ExtendedAsyncSAEngine, migrated: dict[str, Any]
    ) -> ExtendedAsyncSAEngine:
        """What the earlier install wrote: its account and project rows, the domain and
        the scaling group under ids this database minted, and the graph nodes the
        migration built for them under ids of their own."""
        for table in ("domains", "scaling_groups"):
            migrated[table][0].pop("id")
        await populate_fixture(db_engine, {key: migrated[key] for key in _MIGRATED_TABLES})
        async with db_engine.begin() as conn:
            await provision_fixture_entities(conn, _MIGRATED_ENTITIES)
        return db_engine

    async def test_the_seed_lands_on_the_rows_and_nodes_the_database_holds(
        self,
        migrated_database: ExtendedAsyncSAEngine,
        migrated: dict[str, Any],
    ) -> None:
        await populate_fixture(
            migrated_database,
            {key: rows for key, rows in migrated.items() if key not in _MIGRATED_TABLES},
        )

        async with migrated_database.begin_readonly_session() as db_sess:
            nodes = list((await db_sess.scalars(sa.select(VirtualEntityRow))).all())
            memberships = list((await db_sess.scalars(sa.select(EntityMembershipRow))).all())
            bindings = list(await db_sess.scalars(sa.select(ScopeBindingRow)))
            roster = list((await db_sess.execute(sa.select(association_groups_users))).mappings())
            held: dict[str, set[Any]] = {
                "domain": set(await db_sess.scalars(sa.select(DomainRow.id))),
                "resource_group": set(await db_sess.scalars(sa.select(ResourceGroupRow.id))),
                "project": set(await db_sess.scalars(sa.select(ProjectRow.id))),
                "user": set(await db_sess.scalars(sa.select(UserRow.uuid))),
            }
            group_ids = held["project"]

        node_ids = {node.id for node in nodes}
        assert len({(node.entity_type, node.entity_id) for node in nodes}) == len(nodes)
        assert all(
            node.entity_id in held[str(node.entity_type)]
            for node in nodes
            if str(node.entity_type) in held
        )
        assert all(row.virtual_entity_id in node_ids for row in memberships)
        assert all(row.member_entity_id in node_ids for row in memberships)
        assert all(row.virtual_entity_id in node_ids for row in bindings)
        assert all(row.scope_entity_id in node_ids for row in bindings)
        assert roster and all(row["group_id"] in group_ids for row in roster)

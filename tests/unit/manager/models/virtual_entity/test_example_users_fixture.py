"""Tests for the graph rows the account seed declares for its projects."""

from __future__ import annotations

import json
import pathlib
from typing import Any, Final

import pytest

_FIXTURE: Final = (
    pathlib.Path(__file__).resolve().parents[5] / "fixtures" / "manager" / "example-users.json"
)


@pytest.fixture(scope="module")
def seed() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    return loaded


@pytest.fixture(scope="module")
def nodes(seed: dict[str, Any]) -> dict[tuple[str, str], str]:
    return {(row["entity_type"], row["entity_id"]): row["id"] for row in seed["virtual_entities"]}


@pytest.fixture(scope="module")
def memberships(seed: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (row["virtual_entity_id"], row["member_entity_id"]) for row in seed["entity_memberships"]
    }


@pytest.fixture(scope="module")
def bindings(seed: dict[str, Any]) -> set[tuple[str, str]]:
    return {(row["virtual_entity_id"], row["scope_entity_id"]) for row in seed["scope_bindings"]}


class TestExampleUsersGraph:
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
            domain = nodes[("domain", seed["domains"][0]["id"])]
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

"""The ``mgr ops`` catalog listing, built without any manager dependency."""

from __future__ import annotations

import json
from typing import cast

from click.testing import CliRunner

from ai.backend.manager.actions.registry.types import Concern
from ai.backend.manager.actions.types import ActionBacking, ActionGate, ActionKind
from ai.backend.manager.cli.ops import cli


def _list(*args: str) -> list[dict[str, str]]:
    result = CliRunner().invoke(cli, ["list", "--output", "json", *args])
    assert result.exit_code == 0, result.output
    return cast(list[dict[str, str]], json.loads(result.output))


def test_the_catalog_is_not_empty() -> None:
    assert _list()


def test_the_listing_order_is_stable() -> None:
    assert _list() == _list()


def test_the_listing_is_sorted_by_its_address() -> None:
    rows = _list()
    keys = [
        (
            row["concern"],
            row["entity_type"],
            row["field_type"],
            row["operation"],
            row["action_name"],
        )
        for row in rows
    ]
    assert keys == sorted(keys)


def test_concern_filters_the_listing() -> None:
    rows = _list("--concern", "vfolder")
    assert rows
    assert {row["concern"] for row in rows} == {"vfolder"}
    assert len(rows) < len(_list())


def test_field_filters_the_listing() -> None:
    entries = _list("--field", "error_log")
    assert entries
    assert {entry["field_type"] for entry in entries} == {"error_log"}


def test_gate_filters_the_listing() -> None:
    rows = _list("--gate", "anonymous")
    assert rows
    assert {row["gate"] for row in rows} == {"anonymous"}


def test_backing_filters_the_listing() -> None:
    rows = _list("--backing", "generic")
    assert rows
    assert {row["backing"] for row in rows} == {"generic"}


def _entities() -> list[dict[str, str]]:
    result = CliRunner().invoke(cli, ["entities", "--output", "json"])
    assert result.exit_code == 0, result.output
    return cast(list[dict[str, str]], json.loads(result.output))


def test_every_entity_type_of_the_listing_is_named() -> None:
    assert {row["entity_type"] for row in _entities()} == {
        entry["entity_type"] for entry in _list()
    }


def test_an_entity_type_hangs_under_the_area_wiring_it() -> None:
    assert {(row["concern"], row["entity_type"]) for row in _entities()} == {
        (entry["concern"], entry["entity_type"]) for entry in _list()
    }


def test_a_field_type_hangs_under_the_entity_answering_for_it() -> None:
    owned = [row for row in _entities() if row["field_type"] != "-"]
    assert owned
    for row in owned:
        listed = _list(
            "--concern",
            row["concern"],
            "--entity",
            row["entity_type"],
            "--field",
            row["field_type"],
        )
        assert len(listed) == int(row["operations"])


def test_every_wiring_names_a_declared_area() -> None:
    declared = {concern.value for concern in Concern}
    assert {entry["concern"] for entry in _list()} <= declared


def test_an_undeclared_area_is_rejected() -> None:
    result = CliRunner().invoke(cli, ["list", "--concern", "no_such_area"])
    assert result.exit_code != 0


def test_every_declared_column_value_is_explained() -> None:
    for members in (tuple(ActionKind), tuple(ActionGate), tuple(ActionBacking), tuple(Concern)):
        for member in members:
            assert member.describe()


def test_the_listing_help_explains_the_column_values() -> None:
    result = CliRunner().invoke(cli, ["list", "--help"])
    assert result.exit_code == 0, result.output
    assert ActionGate.ANONYMOUS.describe() in result.output
    assert ActionBacking.GENERIC.describe() in result.output


def test_only_a_scope_shaped_operation_declares_scope_types() -> None:
    rows = _list()
    scoped = [row for row in rows if row["kind"] == ActionKind.SCOPE.value]
    assert scoped
    assert all(row["scope_types"] != "-" for row in scoped)
    assert all(row["scope_types"] == "-" for row in rows if row["kind"] != ActionKind.SCOPE.value)


def test_a_caller_named_scope_type_is_declared_alone() -> None:
    """`global` bounds nothing, so listing it beside a concrete type claims both."""
    for row in _list():
        declared = row["scope_types"].split(",")
        assert "global" not in declared or declared == ["global"]


def test_no_type_name_carries_a_colon() -> None:
    for entry in _list():
        assert ":" not in entry["entity_type"]
        assert ":" not in entry["field_type"]
        assert ":" not in entry["concern"]


def test_describe_prints_the_addressed_operation() -> None:
    row = _list("--concern", "vfolder")[0]
    result = CliRunner().invoke(cli, ["describe", row["entity_type"], row["action_name"]])
    assert result.exit_code == 0, result.output
    assert row["action_name"] in result.output
    assert "defined_at" in result.output


def test_describe_reports_an_unwired_address() -> None:
    result = CliRunner().invoke(cli, ["describe", "vfolder", "no_such_operation"])
    assert result.exit_code != 0

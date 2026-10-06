"""Seed files are read, validated per kind and written in the kinds' dependency order."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast, override
from unittest.mock import MagicMock

import pytest
import yaml
from pydantic import BaseModel, ConfigDict

from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.errors.seed import InvalidSeedKindRegistry
from ai.backend.manager.models.specs.types import EntityWithFieldsResult
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.seed.kind import (
    SeedCreation,
    SeedFileItems,
    SeedKind,
    SeedRejection,
    SeedUpsert,
)
from ai.backend.manager.seed.registry import SeedKindRegistry
from ai.backend.manager.seed.result import SeedItemFailure, SeedWriteResult
from ai.backend.manager.seed.runner import SeedApplier, SeedBatch, SeedPlanner


class NamedItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str


class FakeKind(SeedKind[NamedItem]):
    """A kind whose specs are its items, and which refuses the items named ``bad``."""

    _name: str
    _apply_after: frozenset[str]

    def __init__(self, name: str, apply_after: Sequence[str] = ()) -> None:
        self._name = name
        self._apply_after = frozenset(apply_after)

    @override
    def name(self) -> str:
        return self._name

    @override
    def versions(self) -> frozenset[int]:
        return frozenset({1, 2})

    @override
    def apply_after(self) -> frozenset[str]:
        return self._apply_after

    @override
    def schema(self) -> type[NamedItem]:
        return NamedItem

    @override
    def key(self, item: NamedItem) -> str:
        return item.name

    @override
    def reject(self, files: Sequence[SeedFileItems[NamedItem]]) -> list[SeedRejection]:
        return [
            SeedRejection(file.source, "states bad")
            for file in files
            if any(item.name == "bad" for item in file.items)
        ]

    @override
    def creation(self, item: NamedItem) -> SeedCreation:
        return SeedCreation(creator=cast(Any, item), field_creators=())

    @override
    def upsert(self, item: NamedItem) -> SeedUpsert:
        return SeedUpsert(upserter=cast(Any, item), field_upserters=(), field_purgers=())


class FakeRepository(OpsRepository[Any]):
    """Keeps rows by item name; creating a name already held is a unique conflict, and an
    item named ``orphan`` refers to a missing row."""

    rows: dict[str, str]
    calls: list[tuple[str, str]]

    def __init__(self, rows: Sequence[str] = ()) -> None:
        super().__init__(MagicMock(spec=V2DBOpsProvider))
        self.rows = dict.fromkeys(rows, "seeded")
        self.calls = []

    @override
    async def create_entity_with_fields(
        self, creator: Any, field_creators: Sequence[Any]
    ) -> EntityWithFieldsResult[Any, Any]:
        self.calls.append(("create", creator.name))
        if creator.name == "orphan":
            raise ForeignKeyViolationError(constraint_name="fk_fake")
        if creator.name in self.rows:
            raise UniqueConstraintViolationError(constraint_name="pk_fake")
        self.rows[creator.name] = "created"
        return EntityWithFieldsResult(data=creator, fields=[])

    @override
    async def upsert_entity_with_fields(
        self, upserter: Any, field_upserters: Sequence[Any], field_purgers: Sequence[Any]
    ) -> EntityWithFieldsResult[Any, Any]:
        self.calls.append(("upsert", upserter.name))
        self.rows[upserter.name] = "upserted"
        return EntityWithFieldsResult(data=upserter, fields=[])


def _write(path: Path, kind: str, *names: str, version: int = 1) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"kind": kind, "version": version, "items": [{"name": n} for n in names]})
    )
    return path


def _names(batch: SeedBatch) -> list[str]:
    return [item.name for file in batch.files for item in file.items]


def _sources(rejections: Sequence[SeedRejection]) -> set[str]:
    return {rejection.source for rejection in rejections}


class TestKindValidation:
    @pytest.fixture
    def planner(self) -> SeedPlanner:
        return SeedPlanner(SeedKindRegistry([FakeKind("alpha")]))

    def test_a_valid_file_is_planned(self, planner: SeedPlanner, tmp_path: Path) -> None:
        path = _write(tmp_path / "a.yaml", "alpha", "x", "y")
        plan = planner.plan([path])
        assert plan.rejections == []
        [batch] = plan.batches
        assert _names(batch) == ["x", "y"]

    def test_an_unregistered_kind_skips_the_file(
        self, planner: SeedPlanner, tmp_path: Path
    ) -> None:
        good = _write(tmp_path / "a.yaml", "alpha", "x")
        unknown = _write(tmp_path / "b.yaml", "omega", "x")
        plan = planner.plan([good, unknown])
        assert _sources(plan.rejections) == {str(unknown)}
        assert "not a registered kind" in plan.rejections[0].reason
        assert len(plan.batches) == 1

    def test_an_unsupported_version_skips_the_file(
        self, planner: SeedPlanner, tmp_path: Path
    ) -> None:
        path = _write(tmp_path / "a.yaml", "alpha", "x", version=3)
        plan = planner.plan([path])
        assert _sources(plan.rejections) == {str(path)}
        assert "version 3 is not supported" in plan.rejections[0].reason
        assert plan.batches == []

    def test_an_item_off_the_schema_skips_the_file(
        self, planner: SeedPlanner, tmp_path: Path
    ) -> None:
        good = _write(tmp_path / "a.yaml", "alpha", "x")
        broken = tmp_path / "b.yaml"
        broken.write_text(yaml.safe_dump({"kind": "alpha", "version": 1, "items": [{"no": 1}]}))
        plan = planner.plan([good, broken])
        assert _sources(plan.rejections) == {str(broken)}
        [batch] = plan.batches
        assert [file.source for file in batch.files] == [str(good)]

    def test_a_file_without_a_header_is_skipped(self, planner: SeedPlanner, tmp_path: Path) -> None:
        path = tmp_path / "a.yaml"
        path.write_text(yaml.safe_dump([{"name": "x"}]))
        plan = planner.plan([path])
        assert _sources(plan.rejections) == {str(path)}

    def test_unreadable_yaml_is_skipped(self, planner: SeedPlanner, tmp_path: Path) -> None:
        path = tmp_path / "a.yaml"
        path.write_text("kind: [unclosed")
        plan = planner.plan([path])
        assert _sources(plan.rejections) == {str(path)}

    def test_the_kind_check_skips_only_the_files_it_names(
        self, planner: SeedPlanner, tmp_path: Path
    ) -> None:
        good = _write(tmp_path / "a.yaml", "alpha", "x")
        bad = _write(tmp_path / "b.yaml", "alpha", "bad")
        plan = planner.plan([good, bad])
        assert _sources(plan.rejections) == {str(bad)}
        [batch] = plan.batches
        assert [file.source for file in batch.files] == [str(good)]

    def test_a_key_stated_by_two_files_skips_both(
        self, planner: SeedPlanner, tmp_path: Path
    ) -> None:
        first = _write(tmp_path / "a.yaml", "alpha", "x")
        second = _write(tmp_path / "b.yaml", "alpha", "x")
        other = _write(tmp_path / "c.yaml", "alpha", "y")
        plan = planner.plan([first, second, other])
        assert _sources(plan.rejections) == {str(first), str(second)}
        [batch] = plan.batches
        assert [file.source for file in batch.files] == [str(other)]


class TestPaths:
    def test_a_directory_is_read_recursively(self, tmp_path: Path) -> None:
        _write(tmp_path / "top.yaml", "alpha", "a")
        _write(tmp_path / "nested" / "deeper" / "inner.yml", "alpha", "b")
        (tmp_path / "nested" / "README.md").write_text("not a seed")
        plan = SeedPlanner(SeedKindRegistry([FakeKind("alpha")])).plan([tmp_path])
        assert plan.rejections == []
        [batch] = plan.batches
        assert sorted(_names(batch)) == ["a", "b"]

    def test_every_readable_format_is_collected(self, tmp_path: Path) -> None:
        (tmp_path / "a.json").write_text(
            json.dumps({"kind": "alpha", "version": 1, "items": [{"name": "a"}]})
        )
        (tmp_path / "b.toml").write_text('kind = "alpha"\nversion = 1\n[[items]]\nname = "b"\n')
        _write(tmp_path / "c.yaml", "alpha", "c")
        (tmp_path / "d.txt").write_text("not a seed")
        plan = SeedPlanner(SeedKindRegistry([FakeKind("alpha")])).plan([tmp_path])
        assert plan.rejections == []
        [batch] = plan.batches
        assert sorted(_names(batch)) == ["a", "b", "c"]

    def test_a_named_file_of_no_format_is_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "seed.txt"
        path.write_text("kind: alpha")
        plan = SeedPlanner(SeedKindRegistry([FakeKind("alpha")])).plan([path])
        assert [rejection.source for rejection in plan.rejections] == [str(path)]

    def test_a_path_named_twice_is_read_once(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "a.yaml", "alpha", "a")
        plan = SeedPlanner(SeedKindRegistry([FakeKind("alpha")])).plan([path, tmp_path])
        assert plan.rejections == []
        [batch] = plan.batches
        assert len(batch.files) == 1


class TestDependency:
    def test_kinds_are_planned_in_dependency_order(self, tmp_path: Path) -> None:
        registry = SeedKindRegistry([
            FakeKind("user", apply_after=["domain"]),
            FakeKind("keypair", apply_after=["user"]),
            FakeKind("domain"),
        ])
        paths = [
            _write(tmp_path / "1.yaml", "keypair", "k"),
            _write(tmp_path / "2.yaml", "user", "u"),
            _write(tmp_path / "3.yaml", "domain", "d"),
        ]
        plan = SeedPlanner(registry).plan(paths)
        assert [batch.kind.name() for batch in plan.batches] == ["domain", "user", "keypair"]

    def test_a_skipped_dependency_skips_its_dependents(self, tmp_path: Path) -> None:
        registry = SeedKindRegistry([
            FakeKind("domain"),
            FakeKind("user", apply_after=["domain"]),
            FakeKind("keypair", apply_after=["user"]),
            FakeKind("unrelated"),
        ])
        good_domain = _write(tmp_path / "1.yaml", "domain", "d")
        bad_domain = _write(tmp_path / "2.yaml", "domain", "bad")
        user = _write(tmp_path / "3.yaml", "user", "u")
        keypair = _write(tmp_path / "4.yaml", "keypair", "k")
        unrelated = _write(tmp_path / "5.yaml", "unrelated", "z")
        plan = SeedPlanner(registry).plan([good_domain, bad_domain, user, keypair, unrelated])
        assert _sources(plan.rejections) == {str(bad_domain), str(user), str(keypair)}
        assert [batch.kind.name() for batch in plan.batches] == ["domain", "unrelated"]

    def test_a_dependency_with_no_files_does_not_skip(self, tmp_path: Path) -> None:
        registry = SeedKindRegistry([FakeKind("domain"), FakeKind("user", apply_after=["domain"])])
        plan = SeedPlanner(registry).plan([_write(tmp_path / "1.yaml", "user", "u")])
        assert plan.rejections == []
        assert [batch.kind.name() for batch in plan.batches] == ["user"]

    def test_a_version_skip_counts_as_a_skipped_dependency(self, tmp_path: Path) -> None:
        registry = SeedKindRegistry([FakeKind("domain"), FakeKind("user", apply_after=["domain"])])
        domain = _write(tmp_path / "1.yaml", "domain", "d", version=9)
        user = _write(tmp_path / "2.yaml", "user", "u")
        plan = SeedPlanner(registry).plan([domain, user])
        assert _sources(plan.rejections) == {str(domain), str(user)}


class TestRegistry:
    def test_a_cycle_is_refused(self) -> None:
        with pytest.raises(InvalidSeedKindRegistry, match="each applied after the other"):
            SeedKindRegistry([FakeKind("a", apply_after=["b"]), FakeKind("b", apply_after=["a"])])

    def test_an_unregistered_dependency_is_refused(self) -> None:
        with pytest.raises(InvalidSeedKindRegistry, match="unregistered"):
            SeedKindRegistry([FakeKind("a", apply_after=["b"])])

    def test_a_name_registered_twice_is_refused(self) -> None:
        with pytest.raises(InvalidSeedKindRegistry, match="registered twice"):
            SeedKindRegistry([FakeKind("a"), FakeKind("a")])


class TestApply:
    async def test_items_are_written_in_dependency_order(self, tmp_path: Path) -> None:
        registry = SeedKindRegistry([FakeKind("user", apply_after=["domain"]), FakeKind("domain")])
        paths = [
            _write(tmp_path / "1.yaml", "user", "u"),
            _write(tmp_path / "2.yaml", "domain", "d"),
        ]
        repository = FakeRepository()
        await SeedApplier(repository).apply(SeedPlanner(registry).plan(paths), overwrite=False)
        assert repository.calls == [("create", "d"), ("create", "u")]

    async def test_an_item_referring_to_a_missing_row_fails_and_the_rest_are_written(
        self, tmp_path: Path
    ) -> None:
        plan = SeedPlanner(SeedKindRegistry([FakeKind("alpha")])).plan([
            _write(tmp_path / "a.yaml", "alpha", "x", "orphan", "z")
        ])
        repository = FakeRepository()
        results = await SeedApplier(repository).apply(plan, overwrite=False)
        assert results["alpha"] == SeedWriteResult(
            succeeded=["x", "z"],
            failed=[SeedItemFailure("orphan", "refers to a missing row (fk_fake)")],
        )

    async def test_a_conflicting_item_is_skipped_and_listed(self, tmp_path: Path) -> None:
        plan = SeedPlanner(SeedKindRegistry([FakeKind("alpha")])).plan([
            _write(tmp_path / "a.yaml", "alpha", "x", "y", "z")
        ])
        repository = FakeRepository(rows=["y"])
        results = await SeedApplier(repository).apply(plan, overwrite=False)
        assert results["alpha"] == SeedWriteResult(
            succeeded=["x", "z"],
            skipped=[SeedItemFailure("y", "exists (pk_fake)")],
        )
        assert repository.rows == {"x": "created", "y": "seeded", "z": "created"}

    async def test_overwrite_upserts_every_item(self, tmp_path: Path) -> None:
        plan = SeedPlanner(SeedKindRegistry([FakeKind("alpha")])).plan([
            _write(tmp_path / "a.yaml", "alpha", "x", "y")
        ])
        repository = FakeRepository(rows=["y"])
        results = await SeedApplier(repository).apply(plan, overwrite=True)
        assert results["alpha"] == SeedWriteResult(succeeded=["x", "y"])
        assert repository.calls == [("upsert", "x"), ("upsert", "y")]

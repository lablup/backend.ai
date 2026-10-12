"""Seed files are read, validated per kind and written in the kinds' dependency order."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast, override
from unittest.mock import MagicMock

import pytest
import yaml

from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.repositories.ops.v2.seed.provider import SeedOpsProvider
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite, SeedWriteItemResult
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.base import (
    SeedItem,
    SeedItems,
    SeedRejection,
)
from ai.backend.manager.seed.registry import SeedKindRegistry
from ai.backend.manager.seed.result import SeedItemFailure, SeedWriteResult
from ai.backend.manager.seed.runner import SeedApplier, SeedBatch, SeedPlanner
from ai.backend.manager.seed.types import SeedKind


class NamedItem(SeedItem):
    """An item whose specs are the item itself; a file stating one named ``bad`` is
    refused."""

    name: str

    @override
    def key(self) -> str:
        return self.name

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(upserter=cast(Any, self), field_upserters=(), field_purgers=())

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[NamedItem]]) -> list[SeedRejection]:
        return [
            SeedRejection(file.source, "states bad")
            for file in files
            if any(item.name == "bad" for item in file.items)
        ]


class OtherItem(NamedItem):
    """The item model of a second kind."""


def _registry(*names: SeedKind) -> SeedKindRegistry:
    """Kinds of :class:`NamedItem` read in version 1, applied in the order named."""
    return SeedKindRegistry(dict.fromkeys(names, (1, NamedItem)))


class FakeRepository(SeedRepository):
    """Keeps rows by item name. An item named ``orphan`` refers to a missing row, and one
    named ``taken`` collides with a row on another unique key."""

    rows: dict[str, str]
    calls: list[tuple[str, str]]

    def __init__(self, rows: Sequence[str] = ()) -> None:
        super().__init__(MagicMock(spec=SeedOpsProvider))
        self.rows = dict.fromkeys(rows, "seeded")
        self.calls = []

    @override
    async def partial_write(
        self, writes: Sequence[SeedWrite], overwrite: bool
    ) -> list[SeedWriteItemResult]:
        return [self._write(cast(NamedItem, write.upserter).name, overwrite) for write in writes]

    def _write(self, name: str, overwrite: bool) -> SeedWriteItemResult:
        self.calls.append(("upsert" if overwrite else "insert", name))
        if name == "orphan":
            return SeedWriteItemResult(
                written=False, error=ForeignKeyViolationError(constraint_name="fk_fake")
            )
        if name == "taken":
            return SeedWriteItemResult(
                written=False, error=UniqueConstraintViolationError(constraint_name="uq_fake")
            )
        if overwrite:
            self.rows[name] = "upserted"
            return SeedWriteItemResult(written=True)
        if name in self.rows:
            return SeedWriteItemResult(written=False)
        self.rows[name] = "inserted"
        return SeedWriteItemResult(written=True)


def _write(path: Path, kind: str, *names: str, version: int = 1) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({
            "kind": str(kind),
            "version": version,
            "items": [{"name": n} for n in names],
        })
    )
    return path


def _names(batch: SeedBatch) -> list[str]:
    return [item.name for file in batch.files for item in file.items]


def _sources(rejections: Sequence[SeedRejection]) -> set[str]:
    return {rejection.source for rejection in rejections}


class TestKindValidation:
    @pytest.fixture
    def planner(self) -> SeedPlanner:
        return SeedPlanner(_registry(SeedKind.DOMAIN))

    def test_a_valid_file_is_planned(self, planner: SeedPlanner, tmp_path: Path) -> None:
        path = _write(tmp_path / "a.yaml", "domain", "x", "y")
        plan = planner.plan([path])
        assert plan.rejections == []
        [batch] = plan.batches
        assert _names(batch) == ["x", "y"]

    def test_an_unregistered_kind_skips_the_file(
        self, planner: SeedPlanner, tmp_path: Path
    ) -> None:
        good = _write(tmp_path / "a.yaml", "domain", "x")
        unknown = _write(tmp_path / "b.yaml", "omega", "x")
        plan = planner.plan([good, unknown])
        assert _sources(plan.rejections) == {str(unknown)}
        assert "not a registered kind" in plan.rejections[0].reason
        assert len(plan.batches) == 1

    def test_an_unsupported_version_skips_the_file(
        self, planner: SeedPlanner, tmp_path: Path
    ) -> None:
        path = _write(tmp_path / "a.yaml", "domain", "x", version=3)
        plan = planner.plan([path])
        assert _sources(plan.rejections) == {str(path)}
        assert "version 3 is not supported" in plan.rejections[0].reason
        assert plan.batches == []

    def test_an_item_off_the_schema_skips_the_file(
        self, planner: SeedPlanner, tmp_path: Path
    ) -> None:
        good = _write(tmp_path / "a.yaml", "domain", "x")
        broken = tmp_path / "b.yaml"
        broken.write_text(yaml.safe_dump({"kind": "domain", "version": 1, "items": [{"no": 1}]}))
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
        good = _write(tmp_path / "a.yaml", "domain", "x")
        bad = _write(tmp_path / "b.yaml", "domain", "bad")
        plan = planner.plan([good, bad])
        assert _sources(plan.rejections) == {str(bad)}
        [batch] = plan.batches
        assert [file.source for file in batch.files] == [str(good)]

    def test_a_key_stated_by_two_files_skips_both(
        self, planner: SeedPlanner, tmp_path: Path
    ) -> None:
        first = _write(tmp_path / "a.yaml", "domain", "x")
        second = _write(tmp_path / "b.yaml", "domain", "x")
        other = _write(tmp_path / "c.yaml", "domain", "y")
        plan = planner.plan([first, second, other])
        assert _sources(plan.rejections) == {str(first), str(second)}
        [batch] = plan.batches
        assert [file.source for file in batch.files] == [str(other)]


class TestPaths:
    def test_a_directory_is_read_recursively(self, tmp_path: Path) -> None:
        _write(tmp_path / "top.yaml", "domain", "a")
        _write(tmp_path / "nested" / "deeper" / "inner.yml", "domain", "b")
        (tmp_path / "nested" / "README.md").write_text("not a seed")
        plan = SeedPlanner(_registry(SeedKind.DOMAIN)).plan([tmp_path])
        assert plan.rejections == []
        [batch] = plan.batches
        assert sorted(_names(batch)) == ["a", "b"]

    def test_every_readable_format_is_collected(self, tmp_path: Path) -> None:
        (tmp_path / "a.json").write_text(
            json.dumps({"kind": "domain", "version": 1, "items": [{"name": "a"}]})
        )
        (tmp_path / "b.toml").write_text('kind = "domain"\nversion = 1\n[[items]]\nname = "b"\n')
        _write(tmp_path / "c.yaml", "domain", "c")
        (tmp_path / "d.txt").write_text("not a seed")
        plan = SeedPlanner(_registry(SeedKind.DOMAIN)).plan([tmp_path])
        assert plan.rejections == []
        [batch] = plan.batches
        assert sorted(_names(batch)) == ["a", "b", "c"]

    def test_a_named_file_of_no_format_is_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "seed.txt"
        path.write_text("kind: alpha")
        plan = SeedPlanner(_registry(SeedKind.DOMAIN)).plan([path])
        assert [rejection.source for rejection in plan.rejections] == [str(path)]

    def test_a_path_named_twice_is_read_once(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "a.yaml", "domain", "a")
        plan = SeedPlanner(_registry(SeedKind.DOMAIN)).plan([path, tmp_path])
        assert plan.rejections == []
        [batch] = plan.batches
        assert len(batch.files) == 1


class TestOrder:
    def test_kinds_are_planned_in_the_order_seed_kind_declares(self, tmp_path: Path) -> None:
        paths = [
            _write(tmp_path / "1.yaml", SeedKind.PROJECT, "p"),
            _write(tmp_path / "2.yaml", SeedKind.USER, "u"),
            _write(tmp_path / "3.yaml", SeedKind.DOMAIN, "d"),
        ]
        registry = _registry(SeedKind.PROJECT, SeedKind.USER, SeedKind.DOMAIN)
        plan = SeedPlanner(registry).plan(paths)
        assert [batch.kind.name for batch in plan.batches] == [
            SeedKind.DOMAIN,
            SeedKind.USER,
            SeedKind.PROJECT,
        ]

    def test_a_skipped_file_leaves_the_other_kinds_planned(self, tmp_path: Path) -> None:
        bad_domain = _write(tmp_path / "1.yaml", SeedKind.DOMAIN, "bad")
        user = _write(tmp_path / "2.yaml", SeedKind.USER, "u")
        plan = SeedPlanner(_registry(SeedKind.DOMAIN, SeedKind.USER)).plan([bad_domain, user])
        assert _sources(plan.rejections) == {str(bad_domain)}
        assert [batch.kind.name for batch in plan.batches] == [SeedKind.USER]


class TestRead:
    @pytest.fixture
    def planner(self) -> SeedPlanner:
        return SeedPlanner(
            SeedKindRegistry({SeedKind.DOMAIN: (1, NamedItem), SeedKind.USER: (1, OtherItem)})
        )

    def test_each_kind_is_read_with_its_own_model(
        self, planner: SeedPlanner, tmp_path: Path
    ) -> None:
        _write(tmp_path / "a.yaml", "domain", "x")
        _write(tmp_path / "b.yaml", "user", "y")
        read = planner.read([tmp_path])
        assert read.rejections == []
        assert [type(item) for item in read.items(SeedKind.DOMAIN)] == [NamedItem]
        assert [type(item) for item in read.items(SeedKind.USER)] == [OtherItem]

    def test_the_checks_spanning_a_kind_are_left_to_the_plan(
        self, planner: SeedPlanner, tmp_path: Path
    ) -> None:
        _write(tmp_path / "a.yaml", "domain", "bad")
        read = planner.read([tmp_path])
        assert read.rejections == []
        assert [item.key() for item in read.items(SeedKind.DOMAIN)] == ["bad"]

    def test_a_file_that_cannot_be_read_is_listed(
        self, planner: SeedPlanner, tmp_path: Path
    ) -> None:
        good = _write(tmp_path / "a.yaml", "domain", "x")
        unknown = _write(tmp_path / "b.yaml", "omega", "y")
        read = planner.read([good, unknown])
        assert _sources(read.rejections) == {str(unknown)}
        assert [item.key() for item in read.items(SeedKind.DOMAIN)] == ["x"]


class TestApply:
    async def test_items_are_written_in_kind_order(self, tmp_path: Path) -> None:
        paths = [
            _write(tmp_path / "1.yaml", SeedKind.USER, "u"),
            _write(tmp_path / "2.yaml", SeedKind.DOMAIN, "d"),
        ]
        repository = FakeRepository()
        plan = SeedPlanner(_registry(SeedKind.USER, SeedKind.DOMAIN)).plan(paths)
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert repository.calls == [("insert", "d"), ("insert", "u")]

    async def test_an_item_referring_to_a_missing_row_fails_and_the_rest_are_written(
        self, tmp_path: Path
    ) -> None:
        plan = SeedPlanner(_registry(SeedKind.DOMAIN)).plan([
            _write(tmp_path / "a.yaml", "domain", "x", "orphan", "z")
        ])
        repository = FakeRepository()
        results = await SeedApplier(repository).apply(plan, overwrite=False)
        assert results[SeedKind.DOMAIN] == SeedWriteResult(
            succeeded=["x", "z"],
            failed=[SeedItemFailure("orphan", "refers to a missing row (fk_fake)")],
        )

    async def test_an_existing_item_is_kept_and_listed(self, tmp_path: Path) -> None:
        plan = SeedPlanner(_registry(SeedKind.DOMAIN)).plan([
            _write(tmp_path / "a.yaml", "domain", "x", "y", "z")
        ])
        repository = FakeRepository(rows=["y"])
        results = await SeedApplier(repository).apply(plan, overwrite=False)
        assert results[SeedKind.DOMAIN] == SeedWriteResult(
            succeeded=["x", "z"],
            skipped=[SeedItemFailure("y", "exists")],
        )
        assert repository.rows == {"x": "inserted", "y": "seeded", "z": "inserted"}

    @pytest.mark.parametrize("overwrite", [False, True], ids=["insert", "overwrite"])
    async def test_an_item_colliding_on_another_unique_key_is_skipped(
        self, tmp_path: Path, overwrite: bool
    ) -> None:
        plan = SeedPlanner(_registry(SeedKind.DOMAIN)).plan([
            _write(tmp_path / "a.yaml", "domain", "x", "taken")
        ])
        repository = FakeRepository()
        results = await SeedApplier(repository).apply(plan, overwrite=overwrite)
        assert results[SeedKind.DOMAIN] == SeedWriteResult(
            succeeded=["x"],
            skipped=[SeedItemFailure("taken", "collides with a row (uq_fake)")],
        )

    async def test_overwrite_upserts_every_item(self, tmp_path: Path) -> None:
        plan = SeedPlanner(_registry(SeedKind.DOMAIN)).plan([
            _write(tmp_path / "a.yaml", "domain", "x", "y")
        ])
        repository = FakeRepository(rows=["y"])
        results = await SeedApplier(repository).apply(plan, overwrite=True)
        assert results[SeedKind.DOMAIN] == SeedWriteResult(succeeded=["x", "y"])
        assert repository.calls == [("upsert", "x"), ("upsert", "y")]

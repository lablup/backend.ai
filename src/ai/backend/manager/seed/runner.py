from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ai.backend.common.serde.types import FileFormat
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWriteItemResult
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.base import (
    RootSeed,
    SeedItem,
    SeedItems,
    SeedReader,
    SeedRejection,
)
from ai.backend.manager.seed.registry import SeedKindModel, SeedKindRegistry
from ai.backend.manager.seed.result import SeedItemFailure, SeedWriteResult
from ai.backend.manager.seed.types import SeedKind

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class SeedBatch:
    """The accepted files of one kind."""

    kind: SeedKindModel
    files: list[SeedItems[Any]]

    def items(self) -> list[SeedItem]:
        return [item for file in self.files for item in file.items]


@dataclass
class SeedRead:
    """The items of every file read, each with its kind's model, and the files that could
    not be read."""

    by_kind: dict[str, list[SeedItems[Any]]] = field(default_factory=lambda: defaultdict(list))
    rejections: list[SeedRejection] = field(default_factory=list)

    def items(self, kind: str) -> list[SeedItem]:
        return [item for file in self.by_kind.get(kind, []) for item in file.items]


@dataclass
class SeedPlan:
    """The batches to write in the registry's kind order, and the files left out."""

    batches: list[SeedBatch] = field(default_factory=list)
    rejections: list[SeedRejection] = field(default_factory=list)


class SeedPlanner:
    """Reads and validates seed files without touching the database."""

    _registry: SeedKindRegistry
    _reader: SeedReader

    def __init__(self, registry: SeedKindRegistry) -> None:
        self._registry = registry
        self._reader = SeedReader()

    def read(self, paths: Sequence[Path]) -> SeedRead:
        """Each file's root first, then its items with the model the stated kind is
        registered with."""
        read = SeedRead()
        for path in self._collect(paths):
            source = str(path)
            try:
                root = self._reader.read(path)
                kind = self._kind_of(root)
                items = self._items(kind, root)
            except InvalidSeedDocument as e:
                read.rejections.append(SeedRejection(source, str(e)))
                continue
            read.by_kind[kind.name].append(SeedItems(source, items))
        return read

    def plan(self, paths: Sequence[Path]) -> SeedPlan:
        """The files read, less those failing a check spanning the files of their kind."""
        read = self.read(paths)
        plan = SeedPlan()
        for rejection in read.rejections:
            self._reject(plan, rejection)
        for kind in self._registry.ordered():
            files = read.by_kind.get(kind.name)
            if not files:
                continue
            rejections = [*self._duplicate_keys(kind, files), *kind.model.reject(files)]
            for rejection in rejections:
                self._reject(plan, rejection)
            rejected_sources = {rejection.source for rejection in rejections}
            accepted = [file for file in files if file.source not in rejected_sources]
            if accepted:
                plan.batches.append(SeedBatch(kind, accepted))
        return plan

    def _collect(self, paths: Sequence[Path]) -> list[Path]:
        """A directory contributes the files of a readable format; a file named on its own
        is read whatever its suffix, and refused if it names no format."""
        suffixes = FileFormat.all_suffixes()
        collected: dict[Path, None] = {}
        for path in paths:
            if path.is_dir():
                for entry in sorted(path.rglob("*")):
                    if entry.is_file() and entry.suffix.lower() in suffixes:
                        collected[entry] = None
            else:
                collected[path] = None
        return list(collected)

    def _kind_of(self, root: RootSeed[Any]) -> SeedKindModel:
        kind = self._registry.get(root.kind)
        if kind is None:
            raise InvalidSeedDocument(f"{root.kind!r} is not a registered kind")
        return kind

    def _items(self, kind: SeedKindModel, root: RootSeed[Any]) -> list[SeedItem]:
        if root.version != kind.version:
            raise InvalidSeedDocument(
                f"{kind.name} version {root.version} is not supported; version {kind.version}"
            )
        return [kind.model.model_validate(item) for item in root.items]

    def _duplicate_keys(
        self, kind: SeedKindModel, files: Sequence[SeedItems[Any]]
    ) -> list[SeedRejection]:
        sources_by_key: dict[str, set[str]] = defaultdict(set)
        for file in files:
            for item in file.items:
                sources_by_key[item.key()].add(file.source)
        return [
            SeedRejection(source, f"{len(sources)} files state {kind.name} {key}")
            for key, sources in sorted(sources_by_key.items())
            if len(sources) > 1
            for source in sorted(sources)
        ]

    def _reject(self, plan: SeedPlan, rejection: SeedRejection) -> None:
        log.error("skipped a seed file", seed_path=rejection.source, reason=rejection.reason)
        plan.rejections.append(rejection)


class SeedApplier:
    """Writes a plan's items kind by kind in order, in one transaction with a savepoint
    per item.

    The entity row and each field row are inserted unless a row holds their key, and
    ``overwrite`` upserts them instead. An item colliding on another unique key is
    skipped; an item referring to a missing row fails. Either leaves the rest written.
    """

    _repository: SeedRepository

    def __init__(self, repository: SeedRepository) -> None:
        self._repository = repository

    async def apply(self, plan: SeedPlan, overwrite: bool) -> dict[SeedKind, SeedWriteResult]:
        entries = [(batch.kind, item) for batch in plan.batches for item in batch.items()]
        written = await self._repository.partial_write(
            [item.write() for _, item in entries], overwrite
        )
        results = {batch.kind.name: SeedWriteResult() for batch in plan.batches}
        for (kind, item), item_result in zip(entries, written, strict=True):
            self._record(results[kind.name], kind, item.key(), item_result)
        for name, result in results.items():
            log.info(
                "applied a seed kind",
                seed_kind_name=name,
                succeeded_count=len(result.succeeded),
                skipped_count=len(result.skipped),
                failed_count=len(result.failed),
            )
        return results

    def _record(
        self,
        result: SeedWriteResult,
        kind: SeedKindModel,
        key: str,
        item_result: SeedWriteItemResult,
    ) -> None:
        match item_result.error:
            case None if item_result.written:
                result.succeeded.append(key)
            case None:
                result.skipped.append(SeedItemFailure(key, "exists"))
            case UniqueConstraintViolationError() as e:
                log.info(
                    "skipped a seed item colliding with a row",
                    seed_kind_name=kind.name,
                    item_key=key,
                    constraint_name=e.constraint_name,
                )
                result.skipped.append(
                    SeedItemFailure(key, f"collides with a row ({e.constraint_name})")
                )
            case ForeignKeyViolationError() as e:
                log.warning(
                    "failed a seed item referring to a missing row",
                    seed_kind_name=kind.name,
                    item_key=key,
                    constraint_name=e.constraint_name,
                )
                result.failed.append(
                    SeedItemFailure(key, f"refers to a missing row ({e.constraint_name})")
                )

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from ai.backend.common.serde.types import FileFormat
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.seed.document import SeedDocument, SeedDocumentReader
from ai.backend.manager.seed.kind import SeedFileItems, SeedKind, SeedRejection
from ai.backend.manager.seed.registry import SeedKindRegistry
from ai.backend.manager.seed.result import SeedItemFailure, SeedWriteResult

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class SeedBatch:
    """The accepted files of one kind."""

    kind: SeedKind[Any]
    files: list[SeedFileItems[Any]]

    def items(self) -> list[BaseModel]:
        return [item for file in self.files for item in file.items]


@dataclass
class SeedPlan:
    """The batches to write in dependency order, and the files left out."""

    batches: list[SeedBatch] = field(default_factory=list)
    rejections: list[SeedRejection] = field(default_factory=list)


class SeedPlanner:
    """Reads and validates seed files without touching the database."""

    _registry: SeedKindRegistry
    _reader: SeedDocumentReader

    def __init__(self, registry: SeedKindRegistry) -> None:
        self._registry = registry
        self._reader = SeedDocumentReader()

    def plan(self, paths: Sequence[Path]) -> SeedPlan:
        plan = SeedPlan()
        by_kind: dict[str, list[SeedFileItems[Any]]] = defaultdict(list)
        rejected_kinds: set[str] = set()
        for path in self._collect(paths):
            source = str(path)
            try:
                document = self._reader.read(path)
                kind = self._kind_of(document)
            except InvalidSeedDocument as e:
                self._reject(plan, SeedRejection(source, str(e)))
                continue
            try:
                items = self._items(kind, document)
            except InvalidSeedDocument as e:
                self._reject(plan, SeedRejection(source, str(e)))
                rejected_kinds.add(kind.name())
                continue
            by_kind[kind.name()].append(SeedFileItems(source, items))
        for kind in self._registry.ordered():
            files = by_kind.get(kind.name())
            if not files:
                continue
            blocked = sorted(kind.apply_after() & rejected_kinds)
            if blocked:
                rejected_kinds.add(kind.name())
                for file in files:
                    reason = f"applied after {', '.join(blocked)}, which has a skipped file"
                    self._reject(plan, SeedRejection(file.source, reason))
                continue
            rejections = [*self._duplicate_keys(kind, files), *kind.reject(files)]
            for rejection in rejections:
                self._reject(plan, rejection)
            rejected_sources = {rejection.source for rejection in rejections}
            if rejected_sources:
                rejected_kinds.add(kind.name())
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

    def _kind_of(self, document: SeedDocument) -> SeedKind[Any]:
        kind = self._registry.get(document.kind)
        if kind is None:
            raise InvalidSeedDocument(f"{document.kind!r} is not a registered kind")
        return kind

    def _items(self, kind: SeedKind[Any], document: SeedDocument) -> list[BaseModel]:
        if document.version not in kind.versions():
            raise InvalidSeedDocument(
                f"{kind.name()} version {document.version} is not supported;"
                f" one of {sorted(kind.versions())}"
            )
        schema = kind.schema()
        try:
            return [schema.model_validate(item) for item in document.items]
        except ValidationError as e:
            raise InvalidSeedDocument(f"an item does not fit {kind.name()}: {e}") from e

    def _duplicate_keys(
        self, kind: SeedKind[Any], files: Sequence[SeedFileItems[Any]]
    ) -> list[SeedRejection]:
        sources_by_key: dict[str, set[str]] = defaultdict(set)
        for file in files:
            for item in file.items:
                sources_by_key[kind.key(item)].add(file.source)
        return [
            SeedRejection(source, f"{len(sources)} files state {kind.name()} {key}")
            for key, sources in sorted(sources_by_key.items())
            if len(sources) > 1
            for source in sorted(sources)
        ]

    def _reject(self, plan: SeedPlan, rejection: SeedRejection) -> None:
        log.error("skipped a seed file", seed_path=rejection.source, reason=rejection.reason)
        plan.rejections.append(rejection)


class SeedApplier:
    """Writes a plan's items kind by kind in order, one transaction per item.

    An item colliding with a row already there is skipped, and ``overwrite`` upserts it
    instead; an item referring to a missing row fails. Either leaves the rest written.
    """

    _repository: OpsRepository[Any]

    def __init__(self, repository: OpsRepository[Any]) -> None:
        self._repository = repository

    async def apply(self, plan: SeedPlan, overwrite: bool) -> dict[str, SeedWriteResult]:
        results: dict[str, SeedWriteResult] = {}
        for batch in plan.batches:
            kind = batch.kind
            result = SeedWriteResult()
            for item in batch.items():
                key = kind.key(item)
                try:
                    await self._write(kind, item, overwrite)
                except UniqueConstraintViolationError as e:
                    log.info(
                        "skipped a seed item that exists",
                        seed_kind_name=kind.name(),
                        item_key=key,
                        constraint_name=e.constraint_name,
                    )
                    result.skipped.append(SeedItemFailure(key, f"exists ({e.constraint_name})"))
                    continue
                except ForeignKeyViolationError as e:
                    log.warning(
                        "failed a seed item referring to a missing row",
                        seed_kind_name=kind.name(),
                        item_key=key,
                        constraint_name=e.constraint_name,
                    )
                    result.failed.append(
                        SeedItemFailure(key, f"refers to a missing row ({e.constraint_name})")
                    )
                    continue
                result.succeeded.append(key)
            log.info(
                "applied a seed kind",
                seed_kind_name=kind.name(),
                succeeded_count=len(result.succeeded),
                skipped_count=len(result.skipped),
                failed_count=len(result.failed),
            )
            results[kind.name()] = result
        return results

    async def _write(self, kind: SeedKind[Any], item: BaseModel, overwrite: bool) -> None:
        if overwrite:
            upsert = kind.upsert(item)
            await self._repository.upsert_entity_with_fields(
                upsert.upserter, upsert.field_upserters, upsert.field_purgers
            )
            return
        creation = kind.creation(item)
        await self._repository.create_entity_with_fields(creation.creator, creation.field_creators)

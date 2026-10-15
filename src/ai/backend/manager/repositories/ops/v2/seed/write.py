"""Seed writes: each item's rows inserted unless a row holds their key, or upserted, one
savepoint per item."""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.errors.permission import VirtualEntityNotFound
from ai.backend.manager.errors.repository import ForeignKeyViolationError, RepositoryIntegrityError
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite, SeedWriteItemResult
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps


class V2SeedWriteOps(V2WriteOps):
    """The v2 write ops plus the seed item write.

    A violation a spec maps to a domain error is answered as the violation it was mapped
    from, so it fails its own item and no other. A scope with no virtual entity fails its
    item as a missing row.
    """

    async def partial_write_seed_items(
        self, writes: Sequence[SeedWrite], overwrite: bool
    ) -> list[SeedWriteItemResult]:
        """Write each item in its own savepoint, in the order given, so an item refused by
        a constraint leaves the rest written. Any other error raises."""
        results: list[SeedWriteItemResult] = []
        for write in writes:
            try:
                async with self._sess.begin_nested():
                    written = await self._write_seed_item(write, overwrite)
            except RepositoryIntegrityError as e:
                results.append(SeedWriteItemResult(written=False, error=e))
                continue
            except VirtualEntityNotFound as e:
                missing = ForeignKeyViolationError(
                    str(e), table_name=VirtualEntityRow.__tablename__
                )
                results.append(SeedWriteItemResult(written=False, error=missing))
                continue
            except BackendAIError as e:
                if not isinstance(e.__cause__, RepositoryIntegrityError):
                    raise
                results.append(SeedWriteItemResult(written=False, error=e.__cause__))
                continue
            results.append(SeedWriteItemResult(written=written))
        return results

    async def _write_seed_item(self, write: SeedWrite, overwrite: bool) -> bool:
        """Whether any row was written: inserted, or under an overwrite updated with the
        values its spec states. A field row is written under an entity that was already
        there as well."""
        entity = await self.insert_entity_if_absent(write.upserter)
        written = entity.inserted
        if overwrite and not entity.inserted:
            await self.upsert_entity(write.upserter)
            written = bool(write.upserter.build_update_values())
        if overwrite:
            for purger in write.field_purgers:
                await self.batch_purge_field_entities(entity.entity_id, purger)
        inserted = await self.atomic_insert_field_entities_if_absent(
            entity.entity_id, write.field_upserters
        )
        written = written or any(inserted)
        standing = [
            upserter
            for upserter, is_new in zip(write.field_upserters, inserted, strict=True)
            if not is_new
        ]
        if overwrite and standing:
            await self.atomic_upsert_field_entities(entity.entity_id, standing)
            written = written or any(upserter.build_update_values() for upserter in standing)
        for user_id in write.granted_users:
            granted = await self.grant_roles(user_id, [RoleID(entity.entity_id)])
            written = written or any(granted)
        return written

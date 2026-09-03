"""Permission writes: what a role holds per (scope, entity_type) key.

Storage is one ``permissions`` row per operation bit. A READ or UPDATE row with
``all_fields`` grants the operation on every field; one without grants it on its
``permission_fields`` paths and their descendants. The other bits always carry
``all_fields`` and no path rows.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.permission.id import FieldPath, PermissionID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.errors.permission import InvalidFieldPermission
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_field import PermissionFieldRow
from ai.backend.manager.models.specs.permission import (
    PermissionEntry,
    PermissionKey,
    PermissionRevocation,
)
from ai.backend.manager.repositories.ops.v2.permission.read import PermissionReadOps
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps

_PATH_PATTERN = re.compile(r"^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*$")


@dataclass(frozen=True)
class _BitRow:
    """One per-bit row of a key, with its scoped paths."""

    id: PermissionID
    all_fields: bool
    paths: frozenset[FieldPath]


class PermissionWriteOps(V2WriteOps, PermissionReadOps):
    """The general v2 write ops plus the role permission writes."""

    async def set_permissions(self, role_id: RoleID, entries: Sequence[PermissionEntry]) -> None:
        """State what each entry's key holds now; the key's previous rows go,
        their path rows with them."""
        if not entries:
            return
        for entry in entries:
            self._validate_entry(entry)
        await self._sess.execute(
            sa.delete(PermissionRow).where(
                PermissionRow.role_id == role_id,
                self._key_filter([e.key() for e in entries]),
            )
        )
        for entry in entries:
            for bit in self._bits_of(entry.permission):
                await self._insert_bit_row(role_id, entry, bit, True, ())
            for bit, paths in self._scoped_paths(entry.fields).items():
                await self._insert_bit_row(role_id, entry, bit, False, paths)

    async def widen_permissions(self, role_id: RoleID, entries: Sequence[PermissionEntry]) -> None:
        """Add each entry to what its key holds, never taking away.

        A bit on every field makes that operation's path rows redundant, so they
        go; paths join an operation already scoped, and change nothing on one
        already open on every field.
        """
        if not entries:
            return
        for entry in entries:
            self._validate_entry(entry)
        for entry in entries:
            current = await self._locked_bit_rows(role_id, entry.key())
            for bit in self._bits_of(entry.permission):
                row = current.get(bit)
                if row is None:
                    await self._insert_bit_row(role_id, entry, bit, True, ())
                elif not row.all_fields:
                    await self._sess.execute(
                        sa.update(PermissionRow)
                        .values(all_fields=True)
                        .where(PermissionRow.id == row.id)
                    )
                    await self._delete_paths(row.id, row.paths)
            for bit, paths in self._scoped_paths(entry.fields).items():
                row = current.get(bit)
                if row is None:
                    await self._insert_bit_row(role_id, entry, bit, False, paths)
                elif not row.all_fields:
                    await self._insert_paths(row.id, paths)

    async def revoke_permissions(
        self, role_id: RoleID, revocations: Sequence[PermissionRevocation]
    ) -> None:
        """Take each revocation's bits back from its key.

        A ``permission`` bit removes its row, path rows with it. A ``fields`` bit
        removes the path and its descendants from that operation's row; a row
        left with nothing goes. Membership edges are never touched.
        """
        for revocation in revocations:
            for name, bits in revocation.fields.items():
                self._validate_field(name, bits)
            current = await self._locked_bit_rows(role_id, revocation.key())
            for bit in self._bits_of(revocation.permission):
                row = current.pop(bit, None)
                if row is not None:
                    await self._sess.execute(
                        sa.delete(PermissionRow).where(PermissionRow.id == row.id)
                    )
            for bit, paths in self._scoped_paths(revocation.fields).items():
                row = current.get(bit)
                if row is None or row.all_fields:
                    continue
                gone = frozenset(
                    p for p in row.paths if any(self._covers(target, p) for target in paths)
                )
                await self._delete_paths(row.id, gone)
                if gone == row.paths:
                    await self._sess.execute(
                        sa.delete(PermissionRow).where(PermissionRow.id == row.id)
                    )

    # -- Rows ------------------------------------------------------------------------

    async def _insert_bit_row(
        self,
        role_id: RoleID,
        entry: PermissionEntry,
        bit: Permission,
        all_fields: bool,
        paths: Iterable[FieldPath],
    ) -> None:
        row = PermissionRow(
            role_id=role_id,
            scope_type=entry.scope.entity_type(),
            scope_id=str(entry.scope),
            entity_type=entry.entity_type,
            permission=bit,
            all_fields=all_fields,
        )
        self._sess.add(row)
        await self._sess.flush()
        await self._insert_paths(row.id, paths)

    async def _insert_paths(self, permission_id: PermissionID, paths: Iterable[FieldPath]) -> None:
        values = [{"permission_id": permission_id, "path": path} for path in paths]
        if not values:
            return
        await self._sess.execute(
            pg_insert(PermissionFieldRow).values(values).on_conflict_do_nothing()
        )

    async def _delete_paths(self, permission_id: PermissionID, paths: Iterable[FieldPath]) -> None:
        targets = list(paths)
        if not targets:
            return
        await self._sess.execute(
            sa.delete(PermissionFieldRow).where(
                PermissionFieldRow.permission_id == permission_id,
                PermissionFieldRow.path.in_(targets),
            )
        )

    async def _locked_bit_rows(
        self, role_id: RoleID, key: PermissionKey
    ) -> dict[Permission, _BitRow]:
        """The key's per-bit rows with their paths, row-locked for the
        read-merge-write."""
        rows = (
            await self._sess.execute(
                sa.select(PermissionRow.id, PermissionRow.permission, PermissionRow.all_fields)
                .where(PermissionRow.role_id == role_id, self._key_filter([key]))
                .with_for_update()
            )
        ).all()
        if not rows:
            return {}
        paths: dict[PermissionID, set[FieldPath]] = {row.id: set() for row in rows}
        field_rows = (
            await self._sess.execute(
                sa.select(PermissionFieldRow.permission_id, PermissionFieldRow.path).where(
                    PermissionFieldRow.permission_id.in_(list(paths))
                )
            )
        ).all()
        for field_row in field_rows:
            paths[field_row.permission_id].add(field_row.path)
        return {
            Permission(row.permission): _BitRow(
                id=row.id, all_fields=row.all_fields, paths=frozenset(paths[row.id])
            )
            for row in rows
        }

    # -- Values ----------------------------------------------------------------------

    def _validate_entry(self, entry: PermissionEntry) -> None:
        for name, bits in entry.fields.items():
            self._validate_field(name, bits)
            if bits & entry.permission:
                raise InvalidFieldPermission(
                    f"Field {name!r} states {bits & entry.permission!r}, which the entry"
                    " already grants on every field."
                )

    def _validate_field(self, path: FieldPath, bits: Permission) -> None:
        if not _PATH_PATTERN.match(path):
            raise InvalidFieldPermission(f"Malformed field path {path!r}.")
        if bits & ~Permission.field_bearing() or not bits:
            raise InvalidFieldPermission(
                f"Field {path!r} carries {bits!r}; a field scope holds READ|UPDATE bits only."
            )

    def _covers(self, ancestor: FieldPath, path: FieldPath) -> bool:
        return ancestor == path or path.startswith(ancestor + ".")

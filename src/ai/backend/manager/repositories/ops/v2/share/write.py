"""Share writes: own under a cap, lent to a scope alone.

``replace_share`` / ``replace_share_fields`` replace everything before with what holds now,
``widen_*`` add to it, ``narrow_*`` take part of it back, ``unshare`` takes all of it. Every-field caps
and field paths are different statements and keep different methods. An invitation
is a share on offer, so accepting one lives here too, and so does moving an entity
between the scopes it is created in.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping, Sequence

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.id import FieldPath
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.entity_invitation.types import EntityInvitationData
from ai.backend.manager.errors.permission import InvalidFieldPermission
from ai.backend.manager.models.entity_invitation.updaters import EntityInvitationAcceptUpdater
from ai.backend.manager.repositories.ops.v2.cap import V2CapOps
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps

_PATH_PATTERN = re.compile(r"^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*$")


class V2ShareWriteOps(V2WriteOps, V2CapOps):
    """The general write ops plus the shares over existing entities."""

    # -- replace --------------------------------------------------------------------------

    async def replace_share(
        self, scope: EntityIdentifier, entity: EntityIdentifier, cap: Permission
    ) -> None:
        """Lend the entity to the scope, ``cap`` on every field — zero included. States
        what holds now: whatever the scope had of the entity, share or own, goes."""
        share_id = await self._reset_share(scope, entity)
        await self._insert_caps(share_id, dict.fromkeys(self._bits_of(cap)))

    async def replace_share_fields(
        self,
        scope: EntityIdentifier,
        entity: EntityIdentifier,
        fields: Mapping[Permission, Sequence[FieldPath]],
    ) -> None:
        """Lend the entity to the scope on the listed paths only: READ and UPDATE bits,
        a path covering its descendants. States what holds now: whatever the scope had
        of the entity, share or own, goes. A share mixing every-field bits and paths is
        ``replace_share`` then ``widen_share_fields``."""
        self._validate_fields(fields)
        share_id = await self._reset_share(scope, entity)
        await self._insert_caps(share_id, dict(fields))

    # -- widen ----------------------------------------------------------------------------

    async def widen_share(
        self, scope: EntityIdentifier, entity: EntityIdentifier, cap: Permission
    ) -> None:
        """Add ``cap`` on every field to what the scope already holds, never taking
        away: a bit reaching every field drops the paths it makes redundant, and an
        entity the scope owns stays as it is."""
        await self._widen_share(scope, entity, dict.fromkeys(self._bits_of(cap)))

    async def widen_share_fields(
        self,
        scope: EntityIdentifier,
        entity: EntityIdentifier,
        fields: Mapping[Permission, Sequence[FieldPath]],
    ) -> None:
        """Add paths to what the scope already holds, never taking away: paths join a
        bit lent on paths, change nothing on a bit lent on every field, and an entity
        the scope owns stays as it is."""
        self._validate_fields(fields)
        await self._widen_share(scope, entity, dict(fields))

    # -- narrow ---------------------------------------------------------------------------

    async def narrow_share(
        self, scope: EntityIdentifier, entity: EntityIdentifier, cap: Permission
    ) -> None:
        """Take the bits of ``cap`` back from the share, paths with them. The share
        itself stays, listed with whatever is left; silent on a bit never lent and on
        an entity the scope owns."""
        await self._narrow_share(scope, entity, dict.fromkeys(self._bits_of(cap)))

    async def narrow_share_fields(
        self,
        scope: EntityIdentifier,
        entity: EntityIdentifier,
        fields: Mapping[Permission, Sequence[FieldPath]],
    ) -> None:
        """Take the listed paths and their descendants back from the bits they name.
        A bit left with no path goes; a bit lent on every field is not narrowed by a
        path. Silent on what was never lent and on an entity the scope owns."""
        self._validate_fields(fields)
        await self._narrow_share(scope, entity, dict(fields))

    # -- unshare, ownership, invitation ------------------------------------------------

    async def unshare(self, scope: EntityIdentifier, entities: Sequence[EntityIdentifier]) -> None:
        """Take the entities back from the scope, cap rows and paths with them. What
        the scope owns is not a share and stays; silent on what was never shared."""
        await self._unshare(scope, entities)

    async def transfer(
        self,
        from_scopes: Collection[EntityIdentifier],
        to_scopes: Collection[EntityIdentifier],
        entity: EntityIdentifier,
    ) -> None:
        """Move the entity: the scopes it was created in stop owning and governing it,
        and the new ones own and govern it as if it had been created there. A share
        the new scope held becomes own."""
        await self._removed_from(from_scopes, entity)
        await self._created_in(to_scopes, entity)

    async def accept_invitation(
        self, updater: EntityInvitationAcceptUpdater
    ) -> EntityInvitationData | None:
        """Settle the invitation as accepted and share its entity to the invitee.

        ``None`` when nothing was settled — the invitation is gone, already answered,
        or addressed to somebody else; the guards do not say which. Turning one down
        shares nothing and goes through the plain guarded update instead, which is why
        only this direction is a primitive: the settle and the share cannot come apart.

        The share widens rather than states: an offer is somebody else's, and accepting
        one must not cost the invitee access they already had. An invitation without a
        cap hands over every operation on every field.
        """
        row = await self._update_guarded_row_returning(
            updater.row_class,
            updater.target_id_column(),
            updater.target_id_value(),
            updater.guard_conditions(),
            updater.build_values(),
            updater.integrity_error_checks,
        )
        if row is None:
            return None
        data = updater.to_data(row)
        await self.widen_share(
            updater.invitee_user_id,
            data.target,
            data.permission_cap if data.permission_cap is not None else Permission.full(),
        )
        return data

    # -- values ---------------------------------------------------------------------------

    def _validate_fields(self, fields: Mapping[Permission, Sequence[FieldPath]]) -> None:
        if not fields:
            raise InvalidFieldPermission("A field share names at least one operation.")
        for bit, paths in fields.items():
            if bit not in (Permission.READ, Permission.UPDATE):
                raise InvalidFieldPermission(
                    f"{bit!r} cannot be scoped to paths; a field share holds READ or UPDATE."
                )
            if not paths:
                raise InvalidFieldPermission(f"{bit!r} names no path.")
            for path in paths:
                if not _PATH_PATTERN.match(path):
                    raise InvalidFieldPermission(f"Malformed field path {path!r}.")

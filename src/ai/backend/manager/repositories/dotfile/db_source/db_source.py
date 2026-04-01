"""Database source for dotfile repository operations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.types import AccessKey
from ai.backend.manager.data.dotfile.types import DotfileEntry, DotfileQueryResult
from ai.backend.manager.models.domain import domains, query_domain_dotfiles
from ai.backend.manager.models.group import (
    association_groups_users as agus,
)
from ai.backend.manager.models.group import (
    groups,
    query_group_domain,
    query_group_dotfiles,
)
from ai.backend.manager.models.keypair import keypairs, query_bootstrap_script, query_owned_dotfiles
from ai.backend.manager.models.vfolder import query_accessible_vfolders, vfolders

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class DotfileDBSource:
    """Database source for dotfile operations across domain, group, and user scopes."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    # --- Domain dotfiles ---

    async def get_domain_dotfiles(self, domain_name: str) -> DotfileQueryResult:
        async with self._db.begin_readonly() as conn:
            raw_dotfiles, leftover = await query_domain_dotfiles(conn, domain_name)
            entries = (
                [DotfileEntry(path=d["path"], perm=d["perm"], data=d["data"]) for d in raw_dotfiles]
                if raw_dotfiles is not None
                else []
            )
            return DotfileQueryResult(
                entries=entries,
                leftover_space=leftover,
            )

    async def save_domain_dotfiles(self, domain_name: str, packed: bytes) -> None:
        async with self._db.begin() as conn:
            query = domains.update().values(dotfiles=packed).where(domains.c.name == domain_name)
            await conn.execute(query)

    # --- Group dotfiles ---

    async def get_group_dotfiles(self, group_id: uuid.UUID) -> DotfileQueryResult:
        async with self._db.begin_readonly() as conn:
            raw_dotfiles, leftover = await query_group_dotfiles(conn, group_id)
            entries = (
                [DotfileEntry(path=d["path"], perm=d["perm"], data=d["data"]) for d in raw_dotfiles]
                if raw_dotfiles is not None
                else []
            )
            return DotfileQueryResult(
                entries=entries,
                leftover_space=leftover,
            )

    async def save_group_dotfiles(self, group_id: uuid.UUID, packed: bytes) -> None:
        async with self._db.begin() as conn:
            query = groups.update().values(dotfiles=packed).where(groups.c.id == group_id)
            await conn.execute(query)

    # --- User dotfiles ---

    async def get_user_dotfiles(self, access_key: str) -> DotfileQueryResult:
        async with self._db.begin_readonly() as conn:
            raw_dotfiles, leftover = await query_owned_dotfiles(conn, AccessKey(access_key))
            entries = [
                DotfileEntry(path=d["path"], perm=d["perm"], data=d["data"]) for d in raw_dotfiles
            ]
            return DotfileQueryResult(
                entries=entries,
                leftover_space=leftover,
            )

    async def save_user_dotfiles(self, access_key: str, packed: bytes) -> None:
        async with self._db.begin() as conn:
            query = (
                keypairs.update().values(dotfiles=packed).where(keypairs.c.access_key == access_key)
            )
            await conn.execute(query)

    # --- vFolder conflict check ---

    async def check_vfolder_conflict(self, user_uuid: uuid.UUID, path: str) -> bool:
        """Check if a dotfile path conflicts with a user's vFolder name."""
        async with self._db.begin_readonly() as conn:
            duplicate_vfolder = await query_accessible_vfolders(
                conn,
                user_uuid,
                extra_vf_conds=(vfolders.c.name == path),
            )
            return len(duplicate_vfolder) > 0

    # --- Group resolution ---

    async def resolve_group(
        self,
        group_id_or_name: str | uuid.UUID,
        group_domain: str | None,
        user_domain: str,
    ) -> tuple[UUID | None, str | None]:
        """Resolve a group identifier (name or UUID) to a (group_id, domain) pair."""
        # Try to parse as UUID if string
        if isinstance(group_id_or_name, str):
            try:
                group_id_or_name = UUID(group_id_or_name)
            except ValueError:
                pass

        async with self._db.begin_readonly() as conn:
            if isinstance(group_id_or_name, UUID):
                resolved_domain = await query_group_domain(conn, group_id_or_name)
                return group_id_or_name, resolved_domain

            # group_id_or_name is a group name (non-UUID string)
            domain = group_domain if group_domain is not None else user_domain
            query = (
                sa.select(groups.c.id)
                .select_from(groups)
                .where(groups.c.domain_name == domain)
                .where(groups.c.name == group_id_or_name)
            )
            group_id = await conn.scalar(query)
            return group_id, domain

    # --- Group membership ---

    async def get_user_group_ids(self, user_uuid: uuid.UUID) -> list[uuid.UUID]:
        """Get the list of group IDs a user belongs to."""
        async with self._db.begin_readonly() as conn:
            query = sa.select(agus.c.group_id).select_from(agus).where(agus.c.user_id == user_uuid)
            result = await conn.execute(query)
            return [row.group_id for row in result.fetchall()]

    # --- Bootstrap script ---

    async def get_bootstrap_script(self, access_key: str) -> tuple[str, int]:
        async with self._db.begin_readonly() as conn:
            return await query_bootstrap_script(conn, AccessKey(access_key))

    async def save_bootstrap_script(self, access_key: str, script: str) -> None:
        async with self._db.begin() as conn:
            query = (
                keypairs.update()
                .values(bootstrap_script=script)
                .where(keypairs.c.access_key == access_key)
            )
            await conn.execute(query)

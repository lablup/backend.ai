from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, noload, selectinload
from sqlalchemy.orm.strategy_options import _AbstractLoad

from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AccessKey, ImageAlias, SessionId
from ai.backend.manager.api.session import find_dependency_sessions
from ai.backend.manager.data.image.types import ImageIdentifier, ImageStatus
from ai.backend.manager.data.kernel.types import KernelListResult
from ai.backend.manager.data.session.types import SessionListResult
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.kernel import SessionAlreadyExists, SessionNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.group import groups
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.scaling_group import scaling_groups
from ai.backend.manager.models.session import (
    KernelLoadingStrategy,
    SessionDependencyRow,
    SessionRow,
)
from ai.backend.manager.models.session_template import session_templates
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
from ai.backend.manager.utils import query_userinfo


class SessionDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_session_owner(self, session_id: str | SessionId) -> UserData:
        async with self._db.begin_readonly_session() as db_sess:
            query = (
                sa.select(UserRow)
                .join(SessionRow, SessionRow.user_uuid == UserRow.uuid)
                .where(SessionRow.id == session_id)
            )
            user = await db_sess.scalar(query)
            if user is None:
                raise SessionNotFound(f"Session with id {session_id} not found")
            return UserData.from_row(user)

    async def get_session_validated(
        self,
        session_name_or_id: str | SessionId,
        owner_access_key: AccessKey,
        kernel_loading_strategy: KernelLoadingStrategy = KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        allow_stale: bool = False,
        eager_loading_op: Sequence[_AbstractLoad] | None = None,
    ) -> SessionRow:
        async with self._db.begin_readonly_session() as db_sess:
            return await SessionRow.get_session(
                db_sess,
                session_name_or_id,
                owner_access_key,
                kernel_loading_strategy=kernel_loading_strategy,
                allow_stale=allow_stale,
                eager_loading_op=list(eager_loading_op) if eager_loading_op else None,
            )

    async def match_sessions(
        self,
        id_or_name_prefix: str,
        owner_access_key: AccessKey,
    ) -> list[SessionRow]:
        async with self._db.begin_readonly_session() as db_sess:
            return await SessionRow.match_sessions(
                db_sess,
                id_or_name_prefix,
                owner_access_key,
            )

    async def get_session_to_determine_status(
        self,
        session_id: SessionId,
    ) -> SessionRow:
        async with self._db.begin_readonly_session() as db_sess:
            return await SessionRow.get_session_to_determine_status(db_sess, session_id)

    async def get_template_by_id(
        self,
        template_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        async with self._db.begin_readonly() as conn:
            query = (
                sa.select(session_templates.c.template)
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id) & session_templates.c.is_active,
                )
            )
            return await conn.scalar(query)

    async def get_template_info_by_id(
        self,
        template_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        async with self._db.begin_readonly() as conn:
            query = (
                sa.select(session_templates)
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id) & session_templates.c.is_active,
                )
            )
            result = await conn.execute(query)
            template_info = result.fetchone()
            return dict(template_info) if template_info else None

    async def update_session_name(
        self,
        session_name_or_id: str | SessionId,
        new_name: str,
        owner_access_key: AccessKey,
    ) -> SessionRow:
        async def _update(db_session: AsyncSession) -> SessionRow:
            # Check if new name already exists for this owner
            try:
                await SessionRow.get_session(
                    db_session,
                    new_name,
                    owner_access_key,
                    kernel_loading_strategy=KernelLoadingStrategy.NONE,
                )
                raise SessionAlreadyExists(f"Session with name '{new_name}' already exists")
            except SessionNotFound:
                pass  # Session not found, which is good

            # Get the target session
            session_row = await SessionRow.get_session(
                db_session,
                session_name_or_id,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
            )

            # Update session name
            session_row.name = new_name
            for kernel in session_row.kernels:
                kernel.session_name = new_name

            return session_row

        async with self._db.begin_session() as db_sess:
            return await _update(db_sess)

    async def get_container_registry(
        self,
        registry_hostname: str,
        registry_project: str,
    ) -> ContainerRegistryRow | None:
        async with self._db.begin_readonly_session() as db_session:
            query = (
                sa.select(ContainerRegistryRow)
                .where(
                    (ContainerRegistryRow.registry_name == registry_hostname)
                    & (ContainerRegistryRow.project == registry_project)
                )
                .options(
                    load_only(
                        ContainerRegistryRow.url,
                        ContainerRegistryRow.username,
                        ContainerRegistryRow.password,
                        ContainerRegistryRow.project,
                    )
                )
            )
            return cast(ContainerRegistryRow | None, await db_session.scalar(query))

    async def resolve_image(
        self,
        image_identifiers: list[ImageAlias | ImageRef | ImageIdentifier],
        alive_only: bool = True,
    ) -> ImageRow:
        """Resolve an image from the given identifiers.

        When ``alive_only`` is True (default), only images with the ALIVE status
        are considered.  Set it to False to also include DELETED images, which is
        useful when the caller needs to reference images that are no longer active
        (e.g., committing a session whose base image has been deleted).
        """
        async with self._db.begin_readonly_session() as db_sess:
            if alive_only:
                return await ImageRow.resolve(db_sess, image_identifiers)
            return await ImageRow.resolve(
                db_sess,
                image_identifiers,
                filter_by_statuses=[
                    ImageStatus.ALIVE,
                    ImageStatus.DELETED,
                ],
            )

    async def get_customized_image_count(
        self,
        image_visibility: str,
        image_owner_id: str,
    ) -> int:
        async with self._db.begin_readonly_session() as sess:
            query = (
                sa.select(sa.func.count())
                .select_from(ImageRow)
                .where(
                    ImageRow.labels["ai.backend.customized-image.owner"].as_string()
                    == f"{image_visibility}:{image_owner_id}"
                )
                .where(ImageRow.status == ImageStatus.ALIVE)
            )
            result = await sess.scalar(query)
            return result or 0

    async def get_existing_customized_image(
        self,
        new_canonical: str,
        image_visibility: str,
        image_owner_id: str,
        image_name: str,
    ) -> ImageRow | None:
        async with self._db.begin_readonly_session() as sess:
            query = sa.select(ImageRow).where(
                sa.and_(
                    ImageRow.name.like(f"{new_canonical}%"),
                    ImageRow.labels["ai.backend.customized-image.owner"].as_string()
                    == f"{image_visibility}:{image_owner_id}",
                    ImageRow.labels["ai.backend.customized-image.name"].as_string() == image_name,
                    ImageRow.status == ImageStatus.ALIVE,
                )
            )
            return cast(ImageRow | None, await sess.scalar(query))

    async def get_group_name_by_domain_and_id(
        self,
        domain_name: str,
        group_id: uuid.UUID,
    ) -> str | None:
        async with self._db.begin_readonly() as conn:
            query = (
                sa.select(groups.c.name)
                .select_from(groups)
                .where(
                    (groups.c.domain_name == domain_name) & (groups.c.id == group_id),
                )
            )
            return await conn.scalar(query)

    async def get_scaling_group_wsproxy_addr(
        self,
        scaling_group_name: str,
    ) -> str | None:
        async with self._db.begin_readonly() as conn:
            query = (
                sa.select(scaling_groups.c.wsproxy_addr)
                .select_from(scaling_groups)
                .where(scaling_groups.c.name == scaling_group_name)
            )
            result = await conn.execute(query)
            sgroup = result.first()
            return sgroup.wsproxy_addr if sgroup else None

    async def get_session_by_id(
        self,
        session_id: str | SessionId,
    ) -> SessionRow | None:
        async with self._db.begin_readonly_session() as db_session:
            stmt = (
                sa.select(SessionRow)
                .where(SessionRow.id == session_id)
                .options(
                    selectinload(SessionRow.kernels),
                )
            )
            return cast(SessionRow | None, await db_session.scalar(stmt))

    async def modify_session(
        self,
        updater: Updater[SessionRow],
        session_name: str | None = None,
    ) -> SessionRow | None:
        session_id = updater.pk_value

        async with self._db.begin_session() as db_session:
            query_stmt = sa.select(SessionRow).where(SessionRow.id == session_id)
            session_row = await db_session.scalar(query_stmt)
            if session_row is None:
                raise SessionNotFound(f"Session not found (id:{session_id})")

            if session_name and session_row.access_key is not None:
                # Check the owner of the target session has any session with the same name
                try:
                    sess = await SessionRow.get_session(
                        db_session,
                        session_name,
                        AccessKey(session_row.access_key),
                    )
                except SessionNotFound:
                    pass
                else:
                    raise SessionAlreadyExists(
                        f"Duplicate session name. Session(id:{sess.id}) already has the name"
                    )

            # Use execute_updater to apply changes
            result = await execute_updater(db_session, updater)
            if result is None:
                raise SessionNotFound(f"Session not found (id:{session_id})")

            if session_name:
                await db_session.execute(
                    sa.update(KernelRow)
                    .values(session_name=session_name)
                    .where(KernelRow.session_id == session_id)
                )

            # Re-fetch with kernels loaded for the return value
            select_stmt = (
                sa.select(SessionRow)
                .options(selectinload(SessionRow.kernels))
                .execution_options(populate_existing=True)
                .where(SessionRow.id == session_id)
            )
            return cast(SessionRow | None, await db_session.scalar(select_stmt))

    async def query_userinfo(
        self,
        user_id: uuid.UUID,
        requester_access_key: AccessKey,
        user_role: UserRole,
        domain_name: str,
        keypair_resource_policy: dict[str, Any] | None,
        query_domain_name: str,
        group_name: str | None,
        query_on_behalf_of: AccessKey | None = None,
    ) -> tuple[uuid.UUID, uuid.UUID, dict[str, Any]]:
        if group_name is None:
            raise GenericBadRequest("group_name cannot be None")
        async with self._db.begin_readonly() as conn:
            return await query_userinfo(
                conn,
                user_id,
                requester_access_key,
                user_role,
                domain_name,
                keypair_resource_policy,
                query_domain_name,
                group_name,
                query_on_behalf_of=query_on_behalf_of,
            )

    async def _find_dependent_sessions(
        self,
        db_sess: AsyncSession,
        root_session_name_or_id: str | uuid.UUID,
        access_key: AccessKey,
        allow_stale: bool = False,
    ) -> tuple[uuid.UUID, set[uuid.UUID]]:
        """
        Find the root session and all sessions that depend on it (recursively).

        :param db_sess: Database session
        :param root_session_name_or_id: Root session name or ID
        :param access_key: Access key of the session owner
        :param allow_stale: Whether to allow stale sessions
        :return: Tuple of (root_session_id, set of dependent session IDs)
        """

        async def _find_recursive_dependencies(session_id: uuid.UUID) -> set[uuid.UUID]:
            result = await db_sess.execute(
                sa.select(SessionDependencyRow).where(SessionDependencyRow.depends_on == session_id)
            )
            dependent_sessions: set[uuid.UUID] = {x.session_id for x in result.scalars()}

            # Recursively find dependencies
            for dependent_session in list(dependent_sessions):
                recursive_deps = await _find_recursive_dependencies(dependent_session)
                dependent_sessions |= recursive_deps

            return dependent_sessions

        # Get the root session first
        root_session = await SessionRow.get_session(
            db_sess,
            root_session_name_or_id,
            access_key=access_key,
            allow_stale=allow_stale,
        )
        root_session_id = cast(uuid.UUID, root_session.id)
        dependent_ids = await _find_recursive_dependencies(root_session_id)

        return root_session_id, dependent_ids

    async def get_target_session_ids(
        self,
        session_name_or_id: str | uuid.UUID,
        access_key: AccessKey,
        recursive: bool = False,
    ) -> list[SessionId]:
        """
        Get list of session IDs including dependent sessions if recursive.

        :param session_name_or_id: Name or ID of the primary session
        :param access_key: Access key of the session owner
        :param recursive: If True, include dependent sessions
        :return: List of session IDs
        """
        async with self._db.begin_readonly_session() as db_sess:
            try:
                if recursive:
                    # Get root session and dependent sessions
                    root_id, dependent_ids = await self._find_dependent_sessions(
                        db_sess,
                        session_name_or_id,
                        access_key,
                        allow_stale=True,
                    )
                    # Return dependent sessions first, then root session
                    session_ids = [cast(SessionId, sid) for sid in dependent_ids]
                    session_ids.append(cast(SessionId, root_id))
                else:
                    # Get only the main session
                    session = await SessionRow.get_session(
                        db_sess,
                        session_name_or_id,
                        access_key,
                        kernel_loading_strategy=KernelLoadingStrategy.NONE,
                        allow_stale=True,
                    )
                    session_ids = [session.id]

                return session_ids
            except SessionNotFound:
                raise

    async def find_dependency_sessions(
        self,
        session_name_or_id: uuid.UUID | str,
        access_key: AccessKey,
    ) -> dict[str, list[Any] | str]:
        async with self._db.begin_readonly_session() as db_sess:
            return await find_dependency_sessions(
                session_name_or_id,
                db_sess,
                access_key,
            )

    async def get_session_with_group(
        self,
        session_name_or_id: str | SessionId,
        owner_access_key: AccessKey,
        kernel_loading_strategy: KernelLoadingStrategy = KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        allow_stale: bool = False,
    ) -> SessionRow:
        """Get session with group information eagerly loaded"""
        async with self._db.begin_readonly_session() as db_sess:
            return await SessionRow.get_session(
                db_sess,
                session_name_or_id,
                owner_access_key,
                kernel_loading_strategy=kernel_loading_strategy,
                allow_stale=allow_stale,
                eager_loading_op=[selectinload(SessionRow.group)],
            )

    async def get_session_with_routing_minimal(
        self,
        session_name_or_id: str | SessionId,
        owner_access_key: AccessKey,
    ) -> SessionRow:
        """Get session with minimal routing information"""
        async with self._db.begin_readonly_session() as db_sess:
            return await SessionRow.get_session(
                db_sess,
                session_name_or_id,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                eager_loading_op=[
                    selectinload(SessionRow.routing).options(noload("*")),
                ],
            )

    async def search(
        self,
        querier: BatchQuerier,
    ) -> SessionListResult:
        """Search sessions with querier pattern.

        Args:
            querier: BatchQuerier for filtering, ordering, and pagination

        Returns:
            SessionListResult with items, total count, and pagination info
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(SessionRow).options(selectinload(SessionRow.kernels))

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.SessionRow.to_dataclass() for row in result.rows]

            return SessionListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_kernels(
        self,
        querier: BatchQuerier,
    ) -> KernelListResult:
        """Search kernels with querier pattern.

        Args:
            querier: BatchQuerier for filtering, ordering, and pagination

        Returns:
            KernelListResult with items, total count, and pagination info
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(KernelRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.KernelRow.to_kernel_info() for row in result.rows]

            return KernelListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

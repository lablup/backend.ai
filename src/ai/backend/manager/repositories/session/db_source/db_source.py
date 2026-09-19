from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, noload, selectinload
from sqlalchemy.orm.strategy_options import _AbstractLoad

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    KernelId,
    ResourceSlot,
    SessionId,
)
from ai.backend.manager.data.image.types import ImageData, ImageStatus
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate
from ai.backend.manager.data.session.types import (
    SessionData,
    SessionRoutingInfo,
)
from ai.backend.manager.data.user.types import SessionOwnerContext, UserData
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.image import ImageNotFound
from ai.backend.manager.errors.kernel import (
    SessionAlreadyExists,
    SessionNotFound,
    TooManySessionsMatched,
)
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.image.conditions import ImageConditions
from ai.backend.manager.models.image.orders import ImageOrders
from ai.backend.manager.models.image.searchers import ImageSearcher
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import groups
from ai.backend.manager.models.resource_group import resource_groups
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.models.resource_slot import ResourceAllocationRow
from ai.backend.manager.models.session import (
    DEAD_SESSION_STATUSES,
    TERMINAL_SESSION_STATUSES,
    KernelLoadingStrategy,
    SessionDependencyRow,
    SessionRow,
)
from ai.backend.manager.models.session.updaters import SessionUpdater
from ai.backend.manager.models.session_template import SessionTemplateRow
from ai.backend.manager.models.specs.pagination import NoPagination, OffsetPagination
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    execute_batch_querier,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps
from ai.backend.manager.repositories.session.dependency_graph import find_dependency_sessions
from ai.backend.manager.utils import query_userinfo


class SessionDBSource:
    _db: ExtendedAsyncSAEngine
    _ops_provider: V2DBOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine, ops_provider: V2DBOpsProvider) -> None:
        self._db = db
        self._ops_provider = ops_provider

    async def resolve_session_id(
        self,
        session_name_or_id: str,
        user_id: uuid.UUID,
    ) -> SessionId:
        """Infer a session id from ``(session_name_or_id, user_id)`` for legacy callers.

        The goal is to derive a usable session id when only a name is known, not to return
        a validated one. A UUID-shaped input is already an id and is returned verbatim;
        otherwise the live (non-terminal) session owned by the user with that name is
        resolved, matching the ``ix_sessions_unique_name_per_user_nonterminal`` partial
        unique index. DO NOT USE FOR NEW DEVELOPMENT.
        """
        try:
            return SessionId(uuid.UUID(session_name_or_id))
        except (ValueError, TypeError):
            pass
        session_name = session_name_or_id
        query = sa.select(SessionRow).where(
            (SessionRow.name == session_name)
            & (SessionRow.user_uuid == user_id)
            & (~SessionRow.status.in_(TERMINAL_SESSION_STATUSES))
        )
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await execute_batch_querier(
                db_sess, query, BatchQuerier(pagination=NoPagination())
            )
        rows: list[SessionRow] = [row.SessionRow for row in result.rows]
        if not rows:
            raise SessionNotFound(f"Session (name={session_name}) does not exist for the user.")
        if len(rows) > 1:
            # Defensive: the partial unique index should prevent this for non-terminal
            # sessions, but guard against any data that escaped the constraint.
            raise TooManySessionsMatched(
                extra_data={
                    "matches": [
                        {
                            "session_id": row.id,
                            "session_name": row.name,
                            "status": row.status,
                            "created_at": row.created_at,
                        }
                        for row in rows
                    ]
                }
            )
        return rows[0].id

    async def get_session_name(self, session_id: SessionId) -> str:
        """Return the canonical session name for a session id.

        Used to normalize a UUID-shaped path reference back to its real name;
        ownership and state checks remain the caller's job.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(SessionRow.name).where(SessionRow.id == session_id)
            name = await db_sess.scalar(query)
            if name is None:
                raise SessionNotFound(f"Session with id {session_id} not found")
            return name

    async def get_session_owner(self, session_id: str | SessionId) -> UserData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select(UserRow)
                .join(SessionRow, SessionRow.user_uuid == UserRow.uuid)
                .where(SessionRow.id == session_id)
            )
            user = await db_sess.scalar(query)
            if user is None:
                raise SessionNotFound(f"Session with id {session_id} not found")
            return user.to_data()

    async def get_session_validated(
        self,
        session_id: SessionId,
        kernel_loading_strategy: KernelLoadingStrategy = KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        allow_stale: bool = False,
        eager_loading_op: Sequence[_AbstractLoad] | None = None,
    ) -> SessionRow:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            return await self._session_by_id(
                db_sess,
                session_id,
                kernel_loading_strategy=kernel_loading_strategy,
                allow_stale=allow_stale,
                eager_loading_op=eager_loading_op or (),
            )

    async def _session_by_id(
        self,
        db_sess: AsyncSession,
        session_id: SessionId,
        *,
        kernel_loading_strategy: KernelLoadingStrategy,
        allow_stale: bool,
        eager_loading_op: Sequence[_AbstractLoad] = (),
    ) -> SessionRow:
        options: list[_AbstractLoad] = [*eager_loading_op]
        if kernel_loading_strategy != KernelLoadingStrategy.NONE:
            # MAIN_KERNEL_ONLY loads every kernel as well, the same as SessionRow.get_session.
            options.extend([
                noload("*"),
                selectinload(SessionRow.kernels).options(
                    noload("*"),
                    selectinload(KernelRow.agent_row).noload("*"),
                ),
            ])
        options.append(joinedload(SessionRow.user))
        cond = SessionRow.id == session_id
        if not allow_stale:
            cond = cond & ~SessionRow.status.in_(DEAD_SESSION_STATUSES)
        query = (
            sa.select(SessionRow)
            .where(cond)
            .options(*options)
            .execution_options(populate_existing=True)
        )
        session_row = await db_sess.scalar(query)
        if session_row is None:
            raise SessionNotFound(f"Session (id={session_id}) does not exist.")
        return session_row

    async def match_sessions(
        self,
        id_or_name_prefix: str,
        owner_access_key: AccessKey,
    ) -> list[SessionRow]:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            return await SessionRow.match_sessions(
                db_sess,
                id_or_name_prefix,
                owner_access_key,
            )

    async def get_template_by_id(
        self,
        template_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        async with self._db.begin_readonly() as conn:
            query = (
                sa.select(SessionTemplateRow.template)
                .select_from(SessionTemplateRow)
                .where(
                    (SessionTemplateRow.id == template_id) & SessionTemplateRow.is_active,
                )
            )
            return await conn.scalar(query)

    async def get_template_info_by_id(
        self,
        template_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        async with self._db.begin_readonly() as conn:
            query = (
                sa.select(SessionTemplateRow.__table__)
                .select_from(SessionTemplateRow)
                .where(
                    (SessionTemplateRow.id == template_id) & SessionTemplateRow.is_active,
                )
            )
            result = await conn.execute(query)
            template_info = result.fetchone()
            return dict(template_info._mapping) if template_info else None

    async def update_session_name(
        self,
        session_id: SessionId,
        new_name: str,
    ) -> SessionRow:
        async with self._db.begin_session() as db_sess:
            session_row = await self._session_by_id(
                db_sess,
                session_id,
                kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
                allow_stale=False,
            )
            if session_row.access_key is not None:
                # The name is unique among the live sessions of the target session's owner.
                duplicate = await db_sess.scalar(
                    sa.select(SessionRow.id)
                    .where(
                        (SessionRow.name == new_name)
                        & (SessionRow.access_key == session_row.access_key)
                        & (~SessionRow.status.in_(DEAD_SESSION_STATUSES))
                    )
                    .limit(1)
                )
                if duplicate is not None:
                    raise SessionAlreadyExists(f"Session with name '{new_name}' already exists")

            session_row.name = new_name
            for kernel in session_row.kernels:
                kernel.session_name = new_name
            return session_row

    async def resolve_image(self, reference: str, architecture: str) -> ImageData:
        async with self._ops_provider.read_ops() as r:
            result = await r.search_in_global(
                ImageSearcher(
                    pagination=OffsetPagination(limit=1),
                    conditions=[
                        ImageConditions.by_canonical_and_architecture_or_alias(
                            reference, architecture
                        ),
                        ImageConditions.by_statuses([ImageStatus.ALIVE]),
                    ],
                    orders=ImageOrders.canonical_match_then_alive_then_oldest(
                        reference, architecture
                    ),
                )
            )
        if not result.items:
            raise ImageNotFound(f"Unknown image reference: {reference} ({architecture})")
        return result.items[0]

    async def resolve_image_by_canonical(
        self, canonical: str, architecture: str, alive_only: bool = True
    ) -> ImageData:
        statuses = [ImageStatus.ALIVE] if alive_only else [ImageStatus.ALIVE, ImageStatus.DELETED]
        async with self._ops_provider.read_ops() as r:
            result = await r.search_in_global(
                ImageSearcher(
                    pagination=OffsetPagination(limit=1),
                    conditions=[
                        ImageConditions.by_canonical_and_architecture(canonical, architecture),
                        ImageConditions.by_statuses(statuses),
                    ],
                    orders=ImageOrders.alive_then_oldest(),
                )
            )
        if not result.items:
            raise ImageNotFound(f"Unknown image: {canonical} ({architecture})")
        return result.items[0]

    async def get_customized_image_count(self, user_id: uuid.UUID) -> int:
        """How many live customized images were committed for the user."""
        async with self._db.begin_readonly_session_read_committed() as sess:
            query = (
                sa.select(sa.func.count())
                .select_from(ImageRow)
                .where(
                    self._committed_for(user_id),
                    ImageRow.status == ImageStatus.ALIVE,
                )
            )
            result = await sess.scalar(query)
            return result or 0

    async def get_existing_customized_image(
        self,
        new_canonical: str,
        user_id: uuid.UUID,
        image_name: str,
    ) -> ImageRow | None:
        async with self._db.begin_readonly_session_read_committed() as sess:
            query = sa.select(ImageRow).where(
                sa.and_(
                    ImageRow.name.like(f"{new_canonical}%"),
                    self._committed_for(user_id),
                    ImageRow.labels["ai.backend.customized-image.name"].as_string() == image_name,
                    ImageRow.status == ImageStatus.ALIVE,
                )
            )
            return cast(ImageRow | None, await sess.scalar(query))

    def _committed_for(self, user_id: uuid.UUID) -> sa.ColumnElement[bool]:
        """The image is customized and was committed for this user."""
        return sa.and_(ImageRow.customized.is_(True), ImageRow.creator_id == user_id)

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

    async def get_resource_group_wsproxy_addr(
        self,
        resource_group_name: str,
    ) -> str | None:
        async with self._db.begin_readonly() as conn:
            query = (
                sa.select(resource_groups.c.wsproxy_addr)
                .select_from(resource_groups)
                .where(resource_groups.c.name == resource_group_name)
            )
            result = await conn.execute(query)
            sgroup = result.first()
            return sgroup.wsproxy_addr if sgroup else None

    async def get_session_by_id(
        self,
        session_id: str | SessionId,
    ) -> SessionRow | None:
        async with self._db.begin_readonly_session_read_committed() as db_session:
            stmt = (
                sa.select(SessionRow)
                .where(SessionRow.id == session_id)
                .options(
                    selectinload(SessionRow.kernels),
                )
            )
            return cast(SessionRow | None, await db_session.scalar(stmt))

    async def update_session(
        self,
        updater: SessionUpdater,
        session_name: str | None = None,
    ) -> SessionRow | None:
        session_id = updater.session_id

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

            updated = await V2WriteOps(db_session).update_data(updater)
            if updated is None:
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
    ) -> SessionOwnerContext:
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
        root_session_id: SessionId,
        allow_stale: bool = False,
    ) -> tuple[uuid.UUID, set[uuid.UUID]]:
        """
        Find the root session and all sessions that depend on it (recursively).

        :param db_sess: Database session
        :param root_session_id: Root session ID
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
        root_session = await self._session_by_id(
            db_sess,
            root_session_id,
            kernel_loading_strategy=KernelLoadingStrategy.NONE,
            allow_stale=allow_stale,
        )
        dependent_ids = await _find_recursive_dependencies(root_session.id)

        return root_session.id, dependent_ids

    async def get_target_session_ids(
        self,
        session_id: SessionId,
        recursive: bool = False,
    ) -> list[SessionId]:
        """
        Get list of session IDs including dependent sessions if recursive.

        :param session_id: ID of the primary session
        :param recursive: If True, include dependent sessions
        :return: List of session IDs
        """
        async with self._db.begin_readonly_session() as db_sess:
            if recursive:
                # Get root session and dependent sessions
                root_id, dependent_ids = await self._find_dependent_sessions(
                    db_sess,
                    session_id,
                    allow_stale=True,
                )
                # Return dependent sessions first, then root session
                session_ids = [cast(SessionId, sid) for sid in dependent_ids]
                session_ids.append(cast(SessionId, root_id))
            else:
                # Get only the main session
                session = await self._session_by_id(
                    db_sess,
                    session_id,
                    kernel_loading_strategy=KernelLoadingStrategy.NONE,
                    allow_stale=True,
                )
                session_ids = [session.id]

            return session_ids

    async def find_dependency_sessions(
        self,
        session_id: SessionId,
    ) -> dict[str, list[Any] | str]:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            return await find_dependency_sessions(session_id, db_sess)

    async def get_session_with_group(
        self,
        session_id: SessionId,
        kernel_loading_strategy: KernelLoadingStrategy = KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        allow_stale: bool = False,
    ) -> SessionRow:
        """Get session with group information eagerly loaded"""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            return await self._session_by_id(
                db_sess,
                session_id,
                kernel_loading_strategy=kernel_loading_strategy,
                allow_stale=allow_stale,
                eager_loading_op=[selectinload(SessionRow.group)],
            )

    async def get_session_with_routing_minimal(
        self,
        session_id: SessionID,
    ) -> SessionRoutingInfo:
        """Resolve a live session by ``session_id`` into its routing info.

        This is a pure lookup; session access authorization is the caller's
        responsibility. Dead (terminated/cancelled) sessions are excluded. Returns a
        data type rather than a SessionRow so the repository never exposes an ORM row.
        """
        query = (
            sa.select(SessionRow)
            .where((SessionRow.id == session_id) & (~SessionRow.status.in_(DEAD_SESSION_STATUSES)))
            .options(
                noload("*"),
                selectinload(
                    SessionRow.kernels.and_(KernelRow.cluster_role == DEFAULT_ROLE)
                ).options(
                    noload("*"),
                    selectinload(KernelRow.agent_row).noload("*"),
                ),
                joinedload(SessionRow.user),
            )
        )
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await execute_batch_querier(
                db_sess, query, BatchQuerier(pagination=NoPagination())
            )
        rows: list[SessionRow] = [row.SessionRow for row in result.rows]
        if not rows:
            raise SessionNotFound(f"Session (id={session_id}) does not exist.")
        session_row = rows[0]
        main_kernel = session_row.main_kernel
        return SessionRoutingInfo(
            session=session_row.to_dataclass(),
            main_kernel_id=main_kernel.id,
            agent_id=AgentId(main_kernel.agent) if main_kernel.agent is not None else None,
            kernel_host=main_kernel.kernel_host,
            agent_addr=main_kernel.agent_addr,
            service_ports=main_kernel.service_ports or [],
        )

    @staticmethod
    def _resource_allocation_aggregates() -> tuple[Any, Any, Any]:
        """Build the three per-slot aggregate expressions over resource_allocations.

        - requested: SUM(requested)
        - used: currently occupying (free_at IS NULL), coalesced with requested
        - allocated: ever actually allocated (used_at IS NOT NULL), persists after free
        """
        ra = ResourceAllocationRow.__table__
        requested_expr = sa.func.sum(ra.c.requested).label("requested")
        used_expr = (
            sa.func.sum(sa.func.coalesce(ra.c.used, ra.c.requested))
            .filter(ra.c.free_at.is_(None))
            .label("used")
        )
        allocated_expr = sa.func.sum(ra.c.used).filter(ra.c.used_at.isnot(None)).label("allocated")
        return requested_expr, used_expr, allocated_expr

    @staticmethod
    def _rows_to_aggregates(
        rows: Sequence[Any], key_attr: str
    ) -> dict[Any, ResourceAllocationAggregate]:
        requested: dict[Any, ResourceSlot] = {}
        used: dict[Any, ResourceSlot] = {}
        allocated: dict[Any, ResourceSlot] = {}
        for r in rows:
            key = getattr(r, key_attr)
            if r.requested is not None:
                requested.setdefault(key, ResourceSlot())[r.slot_name] = r.requested
            if r.used is not None:
                used.setdefault(key, ResourceSlot())[r.slot_name] = r.used
            if r.allocated is not None:
                allocated.setdefault(key, ResourceSlot())[r.slot_name] = r.allocated
        keys = set(requested) | set(used) | set(allocated)
        return {
            key: ResourceAllocationAggregate(
                requested=requested.get(key, ResourceSlot()),
                used=used.get(key, ResourceSlot()),
                allocated=allocated.get(key, ResourceSlot()),
            )
            for key in keys
        }

    async def batch_get_resource_allocation_by_session(
        self,
        session_ids: Sequence[SessionId],
    ) -> dict[SessionId, ResourceAllocationAggregate]:
        """Aggregate resource_allocations per session (grouped by slot).

        Values are computed live from the resource_allocations table; the deprecated
        JSONB columns are never read.
        """
        if not session_ids:
            return {}
        ra = ResourceAllocationRow.__table__
        kernels = KernelRow.__table__
        requested_expr, used_expr, allocated_expr = self._resource_allocation_aggregates()
        stmt = (
            sa.select(
                kernels.c.session_id.label("session_id"),
                ra.c.slot_name,
                requested_expr,
                used_expr,
                allocated_expr,
            )
            .select_from(ra.join(kernels, ra.c.kernel_id == kernels.c.id))
            .where(kernels.c.session_id.in_(session_ids))
            .group_by(kernels.c.session_id, ra.c.slot_name)
        )
        async with self._db.begin_readonly_session() as db_sess:
            rows = (await db_sess.execute(stmt)).all()
        aggregates = self._rows_to_aggregates(rows, "session_id")
        return {SessionId(key): agg for key, agg in aggregates.items()}

    async def batch_get_resource_allocation_by_kernel(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> dict[KernelId, ResourceAllocationAggregate]:
        """Aggregate resource_allocations per kernel (grouped by slot)."""
        if not kernel_ids:
            return {}
        ra = ResourceAllocationRow.__table__
        requested_expr, used_expr, allocated_expr = self._resource_allocation_aggregates()
        stmt = (
            sa.select(
                ra.c.kernel_id.label("kernel_id"),
                ra.c.slot_name,
                requested_expr,
                used_expr,
                allocated_expr,
            )
            .where(ra.c.kernel_id.in_(kernel_ids))
            .group_by(ra.c.kernel_id, ra.c.slot_name)
        )
        async with self._db.begin_readonly_session() as db_sess:
            rows = (await db_sess.execute(stmt)).all()
        aggregates = self._rows_to_aggregates(rows, "kernel_id")
        return {KernelId(key): agg for key, agg in aggregates.items()}

    async def resolve_image_by_id(
        self,
        image_id: uuid.UUID,
    ) -> ImageRow:
        """Resolve an image by its UUID. Raises ImageNotFound if not found or not alive."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select(ImageRow)
                .where(ImageRow.id == image_id)
                .where(ImageRow.status == ImageStatus.ALIVE)
            )
            row = await db_sess.scalar(query)
            if row is None:
                raise ImageNotFound(f"Image not found: {image_id}")
            return row

    async def get_keypair_resource_policy(
        self,
        access_key: AccessKey,
    ) -> dict[str, Any]:
        """Fetch the keypair resource policy dict for the given access key."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select(KeyPairResourcePolicyRow)
                .join(
                    KeyPairRow,
                    KeyPairRow.resource_policy == KeyPairResourcePolicyRow.name,
                )
                .where(KeyPairRow.access_key == access_key)
            )
            row = await db_sess.scalar(query)
            if row is None:
                return {}
            return {
                "allowed_vfolder_hosts": row.allowed_vfolder_hosts,
            }

    async def get_session_data_by_id(
        self,
        session_id: SessionId,
    ) -> SessionData:
        """Get session data by session ID."""
        async with self._db.begin_readonly_session() as db_sess:
            query = (
                sa.select(SessionRow)
                .options(selectinload(SessionRow.kernels))
                .where(SessionRow.id == session_id)
            )
            row = await db_sess.scalar(query)
            if row is None:
                raise SessionNotFound(f"Session not found: {session_id}")
            return row.to_dataclass()

    async def update_image_last_used_at(
        self,
        image_id: uuid.UUID,
        timestamp: datetime,
    ) -> None:
        async with self._db.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(ImageRow).where(ImageRow.id == image_id).values(last_used_at=timestamp)
            )

from __future__ import annotations

import logging
import uuid
from collections.abc import (
    Iterable,
    Sequence,
)
from datetime import datetime
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    Self,
    cast,
)
from uuid import UUID, uuid4

import sqlalchemy as sa
import yarl
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.orm import (
    Mapped,
    contains_eager,
    foreign,
    mapped_column,
    relationship,
    selectinload,
)

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.types import (
    AccessKey,
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    ResourceSlot,
    SessionTypes,
    VFolderID,
    VFolderMount,
    VFolderMountOptions,
    VFolderMountRequest,
    VFolderUsageMode,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.data.deployment.scale import (
    AutoScalingAction,
    AutoScalingCondition,
    AutoScalingRule,
    AutoScalingRuleCreator,
    ModelDeploymentAutoScalingRuleCreator,
)
from ai.backend.manager.data.deployment.scale_modifier import (
    ModelDeploymentAutoScalingRuleModifier,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleSubStep,
    DeploymentMetadata,
    DeploymentNetworkData,
    DeploymentOptions,
    DeploymentPolicyData,
    DeploymentState,
    DeploymentSummaryData,
    ModelDeploymentAutoScalingRuleData,
    ModelRevisionData,
    ReplicaData,
)
from ai.backend.manager.data.model_serving.types import (
    EndpointAutoScalingRuleData,
    EndpointData,
    EndpointLifecycle,
    EndpointTokenData,
    ScalingState,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.common import ObjectNotFound, ServiceUnavailable
from ai.backend.manager.models.base import (
    GUID,
    Base,
    DecimalType,
    PydanticColumn,
    StrEnumType,
)
from ai.backend.manager.models.routing import RouteStatus
from ai.backend.manager.models.scaling_group import scaling_groups
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.vfolder import prepare_vfolder_mounts
from ai.backend.manager.types import MountOptionModel, UserScope

if TYPE_CHECKING:
    from ai.backend.manager.data.deployment.creator import DeploymentCreator
    from ai.backend.manager.models.deployment_auto_scaling_policy import (
        DeploymentAutoScalingPolicyRow,
    )
    from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
    from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
    from ai.backend.manager.models.replica_group import ReplicaGroupRow
    from ai.backend.manager.models.routing import RoutingRow
    from ai.backend.manager.models.user import UserRow

__all__ = (
    "EndpointAutoScalingRuleRow",
    "EndpointLifecycle",
    "EndpointRow",
    "EndpointTokenRow",
    "ModelServiceHelper",
)


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _get_endpoint_tokens_join_condition() -> Any:
    from ai.backend.manager.models.endpoint import EndpointTokenRow

    return foreign(EndpointTokenRow.endpoint) == EndpointRow.id


def _get_endpoint_revisions_join_condition() -> Any:
    from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow

    return EndpointRow.id == foreign(DeploymentRevisionRow.endpoint)


def _get_primary_replica_group_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.replica_group import ReplicaGroupRow

    return foreign(EndpointRow.primary_replica_group_id) == ReplicaGroupRow.id


def _get_target_replica_group_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.replica_group import ReplicaGroupRow

    return foreign(EndpointRow.target_replica_group_id) == ReplicaGroupRow.id


def _get_current_revision_secondaryjoin() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
    from ai.backend.manager.models.replica_group import ReplicaGroupRow

    return foreign(ReplicaGroupRow.current_revision_id) == DeploymentRevisionRow.id


def _get_deploying_revision_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow

    return foreign(EndpointRow.deploying_revision_id) == DeploymentRevisionRow.id


def _get_endpoint_auto_scaling_policy_join_condition() -> Any:
    from ai.backend.manager.models.deployment_auto_scaling_policy import (
        DeploymentAutoScalingPolicyRow,
    )

    return EndpointRow.id == foreign(DeploymentAutoScalingPolicyRow.endpoint)


def _get_deployment_policy_join_condition() -> Any:
    from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow

    return EndpointRow.id == foreign(DeploymentPolicyRow.endpoint)


def _get_created_user_row_join_condition() -> Any:
    from ai.backend.manager.models.user import UserRow

    return foreign(EndpointRow.created_user) == UserRow.uuid


def _get_session_owner_row_join_condition() -> Any:
    from ai.backend.manager.models.user import UserRow

    return foreign(EndpointRow.session_owner) == UserRow.uuid


def _get_endpoint_token_endpoint_row_join_condition() -> Any:
    return foreign(EndpointTokenRow.endpoint) == EndpointRow.id


class EndpointRow(Base):  # type: ignore[misc]
    __tablename__ = "endpoints"

    __table_args__ = (
        sa.Index(
            "ix_endpoints_lifecycle_sub_step",
            "lifecycle_stage",
            "sub_step",
        ),
    )

    id: Mapped[DeploymentID] = mapped_column(
        "id", GUID(DeploymentID), primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=512), nullable=False)
    created_user: Mapped[UUID] = mapped_column("created_user", GUID, nullable=False)
    session_owner: Mapped[UUID] = mapped_column("session_owner", GUID, nullable=False)
    # minus session count means this endpoint is requested for removal
    replicas: Mapped[int] = mapped_column(
        "replicas", sa.Integer, nullable=False, default=0, server_default="0"
    )
    desired_replicas: Mapped[int | None] = mapped_column(
        "desired_replicas", sa.Integer, nullable=True, default=None, server_default=sa.null()
    )
    domain: Mapped[str] = mapped_column(
        "domain",
        sa.String(length=64),
        sa.ForeignKey("domains.name", ondelete="RESTRICT"),
        nullable=False,
    )
    project: Mapped[UUID] = mapped_column(
        "project",
        GUID,
        sa.ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=False,
    )
    resource_group: Mapped[str] = mapped_column(
        "resource_group",
        sa.String,
        sa.ForeignKey("scaling_groups.name", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    lifecycle_stage: Mapped[EndpointLifecycle] = mapped_column(
        "lifecycle_stage",
        StrEnumType(EndpointLifecycle),
        nullable=False,
        default=EndpointLifecycle.PENDING,
    )
    scaling_state: Mapped[ScalingState] = mapped_column(
        "scaling_state",
        StrEnumType(ScalingState),
        nullable=False,
        default=ScalingState.STABLE,
        server_default=ScalingState.STABLE.value,
    )
    tag: Mapped[str | None] = mapped_column("tag", sa.String(length=64), nullable=True)
    open_to_public: Mapped[bool | None] = mapped_column("open_to_public", sa.Boolean, default=False)
    url: Mapped[str | None] = mapped_column("url", sa.String(length=1024))

    retries: Mapped[int] = mapped_column(
        "retries", sa.Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )
    destroyed_at: Mapped[datetime | None] = mapped_column(
        "destroyed_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )

    # Revision pointers live on the replica groups (see
    # ``primary_replica_group_id`` / ``target_replica_group_id`` below): the
    # current revision is the primary group's ``current_revision_id`` and the
    # deploying revision is the target group's ``target_revision_id``.

    # Replica group references (no FK; mirrors ``RoutingRow.revision`` and
    # avoids a circular FK with ``replica_groups.deployment_id``).
    # ``primary_replica_group_id`` is the group serving traffic;
    # ``target_replica_group_id`` is the group being rolled out (``NULL``
    # in the steady state).
    primary_replica_group_id: Mapped[ReplicaGroupID | None] = mapped_column(
        "primary_replica_group_id", GUID(ReplicaGroupID), nullable=True
    )
    target_replica_group_id: Mapped[ReplicaGroupID | None] = mapped_column(
        "target_replica_group_id", GUID(ReplicaGroupID), nullable=True
    )
    deploying_revision_id: Mapped[DeploymentRevisionID | None] = mapped_column(
        "deploying_revision_id", GUID(DeploymentRevisionID), nullable=True
    )
    sub_step: Mapped[DeploymentLifecycleSubStep | None] = mapped_column(
        "sub_step",
        StrEnumType(DeploymentLifecycleSubStep),
        nullable=True,
        default=None,
    )
    revision_history_limit: Mapped[int] = mapped_column(
        "revision_history_limit",
        sa.Integer,
        nullable=False,
        server_default=sa.text("10"),
    )
    # Per-deployment operational options (snapshot from the scaling
    # group's ``default_deployment_options`` at create time).
    options: Mapped[DeploymentOptions] = mapped_column(
        "options",
        PydanticColumn(DeploymentOptions),
        nullable=False,
        default=DeploymentOptions,
    )

    routings: Mapped[list[RoutingRow]] = relationship("RoutingRow", back_populates="endpoint_row")
    tokens: Mapped[list[EndpointTokenRow]] = relationship(
        "EndpointTokenRow",
        back_populates="endpoint_row",
        primaryjoin=_get_endpoint_tokens_join_condition,
    )
    endpoint_auto_scaling_rules: Mapped[list[EndpointAutoScalingRuleRow]] = relationship(
        "EndpointAutoScalingRuleRow", back_populates="endpoint_row"
    )
    created_user_row: Mapped[UserRow | None] = relationship(
        "UserRow",
        back_populates="created_endpoints",
        foreign_keys=[created_user],
        primaryjoin=_get_created_user_row_join_condition,
    )
    session_owner_row: Mapped[UserRow | None] = relationship(
        "UserRow",
        back_populates="owned_endpoints",
        foreign_keys=[session_owner],
        primaryjoin=_get_session_owner_row_join_condition,
    )

    revisions: Mapped[list[DeploymentRevisionRow]] = relationship(
        "DeploymentRevisionRow",
        back_populates="endpoint_row",
        primaryjoin=_get_endpoint_revisions_join_condition,
        order_by="DeploymentRevisionRow.revision_number.desc()",
    )
    primary_replica_group_row: Mapped[ReplicaGroupRow | None] = relationship(
        "ReplicaGroupRow",
        primaryjoin=_get_primary_replica_group_join_condition,
        viewonly=True,
        uselist=False,
    )
    target_replica_group_row: Mapped[ReplicaGroupRow | None] = relationship(
        "ReplicaGroupRow",
        primaryjoin=_get_target_replica_group_join_condition,
        viewonly=True,
        uselist=False,
    )
    # Sourced from the replica groups: the current revision is the primary
    # group's ``current_revision_id`` and the deploying revision is the
    # target group's ``target_revision_id`` (``None`` when no rollout is in
    # progress). Joined through ``replica_groups`` so existing consumers
    # (``to_deployment_info`` and the ``selectinload`` paths) are unchanged.
    current_revision_row: Mapped[DeploymentRevisionRow | None] = relationship(
        "DeploymentRevisionRow",
        secondary="replica_groups",
        primaryjoin=_get_primary_replica_group_join_condition,
        secondaryjoin=_get_current_revision_secondaryjoin,
        viewonly=True,
        uselist=False,
    )
    deploying_revision_row: Mapped[DeploymentRevisionRow | None] = relationship(
        "DeploymentRevisionRow",
        primaryjoin=_get_deploying_revision_join_condition,
        viewonly=True,
        uselist=False,
    )

    auto_scaling_policy: Mapped[DeploymentAutoScalingPolicyRow | None] = relationship(
        "DeploymentAutoScalingPolicyRow",
        back_populates="endpoint_row",
        primaryjoin=_get_endpoint_auto_scaling_policy_join_condition,
        uselist=False,
    )

    deployment_policy: Mapped[DeploymentPolicyRow | None] = relationship(
        "DeploymentPolicyRow",
        back_populates="endpoint_row",
        primaryjoin=_get_deployment_policy_join_condition,
        uselist=False,
    )

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        endpoint_id: UUID,
        domain: str | None = None,
        project: UUID | None = None,
        user_uuid: UUID | None = None,
        load_routes: bool = False,
        load_tokens: bool = False,
        load_created_user: bool = False,
        load_session_owner: bool = False,
        load_revisions: bool = False,
    ) -> Self:
        """
        :raises: sqlalchemy.orm.exc.NoResultFound
        """
        from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow

        query = sa.select(EndpointRow).filter(EndpointRow.id == endpoint_id)
        if load_routes:
            query = query.options(selectinload(EndpointRow.routings))
        if load_tokens:
            query = query.options(selectinload(EndpointRow.tokens))
        if load_created_user:
            query = query.options(selectinload(EndpointRow.created_user_row))
        if load_session_owner:
            query = query.options(selectinload(EndpointRow.session_owner_row))
        if load_revisions:
            query = query.options(
                # Revision-resolution helpers (``_find_current_revision`` /
                # ``_find_active_revision``) read the group-sourced
                # current/deploying revision relationships, so load only those
                # two revision rows — not the full revision history.
                selectinload(EndpointRow.current_revision_row).selectinload(
                    DeploymentRevisionRow.image_row
                ),
                selectinload(EndpointRow.deploying_revision_row).selectinload(
                    DeploymentRevisionRow.image_row
                ),
            )
        if project:
            query = query.filter(EndpointRow.project == project)
        if domain:
            query = query.filter(EndpointRow.domain == domain)
        if user_uuid:
            query = query.filter(EndpointRow.session_owner == user_uuid)
        result = await session.execute(query)
        row = result.scalar()
        if row is None:
            raise NoResultFound
        return row

    @classmethod
    async def list_endpoint(
        cls,
        session: AsyncSession,
        domain: str | None = None,
        project: UUID | None = None,
        user_uuid: UUID | None = None,
        load_routes: bool = False,
        load_tokens: bool = False,
        load_created_user: bool = False,
        load_session_owner: bool = False,
        load_revisions: bool = False,
        status_filter: Iterable[EndpointLifecycle] = frozenset([EndpointLifecycle.CREATED]),
    ) -> list[Self]:
        from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow

        query = (
            sa.select(EndpointRow)
            .order_by(sa.desc(EndpointRow.created_at))
            .filter(EndpointRow.lifecycle_stage.in_(status_filter))
        )
        if load_routes:
            query = query.options(selectinload(EndpointRow.routings))
        if load_tokens:
            query = query.options(selectinload(EndpointRow.tokens))
        if load_created_user:
            query = query.options(selectinload(EndpointRow.created_user_row))
        if load_session_owner:
            query = query.options(selectinload(EndpointRow.session_owner_row))
        if load_revisions:
            query = query.options(
                # Revision-resolution helpers (``_find_current_revision`` /
                # ``_find_active_revision``) read the group-sourced
                # current/deploying revision relationships, so load only those
                # two revision rows — not the full revision history.
                selectinload(EndpointRow.current_revision_row).selectinload(
                    DeploymentRevisionRow.image_row
                ),
                selectinload(EndpointRow.deploying_revision_row).selectinload(
                    DeploymentRevisionRow.image_row
                ),
            )
        if project:
            query = query.filter(EndpointRow.project == project)
        if domain:
            query = query.filter(EndpointRow.domain == domain)
        if user_uuid:
            query = query.filter(EndpointRow.session_owner == user_uuid)
        result = await session.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def batch_load(
        cls,
        session: AsyncSession,
        endpoint_ids: Sequence[DeploymentID],
        domain: str | None = None,
        project: UUID | None = None,
        user_uuid: UUID | None = None,
        load_routes: bool = False,
        load_tokens: bool = False,
        load_created_user: bool = False,
        load_session_owner: bool = False,
        load_revisions: bool = False,
        status_filter: Iterable[EndpointLifecycle] = frozenset([EndpointLifecycle.CREATED]),
    ) -> Sequence[Self]:
        from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow

        query = (
            sa.select(EndpointRow)
            .order_by(sa.desc(EndpointRow.created_at))
            .filter(
                EndpointRow.lifecycle_stage.in_(status_filter) & EndpointRow.id.in_(endpoint_ids)
            )
        )
        if load_routes:
            query = query.options(selectinload(EndpointRow.routings))
        if load_tokens:
            query = query.options(selectinload(EndpointRow.tokens))
        if load_created_user:
            query = query.options(selectinload(EndpointRow.created_user_row))
        if load_session_owner:
            query = query.options(selectinload(EndpointRow.session_owner_row))
        if load_revisions:
            query = query.options(
                # Revision-resolution helpers (``_find_current_revision`` /
                # ``_find_active_revision``) read the group-sourced
                # current/deploying revision relationships, so load only those
                # two revision rows — not the full revision history.
                selectinload(EndpointRow.current_revision_row).selectinload(
                    DeploymentRevisionRow.image_row
                ),
                selectinload(EndpointRow.deploying_revision_row).selectinload(
                    DeploymentRevisionRow.image_row
                ),
            )
        if project:
            query = query.filter(EndpointRow.project == project)
        if domain:
            query = query.filter(EndpointRow.domain == domain)
        if user_uuid:
            query = query.filter(EndpointRow.session_owner == user_uuid)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def list_by_model(
        cls,
        session: AsyncSession,
        model_id: UUID,
        domain: str | None = None,
        project: UUID | None = None,
        user_uuid: UUID | None = None,
        load_routes: bool = False,
        load_tokens: bool = False,
        load_created_user: bool = False,
        load_session_owner: bool = False,
        load_revisions: bool = False,
        status_filter: Iterable[EndpointLifecycle] = frozenset([EndpointLifecycle.CREATED]),
    ) -> Sequence[Self]:
        from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
        from ai.backend.manager.models.replica_group import ReplicaGroupRow

        # Join through the primary replica group's current revision to find
        # endpoints by model.
        query = (
            sa.select(EndpointRow)
            .join(
                ReplicaGroupRow,
                EndpointRow.primary_replica_group_id == ReplicaGroupRow.id,
            )
            .join(
                DeploymentRevisionRow,
                ReplicaGroupRow.current_revision_id == DeploymentRevisionRow.id,
            )
            .where(
                EndpointRow.lifecycle_stage.in_(status_filter)
                & (DeploymentRevisionRow.model == model_id)
            )
            .order_by(sa.desc(EndpointRow.created_at))
        )
        if load_routes:
            query = query.options(selectinload(EndpointRow.routings))
        if load_tokens:
            query = query.options(selectinload(EndpointRow.tokens))
        if load_created_user:
            query = query.options(selectinload(EndpointRow.created_user_row))
        if load_session_owner:
            query = query.options(selectinload(EndpointRow.session_owner_row))
        if load_revisions:
            query = query.options(
                # Revision-resolution helpers (``_find_current_revision`` /
                # ``_find_active_revision``) read the group-sourced
                # current/deploying revision relationships, so load only those
                # two revision rows — not the full revision history.
                selectinload(EndpointRow.current_revision_row).selectinload(
                    DeploymentRevisionRow.image_row
                ),
                selectinload(EndpointRow.deploying_revision_row).selectinload(
                    DeploymentRevisionRow.image_row
                ),
            )
        if project:
            query = query.filter(EndpointRow.project == project)
        if domain:
            query = query.filter(EndpointRow.domain == domain)
        if user_uuid:
            query = query.filter(EndpointRow.session_owner == user_uuid)
        result = await session.execute(query)
        return result.scalars().all()

    async def create_auto_scaling_rule(
        self,
        session: AsyncSession,
        metric_source: AutoScalingMetricSource,
        metric_name: str,
        min_threshold: Decimal | None,
        max_threshold: Decimal | None,
        step_size: int,
        cooldown_seconds: int = 300,
        min_replicas: int | None = None,
        max_replicas: int | None = None,
    ) -> EndpointAutoScalingRuleRow:
        row = EndpointAutoScalingRuleRow(
            id=uuid4(),
            endpoint=self.id,
            metric_source=metric_source,
            metric_name=metric_name,
            min_threshold=min_threshold,
            max_threshold=max_threshold,
            step_size=step_size,
            cooldown_seconds=cooldown_seconds,
            min_replicas=min_replicas,
            max_replicas=max_replicas,
        )
        session.add(row)
        return row

    @property
    def terminatable_route_statuses(self) -> set[RouteStatus]:
        if self.lifecycle_stage == EndpointLifecycle.DESTROYING:
            return {
                RouteStatus.PROVISIONING,
                RouteStatus.RUNNING,
                RouteStatus.FAILED_TO_START,
            }
        return {
            RouteStatus.RUNNING,
            RouteStatus.FAILED_TO_START,
        }

    @staticmethod
    async def delegate_endpoint_ownership(
        db_session: AsyncSession,
        owner_user_uuid: UUID,
        target_user_uuid: UUID,
        target_access_key: AccessKey,
    ) -> None:
        from ai.backend.manager.models.session import KernelLoadingStrategy, SessionRow

        endpoint_rows = await EndpointRow.list_endpoint(
            db_session,
            user_uuid=owner_user_uuid,
            load_session_owner=True,
            load_routes=True,
            load_tokens=True,
        )
        session_ids: list[UUID] = []
        for row in endpoint_rows:
            row.session_owner = target_user_uuid
            for token_row in row.tokens:
                token_row.delegate_ownership(target_user_uuid)
            for routing_row in row.routings:
                routing_row.delegate_ownership(target_user_uuid)
                if routing_row.session is not None:
                    session_ids.append(routing_row.session)
        session_rows = await SessionRow.list_sessions(
            db_session, session_ids, kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS
        )
        for session_row in session_rows:
            session_row.delegate_ownership(target_user_uuid, target_access_key)

    @property
    def current_revision_id(self) -> DeploymentRevisionID | None:
        """Active revision id, sourced from the primary replica group.

        Requires ``primary_replica_group_row`` to be eagerly loaded.
        """
        group = self.primary_replica_group_row
        return group.current_revision_id if group is not None else None

    def _find_current_revision(self) -> DeploymentRevisionRow | None:
        """Active revision row, sourced from the primary replica group.

        Requires ``current_revision_row`` to be eagerly loaded.
        """
        return self.current_revision_row

    def _find_active_revision(self) -> DeploymentRevisionRow | None:
        """Return the revision representing the deployment's active spec.

        Falls back to the deploying revision (the target group's
        ``target_revision_id``) when the current revision is unset (e.g.
        during the initial DEPLOYING phase before strategy completion).
        Used by display/serialization paths that should reflect the spec
        being deployed rather than rendering empty fields.

        Requires ``current_revision_row`` and ``deploying_revision_row`` to
        be eagerly loaded.
        """
        return self.current_revision_row or self.deploying_revision_row

    def to_summary_data(self) -> DeploymentSummaryData:
        return DeploymentSummaryData(
            id=self.id,
            name=self.name,
            created_user=self.created_user,
            session_owner=self.session_owner,
            domain=self.domain,
            project=self.project,
            resource_group=self.resource_group,
            lifecycle_stage=self.lifecycle_stage,
            tag=self.tag,
            open_to_public=self.open_to_public or False,
            url=self.url,
            current_revision=self.current_revision_id,
            deploying_revision=self.deploying_revision_id,
            replicas=self.replicas,
            desired_replicas=self.desired_replicas,
            created_at=self.created_at,
            destroyed_at=self.destroyed_at,
            sub_step=self.sub_step,
        )

    def to_data(self) -> EndpointData:
        """Convert to EndpointData.

        Requires revisions and revisions.image_row to be eagerly loaded
        via selectinload for revision field population.
        ``_find_active_revision`` prefers ``current_revision`` and falls
        back to ``deploying_revision`` so the projection reflects the
        spec currently being deployed during the initial DEPLOYING
        phase. When neither pointer is set (PENDING endpoint without a
        revision yet, or leftover orphan data), revision-derived fields
        degrade to ``None`` / sentinel defaults and
        ``runtime_variant_id`` stays ``None``; legacy response surfaces
        render that as the historical blank state.
        """
        current_rev = self._find_active_revision()
        return EndpointData(
            id=self.id,
            name=self.name,
            image=(
                current_rev.image_row.to_dataclass()
                if current_rev is not None and current_rev.image_row is not None
                else None
            ),
            domain=self.domain,
            project=self.project,
            resource_group=self.resource_group,
            resource_slots=ResourceSlot({
                r.slot_name: r.quantity for r in current_rev.resource_slot_rows
            })
            if current_rev is not None
            else ResourceSlot({}),
            url=self.url or "",
            model=(
                current_rev.model or uuid.UUID(int=0)
                if current_rev is not None
                else uuid.UUID(int=0)
            ),
            model_definition_path=(
                current_rev.model_definition_path if current_rev is not None else None
            ),
            model_mount_destination=(
                current_rev.model_mount_destination if current_rev is not None else None
            ),
            created_user_id=self.created_user,
            created_user_email=(
                self.created_user_row.email if self.created_user_row is not None else None
            ),
            session_owner_id=self.session_owner,
            session_owner_email=self.session_owner_row.email if self.session_owner_row else "",
            tag=self.tag,
            startup_command=current_rev.startup_command if current_rev is not None else None,
            bootstrap_script=current_rev.bootstrap_script if current_rev is not None else None,
            callback_url=(
                yarl.URL(current_rev.callback_url)
                if current_rev is not None and current_rev.callback_url
                else None
            ),
            environ=current_rev.environ if current_rev is not None else None,
            resource_opts=current_rev.resource_opts if current_rev is not None else None,
            replicas=self.replicas,
            cluster_mode=(
                ClusterMode(current_rev.cluster_mode)
                if current_rev is not None
                else ClusterMode.SINGLE_NODE
            ),
            cluster_size=current_rev.cluster_size if current_rev is not None else 1,
            open_to_public=self.open_to_public if self.open_to_public is not None else False,
            created_at=self.created_at,
            destroyed_at=self.destroyed_at,
            retries=self.retries,
            lifecycle_stage=self.lifecycle_stage,
            runtime_variant_id=(
                RuntimeVariantID(current_rev.runtime_variant_id)
                if current_rev is not None
                else None
            ),
            extra_mounts=current_rev.extra_mounts if current_rev is not None else [],
            scaling_state=self.scaling_state,
            model_definition=current_rev.model_definition if current_rev is not None else None,
            routings=[routing.to_data() for routing in self.routings]
            if self.routings is not None
            else [],
        )

    @classmethod
    def from_deployment_creator(
        cls,
        creator: DeploymentCreator,
    ) -> Self:
        """Create an EndpointRow instance from a DeploymentCreator.

        Revision-level fields (image, resources, etc.) are not set on EndpointRow;
        they belong in DeploymentRevisionRow.
        """
        return cls(
            name=creator.metadata.name,
            created_user=creator.metadata.created_user,
            session_owner=creator.metadata.session_owner,
            replicas=creator.replica_spec.replica_count,
            domain=creator.metadata.domain,
            project=creator.metadata.project,
            resource_group=creator.metadata.resource_group,
            tag=creator.metadata.tag,
            open_to_public=creator.network.open_to_public,
            url=creator.network.url,
            # Fields not in creator - use defaults
            lifecycle_stage=EndpointLifecycle.PENDING,
            retries=0,
            revision_history_limit=creator.metadata.revision_history_limit,
        )

    def to_deployment_info(self) -> DeploymentInfo:
        """Full DeploymentInfo including the resolved current/deploying revision
        rows. Requires the revision-row relationships to be eagerly loaded
        (legacy REST v1 / engine read paths). The revision ids are derived from
        those rows, so no separate replica-group load is needed.
        """
        current_row = self.current_revision_row
        deploying_row = self.deploying_revision_row
        return self._build_deployment_info(
            current_revision_id=DeploymentRevisionID(current_row.id) if current_row else None,
            deploying_revision_id=DeploymentRevisionID(deploying_row.id) if deploying_row else None,
            current_revision=current_row.to_data() if current_row else None,
            deploying_revision=deploying_row.to_data() if deploying_row else None,
            policy=self.deployment_policy.to_data() if self.deployment_policy is not None else None,
        )

    def to_modern_deployment_info(self) -> DeploymentInfo:
        """Lightweight DeploymentInfo carrying only the revision *ids* (sourced
        from the replica groups), without loading the full revision rows. Used
        by the modern (v2) read path, which only needs the ids. Requires the
        replica-group relationships to be eagerly loaded.
        """
        return self._build_deployment_info(
            current_revision_id=self.current_revision_id,
            deploying_revision_id=self.deploying_revision_id,
            current_revision=None,
            deploying_revision=None,
            policy=self.deployment_policy.to_data() if self.deployment_policy is not None else None,
        )

    def _build_deployment_info(
        self,
        current_revision_id: DeploymentRevisionID | None,
        deploying_revision_id: DeploymentRevisionID | None,
        current_revision: ModelRevisionData | None,
        deploying_revision: ModelRevisionData | None,
        policy: DeploymentPolicyData | None = None,
    ) -> DeploymentInfo:
        """Build DeploymentInfo. The revision *ids* and the full
        ``current_revision`` / ``deploying_revision`` data are supplied by the
        caller (the full data is ``None`` on the modern read path).
        """
        return DeploymentInfo(
            id=self.id,
            metadata=DeploymentMetadata(
                name=self.name,
                domain=self.domain,
                project=self.project,
                resource_group=self.resource_group,
                created_user=self.created_user,
                session_owner=self.session_owner,
                created_at=self.created_at,
                revision_history_limit=self.revision_history_limit,
                tag=self.tag,
            ),
            state=DeploymentState(
                lifecycle=self.lifecycle_stage,
                scaling_state=self.scaling_state,
                retry_count=self.retries,
            ),
            replica=ReplicaData(
                replica_count=self.replicas,
                desired_replica_count=self.desired_replicas,
            ),
            network=DeploymentNetworkData(
                open_to_public=self.open_to_public if self.open_to_public is not None else False,
                access_token_ids=None,
                url=self.url,
                preferred_domain_name=None,
            ),
            options=self.options,
            current_revision_id=current_revision_id,
            deploying_revision_id=deploying_revision_id,
            current_revision=current_revision,
            deploying_revision=deploying_revision,
            sub_step=self.sub_step,
            policy=policy,
            primary_replica_group_id=self.primary_replica_group_id,
        )


class EndpointTokenRow(Base):  # type: ignore[misc]
    __tablename__ = "endpoint_tokens"

    id: Mapped[UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    token: Mapped[str] = mapped_column("token", sa.String(), nullable=False)
    endpoint: Mapped[DeploymentID | None] = mapped_column("endpoint", GUID, nullable=True)
    session_owner: Mapped[UUID] = mapped_column("session_owner", GUID, nullable=False)
    domain: Mapped[str] = mapped_column(
        "domain",
        sa.String(length=64),
        sa.ForeignKey("domains.name", ondelete="CASCADE"),
        nullable=False,
    )
    project: Mapped[UUID] = mapped_column(
        "project",
        GUID,
        sa.ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        "expires_at", sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )

    endpoint_row: Mapped[EndpointRow | None] = relationship(
        "EndpointRow",
        back_populates="tokens",
        foreign_keys=[endpoint],
        primaryjoin=_get_endpoint_token_endpoint_row_join_condition,
    )

    def __init__(
        self,
        id: UUID,
        token: str,
        endpoint: DeploymentID,
        domain: str,
        project: UUID,
        session_owner: UUID,
        expires_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.token = token
        self.endpoint = endpoint
        self.domain = domain
        self.project = project
        self.session_owner = session_owner
        self.expires_at = expires_at

    @classmethod
    async def list(
        cls,
        session: AsyncSession,
        endpoint_id: UUID,
        *,
        domain: str | None = None,
        project: UUID | None = None,
        user_uuid: UUID | None = None,
        load_endpoint: bool = False,
    ) -> Sequence[Self]:
        query = (
            sa.select(EndpointTokenRow)
            .filter(EndpointTokenRow.endpoint == endpoint_id)
            .order_by(sa.desc(EndpointTokenRow.created_at))
        )
        if load_endpoint:
            query = query.options(selectinload(EndpointTokenRow.tokens))
        if project:
            query = query.filter(EndpointTokenRow.project == project)
        if domain:
            query = query.filter(EndpointTokenRow.domain == domain)
        if user_uuid:
            query = query.filter(EndpointTokenRow.session_owner == user_uuid)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        token: str,
        *,
        domain: str | None = None,
        project: UUID | None = None,
        user_uuid: UUID | None = None,
        load_endpoint: bool = False,
    ) -> Self:
        query = sa.select(EndpointTokenRow).filter(EndpointTokenRow.token == token)
        if load_endpoint:
            query = query.options(selectinload(EndpointTokenRow.tokens))
        if project:
            query = query.filter(EndpointTokenRow.project == project)
        if domain:
            query = query.filter(EndpointTokenRow.domain == domain)
        if user_uuid:
            query = query.filter(EndpointTokenRow.session_owner == user_uuid)
        result = await session.execute(query)
        row = result.scalar()
        if not row:
            raise NoResultFound
        return row

    def delegate_ownership(self, user_uuid: UUID) -> None:
        self.session_owner = user_uuid

    def to_dataclass(self) -> EndpointTokenData:
        return EndpointTokenData(
            id=self.id,
            token=self.token,
            endpoint=self.endpoint or uuid.UUID(int=0),
            domain=self.domain,
            project=self.project,
            session_owner=self.session_owner,
            created_at=self.created_at,
        )


class EndpointAutoScalingRuleRow(Base):  # type: ignore[misc]
    __tablename__ = "endpoint_auto_scaling_rules"

    id: Mapped[UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    metric_source: Mapped[AutoScalingMetricSource] = mapped_column(
        "metric_source", StrEnumType(AutoScalingMetricSource, use_name=False), nullable=False
    )
    metric_name: Mapped[str] = mapped_column("metric_name", sa.Text(), nullable=False)
    min_threshold: Mapped[Decimal | None] = mapped_column(
        "min_threshold", DecimalType(), nullable=True
    )
    max_threshold: Mapped[Decimal | None] = mapped_column(
        "max_threshold", DecimalType(), nullable=True
    )
    step_size: Mapped[int] = mapped_column("step_size", sa.Integer(), nullable=False)
    cooldown_seconds: Mapped[int] = mapped_column(
        "cooldown_seconds", sa.Integer(), nullable=False, default=300
    )

    min_replicas: Mapped[int | None] = mapped_column("min_replicas", sa.Integer(), nullable=True)
    max_replicas: Mapped[int | None] = mapped_column("max_replicas", sa.Integer(), nullable=True)

    prometheus_query_preset_id: Mapped[UUID | None] = mapped_column(
        "prometheus_query_preset_id",
        GUID,
        sa.ForeignKey("prometheus_query_presets.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        "last_triggered_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )

    endpoint: Mapped[DeploymentID] = mapped_column(
        "endpoint",
        GUID,
        sa.ForeignKey("endpoints.id", ondelete="CASCADE"),
        nullable=False,
    )

    endpoint_row: Mapped[EndpointRow] = relationship(
        "EndpointRow", back_populates="endpoint_auto_scaling_rules", lazy="joined"
    )

    @classmethod
    async def list(
        cls,
        session: AsyncSession,
        endpoint_status_filter: Iterable[EndpointLifecycle] = frozenset([
            EndpointLifecycle.CREATED
        ]),
    ) -> Sequence[Self]:
        query = sa.select(EndpointAutoScalingRuleRow)
        if endpoint_status_filter:
            query = (
                query.join(EndpointAutoScalingRuleRow.endpoint_row)
                .filter(EndpointRow.lifecycle_stage.in_(endpoint_status_filter))
                .options(contains_eager(EndpointAutoScalingRuleRow.endpoint_row))
            )
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get(
        cls, session: AsyncSession, id: UUID, load_endpoint: bool = False
    ) -> EndpointAutoScalingRuleRow:
        query = sa.select(EndpointAutoScalingRuleRow).filter(EndpointAutoScalingRuleRow.id == id)
        if load_endpoint:
            query = query.options(selectinload(EndpointAutoScalingRuleRow.endpoint_row))
        result = await session.execute(query)
        row = result.scalar()
        if not row:
            raise ObjectNotFound(object_name="Endpoint Autoscaling Rule")
        return row

    async def remove_rule(
        self,
        session: AsyncSession,
    ) -> None:
        await session.delete(self)

    def to_data(self) -> EndpointAutoScalingRuleData:
        if self.max_threshold is not None:
            threshold_str = str(self.max_threshold)
            comparator = AutoScalingMetricComparator.GREATER_THAN
        elif self.min_threshold is not None:
            threshold_str = str(self.min_threshold)
            comparator = AutoScalingMetricComparator.LESS_THAN
        else:
            threshold_str = "0"
            comparator = AutoScalingMetricComparator.GREATER_THAN
        return EndpointAutoScalingRuleData(
            id=self.id,
            metric_source=self.metric_source,
            metric_name=self.metric_name,
            threshold=threshold_str,
            comparator=comparator,
            step_size=self.step_size,
            cooldown_seconds=self.cooldown_seconds,
            min_replicas=self.min_replicas or 0,
            max_replicas=self.max_replicas or 0,
            created_at=self.created_at,
            last_triggered_at=self.last_triggered_at,
            endpoint=self.endpoint,
        )

    @classmethod
    def from_creator(cls, endpoint_id: UUID, creator: AutoScalingRuleCreator) -> Self:
        return cls(
            id=uuid4(),
            endpoint=endpoint_id,
            metric_source=creator.condition.metric_source,
            metric_name=creator.condition.metric_name,
            min_threshold=creator.condition.scale_down_threshold,
            max_threshold=creator.condition.scale_up_threshold,
            step_size=creator.action.step_size,
            cooldown_seconds=creator.action.cooldown_seconds,
            min_replicas=creator.action.min_replicas,
            max_replicas=creator.action.max_replicas,
            prometheus_query_preset_id=creator.condition.prometheus_query_preset_id,
        )

    def to_autoscaling_rule(self) -> AutoScalingRule:
        return AutoScalingRule(
            id=self.id,
            condition=AutoScalingCondition(
                metric_source=self.metric_source,
                metric_name=self.metric_name,
                scale_up_threshold=self.max_threshold,
                scale_down_threshold=self.min_threshold,
                prometheus_query_preset_id=self.prometheus_query_preset_id,
            ),
            action=AutoScalingAction(
                step_size=self.step_size,
                cooldown_seconds=self.cooldown_seconds,
                min_replicas=self.min_replicas,
                max_replicas=self.max_replicas,
            ),
            created_at=self.created_at,
            last_triggered_at=self.last_triggered_at,
        )

    # New type conversion methods for Model Deployment

    @classmethod
    def from_model_deployment_creator(cls, creator: ModelDeploymentAutoScalingRuleCreator) -> Self:
        """Create from ModelDeploymentAutoScalingRuleCreator (new type)."""
        return cls(
            id=uuid4(),
            endpoint=creator.model_deployment_id,
            metric_source=creator.metric_source,
            metric_name=creator.metric_name,
            min_threshold=creator.min_threshold,
            max_threshold=creator.max_threshold,
            step_size=creator.step_size,
            cooldown_seconds=creator.time_window,
            min_replicas=creator.min_replicas,
            max_replicas=creator.max_replicas,
            prometheus_query_preset_id=creator.prometheus_query_preset_id,
        )

    def to_model_deployment_data(self) -> ModelDeploymentAutoScalingRuleData:
        """Convert to ModelDeploymentAutoScalingRuleData (new type)."""
        return ModelDeploymentAutoScalingRuleData(
            id=self.id,
            model_deployment_id=self.endpoint,
            metric_source=self.metric_source,
            metric_name=self.metric_name,
            min_threshold=self.min_threshold,
            max_threshold=self.max_threshold,
            step_size=self.step_size,
            time_window=self.cooldown_seconds,
            min_replicas=self.min_replicas,
            max_replicas=self.max_replicas,
            created_at=self.created_at,
            last_triggered_at=self.last_triggered_at,
            prometheus_query_preset_id=self.prometheus_query_preset_id,
        )

    def apply_model_deployment_modifier(
        self, modifier: ModelDeploymentAutoScalingRuleModifier
    ) -> None:
        """Apply ModelDeploymentAutoScalingRuleModifier to update fields.

        Uses fields_to_update() which honours both OptionalState (NOP/UPDATE)
        and TriState (NOP/UPDATE/NULLIFY). Dict keys match DB column names so
        each entry can be applied directly via setattr, preserving NULLIFY
        semantics for nullable columns (min/max_threshold, min/max_replicas,
        prometheus_query_preset_id).
        """
        for column_name, value in modifier.fields_to_update().items():
            setattr(self, column_name, value)


class ModelServiceHelper:
    @staticmethod
    async def check_scaling_group(
        conn: AsyncConnection,
        scaling_group: str,
        owner_access_key: AccessKey,
        target_domain: str,
        target_project: str | ProjectID,
    ) -> str:
        """
        Wrapper of `registry.check_scaling_group()` with additional guards flavored for
        model service included
        """
        from ai.backend.manager.registry import check_scaling_group

        checked_scaling_group = await check_scaling_group(
            conn,
            scaling_group,
            SessionTypes.INFERENCE,
            owner_access_key,
            target_domain,
            target_project,
        )

        query = (
            sa.select(scaling_groups.c.wsproxy_addr, scaling_groups.c.wsproxy_api_token)
            .select_from(scaling_groups)
            .where(scaling_groups.c.name == checked_scaling_group)
        )

        result = await conn.execute(query)
        sgroup = result.first()
        if sgroup is None:
            raise ServiceUnavailable("Scaling group not found")
        wsproxy_addr = sgroup.wsproxy_addr
        if not wsproxy_addr:
            raise ServiceUnavailable("No coordinator configured for this resource group")

        if not sgroup.wsproxy_api_token:
            raise ServiceUnavailable("Scaling group not ready to start model service")

        return checked_scaling_group

    @staticmethod
    async def check_extra_mounts(
        conn: AsyncConnection,
        legacy_etcd_loader: LegacyEtcdLoader,
        storage_manager: StorageSessionManager,
        model_id: UUID,
        model_mount_destination: str,
        extra_mounts: dict[UUID, MountOptionModel],
        user_scope: UserScope,
        resource_policy: dict[str, Any],
    ) -> Sequence[VFolderMount]:
        """
        check if user is allowed to access every folders eagering to mount (other than model VFolder)
        on general session creation lifecycle this check will be completed by `enqueue_session()` function,
        which is not covered by the validation procedure (`create_session(dry_run=True)` call at the bottom part of `create()` API)
        so we have to manually cover this part here.
        """
        if model_id in extra_mounts:
            raise InvalidAPIParameters(
                "Same VFolder appears on both model specification and VFolder mount"
            )

        mount_requests = [
            VFolderMountRequest(
                ref=folder_id,
                dst_path=options.mount_destination,
                options=VFolderMountOptions(
                    permission=options.permission,
                    subpath=options.subpath,
                ),
            )
            for folder_id, options in extra_mounts.items()
        ]
        allowed_vfolder_types = await legacy_etcd_loader.get_vfolder_types()
        vfolder_mounts = await prepare_vfolder_mounts(
            conn,
            storage_manager,
            allowed_vfolder_types,
            user_scope,
            resource_policy,
            mount_requests,
        )

        for vfolder in vfolder_mounts:
            if str(vfolder.kernel_path) == model_mount_destination:
                raise InvalidAPIParameters(
                    "extra_mounts.mount_destination conflicts with model_mount_destination config. Make sure not to shadow value defined at model_mount_destination as a mount destination of extra VFolders."
                )
            if vfolder.usage_mode == VFolderUsageMode.MODEL:
                raise InvalidAPIParameters(
                    "MODEL type VFolders cannot be added as a part of extra_mounts folder"
                )

        return vfolder_mounts

    @staticmethod
    async def _listdir(
        storage_manager: StorageSessionManager,
        proxy_name: str,
        volume_name: str,
        vfid: VFolderID,
        relpath: str,
    ) -> dict[str, Any]:
        manager_facing_client = storage_manager.get_manager_facing_client(proxy_name)
        result = await manager_facing_client.list_files(
            volume_name,
            str(vfid),
            relpath,
        )
        return cast(dict[str, Any], result)

from __future__ import annotations

import logging
from collections.abc import (
    Container,
    Mapping,
    Sequence,
)
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Optional,
    Self,
    cast,
)
from uuid import UUID, uuid4

import sqlalchemy as sa
import trafaret as t
import yarl
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from sqlalchemy import CheckConstraint
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.orm import contains_eager, foreign, relationship, selectinload
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.config import model_definition_iv
from ai.backend.common.types import (
    AccessKey,
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    EndpointId,
    RedisConnectionInfo,
    RuntimeVariant,
    SessionTypes,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.defs import DEFAULT_CHUNK_SIZE
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.types import MountOptionModel, UserScope

from ..errors.exceptions import (
    InvalidAPIParameters,
    ObjectNotFound,
    ServiceUnavailable,
)
from .base import (
    GUID,
    Base,
    DecimalType,
    EndpointIDColumn,
    EnumValueType,
    IDColumn,
    ResourceSlotColumn,
    StrEnumType,
    StructuredJSONObjectListColumn,
    URLColumn,
)
from .image import ImageRow
from .routing import RouteStatus
from .scaling_group import scaling_groups
from .user import UserRow
from .vfolder import VFolderRow, prepare_vfolder_mounts

if TYPE_CHECKING:
    from ai.backend.manager.services.model_serving.types import EndpointTokenData

    from .gql import GraphQueryContext

__all__ = (
    "EndpointRow",
    "EndpointLifecycle",
    "ModelServicePredicateChecker",
    "EndpointStatistics",
    "EndpointTokenRow",
    "EndpointAutoScalingRuleRow",
)


log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class EndpointLifecycle(Enum):
    CREATED = "created"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"


class EndpointRow(Base):
    __tablename__ = "endpoints"

    __table_args__ = (
        CheckConstraint(
            sa.or_(
                sa.column("lifecycle_stage") == EndpointLifecycle.DESTROYED.value,
                sa.column("image").isnot(None),
            ),
            name="ck_image_required_unless_destroyed",
        ),
    )

    id = EndpointIDColumn()
    name = sa.Column("name", sa.String(length=512), nullable=False)
    created_user = sa.Column("created_user", GUID, nullable=False)
    session_owner = sa.Column("session_owner", GUID, nullable=False)
    # minus session count means this endpoint is requested for removal
    replicas = sa.Column("replicas", sa.Integer, nullable=False, default=0, server_default="0")
    image = sa.Column("image", GUID)
    model = sa.Column(
        "model",
        GUID,
        sa.ForeignKey("vfolders.id", ondelete="SET NULL"),
        nullable=True,
    )
    model_mount_destination = sa.Column(
        "model_mount_destination",
        sa.String(length=1024),
        nullable=False,
        default="/models",
        server_default="/models",
    )
    domain = sa.Column(
        "domain",
        sa.String(length=64),
        sa.ForeignKey("domains.name", ondelete="RESTRICT"),
        nullable=False,
    )
    project = sa.Column(
        "project",
        GUID,
        sa.ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=False,
    )
    resource_group = sa.Column(
        "resource_group",
        sa.ForeignKey("scaling_groups.name", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    lifecycle_stage = sa.Column(
        "lifecycle_stage",
        EnumValueType(EndpointLifecycle),
        nullable=False,
        default=EndpointLifecycle.CREATED,
    )
    tag = sa.Column("tag", sa.String(length=64), nullable=True)
    startup_command = sa.Column("startup_command", sa.Text, nullable=True)
    bootstrap_script = sa.Column("bootstrap_script", sa.String(length=16 * 1024), nullable=True)
    callback_url = sa.Column("callback_url", URLColumn, nullable=True, default=sa.null())
    environ = sa.Column("environ", pgsql.JSONB(), nullable=True, default={})
    open_to_public = sa.Column("open_to_public", sa.Boolean, default=False)
    runtime_variant = sa.Column(
        "runtime_variant",
        StrEnumType(RuntimeVariant),
        nullable=False,
        default=RuntimeVariant.CUSTOM,
    )

    model_definition_path = sa.Column("model_definition_path", sa.String(length=128), nullable=True)

    resource_slots = sa.Column("resource_slots", ResourceSlotColumn(), nullable=False)
    url = sa.Column("url", sa.String(length=1024))
    resource_opts = sa.Column("resource_opts", pgsql.JSONB(), nullable=True, default={})
    cluster_mode = sa.Column(
        "cluster_mode",
        sa.String(length=16),
        nullable=False,
        default=ClusterMode.SINGLE_NODE,
        server_default=ClusterMode.SINGLE_NODE.name,
    )
    cluster_size = sa.Column(
        "cluster_size", sa.Integer, nullable=False, default=1, server_default="1"
    )

    extra_mounts = sa.Column(
        "extra_mounts",
        StructuredJSONObjectListColumn(VFolderMount),
        nullable=False,
        default=[],
        server_default="[]",
    )

    retries = sa.Column("retries", sa.Integer, nullable=False, default=0, server_default="0")
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=True,
    )
    destroyed_at = sa.Column(
        "destroyed_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )

    routings = relationship("RoutingRow", back_populates="endpoint_row")
    tokens = relationship(
        "EndpointTokenRow",
        back_populates="endpoint_row",
        primaryjoin="foreign(EndpointTokenRow.endpoint) == EndpointRow.id",
    )
    endpoint_auto_scaling_rules = relationship(
        "EndpointAutoScalingRuleRow", back_populates="endpoint_row"
    )
    image_row = relationship(
        "ImageRow",
        primaryjoin=lambda: foreign(EndpointRow.image) == ImageRow.id,
        foreign_keys=[image],
        back_populates="endpoints",
    )

    model_row = relationship("VFolderRow", back_populates="endpoints")
    created_user_row = relationship(
        "UserRow",
        back_populates="created_endpoints",
        foreign_keys=[created_user],
        primaryjoin=lambda: foreign(EndpointRow.created_user) == UserRow.uuid,
    )
    session_owner_row = relationship(
        "UserRow",
        back_populates="owned_endpoints",
        foreign_keys=[session_owner],
        primaryjoin=lambda: foreign(EndpointRow.session_owner) == UserRow.uuid,
    )

    def __init__(
        self,
        name: str,
        model_definition_path: str | None,
        created_user: UUID,
        session_owner: UUID,
        replicas: int,
        image: ImageRow,
        model: UUID,
        domain: str,
        project: UUID,
        resource_group: str,
        resource_slots: Mapping[str, Any],
        cluster_mode: ClusterMode,
        cluster_size: int,
        extra_mounts: Sequence[VFolderMount],
        runtime_variant: RuntimeVariant,
        *,
        model_mount_destination: Optional[str] = None,
        tag: Optional[str] = None,
        startup_command: Optional[str] = None,
        bootstrap_script: Optional[str] = None,
        callback_url: Optional[yarl.URL] = None,
        environ: Optional[Mapping[str, Any]] = None,
        resource_opts: Optional[Mapping[str, Any]] = None,
        open_to_public: bool = False,
    ):
        self.id = uuid4()
        self.name = name
        self.model_definition_path = model_definition_path
        self.created_user = created_user
        self.session_owner = session_owner
        self.replicas = replicas
        self.image = image.id
        self.model = model
        self.domain = domain
        self.project = project
        self.resource_group = resource_group
        self.resource_slots = resource_slots
        self.cluster_mode = cluster_mode
        self.cluster_size = cluster_size
        self.extra_mounts = extra_mounts
        self.model_mount_destination = model_mount_destination or "/models"
        self.tag = tag
        self.startup_command = startup_command
        self.bootstrap_script = bootstrap_script
        self.callback_url = callback_url
        self.environ = environ
        self.resource_opts = resource_opts
        self.open_to_public = open_to_public
        self.runtime_variant = runtime_variant

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        endpoint_id: UUID,
        domain: Optional[str] = None,
        project: Optional[UUID] = None,
        user_uuid: Optional[UUID] = None,
        load_routes: bool = False,
        load_tokens: bool = False,
        load_image: bool = False,
        load_created_user: bool = False,
        load_session_owner: bool = False,
        load_model: bool = False,
    ) -> Self:
        """
        :raises: sqlalchemy.orm.exc.NoResultFound
        """
        query = sa.select(EndpointRow).filter(EndpointRow.id == endpoint_id)
        if load_routes:
            query = query.options(selectinload(EndpointRow.routings))
        if load_tokens:
            query = query.options(selectinload(EndpointRow.tokens))
        if load_image:
            query = query.options(
                selectinload(EndpointRow.image_row).selectinload(ImageRow.aliases)
            )
        if load_created_user:
            query = query.options(selectinload(EndpointRow.created_user_row))
        if load_session_owner:
            query = query.options(selectinload(EndpointRow.session_owner_row))
        if load_model:
            query = query.options(selectinload(EndpointRow.model_row))
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
    async def list(
        cls,
        session: AsyncSession,
        domain: Optional[str] = None,
        project: Optional[UUID] = None,
        user_uuid: Optional[UUID] = None,
        load_routes: bool = False,
        load_image: bool = False,
        load_tokens: bool = False,
        load_created_user: bool = False,
        load_session_owner: bool = False,
        status_filter: Container[EndpointLifecycle] = frozenset([EndpointLifecycle.CREATED]),
    ) -> list[Self]:
        query = (
            sa.select(EndpointRow)
            .order_by(sa.desc(EndpointRow.created_at))
            .filter(EndpointRow.lifecycle_stage.in_(status_filter))
        )
        if load_routes:
            query = query.options(selectinload(EndpointRow.routings))
        if load_tokens:
            query = query.options(selectinload(EndpointRow.tokens))
        if load_image:
            query = query.options(selectinload(EndpointRow.image_row))
        if load_created_user:
            query = query.options(selectinload(EndpointRow.created_user_row))
        if load_session_owner:
            query = query.options(selectinload(EndpointRow.session_owner_row))
        if project:
            query = query.filter(EndpointRow.project == project)
        if domain:
            query = query.filter(EndpointRow.domain == domain)
        if user_uuid:
            query = query.filter(EndpointRow.session_owner == user_uuid)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def batch_load(
        cls,
        session: AsyncSession,
        endpoint_ids: Sequence[EndpointId],
        domain: Optional[str] = None,
        project: Optional[UUID] = None,
        user_uuid: Optional[UUID] = None,
        load_routes: bool = False,
        load_image: bool = False,
        load_tokens: bool = False,
        load_created_user: bool = False,
        load_session_owner: bool = False,
        status_filter: Container[EndpointLifecycle] = frozenset([EndpointLifecycle.CREATED]),
    ) -> Sequence[Self]:
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
        if load_image:
            query = query.options(selectinload(EndpointRow.image_row))
        if load_created_user:
            query = query.options(selectinload(EndpointRow.created_user_row))
        if load_session_owner:
            query = query.options(selectinload(EndpointRow.session_owner_row))
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
        domain: Optional[str] = None,
        project: Optional[UUID] = None,
        user_uuid: Optional[UUID] = None,
        load_routes: bool = False,
        load_image: bool = False,
        load_tokens: bool = False,
        load_created_user: bool = False,
        load_session_owner: bool = False,
        status_filter: Container[EndpointLifecycle] = frozenset([EndpointLifecycle.CREATED]),
    ) -> Sequence[Self]:
        query = (
            sa.select(EndpointRow)
            .order_by(sa.desc(EndpointRow.created_at))
            .filter(
                EndpointRow.lifecycle_stage.in_(status_filter) & (EndpointRow.model == model_id)
            )
        )
        if load_routes:
            query = query.options(selectinload(EndpointRow.routings))
        if load_tokens:
            query = query.options(selectinload(EndpointRow.tokens))
        if load_image:
            query = query.options(selectinload(EndpointRow.image_row))
        if load_created_user:
            query = query.options(selectinload(EndpointRow.created_user_row))
        if load_session_owner:
            query = query.options(selectinload(EndpointRow.session_owner_row))
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
        threshold: Decimal,
        comparator: AutoScalingMetricComparator,
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
            threshold=threshold,
            comparator=comparator,
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
                RouteStatus.HEALTHY,
                RouteStatus.UNHEALTHY,
                RouteStatus.FAILED_TO_START,
            }
        else:
            return {
                RouteStatus.HEALTHY,
                RouteStatus.UNHEALTHY,
                RouteStatus.FAILED_TO_START,
            }

    @staticmethod
    async def delegate_endpoint_ownership(
        db_session: AsyncSession,
        owner_user_uuid: UUID,
        target_user_uuid: UUID,
        target_access_key: AccessKey,
    ) -> None:
        from .routing import RoutingRow
        from .session import KernelLoadingStrategy, SessionRow

        endpoint_rows = await EndpointRow.list(
            db_session,
            user_uuid=owner_user_uuid,
            load_session_owner=True,
            load_routes=True,
            load_tokens=True,
        )
        session_ids: List[UUID] = []
        for row in endpoint_rows:
            row.session_owner = target_user_uuid
            for token_row in cast(list[EndpointTokenRow], row.tokens):
                token_row.delegate_ownership(target_user_uuid)
            for routing_row in cast(list[RoutingRow], row.routings):
                routing_row.delegate_ownership(target_user_uuid)
                session_ids.append(routing_row.session)
        session_rows = await SessionRow.list_sessions(
            db_session, session_ids, kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS
        )
        for session_row in session_rows:
            session_row.delegate_ownership(target_user_uuid, target_access_key)


class EndpointTokenRow(Base):
    __tablename__ = "endpoint_tokens"

    id = IDColumn()
    token = sa.Column("token", sa.String(), nullable=False)
    endpoint = sa.Column("endpoint", GUID, nullable=True)
    session_owner = sa.Column("session_owner", GUID, nullable=False)
    domain = sa.Column(
        "domain",
        sa.String(length=64),
        sa.ForeignKey("domains.name", ondelete="CASCADE"),
        nullable=False,
    )
    project = sa.Column(
        "project",
        GUID,
        sa.ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
    )

    endpoint_row = relationship(
        "EndpointRow",
        back_populates="tokens",
        foreign_keys=[endpoint],
        primaryjoin=lambda: foreign(EndpointTokenRow.endpoint) == EndpointRow.id,
    )

    def __init__(
        self,
        id: UUID,
        token: str,
        endpoint: UUID,
        domain: str,
        project: UUID,
        session_owner: UUID,
    ) -> None:
        self.id = id
        self.token = token
        self.endpoint = endpoint
        self.domain = domain
        self.project = project
        self.session_owner = session_owner

    @classmethod
    async def list(
        cls,
        session: AsyncSession,
        endpoint_id: UUID,
        *,
        domain: Optional[str] = None,
        project: Optional[UUID] = None,
        user_uuid: Optional[UUID] = None,
        load_endpoint=False,
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
        domain: Optional[str] = None,
        project: Optional[UUID] = None,
        user_uuid: Optional[UUID] = None,
        load_endpoint=False,
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
        from ai.backend.manager.services.model_serving.types import EndpointTokenData

        return EndpointTokenData(
            id=self.id,
            token=self.token,
            endpoint=self.endpoint,
            domain=self.domain,
            project=self.project,
            session_owner=self.session_owner,
            created_at=self.created_at,
        )


class EndpointAutoScalingRuleRow(Base):
    __tablename__ = "endpoint_auto_scaling_rules"

    id = IDColumn()
    metric_source = sa.Column(
        "metric_source", StrEnumType(AutoScalingMetricSource, use_name=False), nullable=False
    )
    metric_name = sa.Column("metric_name", sa.Text(), nullable=False)
    threshold = sa.Column("threshold", DecimalType(), nullable=False)
    comparator = sa.Column(
        "comparator", StrEnumType(AutoScalingMetricComparator, use_name=False), nullable=False
    )
    step_size = sa.Column("step_size", sa.Integer(), nullable=False)
    cooldown_seconds = sa.Column("cooldown_seconds", sa.Integer(), nullable=False, default=300)

    min_replicas = sa.Column("min_replicas", sa.Integer(), nullable=True)
    max_replicas = sa.Column("max_replicas", sa.Integer(), nullable=True)

    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=True,
    )
    last_triggered_at = sa.Column(
        "last_triggered_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )

    endpoint = sa.Column(
        "endpoint",
        GUID,
        sa.ForeignKey("endpoints.id", ondelete="CASCADE"),
        nullable=False,
    )

    endpoint_row = relationship(
        "EndpointRow", back_populates="endpoint_auto_scaling_rules", lazy="joined"
    )

    @classmethod
    async def list(
        cls,
        session: AsyncSession,
        endpoint_status_filter: Container[EndpointLifecycle] = frozenset([
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
        cls, session: AsyncSession, id: UUID, load_endpoint=False
    ) -> "EndpointAutoScalingRuleRow":
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


class ModelServicePredicateChecker:
    @staticmethod
    async def check_scaling_group(
        conn: AsyncConnection,
        scaling_group: str,
        owner_access_key: AccessKey,
        target_domain: str,
        target_project: str | UUID,
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
            sa.select([scaling_groups.c.wsproxy_addr, scaling_groups.c.wsproxy_api_token])
            .select_from(scaling_groups)
            .where((scaling_groups.c.name == checked_scaling_group))
        )

        result = await conn.execute(query)
        sgroup = result.first()
        wsproxy_addr = sgroup["wsproxy_addr"]
        if not wsproxy_addr:
            raise ServiceUnavailable("No coordinator configured for this resource group")

        if not sgroup["wsproxy_api_token"]:
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

        requested_mounts = [*extra_mounts.keys()]
        requested_mount_map: dict[str | UUID, str] = {
            folder_id: options.mount_destination
            for folder_id, options in extra_mounts.items()
            if options.mount_destination
        }
        requested_mount_options: dict[str | UUID, Any] = {
            folder_id: {
                "type": options.type,
                "permission": options.permission,
            }
            for folder_id, options in extra_mounts.items()
        }
        log.debug(
            "requested mounts: {}, mount_map: {}, mount_options: {}",
            requested_mounts,
            requested_mount_map,
            requested_mount_options,
        )
        allowed_vfolder_types = await legacy_etcd_loader.get_vfolder_types()
        vfolder_mounts = await prepare_vfolder_mounts(
            conn,
            storage_manager,
            allowed_vfolder_types,
            user_scope,
            resource_policy,
            requested_mounts,
            requested_mount_map,
            requested_mount_options,
        )

        for vfolder in vfolder_mounts:
            if vfolder.kernel_path == model_mount_destination:
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
        async with storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/list",
            json={
                "volume": volume_name,
                "vfid": str(vfid),
                "relpath": relpath,
            },
        ) as (client_api_url, storage_resp):
            return await storage_resp.json()

    @staticmethod
    async def validate_model_definition(
        storage_manager: StorageSessionManager,
        model_vfolder_row: VFolderRow | Mapping[str, Any],
        model_definition_path: str | None,
    ) -> str | None:
        """
        Checks if model definition YAML exists and is syntactically perfect.
        Returns relative path to customized model-definition.yaml (if any) or None.
        """
        match model_vfolder_row:
            case VFolderRow():
                folder_name = model_vfolder_row.name
                vfid = model_vfolder_row.vfid
                folder_host = model_vfolder_row.host
            case _:
                folder_name = model_vfolder_row["name"]
                vfid = VFolderID(model_vfolder_row["quota_scope_id"], model_vfolder_row["id"])
                folder_host = model_vfolder_row["host"]

        proxy_name, volume_name = storage_manager.get_proxy_and_volume(folder_host)

        if model_definition_path:
            path = Path(model_definition_path)
            storage_reply = await ModelServicePredicateChecker._listdir(
                storage_manager, proxy_name, volume_name, vfid, path.parent.as_posix()
            )
            for item in storage_reply["items"]:
                if item["name"] == path.name:
                    yaml_name = model_definition_path
                    break
            else:
                raise InvalidAPIParameters(
                    f"Model definition YAML file {model_definition_path} not found inside the model storage"
                )
        else:
            storage_reply = await ModelServicePredicateChecker._listdir(
                storage_manager, proxy_name, volume_name, vfid, "."
            )
            model_definition_candidates = ["model-definition.yaml", "model-definition.yml"]
            for item in storage_reply["items"]:
                if item["name"] in model_definition_candidates:
                    yaml_name = item["name"]
                    break
            else:
                raise InvalidAPIParameters(
                    'Model definition YAML file "model-definition.yaml" or "model-definition.yml" not found inside the model storage'
                )

        chunks = bytes()
        async with storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/fetch",
            json={
                "volume": volume_name,
                "vfid": str(vfid),
                "relpath": f"./{yaml_name}",
            },
        ) as (client_api_url, storage_resp):
            while True:
                chunk = await storage_resp.content.read(DEFAULT_CHUNK_SIZE)
                if not chunk:
                    break
                chunks += chunk
        model_definition_yaml = chunks.decode("utf-8")
        yaml = YAML()
        model_definition_dict = yaml.load(model_definition_yaml)
        try:
            model_definition = model_definition_iv.check(model_definition_dict)
            assert model_definition is not None
        except t.DataError as e:
            raise InvalidAPIParameters(
                f"Failed to validate model definition from vFolder {folder_name} (ID"
                f" {vfid.folder_id}): {e}",
            ) from e
        except YAMLError as e:
            raise InvalidAPIParameters(f"Invalid YAML syntax: {e}") from e

        return yaml_name


class EndpointStatistics:
    @classmethod
    async def batch_load_by_endpoint_impl(
        cls,
        redis_stat: RedisConnectionInfo,
        endpoint_ids: Sequence[UUID],
    ) -> Sequence[Optional[Mapping[str, Any]]]:
        async def _build_pipeline(redis: Redis) -> Pipeline:
            pipe = redis.pipeline()
            for endpoint_id in endpoint_ids:
                pipe.get(f"inference.{endpoint_id}.app")
            return pipe

        stats = []
        results = await redis_helper.execute(redis_stat, _build_pipeline)
        for result in results:
            if result is not None:
                stats.append(msgpack.unpackb(result))
            else:
                stats.append(None)
        return stats

    @classmethod
    async def batch_load_by_endpoint(
        cls,
        ctx: "GraphQueryContext",
        endpoint_ids: Sequence[UUID],
    ) -> Sequence[Optional[Mapping[str, Any]]]:
        return await cls.batch_load_by_endpoint_impl(ctx.redis_stat, endpoint_ids)

    @classmethod
    async def batch_load_by_replica(
        cls,
        ctx: GraphQueryContext,
        endpoint_replica_ids: Sequence[tuple[UUID, UUID]],
    ) -> Sequence[Optional[Mapping[str, Any]]]:
        async def _build_pipeline(redis: Redis) -> Pipeline:
            pipe = redis.pipeline()
            for endpoint_id, replica_id in endpoint_replica_ids:
                pipe.get(f"inference.{endpoint_id}.replica.{replica_id}")
            return pipe

        stats = []
        results = await redis_helper.execute(ctx.redis_stat, _build_pipeline)
        for result in results:
            if result is not None:
                stats.append(msgpack.unpackb(result))
            else:
                stats.append(None)
        return stats

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import (
    Container,
    Mapping,
    Sequence,
)
from decimal import Decimal
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Optional,
    Self,
    TypeAlias,
    cast,
)
from uuid import UUID, uuid4

import sqlalchemy as sa
import trafaret as t
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from sqlalchemy import CheckConstraint
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.orm import contains_eager, foreign, relationship, selectinload
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.config import model_definition_iv
from ai.backend.common.types import (
    AccessKey,
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    EndpointId,
    RuntimeVariant,
    SessionTypes,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.data.deployment.scale import (
    AutoScalingAction,
    AutoScalingCondition,
    AutoScalingRule,
    AutoScalingRuleCreator,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentState,
    ExecutionSpec,
    ModelRevisionSpec,
    MountMetadata,
    ReplicaSpec,
    ResourceSpec,
)
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.session.types import SessionStatus

from ..config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ..data.model_serving.creator import EndpointCreator
from ..data.model_serving.types import (
    EndpointAutoScalingRuleData,
    EndpointData,
    EndpointLifecycle,
    EndpointTokenData,
)
from ..errors.api import InvalidAPIParameters
from ..errors.common import ObjectNotFound, ServiceUnavailable
from ..models.storage import StorageSessionManager
from ..types import MountOptionModel, UserScope
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
from .vfolder import prepare_vfolder_mounts

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient

    from .gql import GraphQueryContext

__all__ = (
    "EndpointRow",
    "ModelServiceHelper",
    "EndpointStatistics",
    "EndpointTokenRow",
    "EndpointAutoScalingRuleRow",
    "EndpointLifecycle",
)


ModelServiceSerializableConnectionInfo: TypeAlias = dict[str, list[dict[str, Any]]]

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


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
        sa.Index(
            "ix_endpoints_unique_name_when_not_destroyed",
            "name",
            "domain",
            "project",
            unique=True,
            postgresql_where=(sa.column("lifecycle_stage") != EndpointLifecycle.DESTROYED.value),
        ),
    )

    id = EndpointIDColumn()
    name = sa.Column("name", sa.String(length=512), nullable=False)
    created_user = sa.Column("created_user", GUID, nullable=False)
    session_owner = sa.Column("session_owner", GUID, nullable=False)
    # minus session count means this endpoint is requested for removal
    replicas = sa.Column("replicas", sa.Integer, nullable=False, default=0, server_default="0")
    desired_replicas = sa.Column(
        "desired_replicas", sa.Integer, nullable=True, default=None, server_default=sa.null()
    )
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
        default=EndpointLifecycle.PENDING,
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

    async def generate_route_info(
        self, db_sess: AsyncSession
    ) -> ModelServiceSerializableConnectionInfo:
        from .kernel import KernelRow
        from .routing import RoutingRow

        active_routes = await RoutingRow.list(db_sess, self.id, load_session=True)
        running_main_kernels = await KernelRow.batch_load_main_kernels_by_session_id(
            db_sess,
            [
                r.session
                for r in active_routes
                if r.status in RouteStatus.active_route_statuses()
                and r.session
                and r.session_row.status in [SessionStatus.RUNNING, SessionStatus.CREATING]
            ],
        )
        if (num_routes_without_session := len(active_routes) - len(running_main_kernels)) > 0:
            log.info(
                "generate_route_info(): There are {} active routes without corresponding RUNNING sessions, "
                "which may be still provisioning or being terminated. (Endpoint: {})",
                num_routes_without_session,
                self.id,
            )
        session_id_to_route_map = {r.session: r for r in active_routes}
        connection_info: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        for kernel in running_main_kernels:
            if kernel.service_ports is None:
                log.debug(
                    "generate_route_info(): Kernel {} has no service ports defined. Skipping.",
                    kernel.id,
                )
                continue
            num_inference_ports = len([*filter(lambda x: x["is_inference"], kernel.service_ports)])
            if num_inference_ports > 1:
                log.warning(
                    "generate_route_info(): Multiple ({}) inference ports found. "
                    "Currently only the first-seen inference port is used. (Endpoint: {})",
                    num_inference_ports,
                    self.id,
                )
            for port_info in kernel.service_ports:
                if port_info["is_inference"]:
                    connection_info[port_info["name"]].append({
                        "session_id": str(kernel.session_id),
                        "route_id": str(session_id_to_route_map[kernel.session_id].id),
                        "kernel_host": kernel.kernel_host,
                        "kernel_port": port_info["host_ports"][0],
                    })
                    break
        return connection_info

    def to_data(self) -> EndpointData:
        return EndpointData(
            id=self.id,
            name=self.name,
            image=self.image_row.to_dataclass() if self.image_row else None,
            domain=self.domain,
            project=self.project,
            resource_group=self.resource_group,
            resource_slots=self.resource_slots,
            url=self.url,
            model=self.model,
            model_definition_path=self.model_definition_path,
            model_mount_destination=self.model_mount_destination,
            created_user_id=self.created_user,
            created_user_email=(
                self.created_user_row.email if self.created_user_row is not None else None
            ),
            session_owner_id=self.session_owner,
            session_owner_email=self.session_owner_row.email if self.session_owner_row else "",
            tag=self.tag,
            startup_command=self.startup_command,
            bootstrap_script=self.bootstrap_script,
            callback_url=self.callback_url,
            environ=self.environ,
            resource_opts=self.resource_opts,
            replicas=self.replicas,
            cluster_mode=ClusterMode(self.cluster_mode),
            cluster_size=self.cluster_size,
            open_to_public=self.open_to_public,
            created_at=self.created_at,
            destroyed_at=self.destroyed_at,
            retries=self.retries,
            lifecycle_stage=self.lifecycle_stage,
            runtime_variant=self.runtime_variant,
            extra_mounts=self.extra_mounts,
            routings=[routing.to_data() for routing in self.routings] if self.routings else None,
        )

    @classmethod
    def from_creator(cls, creator: EndpointCreator) -> Self:
        """
        Create an EndpointRow instance from an EndpointCreator instance.
        """
        return cls(
            name=creator.name,
            model_definition_path=creator.model_definition_path,
            created_user=creator.created_user,
            session_owner=creator.session_owner,
            replicas=creator.replicas,
            image=creator.image,
            model=creator.model,
            domain=creator.domain,
            project=creator.project,
            resource_group=creator.resource_group,
            resource_slots=creator.resource_slots,
            cluster_mode=creator.cluster_mode,
            cluster_size=creator.cluster_size,
            extra_mounts=creator.extra_mounts,
            runtime_variant=creator.runtime_variant,
            model_mount_destination=creator.model_mount_destination,
            tag=creator.tag,
            startup_command=creator.startup_command,
            bootstrap_script=creator.bootstrap_script,
            callback_url=creator.callback_url,
            environ=creator.environ,
            resource_opts=creator.resource_opts,
            open_to_public=creator.open_to_public,
        )

    @classmethod
    async def from_deployment_creator(
        cls,
        db_session: AsyncSession,
        creator: DeploymentCreator,
    ) -> Self:
        """
        Create an EndpointRow instance from a DeploymentCreator instance.

        Args:
            db_session: Database session for resolving image information
            creator: DeploymentCreator containing deployment configuration

        Returns:
            EndpointRow instance with image ID resolved from ImageIdentifier

        Raises:
            InvalidAPIParameters: If image is not specified in creator
            ImageNotFound: If image cannot be resolved
        """
        # Image is required
        if not creator.model_revision.image_identifier:
            raise InvalidAPIParameters("Image must be specified in DeploymentCreator")

        # Resolve image ID from ImageIdentifier
        image_row = await ImageRow.lookup(
            db_session,
            creator.model_revision.image_identifier,
        )

        return cls(
            name=creator.metadata.name,
            created_user=creator.metadata.created_user,
            session_owner=creator.metadata.session_owner,
            replicas=creator.replica_spec.replica_count,
            image=image_row.id,
            model=creator.model_revision.mounts.model_vfolder_id,
            model_mount_destination=creator.model_revision.mounts.model_mount_destination,
            model_definition_path=creator.model_revision.mounts.model_definition_path,
            domain=creator.metadata.domain,
            project=creator.metadata.project,
            resource_group=creator.metadata.resource_group,
            tag=creator.metadata.tag,
            startup_command=creator.model_revision.execution.startup_command,
            bootstrap_script=creator.model_revision.execution.bootstrap_script,
            callback_url=creator.model_revision.execution.callback_url,
            environ=creator.model_revision.execution.environ,
            open_to_public=creator.network.open_to_public,
            runtime_variant=creator.model_revision.execution.runtime_variant,
            resource_slots=creator.model_revision.resource_spec.resource_slots,
            url=creator.network.url,
            resource_opts=creator.model_revision.resource_spec.resource_opts,
            cluster_mode=creator.model_revision.resource_spec.cluster_mode,
            cluster_size=creator.model_revision.resource_spec.cluster_size,
            extra_mounts=creator.model_revision.mounts.extra_mounts,
            # Fields not in creator - use defaults
            lifecycle_stage=EndpointLifecycle.PENDING,
            retries=0,
        )

    def to_deployment_info(self) -> DeploymentInfo:
        """
        Convert EndpointRow to DeploymentInfo dataclass.

        If image_row is loaded (via selectinload), ImageIdentifier will be populated.
        Otherwise, ImageIdentifier will be None.
        """
        # Create ImageIdentifier only if image_row is loaded
        image_identifier = ImageIdentifier(
            canonical=self.image_row.name,
            architecture=self.image_row.architecture,
        )
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
                tag=self.tag,
            ),
            state=DeploymentState(
                lifecycle=self.lifecycle_stage,
                retry_count=self.retries,
            ),
            replica_spec=ReplicaSpec(
                replica_count=self.replicas,
                desired_replica_count=self.desired_replicas,
            ),
            network=DeploymentNetworkSpec(
                open_to_public=self.open_to_public,
                url=self.url,
            ),
            model_revisions=[
                ModelRevisionSpec(
                    image_identifier=image_identifier,
                    resource_spec=ResourceSpec(
                        cluster_mode=self.cluster_mode,
                        cluster_size=self.cluster_size,
                        resource_slots=self.resource_slots,
                        resource_opts=self.resource_opts,
                    ),
                    mounts=MountMetadata(
                        model_vfolder_id=self.model,
                        model_definition_path=self.model_definition_path,
                        model_mount_destination=self.model_mount_destination,
                        extra_mounts=self.extra_mounts,
                    ),
                    execution=ExecutionSpec(
                        startup_command=self.startup_command,
                        bootstrap_script=self.bootstrap_script,
                        environ=self.environ,
                        runtime_variant=self.runtime_variant,
                        callback_url=self.callback_url,
                    ),
                ),
            ],
        )


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
        domain: Optional[str] = None,
        project: Optional[UUID] = None,
        user_uuid: Optional[UUID] = None,
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
        cls, session: AsyncSession, id: UUID, load_endpoint: bool = False
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

    def to_data(self) -> EndpointAutoScalingRuleData:
        return EndpointAutoScalingRuleData(
            id=self.id,
            metric_source=self.metric_source,
            metric_name=self.metric_name,
            threshold=self.threshold,
            comparator=self.comparator,
            step_size=self.step_size,
            cooldown_seconds=self.cooldown_seconds,
            min_replicas=self.min_replicas,
            max_replicas=self.max_replicas,
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
            threshold=creator.condition.threshold,
            comparator=creator.condition.comparator,
            step_size=creator.action.step_size,
            cooldown_seconds=creator.action.cooldown_seconds,
            min_replicas=creator.action.min_replicas,
            max_replicas=creator.action.max_replicas,
        )

    def to_autoscaling_rule(self) -> AutoScalingRule:
        return AutoScalingRule(
            id=self.id,
            condition=AutoScalingCondition(
                metric_source=self.metric_source,
                metric_name=self.metric_name,
                threshold=self.threshold,
                comparator=self.comparator,
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


class ModelServiceHelper:
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
        manager_facing_client = storage_manager.get_manager_facing_client(proxy_name)
        result = await manager_facing_client.list_files(
            volume_name,
            str(vfid),
            relpath,
        )
        return cast(dict[str, Any], result)

    @staticmethod
    async def validate_model_definition_file_exists(
        storage_manager: StorageSessionManager,
        folder_host: str,
        vfid: VFolderID,
        suggested_path: str | None,
    ) -> str:
        """
        Checks if model definition file exists in target model VFolder. Returns path to resolved model definition filename.
        Since model service counts both `model-definition.yml` and `model-definition.yaml` as valid definition file name, this function ensures
        at least one model definition file exists under the target VFolder and returns the matched filename.
        """
        proxy_name, volume_name = storage_manager.get_proxy_and_volume(folder_host)

        if suggested_path:
            path = Path(suggested_path)
            storage_reply = await ModelServiceHelper._listdir(
                storage_manager, proxy_name, volume_name, vfid, path.parent.as_posix()
            )
            for item in storage_reply["items"]:
                if item["name"] == path.name:
                    return suggested_path
            else:
                raise InvalidAPIParameters(
                    f"Model definition YAML file {suggested_path} not found inside the model storage"
                )
        else:
            storage_reply = await ModelServiceHelper._listdir(
                storage_manager, proxy_name, volume_name, vfid, "."
            )
            model_definition_candidates = ["model-definition.yaml", "model-definition.yml"]
            for item in storage_reply["items"]:
                if item["name"] in model_definition_candidates:
                    return item["name"]
            else:
                raise InvalidAPIParameters(
                    'Model definition YAML file "model-definition.yaml" or "model-definition.yml" not found inside the model storage'
                )

    @staticmethod
    async def _read_model_definition(
        storage_manager: StorageSessionManager,
        folder_host: str,
        vfid: VFolderID,
        model_definition_filename: str,
    ) -> dict[str, Any]:
        """
        Reads specified model definition file from target VFolder and returns
        """
        proxy_name, volume_name = storage_manager.get_proxy_and_volume(folder_host)
        manager_facing_client = storage_manager.get_manager_facing_client(proxy_name)
        chunks = await manager_facing_client.fetch_file_content(
            volume_name,
            str(vfid),
            f"./{model_definition_filename}",
        )
        model_definition_yaml = chunks.decode("utf-8")
        yaml = YAML()
        return yaml.load(model_definition_yaml)

    @staticmethod
    async def validate_model_definition(
        storage_manager: StorageSessionManager,
        folder_host: str,
        vfid: VFolderID,
        model_definition_path: str,
    ) -> dict[str, Any]:
        """
        Checks if model definition YAML exists and is syntactically perfect.
        Returns validated model definition configuration.
        """
        raw_model_definition = await ModelServiceHelper._read_model_definition(
            storage_manager,
            folder_host,
            vfid,
            model_definition_path,
        )

        try:
            model_definition = model_definition_iv.check(raw_model_definition)
            assert model_definition is not None
            return model_definition
        except t.DataError as e:
            raise InvalidAPIParameters(
                f"Failed to validate model definition from VFolder (ID {vfid.folder_id}): {e}",
            ) from e
        except YAMLError as e:
            raise InvalidAPIParameters(f"Invalid YAML syntax: {e}") from e


class EndpointStatistics:
    @classmethod
    async def batch_load_by_endpoint_impl(
        cls,
        valkey_stat_client: ValkeyStatClient,
        endpoint_ids: Sequence[UUID],
    ) -> Sequence[Optional[Mapping[str, Any]]]:
        endpoint_id_strs = [str(endpoint_id) for endpoint_id in endpoint_ids]
        return await valkey_stat_client.get_inference_app_statistics_batch(endpoint_id_strs)

    @classmethod
    async def batch_load_by_endpoint(
        cls,
        ctx: "GraphQueryContext",
        endpoint_ids: Sequence[UUID],
    ) -> Sequence[Optional[Mapping[str, Any]]]:
        return await cls.batch_load_by_endpoint_impl(ctx.valkey_stat, endpoint_ids)

    @classmethod
    async def batch_load_by_replica(
        cls,
        ctx: GraphQueryContext,
        endpoint_replica_ids: Sequence[tuple[UUID, UUID]],
    ) -> Sequence[Optional[Mapping[str, Any]]]:
        endpoint_replica_pairs = [
            (str(endpoint_id), str(replica_id)) for endpoint_id, replica_id in endpoint_replica_ids
        ]
        return await ctx.valkey_stat.get_inference_replica_statistics_batch(endpoint_replica_pairs)

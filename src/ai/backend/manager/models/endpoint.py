import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, ClassVar, Dict, List, Optional, Self, Union

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_psql
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import relationship

from ai.backend.common.docker import ImageRef
from ai.backend.common.types import BinarySize, SessionId
from ai.backend.manager.models.base import (
    GUID,
    Base,
    IDColumn,
    Item,
    PaginatedList,
    ResourceSlot,
    ResourceSlotColumn,
    StrEnumType,
    batch_result,
    simple_db_mutate,
    simple_db_mutate_returning_item,
)
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.minilang import FieldSpecItem
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow


class EndpointLifecycle(enum.StrEnum):
    CREATING = "CREATING"
    INACTIVE = "INACTIVE"
    UNHEALTHY = "UNHEALTHY"
    HEALTHY = "HEALTHY"
    DESTROYING = "DESTROYING"
    CREATED = "CREATED"
    DESTROYED = "DESTROYED"

    @classmethod
    def inactive_states(cls) -> set["EndpointLifecycle"]:
        return {cls.CREATING, cls.DESTROYING, cls.DESTROYED, cls.INACTIVE}


class EndpointTokenType(enum.StrEnum):
    KEYPAIR = "keypair"
    SESSION = "session"


class EndpointAutoScalingMetricType(enum.StrEnum):
    HTTP_REQUEST_RATE = "http_request_rate"
    HTTP_ERROR_RATE = "http_error_rate"
    HTTP_RESPONSE_TIME = "http_response_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    GPU_USAGE = "gpu_usage"
    GPU_MEMORY_USAGE = "gpu_memory_usage"
    SESSION_COUNT = "session_count"

    @classmethod
    def to_metric_source(cls) -> Dict[str, "AutoScalingMetricSource"]:
        return {
            cls.HTTP_REQUEST_RATE: AutoScalingMetricSource.INFERENCE_FRAMEWORK,
            cls.HTTP_ERROR_RATE: AutoScalingMetricSource.INFERENCE_FRAMEWORK,
            cls.HTTP_RESPONSE_TIME: AutoScalingMetricSource.INFERENCE_FRAMEWORK,
            cls.MEMORY_USAGE: AutoScalingMetricSource.KERNEL,
            cls.CPU_USAGE: AutoScalingMetricSource.KERNEL,
            cls.GPU_USAGE: AutoScalingMetricSource.KERNEL,
            cls.GPU_MEMORY_USAGE: AutoScalingMetricSource.KERNEL,
            cls.SESSION_COUNT: AutoScalingMetricSource.KERNEL,
        }


class AutoScalingMetricSource(enum.StrEnum):
    KERNEL = "kernel"
    INFERENCE_FRAMEWORK = "inference_framework"
    USER = "user"


class AutoScalingMetricComparator(enum.StrEnum):
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="


class EndpointRow(Base):
    __tablename__ = "endpoints"
    __table_args__ = (sa.Index("ix_endpoints_session_owner", "session_owner"),)

    id = IDColumn("id")
    name = sa.Column("name", sa.String(length=64), nullable=False)
    session_owner = sa.Column("session_owner", GUID, sa.ForeignKey("keypairs.access_key"), nullable=False)
    domain = sa.Column("domain", sa.String(length=64), sa.ForeignKey("domains.name"), nullable=False)
    project = sa.Column("project", GUID, sa.ForeignKey("groups.id"), nullable=False)
    desired_session_count = sa.Column("desired_session_count", sa.Integer, nullable=False, default=1)
    image = sa.Column("image", sa.String(length=512), nullable=False)
    resource_slots = sa.Column("resource_slots", ResourceSlotColumn(), nullable=False)
    cluster_mode = sa.Column("cluster_mode", sa.String(length=16), nullable=False, default="single-node")
    cluster_size = sa.Column("cluster_size", sa.Integer, nullable=False, default=1)
    tag = sa.Column("tag", sa.String(length=64), nullable=True)
    startup_command = sa.Column("startup_command", sa.Text, nullable=True)
    bootstrap_script = sa.Column("bootstrap_script", sa.Text, nullable=True)
    shutdown_command = sa.Column("shutdown_command", sa.Text, nullable=True)

    # URL and routing configuration
    service_ports = sa.Column("service_ports", sa_psql.JSONB(), nullable=False)
    url = sa.Column("url", sa.Text, nullable=True)
    open_to_public = sa.Column("open_to_public", sa.Boolean, nullable=False, default=False)

    # Model configuration
    model_definition_path = sa.Column("model_definition_path", sa.Text, nullable=True)
    model = sa.Column("model", GUID, sa.ForeignKey("vfolders.id"), nullable=True)
    environ = sa.Column("environ", sa_psql.JSONB(), nullable=False, default=dict)
    # Additional model configurations can be stored in environ

    # Lifecycle
    lifecycle_stage = sa.Column("lifecycle_stage", StrEnumType(EndpointLifecycle), nullable=False)
    created_user = sa.Column("created_user", GUID, sa.ForeignKey("users.uuid"), nullable=False)
    created_at = sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, default=sa.func.now())
    destroyed_at = sa.Column("destroyed_at", sa.DateTime(timezone=True), nullable=True)
    modified_at = sa.Column("modified_at", sa.DateTime(timezone=True), nullable=False, default=sa.func.now(), onupdate=sa.func.now())

    # Endpoint retries and health checks
    retries = sa.Column("retries", sa.Integer, nullable=False, default=0)

    # Relationships
    keypair_row = relationship("KeyPairRow", back_populates="endpoints")
    domain_row = relationship("DomainRow", back_populates="endpoints")
    group_row = relationship("GroupRow", back_populates="endpoints")
    user_row = relationship("UserRow", back_populates="endpoints")
    model_row = relationship("VFolderRow", back_populates="endpoints")
    sessions = relationship("SessionRow", back_populates="endpoint", cascade="all, delete-orphan")
    tokens = relationship("EndpointTokenRow", back_populates="endpoint", cascade="all, delete-orphan")
    auto_scaling_configs = relationship("EndpointAutoScalingConfigRow", back_populates="endpoint", cascade="all, delete-orphan")

    @classmethod
    async def get(
        cls,
        session: sa.ext.asyncio.AsyncSession,
        endpoint_id: uuid.UUID,
        *,
        domain_name: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        access_key: Optional[str] = None,
    ) -> Optional["EndpointRow"]:
        conditions = [cls.id == endpoint_id]
        if domain_name is not None:
            conditions.append(cls.domain == domain_name)
        if project_id is not None:
            conditions.append(cls.project == project_id)
        if access_key is not None:
            conditions.append(cls.session_owner == access_key)

        query = sa.select(cls).where(sa.and_(*conditions))
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def list(
        cls,
        session: sa.ext.asyncio.AsyncSession,
        *,
        domain_name: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        access_key: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True,
        filter_: Optional[str] = None,
    ) -> PaginatedList:
        conditions = []
        if domain_name is not None:
            conditions.append(cls.domain == domain_name)
        if project_id is not None:
            conditions.append(cls.project == project_id)
        if access_key is not None:
            conditions.append(cls.session_owner == access_key)

        query = sa.select(cls)
        if conditions:
            query = query.where(sa.and_(*conditions))

        # Parse field specification and ordering
        if filter_ is not None:
            from .minilang.queryfilter import QueryFilterParser

            query_filter_parser = QueryFilterParser({
                "id": ("id", None),
                "name": ("name", None),
                "domain": ("domain", None),
                "project": ("project", None),
                "image": ("image", None),
                "created_at": ("created_at", None),
                "modified_at": ("modified_at", None),
                "lifecycle_stage": ("lifecycle_stage", None),
            })
            query = query_filter_parser.append_filter(query, filter_)

        from .minilang.ordering import QueryOrderParser

        order_parser = QueryOrderParser({
            "name": ("name", None),
            "created_at": ("created_at", None),
            "modified_at": ("modified_at", None),
        })
        query = order_parser.append_ordering(query, order_by)

        if order_desc:
            # Reverse the order if desc is requested
            # This is a simplified approach - in practice you'd want to handle this in the parser
            pass

        # Count total items
        count_query = sa.select(sa.func.count()).select_from(query.subquery())
        total_count = await session.scalar(count_query)

        # Apply pagination
        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        items = result.scalars().all()

        return PaginatedList(
            items=list(items),
            total_count=total_count or 0,
        )

    @classmethod
    async def create(
        cls,
        session: sa.ext.asyncio.AsyncSession,
        name: str,
        *,
        session_owner: str,
        domain: str,
        project: uuid.UUID,
        desired_session_count: int = 1,
        image: str,
        resource_slots: ResourceSlot,
        cluster_mode: str = "single-node",
        cluster_size: int = 1,
        tag: Optional[str] = None,
        startup_command: Optional[str] = None,
        bootstrap_script: Optional[str] = None,
        shutdown_command: Optional[str] = None,
        service_ports: Dict[str, Any],
        url: Optional[str] = None,
        open_to_public: bool = False,
        model_definition_path: Optional[str] = None,
        model: Optional[uuid.UUID] = None,
        environ: Optional[Dict[str, Any]] = None,
        lifecycle_stage: EndpointLifecycle = EndpointLifecycle.CREATING,
        created_user: uuid.UUID,
        retries: int = 0,
    ) -> "EndpointRow":
        endpoint = cls(
            name=name,
            session_owner=session_owner,
            domain=domain,
            project=project,
            desired_session_count=desired_session_count,
            image=image,
            resource_slots=resource_slots,
            cluster_mode=cluster_mode,
            cluster_size=cluster_size,
            tag=tag,
            startup_command=startup_command,
            bootstrap_script=bootstrap_script,
            shutdown_command=shutdown_command,
            service_ports=service_ports,
            url=url,
            open_to_public=open_to_public,
            model_definition_path=model_definition_path,
            model=model,
            environ=environ or {},
            lifecycle_stage=lifecycle_stage,
            created_user=created_user,
            retries=retries,
        )
        session.add(endpoint)
        await session.flush()
        return endpoint

    async def update(
        self,
        session: sa.ext.asyncio.AsyncSession,
        **kwargs: Any,
    ) -> Self:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        await session.flush()
        return self

    async def delete(self, session: sa.ext.asyncio.AsyncSession) -> None:
        await session.delete(self)
        await session.flush()

    @property
    def image_ref(self) -> ImageRef:
        return ImageRef.from_image_str(
            self.image,
            project=None,
            registry="",
            architecture="x86_64",
            is_local=False,
        )

    async def resolve_image_ref(
        self, db_session: sa.ext.asyncio.AsyncSession
    ) -> Optional[ImageRow]:
        """
        Resolve the image reference to an ImageRow.
        Returns None if the image is not found.
        """
        query = sa.select(ImageRow).where(
            ImageRow.name == self.image_ref.name,
        )
        result = await db_session.execute(query)
        return result.scalar_one_or_none()


class EndpointTokenRow(Base):
    __tablename__ = "endpoint_tokens"

    id = IDColumn("id")
    endpoint = sa.Column("endpoint", GUID, sa.ForeignKey("endpoints.id"), nullable=False)
    domain = sa.Column("domain", sa.String(length=64), sa.ForeignKey("domains.name"), nullable=False)
    session_owner = sa.Column("session_owner", GUID, sa.ForeignKey("keypairs.access_key"), nullable=False)
    token = sa.Column("token", sa.String(length=1024), nullable=False, unique=True)
    token_type = sa.Column("token_type", StrEnumType(EndpointTokenType), nullable=False)
    valid_until = sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True)
    created_at = sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, default=sa.func.now())

    # Relationships
    endpoint_row = relationship("EndpointRow", back_populates="tokens")
    domain_row = relationship("DomainRow")
    keypair_row = relationship("KeyPairRow")


class EndpointAutoScalingConfigRow(Base):
    __tablename__ = "endpoint_auto_scaling_configs"
    __table_args__ = (sa.UniqueConstraint("endpoint", name="uq_endpoint_auto_scaling_config"),)

    id = IDColumn("id")
    endpoint = sa.Column("endpoint", GUID, sa.ForeignKey("endpoints.id"), nullable=False)

    # Scaling configuration
    min_replicas = sa.Column("min_replicas", sa.Integer, nullable=False, default=1)
    max_replicas = sa.Column("max_replicas", sa.Integer, nullable=False, default=10)

    # Metric configuration
    metric_type = sa.Column(
        "metric_type",
        StrEnumType(EndpointAutoScalingMetricType),
        nullable=False,
    )
    threshold_value = sa.Column("threshold_value", sa.DECIMAL(10, 2), nullable=False)
    comparator = sa.Column(
        "comparator",
        StrEnumType(AutoScalingMetricComparator),
        nullable=False,
        default=AutoScalingMetricComparator.GREATER_THAN,
    )

    # Timing configuration
    evaluation_period = sa.Column(
        "evaluation_period", sa.Integer, nullable=False, default=60
    )  # seconds
    cooldown_period = sa.Column(
        "cooldown_period", sa.Integer, nullable=False, default=300
    )  # seconds

    # Metadata
    created_at = sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, default=sa.func.now())
    modified_at = sa.Column("modified_at", sa.DateTime(timezone=True), nullable=False, default=sa.func.now(), onupdate=sa.func.now())

    # Relationships
    endpoint_row = relationship("EndpointRow", back_populates="auto_scaling_configs")

    @classmethod
    async def get_by_endpoint(
        cls,
        session: sa.ext.asyncio.AsyncSession,
        endpoint_id: uuid.UUID,
    ) -> Optional["EndpointAutoScalingConfigRow"]:
        query = sa.select(cls).where(cls.endpoint == endpoint_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def create_or_update(
        cls,
        session: sa.ext.asyncio.AsyncSession,
        endpoint_id: uuid.UUID,
        min_replicas: int = 1,
        max_replicas: int = 10,
        metric_type: EndpointAutoScalingMetricType = EndpointAutoScalingMetricType.HTTP_REQUEST_RATE,
        threshold_value: Decimal = Decimal("10.0"),
        comparator: AutoScalingMetricComparator = AutoScalingMetricComparator.GREATER_THAN,
        evaluation_period: int = 60,
        cooldown_period: int = 300,
    ) -> "EndpointAutoScalingConfigRow":
        existing = await cls.get_by_endpoint(session, endpoint_id)
        if existing:
            existing.min_replicas = min_replicas
            existing.max_replicas = max_replicas
            existing.metric_type = metric_type
            existing.threshold_value = threshold_value
            existing.comparator = comparator
            existing.evaluation_period = evaluation_period
            existing.cooldown_period = cooldown_period
            await session.flush()
            return existing
        else:
            config = cls(
                endpoint=endpoint_id,
                min_replicas=min_replicas,
                max_replicas=max_replicas,
                metric_type=metric_type,
                threshold_value=threshold_value,
                comparator=comparator,
                evaluation_period=evaluation_period,
                cooldown_period=cooldown_period,
            )
            session.add(config)
            await session.flush()
            return config
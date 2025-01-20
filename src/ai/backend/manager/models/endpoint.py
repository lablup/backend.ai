from __future__ import annotations

import datetime
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
    Optional,
    Self,
    cast,
)
from uuid import UUID, uuid4

import graphene
import jwt
import sqlalchemy as sa
import trafaret as t
import yaml
import yarl
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.config import model_definition_iv
from ai.backend.common.types import (
    MODEL_SERVICE_RUNTIME_PROFILES,
    AccessKey,
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    EndpointId,
    ImageAlias,
    MountPermission,
    MountTypes,
    RedisConnectionInfo,
    ResourceSlot,
    RuntimeVariant,
    SessionTypes,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.defs import DEFAULT_CHUNK_SIZE, SERVICE_MAX_RETRIES
from ai.backend.manager.models.gql_relay import AsyncNode
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.types import MountOptionModel, UserScope

from ..api.exceptions import (
    EndpointNotFound,
    EndpointTokenNotFound,
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
    ForeignKeyIDColumn,
    IDColumn,
    InferenceSessionError,
    Item,
    PaginatedList,
    ResourceSlotColumn,
    StrEnumType,
    StructuredJSONObjectListColumn,
    URLColumn,
    gql_mutation_wrapper,
)
from .gql_models.base import ImageRefType
from .gql_models.image import ImageNode
from .gql_models.vfolder import VirtualFolderNode
from .image import ImageIdentifier, ImageRow
from .minilang import EnumFieldItem
from .minilang.ordering import OrderSpecItem, QueryOrderParser
from .minilang.queryfilter import FieldSpecItem, QueryFilterParser
from .resource_policy import keypair_resource_policies
from .routing import RouteStatus, Routing
from .scaling_group import scaling_groups
from .user import UserRole, UserRow
from .vfolder import VFolderRow, prepare_vfolder_mounts

if TYPE_CHECKING:
    from ai.backend.manager.config import SharedConfig

    from .gql import GraphQueryContext

__all__ = (
    "EndpointRow",
    "Endpoint",
    "EndpointLifecycle",
    "EndpointList",
    "ModelServicePredicateChecker",
    "ModifyEndpoint",
    "EndpointStatistics",
    "EndpointTokenRow",
    "EndpointToken",
    "EndpointTokenList",
    "EndpointAutoScalingRuleRow",
)


log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class EndpointLifecycle(Enum):
    CREATED = "created"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"


class EndpointRow(Base):
    __tablename__ = "endpoints"

    id = EndpointIDColumn()
    name = sa.Column("name", sa.String(length=512), nullable=False)
    created_user = sa.Column(
        "created_user", GUID, sa.ForeignKey("users.uuid", ondelete="RESTRICT"), nullable=False
    )
    session_owner = sa.Column(
        "session_owner", GUID, sa.ForeignKey("users.uuid", ondelete="RESTRICT"), nullable=False
    )
    # minus session count means this endpoint is requested for removal
    replicas = sa.Column("replicas", sa.Integer, nullable=False, default=0, server_default="0")
    image = sa.Column(
        "image", GUID, sa.ForeignKey("images.id", ondelete="RESTRICT"), nullable=False
    )
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
    tokens = relationship("EndpointTokenRow", back_populates="endpoint_row")
    endpoint_auto_scaling_rules = relationship(
        "EndpointAutoScalingRuleRow", back_populates="endpoint_row"
    )
    image_row = relationship("ImageRow", back_populates="endpoints")
    model_row = relationship("VFolderRow", back_populates="endpoints")
    created_user_row = relationship(
        "UserRow", back_populates="created_endpoints", foreign_keys="EndpointRow.created_user"
    )
    session_owner_row = relationship(
        "UserRow", back_populates="owned_endpoints", foreign_keys="EndpointRow.session_owner"
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
        self.cluster_mode = cluster_mode.name
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


class EndpointTokenRow(Base):
    __tablename__ = "endpoint_tokens"

    id = IDColumn()
    token = sa.Column("token", sa.String(), nullable=False)
    endpoint = sa.Column(
        "endpoint", GUID, sa.ForeignKey("endpoints.id", ondelete="SET NULL"), nullable=True
    )
    session_owner = ForeignKeyIDColumn("session_owner", "users.uuid")
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

    endpoint_row = relationship("EndpointRow", back_populates="tokens")

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

    endpoint_row = relationship("EndpointRow", back_populates="endpoint_auto_scaling_rules")

    @classmethod
    async def list(cls, session: AsyncSession, load_endpoint=False) -> Sequence[Self]:
        query = sa.select(EndpointAutoScalingRuleRow)
        if load_endpoint:
            query = query.options(selectinload(EndpointAutoScalingRuleRow.endpoint_row))
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
        shared_config: "SharedConfig",
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
        allowed_vfolder_types = await shared_config.get_vfolder_types()
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

        proxy_name, volume_name = storage_manager.split_host(folder_host)

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
        model_definition_dict = yaml.load(model_definition_yaml, Loader=yaml.FullLoader)
        try:
            model_definition = model_definition_iv.check(model_definition_dict)
            assert model_definition is not None
        except t.DataError as e:
            raise InvalidAPIParameters(
                f"Failed to validate model definition from vFolder {folder_name} (ID"
                f" {vfid.folder_id}): {e}",
            ) from e
        except yaml.error.YAMLError as e:
            raise InvalidAPIParameters(f"Invalid YAML syntax: {e}") from e

        return yaml_name


class RuntimeVariantInfo(graphene.ObjectType):
    """Added in 24.03.5."""

    name = graphene.String()
    human_readable_name = graphene.String()

    @classmethod
    def from_enum(cls, enum: RuntimeVariant) -> Self:
        return cls(name=enum.value, human_readable_name=MODEL_SERVICE_RUNTIME_PROFILES[enum].name)


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


class Endpoint(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    endpoint_id = graphene.UUID()
    image = graphene.String(deprecation_reason="Deprecated since 23.09.9. use `image_object`")
    image_object = graphene.Field(ImageNode, description="Added in 23.09.9.")
    domain = graphene.String()
    project = graphene.String()
    resource_group = graphene.String()
    resource_slots = graphene.JSONString()
    url = graphene.String()
    model = graphene.UUID()
    model_definition_path = graphene.String(description="Added in 24.03.4.")
    model_vfolder = VirtualFolderNode()
    model_mount_destiation = graphene.String(
        deprecation_reason="Deprecated since 24.03.4; use `model_mount_destination` instead"
    )
    model_mount_destination = graphene.String(description="Added in 24.03.4.")
    extra_mounts = graphene.List(lambda: VirtualFolderNode, description="Added in 24.03.4.")
    created_user = graphene.UUID(
        deprecation_reason="Deprecated since 23.09.8. use `created_user_id`"
    )
    created_user_email = graphene.String(description="Added in 23.09.8.")
    created_user_id = graphene.UUID(description="Added in 23.09.8.")
    session_owner = graphene.UUID(
        deprecation_reason="Deprecated since 23.09.8. use `session_owner_id`"
    )
    session_owner_email = graphene.String(description="Added in 23.09.8.")
    session_owner_id = graphene.UUID(description="Added in 23.09.8.")
    tag = graphene.String()
    startup_command = graphene.String()
    bootstrap_script = graphene.String()
    callback_url = graphene.String()
    environ = graphene.JSONString()
    name = graphene.String()
    resource_opts = graphene.JSONString()
    replicas = graphene.Int(description="Added in 24.12.0. Replaces `desired_session_count`.")
    desired_session_count = graphene.Int(
        deprecation_reason="Deprecated since 24.12.0. Use `replicas` instead."
    )
    cluster_mode = graphene.String()
    cluster_size = graphene.Int()
    open_to_public = graphene.Boolean()
    runtime_variant = graphene.Field(RuntimeVariantInfo, description="Added in 24.03.5.")

    created_at = GQLDateTime(required=True)
    destroyed_at = GQLDateTime()

    routings = graphene.List(Routing)
    retries = graphene.Int()
    status = graphene.String()

    lifecycle_stage = graphene.String()

    errors = graphene.List(graphene.NonNull(InferenceSessionError), required=True)

    live_stat = graphene.JSONString(description="Added in 24.12.0.")

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "name": ("endpoints_name", None),
        "model": ("endpoints_model", None),
        "domain": ("endpoints_domain", None),
        "url": ("endpoints_url", None),
        "lifecycle_stage": (EnumFieldItem("endpoints_lifecycle_stage", EndpointLifecycle), None),
        "open_to_public": ("endpoints_open_to_public", None),
        "created_user_email": ("users_email", None),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "name": ("endpoints_name", None),
        "created_at": ("endpoints_created_at", None),
        "model": ("endpoints_model", None),
        "domain": ("endpoints_domain", None),
        "url": ("endpoints_url", None),
        "lifecycle_stage": (EnumFieldItem("endpoints_lifecycle_stage", EndpointLifecycle), None),
        "open_to_public": ("endpoints_open_to_public", None),
        "created_user_email": ("users_email", None),
    }

    @classmethod
    async def from_row(
        cls,
        ctx,  # ctx: GraphQueryContext,
        row: EndpointRow,
    ) -> Self:
        return cls(
            endpoint_id=row.id,
            # image="", # deprecated, row.image_object.name,
            image_object=ImageNode.from_row(row.image_row),
            domain=row.domain,
            project=row.project,
            resource_group=row.resource_group,
            resource_slots=row.resource_slots.to_json(),
            url=row.url,
            model=row.model,
            model_definition_path=row.model_definition_path,
            model_mount_destiation=row.model_mount_destination,
            model_mount_destination=row.model_mount_destination,
            created_user=row.created_user,
            created_user_id=row.created_user,
            created_user_email=row.created_user_row.email,
            session_owner=row.session_owner,
            session_owner_id=row.session_owner,
            session_owner_email=row.session_owner_row.email,
            tag=row.tag,
            startup_command=row.startup_command,
            bootstrap_script=row.bootstrap_script,
            callback_url=row.callback_url,
            environ=row.environ,
            name=row.name,
            resource_opts=row.resource_opts,
            replicas=row.replicas,
            desired_session_count=row.replicas,
            cluster_mode=row.cluster_mode,
            cluster_size=row.cluster_size,
            open_to_public=row.open_to_public,
            created_at=row.created_at,
            destroyed_at=row.destroyed_at,
            retries=row.retries,
            routings=[await Routing.from_row(None, r, endpoint=row) for r in row.routings],
            lifecycle_stage=row.lifecycle_stage.name,
            runtime_variant=RuntimeVariantInfo.from_enum(row.runtime_variant),
        )

    @classmethod
    async def load_count(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        project: UUID | None = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
        filter: Optional[str] = None,
    ) -> int:
        query = sa.select([sa.func.count()]).select_from(
            sa.join(
                EndpointRow,
                UserRow,
                EndpointRow.created_user == UserRow.uuid,
                isouter=True,
            )
        )
        if project is not None:
            query = query.where(EndpointRow.project == project)
        if domain_name is not None:
            query = query.where(EndpointRow.domain == domain_name)
        if user_uuid is not None:
            query = query.where(EndpointRow.session_owner == user_uuid)
        if filter is not None:
            filter_parser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = filter_parser.append_filter(query, filter)

        async with ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        ctx,  #: GraphQueryContext,  # ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
        project: Optional[UUID] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence[Self]:
        query = (
            sa.select(EndpointRow)
            .select_from(
                sa.join(
                    EndpointRow,
                    UserRow,
                    EndpointRow.created_user == UserRow.uuid,
                    isouter=True,
                )
            )
            .limit(limit)
            .offset(offset)
            .options(selectinload(EndpointRow.image_row).selectinload(ImageRow.aliases))
            .options(selectinload(EndpointRow.routings))
            .options(selectinload(EndpointRow.session_owner_row))
        )
        if project is not None:
            query = query.where(EndpointRow.project == project)
        if domain_name is not None:
            query = query.where(EndpointRow.domain == domain_name)
        if user_uuid is not None:
            query = query.where(EndpointRow.session_owner == user_uuid)

        if filter is not None:
            filter_parser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = filter_parser.append_filter(query, filter)
        if order is not None:
            order_parser = QueryOrderParser(cls._queryorder_colmap)
            query = order_parser.append_ordering(query, order)
        else:
            query = query.order_by(sa.desc(EndpointRow.created_at))

        async with ctx.db.begin_readonly_session() as db_session:
            result = await db_session.execute(query)
            return [await cls.from_row(ctx, row) for row in result.scalars().all()]

    @classmethod
    async def load_all(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
        project: Optional[UUID] = None,
    ) -> Sequence["Endpoint"]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await EndpointRow.list(
                session,
                project=project,
                domain=domain_name,
                user_uuid=user_uuid,
                load_image=True,
                load_created_user=True,
                load_session_owner=True,
            )
            return [await Endpoint.from_row(ctx, row) for row in rows]

    @classmethod
    async def load_item(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        endpoint_id: UUID,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
        project: UUID | None = None,
    ) -> Self:
        """
        :raises: ai.backend.manager.api.exceptions.EndpointNotFound
        """
        try:
            async with ctx.db.begin_readonly_session() as session:
                row = await EndpointRow.get(
                    session,
                    endpoint_id=endpoint_id,
                    domain=domain_name,
                    user_uuid=user_uuid,
                    project=project,
                    load_image=True,
                    load_routes=True,
                    load_created_user=True,
                    load_session_owner=True,
                )
                return await Endpoint.from_row(ctx, row)
        except NoResultFound:
            raise EndpointNotFound

    async def resolve_status(self, info: graphene.ResolveInfo) -> str:
        match self.lifecycle_stage:
            case EndpointLifecycle.DESTROYED.name:
                return "DESTROYED"
            case EndpointLifecycle.DESTROYING.name:
                return "DESTROYING"
            case _:
                if len(self.routings) == 0:
                    return "READY"
                elif self.retries > SERVICE_MAX_RETRIES:
                    return "UNHEALTHY"
                elif (spawned_service_count := len([r for r in self.routings])) > 0:
                    healthy_service_count = len([
                        r for r in self.routings if r.status == RouteStatus.HEALTHY.name
                    ])
                    if healthy_service_count == spawned_service_count:
                        return "HEALTHY"
                    unhealthy_service_count = len([
                        r for r in self.routings if r.status == RouteStatus.UNHEALTHY.name
                    ])
                    if unhealthy_service_count > 0:
                        return "DEGRADED"
                return "PROVISIONING"

    async def resolve_model_vfolder(self, info: graphene.ResolveInfo) -> VirtualFolderNode:
        if not self.model:
            raise ObjectNotFound(object_name="VFolder")

        ctx: GraphQueryContext = info.context

        async with ctx.db.begin_readonly_session() as sess:
            vfolder_row = await VFolderRow.get(sess, self.model, load_user=True, load_group=True)
            return VirtualFolderNode.from_row(info, vfolder_row)

    async def resolve_extra_mounts(self, info: graphene.ResolveInfo) -> Sequence[VirtualFolderNode]:
        if not self.endpoint_id:
            raise ObjectNotFound(object_name="Endpoint")

        ctx: GraphQueryContext = info.context

        async with ctx.db.begin_readonly_session() as sess:
            endpoint_row = await EndpointRow.get(sess, self.endpoint_id)
            extra_mount_folder_ids = [m.vfid.folder_id for m in endpoint_row.extra_mounts]
            query = (
                sa.select(VFolderRow)
                .where(VFolderRow.id.in_(extra_mount_folder_ids))
                .options(selectinload(VFolderRow.user_row))
                .options(selectinload(VFolderRow.group_row))
            )
            return [VirtualFolderNode.from_row(info, r) for r in (await sess.scalars(query))]

    async def resolve_errors(self, info: graphene.ResolveInfo) -> Any:
        error_routes = [r for r in self.routings if r.status == RouteStatus.FAILED_TO_START.name]
        errors = []
        for route in error_routes:
            if not route.error_data:
                continue
            match route.error_data["type"]:
                case "session_cancelled":
                    session_id = route.error_data["session_id"]
                case _:
                    session_id = None
            errors.append(
                InferenceSessionError(
                    session_id=session_id,
                    errors=[
                        InferenceSessionError.InferenceSessionErrorInfo(
                            src=e["src"], name=e["name"], repr=e["repr"]
                        )
                        for e in route.error_data["errors"]
                    ],
                )
            )

        return errors

    async def resolve_live_stat(self, info: graphene.ResolveInfo) -> Optional[Mapping[str, Any]]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx, "EndpointStatistics.by_endpoint"
        )
        return await loader.load(self.endpoint_id)


class EndpointList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(Endpoint, required=True)


class ExtraMountInput(graphene.InputObjectType):
    """Added in 24.03.4."""

    vfolder_id = graphene.String()
    mount_destination = graphene.String()
    type = graphene.String(
        description=f"Added in 24.03.4. Set bind type of this mount. Shoud be one of ({','.join([type_.value for type_ in MountTypes])}). Default is 'bind'."
    )
    permission = graphene.String(
        description=f"Added in 24.03.4. Set permission of this mount. Should be one of ({','.join([perm.value for perm in MountPermission])}). Default is null"
    )


class ModifyEndpointInput(graphene.InputObjectType):
    resource_slots = graphene.JSONString()
    resource_opts = graphene.JSONString()
    cluster_mode = graphene.String()
    cluster_size = graphene.Int()
    replicas = graphene.Int(description="Added in 24.12.0. Replaces `desired_session_count`.")
    desired_session_count = graphene.Int(
        deprecation_reason="Deprecated since 24.12.0. Use `replicas` instead."
    )
    image = ImageRefType()
    name = graphene.String()
    resource_group = graphene.String()
    model_definition_path = graphene.String(
        description="Added in 24.03.4. Must be set to `/models` when choosing `runtime_variant` other than `CUSTOM` or `CMD`."
    )
    open_to_public = graphene.Boolean()
    extra_mounts = graphene.List(
        ExtraMountInput,
        description="Added in 24.03.4. MODEL type VFolders are not allowed to be attached to model service session with this option.",
    )
    environ = graphene.JSONString(description="Added in 24.03.5.")
    runtime_variant = graphene.String(description="Added in 24.03.5.")


class ModifyEndpoint(graphene.Mutation):
    allowed_roles = (UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        endpoint_id = graphene.UUID(required=True)
        props = ModifyEndpointInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    endpoint = graphene.Field(lambda: Endpoint, required=False, description="Added in 23.09.8.")

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        endpoint_id: UUID,
        props: ModifyEndpointInput,
    ) -> Self:
        graph_ctx: GraphQueryContext = info.context

        async def _do_mutate() -> Self:
            async with graph_ctx.db.begin_session() as db_session:
                try:
                    endpoint_row = await EndpointRow.get(
                        db_session,
                        endpoint_id,
                        load_session_owner=True,
                        load_model=True,
                        load_routes=True,
                    )
                    match graph_ctx.user["role"]:
                        case UserRole.SUPERADMIN:
                            pass
                        case UserRole.ADMIN:
                            domain_name = graph_ctx.user["domain_name"]
                            if endpoint_row.domain != domain_name:
                                raise EndpointNotFound
                        case _:
                            user_id = graph_ctx.user["uuid"]
                            if endpoint_row.session_owner != user_id:
                                raise EndpointNotFound
                except NoResultFound:
                    raise EndpointNotFound
                if endpoint_row.lifecycle_stage in (
                    EndpointLifecycle.DESTROYING,
                    EndpointLifecycle.DESTROYED,
                ):
                    raise InvalidAPIParameters("Cannot update endpoint marked for removal")

                if (_newval := props.resource_slots) and _newval is not Undefined:
                    endpoint_row.resource_slots = ResourceSlot.from_user_input(_newval, None)

                if (_newval := props.resource_opts) and _newval is not Undefined:
                    endpoint_row.resource_opts = _newval

                if (_newval := props.cluster_mode) and _newval is not Undefined:
                    endpoint_row.cluster_mode = _newval

                if (_newval := props.cluster_size) and _newval is not Undefined:
                    endpoint_row.cluster_size = _newval

                if (_newval := props.model_definition_path) and _newval is not Undefined:
                    endpoint_row.model_definition_path = _newval

                if (_newval := props.environ) is not None and _newval is not Undefined:
                    endpoint_row.environ = _newval

                if (_newval := props.runtime_variant) and _newval is not Undefined:
                    try:
                        endpoint_row.runtime_variant = RuntimeVariant(_newval)
                    except KeyError:
                        raise InvalidAPIParameters(f"Unsupported runtime {_newval}")

                if (
                    (_legacy_replicas := props.desired_session_count) is not None
                    and _legacy_replicas is not Undefined
                    and (_new_replicas := props.replicas) is not None
                    and _new_replicas is not Undefined
                ):
                    raise InvalidAPIParameters(
                        "Cannot set both desired_session_count and replicas. Use replicas for future use."
                    )

                if (
                    _newval := props.desired_session_count
                ) is not None and _newval is not Undefined:
                    endpoint_row.replicas = _newval

                if (_newval := props.replicas) is not None and _newval is not Undefined:
                    endpoint_row.replicas = _newval

                if (_newval := props.resource_group) and _newval is not Undefined:
                    endpoint_row.resource_group = _newval

                if (image := props.image) and image is not Undefined:
                    image_name = image["name"]
                    arch = image.get("architecture")
                    image_row = await ImageRow.resolve(
                        db_session, [ImageIdentifier(image_name, arch), ImageAlias(image_name)]
                    )
                    endpoint_row.image = image_row.id

                session_owner: UserRow = endpoint_row.session_owner_row

                conn = await db_session.connection()
                assert conn

                await ModelServicePredicateChecker.check_scaling_group(
                    conn,
                    endpoint_row.resource_group,
                    session_owner.main_access_key,
                    endpoint_row.domain,
                    endpoint_row.project,
                )

                def _get_vfolder_id(id_input: str) -> UUID:
                    _, raw_vfolder_id = AsyncNode.resolve_global_id(info, id_input)
                    if not raw_vfolder_id:
                        raw_vfolder_id = id_input
                    return UUID(raw_vfolder_id)

                user_scope = UserScope(
                    domain_name=endpoint_row.domain,
                    group_id=endpoint_row.project,
                    user_uuid=session_owner.uuid,
                    user_role=session_owner.role,
                )

                query = (
                    sa.select([keypair_resource_policies])
                    .select_from(keypair_resource_policies)
                    .where(keypair_resource_policies.c.name == session_owner.resource_policy)
                )
                result = await conn.execute(query)

                resource_policy = result.first()
                if (extra_mounts_input := props.extra_mounts) is not Undefined:
                    extra_mounts_input = cast(list[ExtraMountInput], extra_mounts_input)
                    extra_mounts = {
                        _get_vfolder_id(m.vfolder_id): MountOptionModel(
                            mount_destination=(
                                m.mount_destination
                                if m.mount_destination is not Undefined
                                else None
                            ),
                            type=MountTypes(m.type) if m.type is not Undefined else MountTypes.BIND,
                            permission=(
                                MountPermission(m.permission)
                                if m.permission is not Undefined
                                else None
                            ),
                        )
                        for m in extra_mounts_input
                    }
                    vfolder_mounts = await ModelServicePredicateChecker.check_extra_mounts(
                        conn,
                        graph_ctx.shared_config,
                        graph_ctx.storage_manager,
                        endpoint_row.model,
                        endpoint_row.model_mount_destination,
                        extra_mounts,
                        user_scope,
                        resource_policy,
                    )
                    endpoint_row.extra_mounts = vfolder_mounts

                if endpoint_row.runtime_variant == RuntimeVariant.CUSTOM:
                    await ModelServicePredicateChecker.validate_model_definition(
                        graph_ctx.storage_manager,
                        endpoint_row.model_row,
                        endpoint_row.model_definition_path,
                    )
                elif (
                    endpoint_row.runtime_variant != RuntimeVariant.CMD
                    and endpoint_row.model_mount_destination != "/models"
                ):
                    raise InvalidAPIParameters(
                        "Model mount destination must be /models for non-custom runtimes"
                    )
                # from AgentRegistry.handle_route_creation()

                async with graph_ctx.db.begin_session() as db_session:
                    image_row = await ImageRow.resolve(
                        db_session,
                        [
                            ImageIdentifier(
                                endpoint_row.image_row.name, endpoint_row.image_row.architecture
                            ),
                        ],
                    )

                await graph_ctx.registry.create_session(
                    "",
                    image_row.image_ref,
                    user_scope,
                    session_owner.main_access_key,
                    resource_policy,
                    SessionTypes.INFERENCE,
                    {
                        "mounts": [
                            endpoint_row.model,
                            *[m.vfid.folder_id for m in endpoint_row.extra_mounts],
                        ],
                        "mount_map": {
                            endpoint_row.model: endpoint_row.model_mount_destination,
                            **{
                                m.vfid.folder_id: m.kernel_path.as_posix()
                                for m in endpoint_row.extra_mounts
                            },
                        },
                        "mount_options": {
                            m.vfid.folder_id: {"permission": m.mount_perm}
                            for m in endpoint_row.extra_mounts
                        },
                        "environ": endpoint_row.environ,
                        "scaling_group": endpoint_row.resource_group,
                        "resources": endpoint_row.resource_slots,
                        "resource_opts": endpoint_row.resource_opts,
                        "preopen_ports": None,
                        "agent_list": None,
                    },
                    ClusterMode[endpoint_row.cluster_mode],
                    endpoint_row.cluster_size,
                    bootstrap_script=endpoint_row.bootstrap_script,
                    startup_command=endpoint_row.startup_command,
                    tag=endpoint_row.tag,
                    callback_url=endpoint_row.callback_url,
                    sudo_session_enabled=session_owner.sudo_session_enabled,
                    dry_run=True,
                )

                await db_session.commit()

                return cls(
                    True,
                    "success",
                    await Endpoint.from_row(graph_ctx, endpoint_row),
                )

        return await gql_mutation_wrapper(
            cls,
            _do_mutate,
        )


class EndpointToken(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    token = graphene.String(required=True)
    endpoint_id = graphene.UUID(required=True)
    domain = graphene.String(required=True)
    project = graphene.String(required=True)
    session_owner = graphene.UUID(required=True)

    created_at = GQLDateTime(required=True)
    valid_until = GQLDateTime()

    @classmethod
    async def from_row(
        cls,
        ctx,  # ctx: GraphQueryContext,
        row: EndpointTokenRow,
    ) -> Self:
        return cls(
            token=row.token,
            endpoint_id=row.endpoint,
            domain=row.domain,
            project=row.project,
            session_owner=row.session_owner,
            created_at=row.created_at,
        )

    @classmethod
    async def load_count(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        endpoint_id: Optional[UUID] = None,
        project: Optional[UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
    ) -> int:
        query = sa.select([sa.func.count()]).select_from(EndpointTokenRow)
        if endpoint_id is not None:
            query = query.where(EndpointTokenRow.endpoint == endpoint_id)
        if project:
            query = query.filter(EndpointTokenRow.project == project)
        if domain_name:
            query = query.filter(EndpointTokenRow.domain == domain_name)
        if user_uuid:
            query = query.filter(EndpointTokenRow.session_owner == user_uuid)
        async with ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        ctx,  # ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        endpoint_id: Optional[UUID] = None,
        filter: str | None = None,
        order: str | None = None,
        project: Optional[UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
    ) -> Sequence[Self]:
        query = (
            sa.select(EndpointTokenRow)
            .limit(limit)
            .offset(offset)
            .order_by(sa.desc(EndpointTokenRow.created_at))
        )
        if endpoint_id is not None:
            query = query.where(EndpointTokenRow.endpoint == endpoint_id)
        if project:
            query = query.filter(EndpointTokenRow.project == project)
        if domain_name:
            query = query.filter(EndpointTokenRow.domain == domain_name)
        if user_uuid:
            query = query.filter(EndpointTokenRow.session_owner == user_uuid)
        """
        if filter is not None:
            parser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = parser.append_filter(query, filter)
        if order is not None:
            parser = QueryOrderParser(cls._queryorder_colmap)
            query = parser.append_ordering(query, order)
        """
        async with ctx.db.begin_readonly_session() as session:
            result = await session.execute(query)
            return [await cls.from_row(ctx, row) for row in result.scalars().all()]

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
        endpoint_id: UUID,
        *,
        project: Optional[UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
    ) -> Sequence[Self]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await EndpointTokenRow.list(
                session,
                endpoint_id,
                project=project,
                domain=domain_name,
                user_uuid=user_uuid,
            )
        return [await cls.from_row(ctx, row) for row in rows]

    @classmethod
    async def load_item(
        cls,
        ctx,  # ctx: GraphQueryContext,
        token: str,
        *,
        project: Optional[UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
    ) -> Self:
        try:
            async with ctx.db.begin_readonly_session() as session:
                row = await EndpointTokenRow.get(
                    session, token, project=project, domain=domain_name, user_uuid=user_uuid
                )
        except NoResultFound:
            raise EndpointTokenNotFound
        return await cls.from_row(ctx, row)

    async def resolve_valid_until(
        self,
        info: graphene.ResolveInfo,
    ) -> datetime.datetime | None:
        try:
            decoded = jwt.decode(
                self.token,
                algorithms=["HS256"],
                options={"verify_signature": False, "verify_exp": False},
            )
        except jwt.DecodeError:
            return None
        if "exp" not in decoded:
            return None
        return datetime.datetime.fromtimestamp(decoded["exp"])


class EndpointTokenList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(EndpointToken, required=True)

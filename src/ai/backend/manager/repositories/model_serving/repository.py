import asyncio
import uuid
from typing import Any, cast

import sqlalchemy as sa
from pydantic import HttpUrl
from sqlalchemy.exc import IntegrityError, NoResultFound, StatementError
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.contexts.user import current_user
from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import BackendAIError, VFolderNotFound
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    MountPermission,
    MountTypes,
    RuntimeVariant,
    SessionTypes,
)
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.data.model_serving.types import (
    EndpointAccessValidationData,
    EndpointAutoScalingRuleData,
    EndpointAutoScalingRuleListResult,
    EndpointData,
    EndpointTokenData,
    MutationResult,
    RoutingData,
    ScalingGroupData,
    ServiceSearchItem,
    ServiceSearchResult,
    UserData,
)
from ai.backend.manager.data.vfolder.types import VFolderOwnershipType
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.errors.resource import DatabaseConnectionUnavailable
from ai.backend.manager.errors.service import EndpointNotFound
from ai.backend.manager.models.endpoint import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointAutoScalingRuleRow,
    EndpointLifecycle,
    EndpointRow,
    EndpointTokenRow,
    ModelServiceHelper,
)
from ai.backend.manager.models.group import resolve_group_name_or_id
from ai.backend.manager.models.image import ImageAlias, ImageIdentifier, ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import keypair_resource_policies
from ai.backend.manager.models.routing import RouteStatus, RoutingRow
from ai.backend.manager.models.scaling_group import scaling_groups
from ai.backend.manager.models.session import KernelLoadingStrategy, SessionRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_retry
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    Updater,
    execute_batch_querier,
    execute_creator,
    execute_updater,
)
from ai.backend.manager.repositories.model_serving.updaters import EndpointUpdaterSpec
from ai.backend.manager.services.model_serving.actions.modify_endpoint import ModifyEndpointAction
from ai.backend.manager.services.model_serving.exceptions import (
    GenericForbidden,
    InvalidAPIParameters,
)
from ai.backend.manager.types import MountOptionModel, UserScope

model_serving_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.MODEL_SERVING_REPOSITORY)
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class ModelServingRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @model_serving_repository_resilience.apply()
    async def get_endpoint_by_id(self, endpoint_id: uuid.UUID) -> EndpointData | None:
        """
        Get endpoint by ID.
        Returns None if endpoint doesn't exist.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            endpoint = await self._get_endpoint_by_id(
                session,
                endpoint_id,
                load_routes=True,
                load_session_owner=True,
                load_model=True,
                load_image=True,
            )
            if not endpoint:
                return None

            return endpoint.to_data()

    @model_serving_repository_resilience.apply()
    async def get_endpoint_access_validation_data(
        self, endpoint_id: uuid.UUID
    ) -> EndpointAccessValidationData | None:
        """
        Get minimal endpoint data required for access validation.
        Returns None if endpoint doesn't exist.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = (
                sa.select(EndpointRow)
                .where(EndpointRow.id == endpoint_id)
                .options(selectinload(EndpointRow.session_owner_row))
            )
            result = await session.execute(stmt)
            endpoint_row = result.scalar_one_or_none()
            if endpoint_row is None:
                return None

            return EndpointAccessValidationData(
                session_owner_id=endpoint_row.session_owner,
                session_owner_role=(
                    endpoint_row.session_owner_row.role if endpoint_row.session_owner_row else None
                ),
                domain=endpoint_row.domain,
            )

    @model_serving_repository_resilience.apply()
    async def get_endpoint_by_name_validated(
        self, name: str, user_id: uuid.UUID
    ) -> EndpointData | None:
        """
        Get endpoint by name with ownership validation.
        Returns None if endpoint doesn't exist or user doesn't own it.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            endpoint = await self._get_endpoint_by_name(session, name, user_id)
            if not endpoint:
                return None
            return endpoint.to_data()

    @model_serving_repository_resilience.apply()
    async def list_endpoints_by_owner_validated(
        self, session_owner_id: uuid.UUID, name: str | None = None
    ) -> list[EndpointData]:
        """
        List endpoints owned by a specific user with optional name filter.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            query_conds = (EndpointRow.session_owner == session_owner_id) & (
                EndpointRow.lifecycle_stage == EndpointLifecycle.CREATED
            )
            if name:
                query_conds &= EndpointRow.name == name

            query = (
                sa.select(EndpointRow)
                .where(query_conds)
                .options(selectinload(EndpointRow.routings))
            )
            result = await session.execute(query)
            rows = cast(list[EndpointRow], result.scalars().all())
            return [row.to_data() for row in rows]

    @model_serving_repository_resilience.apply()
    async def check_endpoint_name_uniqueness(self, name: str) -> bool:
        """
        Check if endpoint name is unique (not already taken by non-destroyed endpoints).
        Returns True if name is available, False if taken.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            query = sa.select(EndpointRow).where(
                (EndpointRow.lifecycle_stage != EndpointLifecycle.DESTROYED)
                & (EndpointRow.name == name)
            )
            result = await session.execute(query)
            existing_endpoint = result.scalar()

            return existing_endpoint is None

    @model_serving_repository_resilience.apply()
    async def create_endpoint_validated(
        self, creator: Creator[EndpointRow], registry: AgentRegistry
    ) -> EndpointData:
        """
        Create a new endpoint after validation.
        """
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            endpoint_row = await EndpointRow.get(
                db_sess,
                result.row.id,
                load_created_user=True,
                load_session_owner=True,
                load_image=True,
                load_routes=True,
            )
            endpoint_before_assign_url = endpoint_row.to_data()
            endpoint_row.url = await registry.create_appproxy_endpoint(
                db_sess, endpoint_before_assign_url
            )
            return endpoint_row.to_data()

    @model_serving_repository_resilience.apply()
    async def update_endpoint_lifecycle(
        self,
        endpoint_id: uuid.UUID,
        lifecycle_stage: EndpointLifecycle,
        replicas: int | None = None,
    ) -> bool:
        """
        Update endpoint lifecycle stage.
        Returns True if updated, False if not found.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, endpoint_id)
            if not endpoint:
                return False

            update_values: dict[str, Any] = {"lifecycle_stage": lifecycle_stage}
            if lifecycle_stage == EndpointLifecycle.DESTROYED:
                update_values["destroyed_at"] = sa.func.now()
            if replicas is not None:
                update_values["replicas"] = replicas

            query = (
                sa.update(EndpointRow).where(EndpointRow.id == endpoint_id).values(update_values)
            )
            await session.execute(query)

        return True

    @model_serving_repository_resilience.apply()
    async def clear_endpoint_errors(self, endpoint_id: uuid.UUID) -> bool:
        """
        Clear endpoint errors (failed routes and reset retry count).
        Returns True if cleared, False if not found.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, endpoint_id)
            if not endpoint:
                return False

            # Delete failed routes
            delete_query = sa.delete(RoutingRow).where(
                (RoutingRow.endpoint == endpoint_id)
                & (RoutingRow.status == RouteStatus.FAILED_TO_START)
            )
            await session.execute(delete_query)

            # Reset retry count
            update_query = (
                sa.update(EndpointRow).values({"retries": 0}).where(EndpointRow.id == endpoint_id)
            )
            await session.execute(update_query)

        return True

    @model_serving_repository_resilience.apply()
    async def get_route_by_id(
        self,
        route_id: uuid.UUID,
        service_id: uuid.UUID,
    ) -> RoutingData | None:
        """
        Get route by ID.
        Returns None if route doesn't exist or doesn't belong to service.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            route = await self._get_route_by_id(session, route_id, load_endpoint=True)
            if not route or route.endpoint != service_id:
                return None

            return route.to_data()

    @model_serving_repository_resilience.apply()
    async def update_route_traffic(
        self,
        valkey_live: ValkeyLiveClient,
        route_id: uuid.UUID,
        service_id: uuid.UUID,
        traffic_ratio: float,
    ) -> EndpointData | None:
        """
        Update route traffic ratio.
        Returns updated endpoint data if successful, None if not found.
        """
        async with self._db.begin_session() as session:
            route = await self._get_route_by_id(session, route_id, load_endpoint=True)
            if not route or route.endpoint != service_id:
                return None

            query = (
                sa.update(RoutingRow)
                .where(RoutingRow.id == route_id)
                .values({"traffic_ratio": traffic_ratio})
            )
            await session.execute(query)

            endpoint = await self._get_endpoint_by_id(
                session, service_id, load_routes=True, load_session_owner=True
            )
            if endpoint is None:
                raise NoResultFound

            await valkey_live.store_live_data(
                f"endpoint.{service_id}.session.{route.session}.traffic_ratio",
                str(traffic_ratio),
            )
            return endpoint.to_data()

    @model_serving_repository_resilience.apply()
    async def decrease_endpoint_replicas(self, service_id: uuid.UUID) -> bool:
        """
        Decrease endpoint replicas by 1.
        Returns True if decreased, False if not found.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, service_id, load_session_owner=True)
            if not endpoint:
                return False

            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == service_id)
                .values({"replicas": endpoint.replicas - 1})
            )
            await session.execute(query)

        return True

    @model_serving_repository_resilience.apply()
    async def create_endpoint_token(
        self,
        creator: Creator[EndpointTokenRow],
    ) -> EndpointTokenData | None:
        """
        Create endpoint token.
        Returns token data if created, None if endpoint not found.
        """
        async with self._db.begin_session() as session:
            endpoint_id = creator.spec.endpoint  # type: ignore[attr-defined]
            endpoint = await self._get_endpoint_by_id(session, endpoint_id)
            if not endpoint:
                return None

            result = await execute_creator(session, creator)
            return result.row.to_dataclass()

    @model_serving_repository_resilience.apply()
    async def get_scaling_group_info(self, scaling_group_name: str) -> ScalingGroupData | None:
        """
        Get scaling group information (wsproxy details).
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            query = (
                sa.select(scaling_groups.c.wsproxy_addr, scaling_groups.c.wsproxy_api_token)
                .select_from(scaling_groups)
                .where(scaling_groups.c.name == scaling_group_name)
            )
            result = await session.execute(query)
            row = result.first()
            if not row:
                return None

            return ScalingGroupData(
                wsproxy_addr=row.wsproxy_addr, wsproxy_api_token=row.wsproxy_api_token
            )

    @model_serving_repository_resilience.apply()
    async def get_user_by_id(self, user_id: uuid.UUID) -> UserData | None:
        """
        Get user information by ID.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            query = sa.select(UserRow).where(UserRow.uuid == user_id)
            result = await session.execute(query)
            user_row: UserRow | None = result.scalar()
            if not user_row:
                return None

            return user_row.to_model_serving_user_data()

    async def _get_endpoint_by_id(
        self,
        session: SASession,
        endpoint_id: uuid.UUID,
        load_routes: bool = False,
        load_image: bool = False,
        load_session_owner: bool = False,
        load_model: bool = False,
    ) -> EndpointRow | None:
        """
        Private method to get endpoint by ID using an existing session.
        """
        try:
            return await EndpointRow.get(
                session,
                endpoint_id,
                load_routes=load_routes,
                load_image=load_image,
                load_session_owner=load_session_owner,
                load_model=load_model,
            )
        except NoResultFound:
            return None

    async def _get_endpoint_by_name(
        self, session: SASession, name: str, user_id: uuid.UUID
    ) -> EndpointRow | None:
        """
        Private method to get endpoint by name and owner using an existing session.
        """
        query = sa.select(EndpointRow).where(
            (EndpointRow.name == name) & (EndpointRow.session_owner == user_id)
        )
        result = await session.execute(query)

        return result.scalar()

    async def _get_route_by_id(
        self,
        session: SASession,
        route_id: uuid.UUID,
        load_endpoint: bool = False,
        load_session: bool = False,
    ) -> RoutingRow | None:
        """
        Private method to get route by ID using an existing session.
        """
        try:
            return await RoutingRow.get(
                session, route_id, load_endpoint=load_endpoint, load_session=load_session
            )
        except NoResultFound:
            return None

    async def _validate_endpoint_access(
        self,
        session: SASession,
        endpoint: EndpointRow,
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
    ) -> bool:
        """
        Private method to validate user access to endpoint.
        """
        query = sa.select(UserRow).where(UserRow.uuid == endpoint.session_owner)
        result = await session.execute(query)
        owner = result.scalar()

        if owner is None:
            return False

        match user_role:
            case UserRole.SUPERADMIN:
                return True
            case UserRole.ADMIN:
                if owner.role == UserRole.SUPERADMIN:
                    return False
                return endpoint.domain == domain_name
            case _:
                return owner.uuid == user_id

    @model_serving_repository_resilience.apply()
    async def get_vfolder_ownership_type(self, vfolder_id: uuid.UUID) -> VFolderOwnershipType:
        """
        Get VFolder ownership type by VFolder ID.
        Raises VFolderNotFound if vfolder not found by the given ID.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(VFolderRow.ownership_type).where(VFolderRow.id == vfolder_id)
            result = await session.execute(stmt)
            vfolder_ownership_type = result.scalar_one_or_none()

            if vfolder_ownership_type is None:
                raise VFolderNotFound(f"VFolder with ID {vfolder_id} not found.")

            return vfolder_ownership_type

    @model_serving_repository_resilience.apply()
    async def get_user_with_keypair(self, user_id: uuid.UUID) -> Any | None:
        """
        Get user with their main access key.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            query = sa.select(sa.join(UserRow, KeyPairRow, KeyPairRow.user == UserRow.uuid)).where(
                UserRow.uuid == user_id
            )
            result = await session.execute(query)
            return result.fetchone()

    @model_serving_repository_resilience.apply()
    async def get_keypair_resource_policy(self, policy_name: str) -> Any | None:
        """
        Get keypair resource policy by name.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            query = (
                sa.select(keypair_resource_policies)
                .select_from(keypair_resource_policies)
                .where(keypair_resource_policies.c.name == policy_name)
            )
            result = await session.execute(query)
            return result.first()

    @model_serving_repository_resilience.apply()
    async def get_endpoint_for_appproxy_update(self, service_id: uuid.UUID) -> EndpointRow | None:
        """
        Get endpoint with routes loaded for AppProxy updates.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            return await self._get_endpoint_by_id(session, service_id, load_routes=True)

    @model_serving_repository_resilience.apply()
    async def get_route_with_session(self, route_id: uuid.UUID) -> RoutingRow | None:
        """
        Get route with endpoint and session data loaded.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            return await self._get_route_by_id(
                session, route_id, load_endpoint=True, load_session=True
            )

    @model_serving_repository_resilience.apply()
    async def update_endpoint_replicas(
        self,
        endpoint_id: uuid.UUID,
        replicas: int,
    ) -> bool:
        """
        Update endpoint replicas.
        Returns True if updated, False if not found.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, endpoint_id)
            if not endpoint:
                return False

            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == endpoint_id)
                .values({"replicas": replicas})
            )
            await session.execute(query)
        return True

    @model_serving_repository_resilience.apply()
    async def get_auto_scaling_rule_by_id(
        self,
        rule_id: uuid.UUID,
    ) -> EndpointAutoScalingRuleData | None:
        """
        Get auto scaling rule by ID.
        Returns None if rule doesn't exist.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            try:
                rule = await EndpointAutoScalingRuleRow.get(session, rule_id, load_endpoint=True)
                if not rule:
                    return None

                return rule.to_data()
            except ObjectNotFound:
                return None

    @model_serving_repository_resilience.apply()
    async def create_auto_scaling_rule(
        self,
        endpoint_id: uuid.UUID,
        metric_source: AutoScalingMetricSource,
        metric_name: str,
        threshold: Any,
        comparator: AutoScalingMetricComparator,
        step_size: int,
        cooldown_seconds: int,
        min_replicas: int | None = None,
        max_replicas: int | None = None,
    ) -> EndpointAutoScalingRuleData | None:
        """
        Create auto scaling rule.
        Returns the created rule if successful, None if endpoint not found or inactive.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, endpoint_id)
            if not endpoint:
                return None

            if endpoint.lifecycle_stage in EndpointLifecycle.inactive_states():
                return None

            rule = await endpoint.create_auto_scaling_rule(
                session,
                metric_source,
                metric_name,
                threshold,
                comparator,
                step_size,
                cooldown_seconds=cooldown_seconds,
                min_replicas=min_replicas,
                max_replicas=max_replicas,
            )
            return rule.to_data()

    @model_serving_repository_resilience.apply()
    async def update_auto_scaling_rule(
        self,
        updater: Updater[EndpointAutoScalingRuleRow],
    ) -> EndpointAutoScalingRuleData | None:
        """
        Update auto scaling rule.
        Returns the updated rule if successful, None if not found or endpoint inactive.
        """
        rule_id = uuid.UUID(str(updater.pk_value))

        async with self._db.begin_session() as session:
            try:
                # Validate lifecycle stage before update
                rule = await EndpointAutoScalingRuleRow.get(session, rule_id, load_endpoint=True)
                if not rule:
                    return None

                if rule.endpoint_row.lifecycle_stage in EndpointLifecycle.inactive_states():
                    return None

                # Use execute_updater to apply changes
                result = await execute_updater(session, updater)
                if result is None:
                    return None

                return result.row.to_data()
            except ObjectNotFound:
                return None

    @model_serving_repository_resilience.apply()
    async def delete_auto_scaling_rule(
        self,
        rule_id: uuid.UUID,
    ) -> bool:
        """
        Delete auto scaling rule.
        Returns True if deleted, False if not found.
        """
        async with self._db.begin_session() as session:
            try:
                rule = await EndpointAutoScalingRuleRow.get(session, rule_id, load_endpoint=True)
                if not rule:
                    return False

                await session.delete(rule)
                return True
            except NoResultFound:
                return False

    @model_serving_repository_resilience.apply()
    async def resolve_group_id(
        self, domain_name: str, group_name_or_id: str | uuid.UUID
    ) -> uuid.UUID | None:
        """
        Resolve group name or ID to group ID.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            conn = await session.connection()
            if conn is None:
                raise DatabaseConnectionUnavailable("Database connection is not available")
            return await resolve_group_name_or_id(conn, domain_name, group_name_or_id)

    @model_serving_repository_resilience.apply()
    async def get_session_by_id(
        self, session_id: uuid.UUID, kernel_loading_strategy: KernelLoadingStrategy
    ) -> SessionRow | None:
        """
        Get session by ID with specified kernel loading strategy.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            try:
                return await SessionRow.get_session(
                    session, session_id, None, kernel_loading_strategy=kernel_loading_strategy
                )
            except NoResultFound:
                return None

    @model_serving_repository_resilience.apply()
    async def resolve_image_for_endpoint_creation(
        self, identifiers: list[ImageIdentifier | ImageAlias | ImageRef]
    ) -> ImageRow:
        """
        Resolve image for endpoint creation.
        This is a special case where we need the actual ImageRow object
        because EndpointRow constructor requires it.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            return await ImageRow.resolve(session, identifiers)

    @model_serving_repository_resilience.apply()
    async def modify_endpoint(
        self,
        action: ModifyEndpointAction,
        agent_registry: AgentRegistry,
        legacy_etcd_config_loader: LegacyEtcdLoader,
        storage_manager: StorageSessionManager,
    ) -> MutationResult:
        """
        Modify an endpoint with all validations and checks.
        This method handles all database operations for endpoint modification.
        """

        async def _do_mutate() -> MutationResult:
            async with self._db.begin_session() as db_session:
                try:
                    endpoint_row = await EndpointRow.get(
                        db_session,
                        action.endpoint_id,
                        load_session_owner=True,
                        load_model=True,
                        load_routes=True,
                        load_image=True,
                    )
                    user_data = current_user()
                    if user_data is None:
                        raise GenericForbidden("User context not available.")
                    match user_data.role:
                        case UserRole.SUPERADMIN:
                            pass
                        case UserRole.ADMIN:
                            domain_name = user_data.domain_name
                            if endpoint_row.domain != domain_name:
                                raise EndpointNotFound
                        case _:
                            user_id = user_data.user_id
                            if endpoint_row.session_owner != user_id:
                                raise EndpointNotFound
                except NoResultFound as e:
                    raise EndpointNotFound from e

                if endpoint_row.lifecycle_stage in (
                    EndpointLifecycle.DESTROYING,
                    EndpointLifecycle.DESTROYED,
                ):
                    raise InvalidAPIParameters("Cannot update endpoint marked for removal")

                spec = cast(EndpointUpdaterSpec, action.updater.spec)
                spec.apply_to_row(endpoint_row)

                image_ref = spec.image.optional_value()
                if image_ref is not None:
                    image_name = image_ref.name
                    arch = image_ref.architecture.value()
                    # This needs to happen within the transaction
                    image_row = await ImageRow.resolve(
                        db_session, [ImageIdentifier(image_name, arch), ImageAlias(image_name)]
                    )
                    endpoint_row.image = image_row.id

                session_owner = endpoint_row.session_owner_row
                if session_owner is None:
                    raise InvalidAPIParameters("Session owner not found for endpoint")
                if session_owner.main_access_key is None:
                    raise InvalidAPIParameters("Session owner has no access key")
                if session_owner.role is None:
                    raise InvalidAPIParameters("Session owner has no role")

                conn = await db_session.connection()
                if conn is None:
                    raise DatabaseConnectionUnavailable("Database connection is not available")

                await ModelServiceHelper.check_scaling_group(
                    conn,
                    endpoint_row.resource_group,
                    AccessKey(session_owner.main_access_key),
                    endpoint_row.domain,
                    endpoint_row.project,
                )

                user_scope = UserScope(
                    domain_name=endpoint_row.domain,
                    group_id=endpoint_row.project,
                    user_uuid=session_owner.uuid,
                    user_role=session_owner.role.value,
                )

                resource_policy_row = await self.get_keypair_resource_policy(
                    session_owner.resource_policy
                )
                if not resource_policy_row:
                    raise InvalidAPIParameters("Resource policy not found")
                resource_policy = resource_policy_row._mapping  # for backward compatibility
                extra_mounts_input = spec.extra_mounts.optional_value()
                if extra_mounts_input is not None:
                    extra_mounts = {
                        mount.vfolder_id.value(): MountOptionModel(
                            mount_destination=(
                                mount.mount_destination.value()
                                if mount.mount_destination.optional_value() is not None
                                else None
                            ),
                            type=MountTypes(mount.type.value())
                            if mount.type.optional_value() is not None
                            else MountTypes.BIND,
                            permission=(
                                MountPermission(mount.permission.value())
                                if mount.permission.optional_value() is not None
                                else None
                            ),
                        )
                        for mount in extra_mounts_input
                    }
                    if endpoint_row.model is None:
                        raise InvalidAPIParameters("Endpoint has no model")
                    vfolder_mounts = await ModelServiceHelper.check_extra_mounts(
                        conn,
                        legacy_etcd_config_loader,
                        storage_manager,
                        endpoint_row.model,
                        endpoint_row.model_mount_destination,
                        extra_mounts,
                        user_scope,
                        resource_policy,
                    )
                    endpoint_row.extra_mounts = list(vfolder_mounts)

                if endpoint_row.runtime_variant == RuntimeVariant.CUSTOM:
                    if endpoint_row.model_row is None:
                        raise InvalidAPIParameters("Endpoint has no model row")
                    vfid = endpoint_row.model_row.vfid
                    yaml_path = await ModelServiceHelper.validate_model_definition_file_exists(
                        storage_manager,
                        endpoint_row.model_row.host,
                        vfid,
                        endpoint_row.model_definition_path,
                    )
                    await ModelServiceHelper.validate_model_definition(
                        storage_manager,
                        endpoint_row.model_row.host,
                        vfid,
                        yaml_path,
                    )
                elif (
                    endpoint_row.runtime_variant != RuntimeVariant.CMD
                    and endpoint_row.model_mount_destination != "/models"
                ):
                    raise InvalidAPIParameters(
                        "Model mount destination must be /models for non-custom runtimes"
                    )

                # This needs to happen within the transaction for validation
                if endpoint_row.image_row is None:
                    raise InvalidAPIParameters("Endpoint has no image row")
                image_row = await ImageRow.resolve(
                    db_session,
                    [
                        ImageIdentifier(
                            endpoint_row.image_row.name, endpoint_row.image_row.architecture
                        ),
                    ],
                )

                await agent_registry.create_session(
                    "",
                    image_row.image_ref,
                    user_scope,
                    AccessKey(session_owner.main_access_key),
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
                    ClusterMode(endpoint_row.cluster_mode),
                    endpoint_row.cluster_size,
                    bootstrap_script=endpoint_row.bootstrap_script,
                    startup_command=endpoint_row.startup_command,
                    tag=endpoint_row.tag,
                    callback_url=endpoint_row.callback_url,
                    sudo_session_enabled=session_owner.sudo_session_enabled,
                    dry_run=True,
                )

                await db_session.commit()
                return MutationResult(
                    success=True,
                    message="success",
                    data=endpoint_row.to_data(),
                )

        try:
            return await execute_with_retry(_do_mutate)
        except IntegrityError as e:
            return MutationResult(success=False, message=f"integrity error: {e}", data=None)
        except StatementError as e:
            orig_exc = e.orig
            return MutationResult(success=False, message=str(orig_exc), data=None)
        except (TimeoutError, asyncio.CancelledError):
            raise
        except Exception:
            raise

    @model_serving_repository_resilience.apply()
    async def search_auto_scaling_rules(
        self,
        querier: BatchQuerier,
    ) -> EndpointAutoScalingRuleListResult:
        """
        Search auto scaling rules.
        Access control conditions should be injected into querier.conditions by the caller.
        """
        async with self._db.begin_readonly_session() as session:
            query = sa.select(EndpointAutoScalingRuleRow).join(
                EndpointRow, EndpointAutoScalingRuleRow.endpoint == EndpointRow.id
            )

            result = await execute_batch_querier(session, query, querier)

            items = [row.EndpointAutoScalingRuleRow.to_data() for row in result.rows]

            return EndpointAutoScalingRuleListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    @model_serving_repository_resilience.apply()
    async def search_services_paginated(
        self,
        session_owner_id: uuid.UUID,
        querier: BatchQuerier,
    ) -> ServiceSearchResult:
        """
        Search services with pagination.
        Base conditions (session_owner, lifecycle_stage) are applied as security constraints.
        Additional filter/pagination conditions come from the querier.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            query = (
                sa.select(EndpointRow)
                .where(EndpointRow.session_owner == session_owner_id)
                .where(EndpointRow.lifecycle_stage == EndpointLifecycle.CREATED)
                .options(selectinload(EndpointRow.routings))
            )

            result = await execute_batch_querier(session, query, querier)

            items: list[ServiceSearchItem] = []
            for row in result.rows:
                ep = row.EndpointRow
                routings_data = [r.to_data() for r in ep.routings] if ep.routings else None
                active_route_count = (
                    len([r for r in ep.routings if r.status == RouteStatus.HEALTHY])
                    if ep.routings
                    else 0
                )
                items.append(
                    ServiceSearchItem(
                        id=ep.id,
                        name=ep.name,
                        replicas=ep.replicas,
                        active_route_count=active_route_count,
                        service_endpoint=HttpUrl(ep.url) if ep.url else None,
                        open_to_public=ep.open_to_public or False,
                        resource_slots=ep.resource_slots,
                        routings=routings_data,
                    )
                )

            return ServiceSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

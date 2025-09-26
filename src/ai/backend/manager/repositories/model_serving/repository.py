import asyncio
import uuid
from typing import Any, Optional, cast

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.docker import ImageRef
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import (
    ClusterMode,
    MountPermission,
    MountTypes,
    RuntimeVariant,
    SessionTypes,
)
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.data.model_serving.creator import EndpointCreator
from ai.backend.manager.data.model_serving.types import (
    EndpointAutoScalingRuleData,
    EndpointData,
    EndpointTokenData,
    MutationResult,
    RoutingData,
    ScalingGroupData,
    UserData,
)
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.errors.common import ObjectNotFound
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
from ai.backend.manager.services.model_serving.actions.modify_endpoint import ModifyEndpointAction
from ai.backend.manager.services.model_serving.exceptions import InvalidAPIParameters
from ai.backend.manager.types import MountOptionModel, UserScope

# Layer-specific decorator for model_serving repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.MODEL_SERVING)


class ModelServingRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def get_endpoint_by_id_validated(
        self, endpoint_id: uuid.UUID, user_id: uuid.UUID, user_role: UserRole, domain_name: str
    ) -> Optional[EndpointData]:
        """
        Get endpoint by ID with access control validation.
        Returns None if endpoint doesn't exist or user doesn't have access.
        """
        async with self._db.begin_readonly_session() as session:
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

            if not await self._validate_endpoint_access(
                session, endpoint, user_id, user_role, domain_name
            ):
                return None

            return endpoint.to_data()

    @repository_decorator()
    async def get_endpoint_by_name_validated(
        self, name: str, user_id: uuid.UUID
    ) -> Optional[EndpointData]:
        """
        Get endpoint by name with ownership validation.
        Returns None if endpoint doesn't exist or user doesn't own it.
        """
        async with self._db.begin_readonly_session() as session:
            endpoint = await self._get_endpoint_by_name(session, name, user_id)
            if not endpoint:
                return None
            return endpoint.to_data()

    @repository_decorator()
    async def list_endpoints_by_owner_validated(
        self, session_owner_id: uuid.UUID, name: Optional[str] = None
    ) -> list[EndpointData]:
        """
        List endpoints owned by a specific user with optional name filter.
        """
        async with self._db.begin_readonly_session() as session:
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
            data_list = [row.to_data() for row in rows]

            return data_list

    @repository_decorator()
    async def check_endpoint_name_uniqueness(self, name: str) -> bool:
        """
        Check if endpoint name is unique (not already taken by non-destroyed endpoints).
        Returns True if name is available, False if taken.
        """
        async with self._db.begin_readonly_session() as session:
            query = sa.select(EndpointRow).where(
                (EndpointRow.lifecycle_stage != EndpointLifecycle.DESTROYED)
                & (EndpointRow.name == name)
            )
            result = await session.execute(query)
            existing_endpoint = result.scalar()

            return existing_endpoint is None

    @repository_decorator()
    async def create_endpoint_validated(
        self, endpoint_creator: EndpointCreator, registry: AgentRegistry
    ) -> EndpointData:
        """
        Create a new endpoint after validation.
        """
        async with self._db.begin_session() as db_sess:
            endpoint_row = EndpointRow.from_creator(endpoint_creator)
            db_sess.add(endpoint_row)
            await db_sess.flush()
            endpoint_row = await EndpointRow.get(
                db_sess,
                endpoint_row.id,
                load_created_user=True,
                load_session_owner=True,
                load_image=True,
                load_routes=True,
            )
            endpoint_before_assign_url = endpoint_row.to_data()
            endpoint_row.url = await registry.create_appproxy_endpoint(
                db_sess, endpoint_before_assign_url
            )
            data = endpoint_row.to_data()

        return data

    @repository_decorator()
    async def update_endpoint_lifecycle_validated(
        self,
        endpoint_id: uuid.UUID,
        lifecycle_stage: EndpointLifecycle,
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
        replicas: Optional[int] = None,
    ) -> bool:
        """
        Update endpoint lifecycle stage with access validation.
        Returns True if updated, False if not found or no access.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, endpoint_id)
            if not endpoint:
                return False

            if not await self._validate_endpoint_access(
                session, endpoint, user_id, user_role, domain_name
            ):
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

    @repository_decorator()
    async def clear_endpoint_errors_validated(
        self, endpoint_id: uuid.UUID, user_id: uuid.UUID, user_role: UserRole, domain_name: str
    ) -> bool:
        """
        Clear endpoint errors (failed routes and reset retry count) with access validation.
        Returns True if cleared, False if not found or no access.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, endpoint_id)
            if not endpoint:
                return False

            if not await self._validate_endpoint_access(
                session, endpoint, user_id, user_role, domain_name
            ):
                return False

            # Delete failed routes
            query = sa.delete(RoutingRow).where(
                (RoutingRow.endpoint == endpoint_id)
                & (RoutingRow.status == RouteStatus.FAILED_TO_START)
            )
            await session.execute(query)

            # Reset retry count
            query = (
                sa.update(EndpointRow).values({"retries": 0}).where(EndpointRow.id == endpoint_id)
            )
            await session.execute(query)

        return True

    @repository_decorator()
    async def get_route_by_id_validated(
        self,
        route_id: uuid.UUID,
        service_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
    ) -> Optional[RoutingData]:
        """
        Get route by ID with endpoint ownership validation.
        Returns None if route doesn't exist, doesn't belong to service, or user doesn't have access.
        """
        async with self._db.begin_readonly_session() as session:
            route = await self._get_route_by_id(session, route_id, load_endpoint=True)
            if not route or route.endpoint != service_id:
                return None

            if not await self._validate_endpoint_access(
                session, route.endpoint_row, user_id, user_role, domain_name
            ):
                return None

            return route.to_data()

    @repository_decorator()
    async def update_route_traffic_validated(
        self,
        valkey_live: ValkeyLiveClient,
        route_id: uuid.UUID,
        service_id: uuid.UUID,
        traffic_ratio: float,
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
    ) -> Optional[EndpointData]:
        """
        Update route traffic ratio with access validation.
        Returns updated endpoint data if successful, None if not found or no access.
        """
        async with self._db.begin_session() as session:
            route = await self._get_route_by_id(session, route_id, load_endpoint=True)
            if not route or route.endpoint != service_id:
                return None

            if not await self._validate_endpoint_access(
                session, route.endpoint_row, user_id, user_role, domain_name
            ):
                return None

            query = (
                sa.update(RoutingRow)
                .where(RoutingRow.id == route_id)
                .values({"traffic_ratio": traffic_ratio})
            )
            await session.execute(query)

            endpoint = await self._get_endpoint_by_id(session, service_id, load_routes=True)
            if endpoint is None:
                raise NoResultFound

            await valkey_live.store_live_data(
                f"endpoint.{service_id}.session.{route.session}.traffic_ratio",
                str(traffic_ratio),
            )
            return endpoint.to_data()

    @repository_decorator()
    async def decrease_endpoint_replicas_validated(
        self, service_id: uuid.UUID, user_id: uuid.UUID, user_role: UserRole, domain_name: str
    ) -> bool:
        """
        Decrease endpoint replicas by 1 with access validation.
        Returns True if decreased, False if not found or no access.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, service_id, load_session_owner=True)
            if not endpoint:
                return False

            if not await self._validate_endpoint_access(
                session, endpoint, user_id, user_role, domain_name
            ):
                return False

            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == service_id)
                .values({"replicas": endpoint.replicas - 1})
            )
            await session.execute(query)

        return True

    @repository_decorator()
    async def create_endpoint_token_validated(
        self, token_row: EndpointTokenRow, user_id: uuid.UUID, user_role: UserRole, domain_name: str
    ) -> Optional[EndpointTokenData]:
        """
        Create endpoint token with access validation.
        Returns token data if created, None if no access to endpoint.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, token_row.endpoint)
            if not endpoint:
                return None

            if not await self._validate_endpoint_access(
                session, endpoint, user_id, user_role, domain_name
            ):
                return None

            session.add(token_row)
            await session.commit()
            await session.refresh(token_row)

            return token_row.to_dataclass()

    @repository_decorator()
    async def get_scaling_group_info(self, scaling_group_name: str) -> Optional[ScalingGroupData]:
        """
        Get scaling group information (wsproxy details).
        """
        async with self._db.begin_readonly_session() as session:
            query = (
                sa.select([scaling_groups.c.wsproxy_addr, scaling_groups.c.wsproxy_api_token])
                .select_from(scaling_groups)
                .where((scaling_groups.c.name == scaling_group_name))
            )
            result = await session.execute(query)
            row = result.first()
            if not row:
                return None

            return ScalingGroupData(
                wsproxy_addr=row["wsproxy_addr"], wsproxy_api_token=row["wsproxy_api_token"]
            )

    @repository_decorator()
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[UserData]:
        """
        Get user information by ID.
        """
        async with self._db.begin_readonly_session() as session:
            query = sa.select(UserRow).where(UserRow.uuid == user_id)
            result = await session.execute(query)
            user_row: Optional[UserRow] = result.scalar()
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
    ) -> Optional[EndpointRow]:
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
    ) -> Optional[EndpointRow]:
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
    ) -> Optional[RoutingRow]:
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
        if endpoint.session_owner is None:
            return True

        query = sa.select(UserRow).where(UserRow.uuid == endpoint.session_owner)
        result = await session.execute(query)
        owner = result.scalar()

        match user_role:
            case UserRole.SUPERADMIN:
                return True
            case UserRole.ADMIN:
                if owner.role == UserRole.SUPERADMIN:
                    return False
                return endpoint.domain == domain_name
            case _:
                return owner.uuid == user_id

    @repository_decorator()
    async def get_vfolder_by_id(self, vfolder_id: uuid.UUID) -> Optional[VFolderRow]:
        """
        Get VFolder by ID.
        """
        async with self._db.begin_readonly_session() as session:
            return await VFolderRow.get(session, vfolder_id)

    @repository_decorator()
    async def get_user_with_keypair(self, user_id: uuid.UUID) -> Optional[Any]:
        """
        Get user with their main access key.
        """
        async with self._db.begin_readonly_session() as session:
            query = sa.select(sa.join(UserRow, KeyPairRow, KeyPairRow.user == UserRow.uuid)).where(
                UserRow.uuid == user_id
            )
            result = await session.execute(query)
            return result.fetchone()

    @repository_decorator()
    async def get_keypair_resource_policy(self, policy_name: str) -> Optional[Any]:
        """
        Get keypair resource policy by name.
        """
        async with self._db.begin_readonly_session() as session:
            query = (
                sa.select([keypair_resource_policies])
                .select_from(keypair_resource_policies)
                .where(keypair_resource_policies.c.name == policy_name)
            )
            result = await session.execute(query)
            return result.first()

    @repository_decorator()
    async def get_endpoint_for_appproxy_update(
        self, service_id: uuid.UUID
    ) -> Optional[EndpointRow]:
        """
        Get endpoint with routes loaded for AppProxy updates.
        """
        async with self._db.begin_readonly_session() as session:
            return await self._get_endpoint_by_id(session, service_id, load_routes=True)

    @repository_decorator()
    async def get_route_with_session(self, route_id: uuid.UUID) -> Optional[RoutingRow]:
        """
        Get route with endpoint and session data loaded.
        """
        async with self._db.begin_readonly_session() as session:
            return await self._get_route_by_id(
                session, route_id, load_endpoint=True, load_session=True
            )

    @repository_decorator()
    async def update_endpoint_replicas_validated(
        self,
        endpoint_id: uuid.UUID,
        replicas: int,
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
    ) -> bool:
        """
        Update endpoint replicas with access validation.
        Returns True if updated, False if not found or no access.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, endpoint_id)
            if not endpoint:
                return False

            if not await self._validate_endpoint_access(
                session, endpoint, user_id, user_role, domain_name
            ):
                return False

            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == endpoint_id)
                .values({"replicas": replicas})
            )
            await session.execute(query)
        return True

    @repository_decorator()
    async def get_auto_scaling_rule_by_id_validated(
        self,
        rule_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
    ) -> Optional[EndpointAutoScalingRuleData]:
        """
        Get auto scaling rule by ID with access validation.
        Returns None if rule doesn't exist or user doesn't have access.
        """
        async with self._db.begin_readonly_session() as session:
            try:
                rule = await EndpointAutoScalingRuleRow.get(session, rule_id, load_endpoint=True)
                if not rule:
                    return None

                if not await self._validate_endpoint_access(
                    session, rule.endpoint_row, user_id, user_role, domain_name
                ):
                    return None

                return rule.to_data()
            except ObjectNotFound:
                return None

    @repository_decorator()
    async def create_auto_scaling_rule_validated(
        self,
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
        endpoint_id: uuid.UUID,
        metric_source: AutoScalingMetricSource,
        metric_name: str,
        threshold: Any,
        comparator: AutoScalingMetricComparator,
        step_size: int,
        cooldown_seconds: int,
        min_replicas: Optional[int] = None,
        max_replicas: Optional[int] = None,
    ) -> Optional[EndpointAutoScalingRuleData]:
        """
        Create auto scaling rule with access validation.
        Returns the created rule if successful, None if no access.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, endpoint_id)
            if not endpoint:
                return None

            if not await self._validate_endpoint_access(
                session, endpoint, user_id, user_role, domain_name
            ):
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

    @repository_decorator()
    async def update_auto_scaling_rule_validated(
        self,
        rule_id: uuid.UUID,
        fields_to_update: dict[str, Any],
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
    ) -> Optional[EndpointAutoScalingRuleData]:
        """
        Update auto scaling rule with access validation.
        Returns the updated rule if successful, None if not found or no access.
        """
        async with self._db.begin_session() as session:
            try:
                rule = await EndpointAutoScalingRuleRow.get(session, rule_id, load_endpoint=True)
                if not rule:
                    return None

                if not await self._validate_endpoint_access(
                    session, rule.endpoint_row, user_id, user_role, domain_name
                ):
                    return None

                if rule.endpoint_row.lifecycle_stage in EndpointLifecycle.inactive_states():
                    return None

                for key, value in fields_to_update.items():
                    setattr(rule, key, value)

                return rule.to_data()
            except ObjectNotFound:
                return None

    @repository_decorator()
    async def delete_auto_scaling_rule_validated(
        self,
        rule_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
    ) -> bool:
        """
        Delete auto scaling rule with access validation.
        Returns True if deleted, False if not found or no access.
        """
        async with self._db.begin_session() as session:
            try:
                rule = await EndpointAutoScalingRuleRow.get(session, rule_id, load_endpoint=True)
                if not rule:
                    return False

                if not await self._validate_endpoint_access(
                    session, rule.endpoint_row, user_id, user_role, domain_name
                ):
                    return False

                await session.delete(rule)
                return True
            except NoResultFound:
                return False

    @repository_decorator()
    async def resolve_group_id(
        self, domain_name: str, group_name_or_id: str | uuid.UUID
    ) -> Optional[uuid.UUID]:
        """
        Resolve group name or ID to group ID.
        """
        async with self._db.begin_readonly_session() as session:
            conn = await session.connection()
            assert conn is not None
            return await resolve_group_name_or_id(conn, domain_name, group_name_or_id)

    @repository_decorator()
    async def get_session_by_id(
        self, session_id: uuid.UUID, kernel_loading_strategy: KernelLoadingStrategy
    ) -> Optional[SessionRow]:
        """
        Get session by ID with specified kernel loading strategy.
        """
        async with self._db.begin_readonly_session() as session:
            try:
                return await SessionRow.get_session(
                    session, session_id, None, kernel_loading_strategy=kernel_loading_strategy
                )
            except NoResultFound:
                return None

    @repository_decorator()
    async def resolve_image_for_endpoint_creation(
        self, identifiers: list[ImageIdentifier | ImageAlias | ImageRef]
    ) -> ImageRow:
        """
        Resolve image for endpoint creation.
        This is a special case where we need the actual ImageRow object
        because EndpointRow constructor requires it.
        """
        async with self._db.begin_readonly_session() as session:
            return await ImageRow.resolve(session, identifiers)

    @repository_decorator()
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
                    match action.requester_ctx.user_role:
                        case UserRole.SUPERADMIN:
                            pass
                        case UserRole.ADMIN:
                            domain_name = action.requester_ctx.domain_name
                            if endpoint_row.domain != domain_name:
                                raise EndpointNotFound
                        case _:
                            user_id = action.requester_ctx.user_id
                            if endpoint_row.session_owner != user_id:
                                raise EndpointNotFound
                except NoResultFound:
                    raise EndpointNotFound
                if endpoint_row.lifecycle_stage in (
                    EndpointLifecycle.DESTROYING,
                    EndpointLifecycle.DESTROYED,
                ):
                    raise InvalidAPIParameters("Cannot update endpoint marked for removal")

                fields_to_update = action.modifier.fields_to_update()
                for key, value in fields_to_update.items():
                    setattr(endpoint_row, key, value)

                fields_to_update_require_none_check = (
                    action.modifier.fields_to_update_require_none_check()
                )
                for key, value in fields_to_update_require_none_check.items():
                    if value is not None:
                        setattr(endpoint_row, key, value)

                image_ref = action.modifier.image.optional_value()
                if image_ref is not None:
                    image_name = image_ref.name
                    arch = image_ref.architecture.value()
                    # This needs to happen within the transaction
                    image_row = await ImageRow.resolve(
                        db_session, [ImageIdentifier(image_name, arch), ImageAlias(image_name)]
                    )
                    endpoint_row.image = image_row.id

                session_owner: UserRow = endpoint_row.session_owner_row

                conn = await db_session.connection()
                assert conn

                await ModelServiceHelper.check_scaling_group(
                    conn,
                    endpoint_row.resource_group,
                    session_owner.main_access_key,
                    endpoint_row.domain,
                    endpoint_row.project,
                )

                user_scope = UserScope(
                    domain_name=endpoint_row.domain,
                    group_id=endpoint_row.project,
                    user_uuid=session_owner.uuid,
                    user_role=session_owner.role,
                )

                resource_policy = await self.get_keypair_resource_policy(
                    session_owner.resource_policy
                )
                if not resource_policy:
                    raise InvalidAPIParameters("Resource policy not found")
                extra_mounts_input = action.modifier.extra_mounts.optional_value()
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
                    endpoint_row.extra_mounts = vfolder_mounts

                if endpoint_row.runtime_variant == RuntimeVariant.CUSTOM:
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
        except (asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except Exception:
            raise

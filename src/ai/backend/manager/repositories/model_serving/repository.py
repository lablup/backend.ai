import uuid
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.manager.data.model_serving.types import (
    EndpointData,
    EndpointTokenData,
    RoutingData,
    ScalingGroupData,
    UserData,
)
from ai.backend.manager.models.endpoint import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointAutoScalingRuleRow,
    EndpointLifecycle,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import keypair_resource_policies
from ai.backend.manager.models.routing import RouteStatus, RoutingRow
from ai.backend.manager.models.scaling_group import scaling_groups
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow


class ModelServingRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_endpoint_by_id_validated(
        self, endpoint_id: uuid.UUID, user_id: uuid.UUID, user_role: UserRole, domain_name: str
    ) -> Optional[EndpointData]:
        """
        Get endpoint by ID with access control validation.
        Returns None if endpoint doesn't exist or user doesn't have access.
        """
        async with self._db.begin_readonly_session() as session:
            endpoint = await self._get_endpoint_by_id(
                session, endpoint_id, load_routes=True, load_session_owner=True, load_model=True
            )
            if not endpoint:
                return None

            if not self._validate_endpoint_access(endpoint, user_id, user_role, domain_name):
                return None

            data = EndpointData.from_row(endpoint)
        return data

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
            data = EndpointData.from_row(endpoint)
        return data

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
            rows = result.scalars().all()
            data_list = [EndpointData.from_row(row) for row in rows]
        return data_list

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

    async def create_endpoint_validated(self, endpoint_row: EndpointRow) -> EndpointData:
        """
        Create a new endpoint after validation.
        """
        async with self._db.begin_session() as session:
            session.add(endpoint_row)
            await session.flush()
            await session.refresh(endpoint_row)
            data = EndpointData.from_row(endpoint_row)
        return data

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

            if not self._validate_endpoint_access(endpoint, user_id, user_role, domain_name):
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

            if not self._validate_endpoint_access(endpoint, user_id, user_role, domain_name):
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

            if not self._validate_endpoint_access(
                route.endpoint_row, user_id, user_role, domain_name
            ):
                return None

            data = RoutingData.from_row(route)
        return data

    async def update_route_traffic_validated(
        self,
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

            if not self._validate_endpoint_access(
                route.endpoint_row, user_id, user_role, domain_name
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
            data = EndpointData.from_row(endpoint)
        return data

    async def decrease_endpoint_replicas_validated(
        self, service_id: uuid.UUID, user_id: uuid.UUID, user_role: UserRole, domain_name: str
    ) -> bool:
        """
        Decrease endpoint replicas by 1 with access validation.
        Returns True if decreased, False if not found or no access.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, service_id)
            if not endpoint:
                return False

            if not self._validate_endpoint_access(endpoint, user_id, user_role, domain_name):
                return False

            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == service_id)
                .values({"replicas": endpoint.replicas - 1})
            )
            await session.execute(query)
        return True

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

            if not self._validate_endpoint_access(endpoint, user_id, user_role, domain_name):
                return None

            session.add(token_row)
            await session.commit()
            await session.refresh(token_row)
            data = EndpointTokenData.from_row(token_row)
        return data

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

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[UserData]:
        """
        Get user information by ID.
        """
        async with self._db.begin_readonly_session() as session:
            query = sa.select(UserRow).where(UserRow.uuid == user_id)
            result = await session.execute(query)
            user_row = result.scalar()
            if not user_row:
                return None
            data = UserData.from_row(user_row)
        return data

    async def _get_endpoint_by_id(
        self,
        session: SASession,
        endpoint_id: uuid.UUID,
        load_routes: bool = False,
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

    def _validate_endpoint_access(
        self, endpoint: EndpointRow, user_id: uuid.UUID, user_role: UserRole, domain_name: str
    ) -> bool:
        """
        Private method to validate user access to endpoint.
        """
        match user_role:
            case UserRole.SUPERADMIN:
                return True
            case UserRole.ADMIN:
                return endpoint.domain == domain_name
            case _:
                return endpoint.session_owner == user_id

    async def get_vfolder_by_id(self, vfolder_id: uuid.UUID) -> Optional[VFolderRow]:
        """
        Get VFolder by ID.
        """
        async with self._db.begin_readonly_session() as session:
            return await VFolderRow.get(session, vfolder_id)

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

    async def get_endpoint_for_appproxy_update(
        self, service_id: uuid.UUID
    ) -> Optional[EndpointRow]:
        """
        Get endpoint with routes loaded for AppProxy updates.
        """
        async with self._db.begin_readonly_session() as session:
            return await self._get_endpoint_by_id(session, service_id, load_routes=True)

    async def get_route_with_session(self, route_id: uuid.UUID) -> Optional[RoutingRow]:
        """
        Get route with endpoint and session data loaded.
        """
        async with self._db.begin_readonly_session() as session:
            return await self._get_route_by_id(
                session, route_id, load_endpoint=True, load_session=True
            )

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

            if not self._validate_endpoint_access(endpoint, user_id, user_role, domain_name):
                return False

            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == endpoint_id)
                .values({"replicas": replicas})
            )
            await session.execute(query)
        return True

    async def get_auto_scaling_rule_by_id_validated(
        self,
        rule_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
    ) -> Optional[EndpointAutoScalingRuleRow]:
        """
        Get auto scaling rule by ID with access validation.
        Returns None if rule doesn't exist or user doesn't have access.
        """
        async with self._db.begin_readonly_session() as session:
            try:
                rule = await EndpointAutoScalingRuleRow.get(session, rule_id, load_endpoint=True)
                if not rule:
                    return None

                if not self._validate_endpoint_access(
                    rule.endpoint_row, user_id, user_role, domain_name
                ):
                    return None

                return rule
            except NoResultFound:
                return None

    async def create_auto_scaling_rule_validated(
        self,
        endpoint_id: uuid.UUID,
        metric_source: AutoScalingMetricSource,
        metric_name: str,
        threshold: Any,
        comparator: AutoScalingMetricComparator,
        step_size: int,
        cooldown_seconds: int,
        min_replicas: int,
        max_replicas: int,
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
    ) -> Optional[EndpointAutoScalingRuleRow]:
        """
        Create auto scaling rule with access validation.
        Returns the created rule if successful, None if no access.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, endpoint_id)
            if not endpoint:
                return None

            if not self._validate_endpoint_access(endpoint, user_id, user_role, domain_name):
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
            return rule

    async def update_auto_scaling_rule_validated(
        self,
        rule_id: uuid.UUID,
        fields_to_update: dict[str, Any],
        user_id: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
    ) -> Optional[EndpointAutoScalingRuleRow]:
        """
        Update auto scaling rule with access validation.
        Returns the updated rule if successful, None if not found or no access.
        """
        async with self._db.begin_session() as session:
            try:
                rule = await EndpointAutoScalingRuleRow.get(session, rule_id, load_endpoint=True)
                if not rule:
                    return None

                if not self._validate_endpoint_access(
                    rule.endpoint_row, user_id, user_role, domain_name
                ):
                    return None

                if rule.endpoint_row.lifecycle_stage in EndpointLifecycle.inactive_states():
                    return None

                for key, value in fields_to_update.items():
                    setattr(rule, key, value)

                return rule
            except NoResultFound:
                return None

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

                if not self._validate_endpoint_access(
                    rule.endpoint_row, user_id, user_role, domain_name
                ):
                    return False

                await session.delete(rule)
                return True
            except NoResultFound:
                return False

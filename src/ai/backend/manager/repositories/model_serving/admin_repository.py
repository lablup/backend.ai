import uuid
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.model_serving.types import (
    EndpointAutoScalingRuleData,
    EndpointAutoScalingRuleListResult,
    EndpointData,
    EndpointTokenData,
    RoutingData,
)
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.endpoint import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointAutoScalingRuleRow,
    EndpointLifecycle,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.routing import RouteStatus, RoutingRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

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


class AdminModelServingRepository:
    """
    Repository for admin-specific model serving operations that bypass ownership checks.
    This should only be used by superadmin users.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @model_serving_repository_resilience.apply()
    async def get_endpoint_by_id_force(self, endpoint_id: uuid.UUID) -> Optional[EndpointData]:
        """
        Get endpoint by ID without access control validation.
        Returns None if endpoint doesn't exist.
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
            data = endpoint.to_data()
        return data

    @model_serving_repository_resilience.apply()
    async def update_endpoint_lifecycle_force(
        self,
        endpoint_id: uuid.UUID,
        lifecycle_stage: EndpointLifecycle,
        replicas: Optional[int] = None,
    ) -> bool:
        """
        Update endpoint lifecycle stage without access validation.
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
    async def clear_endpoint_errors_force(self, endpoint_id: uuid.UUID) -> bool:
        """
        Clear endpoint errors (failed routes and reset retry count) without access validation.
        Returns True if cleared, False if not found.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, endpoint_id)
            if not endpoint:
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

    @model_serving_repository_resilience.apply()
    async def get_route_by_id_force(
        self, route_id: uuid.UUID, service_id: uuid.UUID
    ) -> Optional[RoutingData]:
        """
        Get route by ID without endpoint ownership validation.
        Returns None if route doesn't exist or doesn't belong to service.
        """
        async with self._db.begin_readonly_session() as session:
            route = await self._get_route_by_id(session, route_id, load_endpoint=True)
            if not route or route.endpoint != service_id:
                return None
            data = route.to_data()
        return data

    @model_serving_repository_resilience.apply()
    async def update_route_traffic_force(
        self,
        valkey_live: ValkeyLiveClient,
        route_id: uuid.UUID,
        service_id: uuid.UUID,
        traffic_ratio: float,
    ) -> Optional[EndpointData]:
        """
        Update route traffic ratio without access validation.
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

            endpoint = await self._get_endpoint_by_id(session, service_id, load_routes=True)
            if endpoint is None:
                raise NoResultFound
            data = endpoint.to_data()

            await valkey_live.store_live_data(
                f"endpoint.{service_id}.session.{route.session}.traffic_ratio",
                str(traffic_ratio),
            )
        return data

    @model_serving_repository_resilience.apply()
    async def decrease_endpoint_replicas_force(self, service_id: uuid.UUID) -> bool:
        """
        Decrease endpoint replicas by 1 without access validation.
        Returns True if decreased, False if not found.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, service_id)
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
    async def create_endpoint_token_force(
        self, token_row: EndpointTokenRow
    ) -> Optional[EndpointTokenData]:
        """
        Create endpoint token without access validation.
        Returns token data if created, None if endpoint not found.
        """
        async with self._db.begin_session() as session:
            endpoint = await self._get_endpoint_by_id(session, token_row.endpoint)
            if not endpoint:
                return None

            session.add(token_row)
            await session.commit()
            await session.refresh(token_row)
            data = token_row.to_dataclass()
        return data

    async def _get_endpoint_by_id(
        self,
        session: SASession,
        endpoint_id: uuid.UUID,
        load_routes: bool = False,
        load_session_owner: bool = False,
        load_model: bool = False,
        load_image: bool = False,
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
                load_image=load_image,
            )
        except NoResultFound:
            return None

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

    @model_serving_repository_resilience.apply()
    async def update_endpoint_replicas_force(self, endpoint_id: uuid.UUID, replicas: int) -> bool:
        """
        Update endpoint replicas without access validation.
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
    async def get_auto_scaling_rule_by_id_force(
        self, rule_id: uuid.UUID
    ) -> Optional[EndpointAutoScalingRuleData]:
        """
        Get auto scaling rule by ID without access validation.
        Returns None if rule doesn't exist.
        """
        async with self._db.begin_readonly_session() as session:
            try:
                row = await EndpointAutoScalingRuleRow.get(session, rule_id, load_endpoint=True)
            except ObjectNotFound:
                return None
            return row.to_data()

    @model_serving_repository_resilience.apply()
    async def create_auto_scaling_rule_force(
        self,
        endpoint_id: uuid.UUID,
        metric_source: AutoScalingMetricSource,
        metric_name: str,
        threshold: Any,
        comparator: AutoScalingMetricComparator,
        step_size: int,
        cooldown_seconds: int = 300,
        min_replicas: Optional[int] = None,
        max_replicas: Optional[int] = None,
    ) -> Optional[EndpointAutoScalingRuleData]:
        """
        Create auto scaling rule without access validation.
        Returns the created rule if successful, None if endpoint not found.
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
    async def update_auto_scaling_rule_force(
        self, updater: Updater[EndpointAutoScalingRuleRow]
    ) -> Optional[EndpointAutoScalingRuleData]:
        """
        Update auto scaling rule without access validation.
        Returns the updated rule if successful, None if not found.
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
    async def delete_auto_scaling_rule_force(self, rule_id: uuid.UUID) -> bool:
        """
        Delete auto scaling rule without access validation.
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
    async def search_auto_scaling_rules_force(
        self,
        querier: BatchQuerier,
    ) -> EndpointAutoScalingRuleListResult:
        """
        Search auto scaling rules without access validation.
        Returns all matching rules regardless of ownership.
        """
        async with self._db.begin_readonly_session() as session:
            query = sa.select(EndpointAutoScalingRuleRow)

            result = await execute_batch_querier(session, query, querier)

            items = [row.EndpointAutoScalingRuleRow.to_data() for row in result.rows]

            return EndpointAutoScalingRuleListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

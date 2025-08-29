"""Database source implementation for deployment repository."""

import uuid
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, AsyncIterator, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import sessionmaker

from ai.backend.common.types import SessionId
from ai.backend.manager.data.model_serving.types import EndpointLifecycle, RouteStatus
from ai.backend.manager.models.endpoint import EndpointAutoScalingRuleRow, EndpointRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from ..types import (
    AutoScalingRuleData,
    EndpointCreationArgs,
    EndpointData,
    EndpointWithRoutesData,
    RouteData,
)


@dataclass
class EndpointWithRoutesRawData:
    """Internal data structure for endpoint with routes from database."""

    endpoint_row: EndpointRow
    route_rows: list[RoutingRow]


class DeploymentDBSource:
    """Database source for deployment-related operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @actxmgr
    async def _begin_readonly_read_committed(self) -> AsyncIterator[SAConnection]:
        """
        Begin a read-only connection with READ COMMITTED isolation level.
        """
        async with self._db.connect() as conn:
            # Set isolation level to READ COMMITTED
            conn_with_isolation = await conn.execution_options(
                isolation_level="READ COMMITTED",
                postgresql_readonly=True,
            )
            async with conn_with_isolation.begin():
                yield conn_with_isolation

    @actxmgr
    async def _begin_readonly_session_read_committed(self) -> AsyncIterator[SASession]:
        """
        Begin a read-only session with READ COMMITTED isolation level.
        """
        async with self._db.connect() as conn:
            # Set isolation level to READ COMMITTED and readonly mode
            conn_with_isolation = await conn.execution_options(
                isolation_level="READ COMMITTED",
                postgresql_readonly=True,
            )
            async with conn_with_isolation.begin():
                # Configure session factory with the connection
                sess_factory = sessionmaker(
                    bind=conn_with_isolation,
                    class_=SASession,
                    expire_on_commit=False,
                )
                session = sess_factory()
                yield session

    @actxmgr
    async def _begin_session_read_committed(self) -> AsyncIterator[SASession]:
        """
        Begin a read-write session with READ COMMITTED isolation level.
        """
        async with self._db.connect() as conn:
            # Set isolation level to READ COMMITTED
            conn_with_isolation = await conn.execution_options(isolation_level="READ COMMITTED")
            async with conn_with_isolation.begin():
                # Configure session factory with the connection
                sess_factory = sessionmaker(
                    bind=conn_with_isolation,
                    class_=SASession,
                    expire_on_commit=False,
                )
                session = sess_factory()
                yield session
                await session.commit()

    # Endpoint operations

    async def create_endpoint(
        self,
        args: EndpointCreationArgs,
    ) -> uuid.UUID:
        """Create a new endpoint in the database."""
        endpoint_id = uuid.uuid4()

        async with self._begin_session_read_committed() as db_sess:
            # Extract resource_group from resource_opts if not provided
            resource_group = args.scaling_group or (args.resource_opts or {}).get(
                "scaling_group", "default"
            )

            # Extract resource_slots from resource_opts
            resource_slots = (args.resource_opts or {}).get("resources", {})

            endpoint = EndpointRow(
                id=endpoint_id,
                name=args.name,
                model=args.model_id,
                created_user=args.owner_id,
                session_owner=args.owner_id,  # Also set session_owner
                project=args.group_id,
                domain=args.domain_name,
                resource_group=resource_group,  # Required field
                image=args.image,  # Set the resolved image ID
                lifecycle_stage=EndpointLifecycle.CREATED,
                open_to_public=args.is_public,
                runtime_variant=args.runtime_variant,
                replicas=args.desired_session_count,
                resource_slots=resource_slots,  # Required field
                resource_opts=args.resource_opts or {},
            )
            db_sess.add(endpoint)

        return endpoint_id

    async def get_endpoint(
        self,
        endpoint_id: uuid.UUID,
    ) -> Optional[EndpointData]:
        """Get endpoint by ID."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointRow).where(EndpointRow.id == endpoint_id)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()

            if not row:
                return None

            return EndpointData(
                endpoint_id=row.id,
                name=row.name,
                model_id=row.model,
                owner_id=row.created_user,
                group_id=row.project,
                domain_name=row.domain,
                lifecycle=row.lifecycle_stage,
                is_public=row.open_to_public,
                runtime_variant=row.runtime_variant,
                desired_session_count=row.replicas,
                created_at=row.created_at,
                service_endpoint=row.url,
                resource_opts=row.resource_opts or {},
            )

    async def get_all_active_endpoints(self) -> list[EndpointData]:
        """Get all active endpoints."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            rows = await self._fetch_active_endpoints(db_sess)

        return self._transform_endpoint_rows(rows)

    async def _fetch_active_endpoints(
        self,
        db_sess,
    ) -> list[EndpointRow]:
        """Fetch all active endpoints from database."""
        query = sa.select(EndpointRow).where(
            EndpointRow.lifecycle_stage.in_([
                EndpointLifecycle.CREATED,
                EndpointLifecycle.DESTROYING,
            ])
        )
        result = await db_sess.execute(query)
        return result.scalars().all()

    def _transform_endpoint_rows(
        self,
        rows: list[EndpointRow],
    ) -> list[EndpointData]:
        """Transform endpoint rows to data objects."""
        return [
            EndpointData(
                endpoint_id=row.id,
                name=row.name,
                model_id=row.model,
                owner_id=row.created_user,
                group_id=row.project,
                domain_name=row.domain,
                lifecycle=row.lifecycle_stage,
                is_public=row.open_to_public,
                runtime_variant=row.runtime_variant,
                desired_session_count=row.replicas,
                created_at=row.created_at,
                service_endpoint=row.url,
                resource_opts=row.resource_opts or {},
            )
            for row in rows
        ]

    async def update_endpoint_lifecycle(
        self,
        endpoint_id: uuid.UUID,
        lifecycle: EndpointLifecycle,
    ) -> bool:
        """Update endpoint lifecycle status."""
        async with self._begin_session_read_committed() as db_sess:
            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == endpoint_id)
                .values(lifecycle_stage=lifecycle)
            )
            result = await db_sess.execute(query)
            return result.rowcount > 0

    async def update_endpoint_replicas(
        self,
        endpoint_id: uuid.UUID,
        desired_session_count: int,
    ) -> bool:
        """Update endpoint desired session count."""
        async with self._begin_session_read_committed() as db_sess:
            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == endpoint_id)
                .values(replicas=desired_session_count)
            )
            result = await db_sess.execute(query)
            return result.rowcount > 0

    async def update_endpoint_replicas_and_rebalance(
        self,
        endpoint_id: uuid.UUID,
        target_replicas: int,
    ) -> bool:
        """Update endpoint replicas and rebalance traffic ratios in a single transaction."""
        async with self._begin_session_read_committed() as db_sess:
            # Update endpoint replica count
            updated = await self._update_endpoint_replicas(db_sess, endpoint_id, target_replicas)
            if not updated:
                return False

            # Rebalance traffic ratios for all routes
            await self._rebalance_traffic_ratios(db_sess, endpoint_id, target_replicas)
            return True

    async def _update_endpoint_replicas(
        self,
        db_sess,
        endpoint_id: uuid.UUID,
        target_replicas: int,
    ) -> bool:
        """Private method to update endpoint replicas."""
        query = (
            sa.update(EndpointRow)
            .where(EndpointRow.id == endpoint_id)
            .values(replicas=target_replicas)
        )
        result = await db_sess.execute(query)
        return result.rowcount > 0

    async def _rebalance_traffic_ratios(
        self,
        db_sess,
        endpoint_id: uuid.UUID,
        target_replicas: int,
    ) -> None:
        """Private method to rebalance traffic ratios for all routes."""
        if target_replicas <= 0:
            return

        new_ratio = 1.0 / target_replicas
        query = (
            sa.update(RoutingRow)
            .where(RoutingRow.endpoint == endpoint_id)
            .values(traffic_ratio=new_ratio)
        )
        await db_sess.execute(query)

    async def delete_endpoint_with_routes(
        self,
        endpoint_id: uuid.UUID,
    ) -> bool:
        """Delete an endpoint and all its routes in a single transaction."""
        async with self._begin_session_read_committed() as db_sess:
            # Delete routes first, then endpoint
            deleted = await self._delete_routes_and_endpoint(db_sess, endpoint_id)
            return deleted

    # Route operations

    async def create_route(
        self,
        endpoint_id: uuid.UUID,
        traffic_ratio: float,
    ) -> uuid.UUID:
        """Create a new route for an endpoint."""
        route_id = uuid.uuid4()

        async with self._begin_session_read_committed() as db_sess:
            # First get the endpoint to get owner, domain, and project info
            query = sa.select(EndpointRow).where(EndpointRow.id == endpoint_id)
            result = await db_sess.execute(query)
            endpoint = result.scalar_one_or_none()

            if not endpoint:
                raise ValueError(f"Endpoint {endpoint_id} not found")

            route = RoutingRow(
                id=route_id,
                endpoint=endpoint_id,
                session=None,
                session_owner=endpoint.created_user,
                domain=endpoint.domain,
                project=endpoint.project,
                status=RouteStatus.PROVISIONING,
                traffic_ratio=traffic_ratio,
            )
            db_sess.add(route)

        return route_id

    async def get_routes_by_endpoint(
        self,
        endpoint_id: uuid.UUID,
    ) -> list[RouteData]:
        """Get all routes for an endpoint."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(RoutingRow).where(RoutingRow.endpoint == endpoint_id)
            result = await db_sess.execute(query)
            rows = result.scalars().all()

            return [
                RouteData(
                    route_id=row.id,
                    endpoint_id=row.endpoint,
                    session_id=SessionId(row.session) if row.session else None,
                    status=row.status,
                    traffic_ratio=row.traffic_ratio,
                    created_at=row.created_at,
                    error_data=row.error_data or {},
                )
                for row in rows
            ]

    async def update_route_session(
        self,
        route_id: uuid.UUID,
        session_id: SessionId,
    ) -> bool:
        """Update route with session ID."""
        async with self._begin_session_read_committed() as db_sess:
            query = (
                sa.update(RoutingRow)
                .where(RoutingRow.id == route_id)
                .values(session=session_id, status=RouteStatus.PROVISIONING)
            )
            result = await db_sess.execute(query)
            return result.rowcount > 0

    async def update_route_status(
        self,
        route_id: uuid.UUID,
        status: RouteStatus,
        error_data: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Update route status."""
        async with self._begin_session_read_committed() as db_sess:
            values: dict[str, Any] = {"status": status}
            if error_data is not None:
                values["error_data"] = error_data

            query = sa.update(RoutingRow).where(RoutingRow.id == route_id).values(**values)
            result = await db_sess.execute(query)
            return result.rowcount > 0

    async def update_route_traffic_ratio(
        self,
        route_id: uuid.UUID,
        traffic_ratio: float,
    ) -> bool:
        """Update route traffic ratio."""
        async with self._begin_session_read_committed() as db_sess:
            query = (
                sa.update(RoutingRow)
                .where(RoutingRow.id == route_id)
                .values(traffic_ratio=traffic_ratio)
            )
            result = await db_sess.execute(query)
            return result.rowcount > 0

    async def delete_route(
        self,
        route_id: uuid.UUID,
    ) -> bool:
        """Delete a route."""
        async with self._begin_session_read_committed() as db_sess:
            query = sa.delete(RoutingRow).where(RoutingRow.id == route_id)
            result = await db_sess.execute(query)
            return result.rowcount > 0

    async def _delete_routes_and_endpoint(
        self,
        db_sess,
        endpoint_id: uuid.UUID,
    ) -> bool:
        """Private method to delete routes and endpoint in a single transaction."""
        # First delete all routes for this endpoint
        routes_query = sa.delete(RoutingRow).where(RoutingRow.endpoint == endpoint_id)
        await db_sess.execute(routes_query)

        # Then delete the endpoint itself
        endpoint_query = sa.delete(EndpointRow).where(EndpointRow.id == endpoint_id)
        result = await db_sess.execute(endpoint_query)
        return result.rowcount > 0

    async def get_endpoint_with_routes(
        self,
        endpoint_id: uuid.UUID,
    ) -> Optional[EndpointWithRoutesData]:
        """Get endpoint with all its routes in a single database query."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            # Fetch all data from database in one session
            raw_data = await self._fetch_endpoint_and_routes(db_sess, endpoint_id)

            if not raw_data:
                return None

            # Transform database rows to data objects
            return self._transform_endpoint_and_routes(raw_data)

    async def _fetch_endpoint_and_routes(
        self,
        db_sess,
        endpoint_id: uuid.UUID,
    ) -> Optional[EndpointWithRoutesRawData]:
        """Fetch endpoint and routes from database."""
        # Fetch endpoint
        endpoint_query = sa.select(EndpointRow).where(EndpointRow.id == endpoint_id)
        endpoint_result = await db_sess.execute(endpoint_query)
        endpoint_row = endpoint_result.scalar_one_or_none()

        if not endpoint_row:
            return None

        # Fetch routes for this endpoint
        routes_query = sa.select(RoutingRow).where(RoutingRow.endpoint == endpoint_id)
        routes_result = await db_sess.execute(routes_query)
        route_rows = routes_result.scalars().all()

        return EndpointWithRoutesRawData(
            endpoint_row=endpoint_row,
            route_rows=route_rows,
        )

    def _transform_endpoint_and_routes(
        self,
        raw_data: EndpointWithRoutesRawData,
    ) -> EndpointWithRoutesData:
        """Transform database rows to data objects."""
        endpoint_row = raw_data.endpoint_row
        route_rows = raw_data.route_rows

        endpoint_data = EndpointData(
            endpoint_id=endpoint_row.id,
            name=endpoint_row.name,
            model_id=endpoint_row.model,
            owner_id=endpoint_row.created_user,
            group_id=endpoint_row.project,
            domain_name=endpoint_row.domain,
            lifecycle=endpoint_row.lifecycle_stage,
            is_public=endpoint_row.open_to_public,
            runtime_variant=endpoint_row.runtime_variant,
            desired_session_count=endpoint_row.replicas,
            created_at=endpoint_row.created_at,
            service_endpoint=endpoint_row.url,
            resource_opts=endpoint_row.resource_opts or {},
        )

        routes_data = [
            RouteData(
                route_id=row.id,
                endpoint_id=row.endpoint,
                session_id=SessionId(row.session) if row.session else None,
                status=row.status,
                traffic_ratio=row.traffic_ratio,
                created_at=row.created_at,
                error_data=row.error_data,
            )
            for row in route_rows
        ]

        return EndpointWithRoutesData(
            endpoint=endpoint_data,
            routes=routes_data,
        )

    # Auto-scaling rule operations

    async def create_auto_scaling_rule(
        self,
        endpoint_id: uuid.UUID,
        metric_source: str,
        metric_name: str,
        threshold: str,
        comparator: str,
        step_size: int,
        cooldown_seconds: int,
        min_replicas: Optional[int] = None,
        max_replicas: Optional[int] = None,
    ) -> uuid.UUID:
        """Create a new auto-scaling rule."""
        rule_id = uuid.uuid4()

        async with self._begin_session_read_committed() as db_sess:
            rule = EndpointAutoScalingRuleRow(
                id=rule_id,
                endpoint_id=endpoint_id,
                metric_source=metric_source,
                metric_name=metric_name,
                threshold=Decimal(threshold),
                comparator=comparator,
                step_size=step_size,
                cooldown_seconds=cooldown_seconds,
                min_replicas=min_replicas,
                max_replicas=max_replicas,
            )
            db_sess.add(rule)

        return rule_id

    async def get_auto_scaling_rule(
        self,
        rule_id: uuid.UUID,
    ) -> Optional[AutoScalingRuleData]:
        """Get auto-scaling rule by ID."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointAutoScalingRuleRow).where(
                EndpointAutoScalingRuleRow.id == rule_id
            )
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()

            if not row:
                return None

            return AutoScalingRuleData(
                rule_id=row.id,
                endpoint_id=row.endpoint_id,
                metric_source=row.metric_source,
                metric_name=row.metric_name,
                threshold=row.threshold,
                comparator=row.comparator,
                step_size=row.step_size,
                cooldown_seconds=row.cooldown_seconds,
                min_replicas=row.min_replicas,
                max_replicas=row.max_replicas,
                enabled=row.enabled,
                created_at=row.created_at,
            )

    async def update_auto_scaling_rule(
        self,
        rule_id: uuid.UUID,
        updates: dict[str, Any],
    ) -> bool:
        """Update auto-scaling rule."""
        async with self._begin_session_read_committed() as db_sess:
            query = (
                sa.update(EndpointAutoScalingRuleRow)
                .where(EndpointAutoScalingRuleRow.id == rule_id)
                .values(**updates)
            )
            result = await db_sess.execute(query)
            return result.rowcount > 0

    async def delete_auto_scaling_rule(
        self,
        rule_id: uuid.UUID,
    ) -> bool:
        """Delete an auto-scaling rule."""
        async with self._begin_session_read_committed() as db_sess:
            query = sa.delete(EndpointAutoScalingRuleRow).where(
                EndpointAutoScalingRuleRow.id == rule_id
            )
            result = await db_sess.execute(query)
            return result.rowcount > 0

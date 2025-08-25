"""Database source implementation for deployment repository."""

import uuid
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload, sessionmaker

from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.data.deployment.modifier import DeploymentModifier
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.data.model_serving.types import EndpointLifecycle, RouteStatus
from ai.backend.manager.data.vfolder.types import VFolderLocation
from ai.backend.manager.errors.service import EndpointNotFound, NoUpdatesToApply
from ai.backend.manager.models.endpoint import (
    EndpointRow,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow

from ..types import (
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
        creator: DeploymentCreator,
    ) -> DeploymentInfo:
        """Create a new endpoint in the database and return DeploymentInfo."""
        async with self._begin_session_read_committed() as db_sess:
            endpoint = await EndpointRow.from_deployment_creator(db_sess, creator)
            db_sess.add(endpoint)
            await db_sess.flush()

            # Load image_row relationship for to_deployment_info
            await db_sess.refresh(endpoint, ["image_row"])
            deployment_info = endpoint.to_deployment_info()

        return deployment_info

    async def get_endpoint(
        self,
        endpoint_id: uuid.UUID,
    ) -> DeploymentInfo:
        """Get endpoint by ID.

        Raises:
            EndpointNotFound: If the endpoint does not exist
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select(EndpointRow)
                .where(EndpointRow.id == endpoint_id)
                .options(selectinload(EndpointRow.image_row))
            )
            result = await db_sess.execute(query)
            row: Optional[EndpointRow] = result.scalar_one_or_none()

            if not row:
                raise EndpointNotFound(f"Endpoint {endpoint_id} not found")

            return row.to_deployment_info()

    async def get_all_active_endpoints(self) -> list[DeploymentInfo]:
        """Get all active endpoints."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            rows = await self._fetch_active_endpoints(db_sess)

        return [row.to_deployment_info() for row in rows]

    async def _fetch_active_endpoints(
        self,
        db_sess: SASession,
    ) -> list[EndpointRow]:
        """Fetch all active endpoints from database."""
        from sqlalchemy.orm import selectinload

        query = (
            sa.select(EndpointRow)
            .where(
                EndpointRow.lifecycle_stage.in_([
                    EndpointLifecycle.CREATED,
                    EndpointLifecycle.DESTROYING,
                ])
            )
            .options(selectinload(EndpointRow.image_row))
        )
        result = await db_sess.execute(query)
        return result.scalars().all()

    async def list_endpoints_by_name(
        self,
        session_owner_id: uuid.UUID,
        name: Optional[str] = None,
    ) -> list[DeploymentInfo]:
        """List endpoints owned by a specific user with optional name filter."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            from sqlalchemy.orm import selectinload

            # Build query with base conditions
            query = (
                sa.select(EndpointRow)
                .where(
                    EndpointRow.session_owner == session_owner_id,
                    EndpointRow.lifecycle_stage == EndpointLifecycle.CREATED,
                )
                .options(selectinload(EndpointRow.image_row))
            )

            # Add name filter if provided
            if name is not None:
                query = query.where(EndpointRow.name == name)

            result = await db_sess.execute(query)
            rows = result.scalars().all()

            return [row.to_deployment_info() for row in rows]

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
        db_sess: SASession,
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
        db_sess: SASession,
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

    async def update_endpoint_with_modifier(
        self,
        endpoint_id: uuid.UUID,
        modifier: DeploymentModifier,
    ) -> DeploymentInfo:
        """Update endpoint using a deployment modifier.

        Args:
            endpoint_id: ID of the endpoint to update
            modifier: Deployment modifier containing partial updates

        Returns:
            DeploymentInfo: Updated deployment information

        Raises:
            NoUpdatesToApply: If there are no updates to apply
            EndpointNotFound: If the endpoint does not exist
        """
        # Extract updates from the modifier
        updates = modifier.fields_to_update()

        if not updates:
            raise NoUpdatesToApply(f"No updates to apply for endpoint {endpoint_id}")

        async with self._begin_session_read_committed() as db_sess:
            # Directly use the updates since fields_to_update returns column-ready values
            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == endpoint_id)
                .values(**updates)
                .returning(EndpointRow)
            )
            result = await db_sess.execute(query)
            updated_row = result.scalar_one_or_none()

            if not updated_row:
                raise EndpointNotFound(f"Endpoint {endpoint_id} not found")

            return updated_row.to_deployment_info()

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
        db_sess: SASession,
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
    ) -> EndpointWithRoutesData:
        """Get endpoint with all its routes in a single database query.

        Raises:
            EndpointNotFound: If the endpoint does not exist
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            # Fetch all data from database in one session
            raw_data = await self._fetch_endpoint_and_routes(db_sess, endpoint_id)

            if not raw_data:
                raise EndpointNotFound(f"Endpoint {endpoint_id} not found")

            # Transform database rows to data objects
            return self._transform_endpoint_and_routes(raw_data)

    async def _fetch_endpoint_and_routes(
        self,
        db_sess: SASession,
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

    async def _resolve_group_id(
        self,
        db_sess: SASession,
        domain_name: str,
        group_name: str,
    ) -> Optional[uuid.UUID]:
        """Private method to resolve group ID."""
        from ai.backend.manager.models.group import GroupRow

        query = sa.select(GroupRow.id).where(
            sa.and_(
                GroupRow.domain_name == domain_name,
                GroupRow.name == group_name,
            )
        )
        result = await db_sess.execute(query)
        return result.scalar_one_or_none()

    async def get_vfolder_by_id(
        self,
        vfolder_id: uuid.UUID,
    ) -> Optional[VFolderLocation]:
        """Get vfolder location information by ID.

        Args:
            vfolder_id: ID of the vfolder

        Returns:
            VFolderLocation if found, None otherwise
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(VFolderRow).where(VFolderRow.id == vfolder_id)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()

            if row is None:
                return None

            return VFolderLocation(
                id=row.id,
                quota_scope_id=row.quota_scope_id,
                host=row.host,
            )

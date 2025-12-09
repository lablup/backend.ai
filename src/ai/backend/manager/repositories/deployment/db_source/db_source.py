"""Database source implementation for deployment repository."""

import uuid
from collections import defaultdict
from collections.abc import Mapping, Sequence
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload, sessionmaker

from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.types import (
    MODEL_SERVICE_RUNTIME_PROFILES,
    AccessKey,
    KernelId,
    RuntimeVariant,
    SessionId,
)
from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.data.deployment.modifier import DeploymentModifier
from ai.backend.manager.data.deployment.scale import AutoScalingRule, AutoScalingRuleCreator
from ai.backend.manager.data.deployment.scale_modifier import AutoScalingRuleModifier
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentInfoWithAutoScalingRules,
    EndpointLifecycle,
    RouteInfo,
    RouteStatus,
    ScaleOutDecision,
)
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.vfolder.types import VFolderLocation
from ai.backend.manager.errors.resource import ProjectNotFound, ScalingGroupProxyTargetNotFound
from ai.backend.manager.errors.service import (
    AutoScalingRuleNotFound,
    EndpointNotFound,
    NoUpdatesToApply,
)
from ai.backend.manager.errors.storage import VFolderNotFound
from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    ModelServiceHelper,
)
from ai.backend.manager.models.group import groups
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import scaling_groups
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    ContainerUserContext,
    DeploymentContext,
    ImageContext,
    UserContext,
)
from ai.backend.manager.utils import query_userinfo_from_session

from ..types import (
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
    _storage_manager: StorageSessionManager

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        storage_manager: StorageSessionManager,
    ) -> None:
        self._db = db
        self._storage_manager = storage_manager

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
            await self._check_group_exists(db_sess, creator.domain, creator.project)
            endpoint = await EndpointRow.from_deployment_creator(db_sess, creator)
            db_sess.add(endpoint)
            await db_sess.flush()

            stmt = (
                sa.select(EndpointRow)
                .where(EndpointRow.id == endpoint.id)
                .options(selectinload(EndpointRow.image_row))
            )
            result = await db_sess.execute(stmt)
            endpoint_result: EndpointRow = result.scalar_one()
            deployment_info = endpoint_result.to_deployment_info()
        return deployment_info

    async def _check_group_exists(
        self,
        db_sess: SASession,
        domain_name: str,
        group_id: uuid.UUID,
    ) -> None:
        query = (
            sa.select(groups.c.id)
            .where(
                sa.and_(
                    groups.c.domain_name == domain_name,
                    groups.c.id == group_id,
                )
            )
            .limit(1)
        )

        result = await db_sess.execute(query)
        if result.first() is None:
            raise ProjectNotFound(f"Project {group_id} not found in domain {domain_name}")

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

    async def get_endpoints_by_ids(
        self,
        endpoint_ids: set[uuid.UUID],
    ) -> list[DeploymentInfo]:
        """Get endpoints by their IDs."""
        if not endpoint_ids:
            return []

        async with self._begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select(EndpointRow)
                .where(
                    sa.and_(
                        EndpointRow.id.in_(endpoint_ids),
                        EndpointRow.lifecycle_stage.in_(EndpointLifecycle.active_states()),
                    )
                )
                .options(selectinload(EndpointRow.image_row))
            )
            result = await db_sess.execute(query)
            rows: Sequence[EndpointRow] = result.scalars().all()

            return [row.to_deployment_info() for row in rows]

    async def get_endpoints_by_statuses(
        self, statuses: list[EndpointLifecycle]
    ) -> list[DeploymentInfo]:
        """Get all active endpoints."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            rows = await self._get_endpoints_by_statuses(db_sess, statuses)

        return [row.to_deployment_info() for row in rows]

    async def _get_endpoints_by_statuses(
        self,
        db_sess: SASession,
        statuses: list[EndpointLifecycle],
    ) -> list[EndpointRow]:
        """Fetch endpoints by lifecycle statuses."""
        query = (
            sa.select(EndpointRow)
            .where(EndpointRow.lifecycle_stage.in_(statuses))
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

    async def get_modified_endpoint(
        self,
        endpoint_id: uuid.UUID,
        modifier: DeploymentModifier,
    ) -> DeploymentInfo:
        """Get modified endpoint without applying changes.

        Args:
            endpoint_id: ID of the endpoint to modify
            modifier: Deployment modifier containing partial updates

        Returns:
            DeploymentInfo: Modified deployment information

        Raises:
            EndpointNotFound: If the endpoint does not exist
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            # Fetch existing endpoint
            query = (
                sa.select(EndpointRow)
                .where(EndpointRow.id == endpoint_id)
                .options(selectinload(EndpointRow.image_row))
            )
            result = await db_sess.execute(query)
            existing_row: Optional[EndpointRow] = result.scalar_one_or_none()

            if not existing_row:
                raise EndpointNotFound(f"Endpoint {endpoint_id} not found")

            # Apply modifier to get updated values
            updates = modifier.fields_to_update()
            for field, value in updates.items():
                setattr(existing_row, field, value)
            return existing_row.to_deployment_info()

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

    async def update_endpoint_lifecycle_bulk(
        self,
        endpoint_ids: list[uuid.UUID],
        prevoius_statuses: list[EndpointLifecycle],
        new_status: EndpointLifecycle,
    ) -> None:
        """Update lifecycle status for multiple endpoints."""
        if not endpoint_ids:
            return

        async with self._begin_session_read_committed() as db_sess:
            query = (
                sa.update(EndpointRow)
                .where(
                    sa.and_(
                        EndpointRow.id.in_(endpoint_ids),
                        EndpointRow.lifecycle_stage.in_(prevoius_statuses),
                    )
                )
                .values(lifecycle_stage=new_status)
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

    # AutoScalingRule operations

    async def create_autoscaling_rule(
        self,
        endpoint_id: uuid.UUID,
        creator: AutoScalingRuleCreator,
    ) -> AutoScalingRule:
        """Create a new autoscaling rule for an endpoint."""
        async with self._begin_session_read_committed() as db_sess:
            # First get the endpoint to ensure it exists
            query = sa.select(EndpointRow).where(EndpointRow.id == endpoint_id)
            result = await db_sess.execute(query)
            endpoint = result.scalar_one_or_none()
            if not endpoint:
                raise EndpointNotFound(f"Endpoint {endpoint_id} not found")

            row = EndpointAutoScalingRuleRow.from_creator(endpoint_id=endpoint_id, creator=creator)
            db_sess.add(row)
            await db_sess.flush()
            rule = row.to_autoscaling_rule()
        return rule

    async def list_autoscaling_rules(
        self,
        endpoint_id: uuid.UUID,
    ) -> list[AutoScalingRule]:
        """List all autoscaling rules for an endpoint."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            # First get the endpoint to ensure it exists
            query = sa.select(EndpointRow).where(EndpointRow.id == endpoint_id)
            result = await db_sess.execute(query)
            endpoint = result.scalar_one_or_none()
            if not endpoint:
                raise EndpointNotFound(f"Endpoint {endpoint_id} not found")
            query = sa.select(EndpointAutoScalingRuleRow).where(
                EndpointAutoScalingRuleRow.endpoint == endpoint_id
            )
            result = await db_sess.execute(query)
            rows = result.scalars().all()
            return [row.to_autoscaling_rule() for row in rows]

    async def update_autoscaling_rule(
        self,
        rule_id: uuid.UUID,
        modifier: AutoScalingRuleModifier,
    ) -> AutoScalingRule:
        """Update an existing autoscaling rule."""
        updates = modifier.fields_to_update()

        if not updates:
            raise NoUpdatesToApply(f"No updates to apply for autoscaling rule {rule_id}")

        async with self._begin_session_read_committed() as db_sess:
            query = (
                sa.update(EndpointAutoScalingRuleRow)
                .where(EndpointAutoScalingRuleRow.id == rule_id)
                .values(**updates)
                .returning(EndpointAutoScalingRuleRow)
            )
            result = await db_sess.execute(query)
            updated_row: Optional[EndpointAutoScalingRuleRow] = result.scalar_one_or_none()

            if not updated_row:
                raise AutoScalingRuleNotFound(f"Autoscaling rule {rule_id} not found")
            return updated_row.to_autoscaling_rule()

    async def delete_autoscaling_rule(
        self,
        rule_id: uuid.UUID,
    ) -> bool:
        """Delete an autoscaling rule."""
        async with self._begin_session_read_committed() as db_sess:
            query = sa.delete(EndpointAutoScalingRuleRow).where(
                EndpointAutoScalingRuleRow.id == rule_id
            )
            result = await db_sess.execute(query)
            return result.rowcount > 0

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

    async def get_endpoint_id_by_session(
        self,
        session_id: uuid.UUID,
    ) -> Optional[uuid.UUID]:
        """
        Get endpoint ID associated with a session.

        Args:
            session_id: ID of the session

        Returns:
            Endpoint ID if found, None otherwise
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(RoutingRow.endpoint).where(RoutingRow.session == session_id)
            result = await db_sess.execute(query)
            endpoint_id = result.scalar_one_or_none()
            return endpoint_id

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

    # Additional methods for DeploymentExecutor

    async def get_endpoints_with_autoscaling_rules(
        self,
    ) -> list[DeploymentInfoWithAutoScalingRules]:
        """Get endpoints that have autoscaling rules."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            # Fetch endpoints that have autoscaling rules
            query = (
                sa.select(EndpointRow)
                .where(EndpointRow.lifecycle_stage.in_(EndpointLifecycle.need_scaling_states()))
                .join(
                    EndpointAutoScalingRuleRow,
                    EndpointRow.id == EndpointAutoScalingRuleRow.endpoint_id,
                )
                .distinct()
            )
            endpoint_result = await db_sess.execute(query)
            endpoint_rows: Sequence[EndpointRow] = endpoint_result.scalars().all()
            if not endpoint_rows:
                return []
            # Fetch all rules for these endpoints
            endpoint_ids = [row.id for row in endpoint_rows]
            rules_query = sa.select(EndpointAutoScalingRuleRow).where(
                EndpointAutoScalingRuleRow.endpoint.in_(endpoint_ids)
            )
            rules_result = await db_sess.execute(rules_query)
            rule_rows: Sequence[EndpointAutoScalingRuleRow] = rules_result.scalars().all()

            # Group rules by endpoint
            rules_by_endpoint: dict[uuid.UUID, list[AutoScalingRule]] = {}
            for rule_row in rule_rows:
                if rule_row.endpoint_id not in rules_by_endpoint:
                    rules_by_endpoint[rule_row.endpoint_id] = []
                rules_by_endpoint[rule_row.endpoint_id].append(rule_row.to_autoscaling_rule())

            # Build result
            result = []
            for endpoint_row in endpoint_rows:
                # Convert to DeploymentInfo
                deployment_info = endpoint_row.to_deployment_info()
                rules = rules_by_endpoint.get(endpoint_row.id, [])
                result.append(
                    DeploymentInfoWithAutoScalingRules(
                        deployment_info=deployment_info,
                        rules=rules,
                    )
                )

            return result

    async def batch_update_desired_replicas(
        self,
        updates: dict[uuid.UUID, int],
    ) -> None:
        """Batch update desired replicas for multiple endpoints."""
        if not updates:
            return

        async with self._begin_session_read_committed() as db_sess:
            for endpoint_id, desired_replicas in updates.items():
                query = (
                    sa.update(EndpointRow)
                    .where(
                        sa.and_(
                            EndpointRow.id == endpoint_id,
                            EndpointRow.lifecycle_stage.in_(EndpointLifecycle.active_states()),
                        )
                    )
                    .values(desired_replicas=desired_replicas)
                )
                await db_sess.execute(query)

    async def update_autoscaling_rule_triggered(
        self,
        rule_id: uuid.UUID,
        triggered_at: datetime,
    ) -> bool:
        """Update the last triggered time for an autoscaling rule."""
        async with self._begin_session_read_committed() as db_sess:
            query = (
                sa.update(EndpointAutoScalingRuleRow)
                .where(EndpointAutoScalingRuleRow.id == rule_id)
                .values(last_triggered_at=triggered_at)
            )
            result = await db_sess.execute(query)
            return result.rowcount > 0

    async def fetch_kernels_by_session_ids(
        self,
        session_ids: list[SessionId],
    ) -> list[tuple[KernelId, SessionId]]:
        """Fetch kernel IDs and their session IDs for given sessions.

        Args:
            session_ids: List of session IDs

        Returns:
            List of (kernel_id, session_id) tuples
        """
        if not session_ids:
            return []

        async with self._begin_readonly_session_read_committed() as db_sess:
            from ai.backend.manager.models.kernel import KernelRow

            query = sa.select(
                KernelRow.id,
                KernelRow.session_id,
            ).where(KernelRow.session_id.in_(session_ids))

            result = await db_sess.execute(query)
            return [(KernelId(row[0]), SessionId(row[1])) for row in result]

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
    ) -> VFolderLocation:
        """Get vfolder location information by ID.

        Args:
            vfolder_id: ID of the vfolder

        Returns:
            VFolderLocation if found, None otherwise
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(VFolderRow).where(VFolderRow.id == vfolder_id)
            result = await db_sess.execute(query)
            row: Optional[VFolderRow] = result.scalar_one_or_none()
            if row is None:
                raise VFolderNotFound(f"VFolder {vfolder_id} not found")
            return VFolderLocation(
                id=row.id,
                quota_scope_id=row.quota_scope_id,
                host=row.host,
                ownership_type=row.ownership_type,
            )

    async def fetch_scaling_group_proxy_targets(
        self,
        scaling_group: set[str],
    ) -> Mapping[str, Optional[ScalingGroupProxyTarget]]:
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select([
                    scaling_groups.c.name,
                    scaling_groups.c.wsproxy_addr,
                    scaling_groups.c.wsproxy_api_token,
                ])
                .select_from(scaling_groups)
                .where((scaling_groups.c.name.in_(scaling_group)))
            )
            result = await db_sess.execute(query)
            rows = result.all()
            if not rows:
                raise ScalingGroupProxyTargetNotFound(
                    f"Scaling group proxy target not found for groups: {scaling_group}"
                )
            scaling_group_targets: defaultdict[str, Optional[ScalingGroupProxyTarget]] = (
                defaultdict(lambda: None)
            )
            for row in rows:
                if row.wsproxy_addr is None or row.wsproxy_api_token is None:
                    continue
                scaling_group_targets[row.name] = ScalingGroupProxyTarget(
                    addr=row.wsproxy_addr,
                    api_token=row.wsproxy_api_token,
                )
            return scaling_group_targets

    async def fetch_auto_scaling_rules_by_endpoint_ids(
        self,
        endpoint_ids: set[uuid.UUID],
    ) -> Mapping[uuid.UUID, list[AutoScalingRule]]:
        """Fetch autoscaling rules for given endpoint IDs."""
        if not endpoint_ids:
            return {}

        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointAutoScalingRuleRow).where(
                EndpointAutoScalingRuleRow.endpoint.in_(endpoint_ids)
            )
            result = await db_sess.execute(query)
            rows: Sequence[EndpointAutoScalingRuleRow] = result.scalars().all()

            rules_by_endpoint: defaultdict[uuid.UUID, list[AutoScalingRule]] = defaultdict(list)
            for row in rows:
                if row.endpoint not in rules_by_endpoint:
                    rules_by_endpoint[row.endpoint] = []
                rules_by_endpoint[row.endpoint].append(row.to_autoscaling_rule())

            return rules_by_endpoint

    async def fetch_active_routes_by_endpoint_ids(
        self,
        endpoint_ids: set[uuid.UUID],
    ) -> Mapping[uuid.UUID, list[RouteInfo]]:
        """Fetch routes for given endpoint IDs."""
        if not endpoint_ids:
            return {}

        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(RoutingRow).where(
                sa.and_(
                    RoutingRow.endpoint.in_(endpoint_ids),
                    RoutingRow.status.in_(RouteStatus.active_route_statuses()),
                )
            )
            result = await db_sess.execute(query)
            rows: Sequence[RoutingRow] = result.scalars().all()
            routes_by_endpoint: defaultdict[uuid.UUID, list[RouteInfo]] = defaultdict(list)
            for row in rows:
                if row.endpoint not in routes_by_endpoint:
                    routes_by_endpoint[row.endpoint] = []
                routes_by_endpoint[row.endpoint].append(row.to_route_info())
            return routes_by_endpoint

    async def scale_routes(
        self,
        scale_outs: Sequence[ScaleOutDecision],
        scale_ins: Sequence[RouteInfo],
    ) -> None:
        """Scale out/in routes based on provided mappings."""
        async with self._begin_session_read_committed() as db_sess:
            # Scale out routes
            new_routes = []
            for scale_out in scale_outs:
                for _ in range(scale_out.new_replica_count):
                    route = RoutingRow.by_deployment_info(scale_out.deployment_info)
                    new_routes.append(route)
            db_sess.add_all(new_routes)
            # Scale in routes
            query = (
                sa.update(RoutingRow)
                .where(RoutingRow.id.in_([route.route_id for route in scale_ins]))
                .values(traffic_ratio=0.0, status=RouteStatus.TERMINATING)
            )
            await db_sess.execute(query)

    # Route operations

    async def get_routes_by_statuses(
        self,
        statuses: list[RouteStatus],
    ) -> list[RouteData]:
        """Get routes by their statuses.

        Args:
            statuses: List of route statuses to filter by

        Returns:
            List of RouteData objects matching the statuses
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(RoutingRow).where(RoutingRow.status.in_(statuses))
            result = await db_sess.execute(query)
            rows: Sequence[RoutingRow] = result.scalars().all()

            route_data_list: list[RouteData] = []
            for row in rows:
                route_data = RouteData(
                    route_id=row.id,
                    endpoint_id=row.endpoint,
                    session_id=SessionId(row.session) if row.session else None,
                    status=row.status,
                    traffic_ratio=row.traffic_ratio,
                    created_at=row.created_at,
                    error_data=row.error_data or {},
                )
                route_data_list.append(route_data)

            return route_data_list

    async def update_route_status_bulk(
        self,
        route_ids: set[uuid.UUID],
        previous_statuses: list[RouteStatus],
        new_status: RouteStatus,
    ) -> None:
        """Update status for multiple routes.

        Args:
            route_ids: IDs of routes to update
            previous_statuses: Current statuses to validate against
            new_status: New status to set
        """
        if not route_ids:
            return

        async with self._begin_session_read_committed() as db_sess:
            query = (
                sa.update(RoutingRow)
                .where(
                    sa.and_(
                        RoutingRow.id.in_(route_ids),
                        RoutingRow.status.in_(previous_statuses),
                    )
                )
                .values(status=new_status)
            )
            await db_sess.execute(query)

    async def mark_terminating_route_status_bulk(
        self,
        route_ids: set[uuid.UUID],
    ) -> None:
        """
        Mark routes as TERMINATING.

        Args:
            route_ids: IDs of routes to update
            previous_statuses: Current statuses to validate against
            new_status: New status to set
        """
        if not route_ids:
            return
        async with self._begin_session_read_committed() as db_sess:
            query = (
                sa.update(RoutingRow)
                .where(
                    RoutingRow.id.in_(route_ids),
                )
                .values(status=RouteStatus.TERMINATING)
            )
            await db_sess.execute(query)

    async def update_desired_replicas_bulk(
        self,
        replica_updates: Mapping[uuid.UUID, int],
    ) -> None:
        """Batch update desired replicas for multiple endpoints."""
        if not replica_updates:
            return

        async with self._begin_session_read_committed() as db_sess:
            for endpoint_id, desired_replicas in replica_updates.items():
                query = (
                    sa.update(EndpointRow)
                    .where(
                        sa.and_(
                            EndpointRow.id == endpoint_id,
                            EndpointRow.lifecycle_stage.in_(EndpointLifecycle.active_states()),
                        )
                    )
                    .values(desired_replicas=desired_replicas)
                )
                await db_sess.execute(query)

    async def update_endpoint_urls_bulk(
        self,
        url_updates: Mapping[uuid.UUID, str],
    ) -> None:
        """Batch update endpoint URLs for multiple endpoints.

        Args:
            url_updates: Mapping of endpoint IDs to their registered URLs
        """
        if not url_updates:
            return

        async with self._begin_session_read_committed() as db_sess:
            for endpoint_id, url in url_updates.items():
                query = sa.update(EndpointRow).where(EndpointRow.id == endpoint_id).values(url=url)
                await db_sess.execute(query)

    async def update_route_sessions(
        self,
        route_session_ids: Mapping[uuid.UUID, SessionId],
    ) -> None:
        """Update session IDs for multiple routes.

        Args:
            route_session_ids: Mapping of route IDs to new session IDs
        """
        if not route_session_ids:
            return

        async with self._begin_session_read_committed() as db_sess:
            for route_id, session_id in route_session_ids.items():
                query = (
                    sa.update(RoutingRow)
                    .where(sa.and_(RoutingRow.id == route_id, RoutingRow.session.is_(None)))
                    .values(session=session_id)
                )
                await db_sess.execute(query)

    async def delete_routes_by_route_ids(
        self,
        route_ids: set[uuid.UUID],
    ) -> None:
        """Delete multiple routes by their IDs.

        Args:
            route_ids: Set of route IDs to delete
        """
        if not route_ids:
            return

        async with self._begin_session_read_committed() as db_sess:
            query = sa.delete(RoutingRow).where(
                sa.and_(
                    RoutingRow.id.in_(route_ids),
                    RoutingRow.status == RouteStatus.TERMINATING,
                )
            )
            await db_sess.execute(query)

    async def fetch_deployment_context(
        self,
        deployment_info: DeploymentInfo,
    ) -> DeploymentContext:
        """Fetch all context data needed for session creation from deployment info.

        Args:
            deployment_info: Deployment information

        Returns:
            DeploymentContext: Context data needed for session creation
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            # Fetch created user info
            created_user_query = (
                sa.select(UserRow, keypairs.c.access_key)
                .select_from(sa.join(UserRow, keypairs, UserRow.uuid == keypairs.c.user))
                .where(UserRow.uuid == deployment_info.metadata.created_user)
            )
            created_user_result = await db_sess.execute(created_user_query)
            created_user_row = created_user_result.first()
            if not created_user_row:
                raise ValueError(f"Created user {deployment_info.metadata.created_user} not found")

            # Fetch session owner info if different
            if deployment_info.metadata.session_owner != deployment_info.metadata.created_user:
                session_owner_query = (
                    sa.select(UserRow, keypairs.c.access_key)
                    .select_from(sa.join(UserRow, keypairs, UserRow.uuid == keypairs.c.user))
                    .where(UserRow.uuid == deployment_info.metadata.session_owner)
                )
                session_owner_result = await db_sess.execute(session_owner_query)
                session_owner_row = session_owner_result.first()
                if not session_owner_row:
                    raise ValueError(
                        f"Session owner {deployment_info.metadata.session_owner} not found"
                    )
            else:
                session_owner_row = created_user_row

            # Use query_userinfo_from_session to get group_id and resource_policy
            # This also validates domain, group access permissions
            owner_uuid, group_id, resource_policy = await query_userinfo_from_session(
                db_sess,
                created_user_row.UserRow.uuid,
                AccessKey(created_user_row.access_key),
                created_user_row.UserRow.role,
                created_user_row.UserRow.domain_name,
                None,  # No keypair_resource_policy
                deployment_info.metadata.domain,
                deployment_info.metadata.project,
                query_on_behalf_of=AccessKey(session_owner_row.access_key)
                if session_owner_row != created_user_row
                else None,
            )

            # Resolve image
            target_revision = deployment_info.target_revision()
            if not target_revision:
                raise ValueError("Deployment has no target revision")

            image_row = await ImageRow.resolve(
                db_sess,
                [target_revision.image_identifier],
            )

            # Build DeploymentContext
            return DeploymentContext(
                created_user=UserContext(
                    uuid=created_user_row.UserRow.uuid,
                    access_key=AccessKey(created_user_row.access_key),
                    role=str(created_user_row.UserRow.role),
                    sudo_session_enabled=created_user_row.UserRow.sudo_session_enabled or False,
                ),
                session_owner=UserContext(
                    uuid=session_owner_row.UserRow.uuid,
                    access_key=AccessKey(session_owner_row.access_key),
                    role=str(session_owner_row.UserRow.role),
                    sudo_session_enabled=session_owner_row.UserRow.sudo_session_enabled or False,
                ),
                container_user=ContainerUserContext(
                    uid=session_owner_row.UserRow.container_uid,
                    main_gid=session_owner_row.UserRow.container_main_gid,
                    supplementary_gids=session_owner_row.UserRow.container_gids or [],
                ),
                group_id=group_id,
                resource_policy=dict(resource_policy),
                image=ImageContext(
                    ref=image_row.image_ref,
                    labels=image_row.labels or {},
                ),
            )

    async def fetch_session_statuses_by_route_ids(
        self,
        route_ids: set[uuid.UUID],
    ) -> Mapping[uuid.UUID, Optional[SessionStatus]]:
        """Fetch session statuses for multiple routes.

        Args:
            route_ids: Set of route IDs to fetch session statuses for

        Returns:
            Mapping of route_id to SessionStatus (None if no session)
        """
        if not route_ids:
            return {}

        async with self._begin_readonly_session_read_committed() as db_sess:
            from ai.backend.manager.models.session import SessionRow

            # LEFT JOIN으로 route와 session 정보를 한 번에 가져오기
            query = (
                sa.select(
                    RoutingRow.id,
                    SessionRow.status,
                )
                .select_from(RoutingRow)
                .outerjoin(SessionRow, RoutingRow.session == SessionRow.id)
                .where(RoutingRow.id.in_(route_ids))
            )

            result = await db_sess.execute(query)
            rows = result.all()

            # 결과를 매핑으로 변환
            status_map: dict[uuid.UUID, Optional[SessionStatus]] = {}
            for route_id, session_status in rows:
                status_map[route_id] = session_status

            return status_map

    async def generate_route_connection_info(
        self,
        endpoint_id: uuid.UUID,
    ) -> dict[str, Any]:
        async with self._begin_readonly_session_read_committed() as db_sess:
            endpoint = await EndpointRow.get(
                db_sess,
                endpoint_id,
                load_routes=True,
            )
            if not endpoint:
                raise EndpointNotFound(f"Endpoint {endpoint_id} not found")
            return await endpoint.generate_route_info(db_sess)

    async def get_endpoint_health_check_config(
        self,
        endpoint_id: uuid.UUID,
    ) -> Optional[ModelHealthCheck]:
        async with self._begin_readonly_session_read_committed() as db_sess:
            endpoint = await EndpointRow.get(
                db_sess,
                endpoint_id,
                load_created_user=True,
                load_session_owner=True,
                load_image=True,
                load_routes=True,
            )
            if not endpoint:
                raise EndpointNotFound(str(endpoint_id))

            # Get model vfolder for health check config
            model = await VFolderRow.get(db_sess, endpoint.model)
            if not model:
                return None

            endpoint_data = endpoint.to_data()
            _info: ModelHealthCheck | None = None

            # Check runtime profile for health check endpoint
            if _path := MODEL_SERVICE_RUNTIME_PROFILES[
                endpoint_data.runtime_variant
            ].health_check_endpoint:
                _info = ModelHealthCheck(path=_path)
            elif endpoint_data.runtime_variant == RuntimeVariant.CUSTOM:
                # For custom runtime, check model definition file
                model_definition_path = (
                    await ModelServiceHelper.validate_model_definition_file_exists(
                        self._storage_manager,
                        model.host,
                        model.vfid,
                        endpoint_data.model_definition_path,
                    )
                )
                model_definition = await ModelServiceHelper.validate_model_definition(
                    self._storage_manager,
                    model.host,
                    model.vfid,
                    model_definition_path,
                )

                # Check each model in the definition for health check config
                for model_info in model_definition["models"]:
                    if health_check_info := model_info.get("service", {}).get("health_check"):
                        _info = ModelHealthCheck(
                            path=health_check_info["path"],
                            interval=health_check_info.get("interval"),
                            max_retries=health_check_info.get("max_retries"),
                            max_wait_time=health_check_info.get("max_wait_time"),
                            expected_status_code=health_check_info.get("expected_status_code"),
                        )
                        break

            return _info

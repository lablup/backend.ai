"""Database source implementation for deployment repository."""

import uuid
from collections import Counter, defaultdict
from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload

from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.permission.types import EntityType, FieldType
from ai.backend.common.exception import DeploymentNameAlreadyExists
from ai.backend.common.types import (
    MODEL_SERVICE_RUNTIME_PROFILES,
    AccessKey,
    KernelId,
    RuntimeVariant,
    SessionId,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.deployment.creator import DeploymentPolicyConfig
from ai.backend.manager.data.deployment.scale import (
    AutoScalingRule,
    AutoScalingRuleCreator,
    ModelDeploymentAutoScalingRuleCreator,
)
from ai.backend.manager.data.deployment.scale_modifier import (
    AutoScalingRuleModifier,
    ModelDeploymentAutoScalingRuleModifier,
)
from ai.backend.manager.data.deployment.types import (
    AccessTokenSearchResult,
    AutoScalingRuleSearchResult,
    DeploymentInfo,
    DeploymentInfoSearchResult,
    DeploymentInfoWithAutoScalingRules,
    DeploymentPolicySearchResult,
    ModelDeploymentAccessTokenData,
    ModelDeploymentAutoScalingRuleData,
    ModelRevisionData,
    RevisionSearchResult,
    RouteInfo,
    RouteSearchResult,
    RouteStatus,
    ScalingGroupCleanupConfig,
)
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.vfolder.types import VFolderLocation
from ai.backend.manager.errors.deployment import (
    DeploymentHasNoTargetRevision,
    DeploymentRevisionNotFound,
    UserNotFoundInDeployment,
)
from ai.backend.manager.errors.resource import ProjectNotFound, ScalingGroupProxyTargetNotFound
from ai.backend.manager.errors.service import (
    AutoScalingPolicyNotFound,
    AutoScalingRuleNotFound,
    DeploymentPolicyNotFound,
    EndpointNotFound,
    NoUpdatesToApply,
)
from ai.backend.manager.errors.storage import VFolderNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyData,
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import (
    DeploymentPolicyData,
    DeploymentPolicyRow,
)
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
    ModelServiceHelper,
)
from ai.backend.manager.models.group import GroupRow, groups
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow, scaling_groups
from ai.backend.manager.models.scheduling_history import (
    DeploymentHistoryRow,
    RouteHistoryRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    execute_batch_querier,
    execute_creator,
)
from ai.backend.manager.repositories.base.creator import (
    BulkCreator,
)
from ai.backend.manager.repositories.base.purger import (
    Purger,
    PurgerResult,
    execute_purger,
)
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACEntityCreator,
    execute_rbac_entity_creator,
)
from ai.backend.manager.repositories.base.rbac.field_creator import (
    RBACFieldCreator,
    execute_rbac_field_creator,
)
from ai.backend.manager.repositories.base.updater import (
    BatchUpdater,
    Updater,
    execute_batch_updater,
    execute_updater,
)
from ai.backend.manager.repositories.deployment.creators import (
    DeploymentCreatorSpec,
    DeploymentPolicyCreatorSpec,
    DeploymentRevisionCreatorSpec,
)
from ai.backend.manager.repositories.deployment.creators.endpoint import LegacyEndpointCreatorSpec
from ai.backend.manager.repositories.deployment.types import (
    RouteData,
    RouteServiceDiscoveryInfo,
)
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    ContainerUserContext,
    DeploymentContext,
    ImageContext,
    UserContext,
)
from ai.backend.manager.utils import query_userinfo_from_session


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
                sess_factory = async_sessionmaker(
                    bind=conn_with_isolation,
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
                sess_factory = async_sessionmaker(
                    bind=conn_with_isolation,
                    expire_on_commit=False,
                )
                session = sess_factory()
                yield session
                await session.commit()

    # Endpoint operations

    async def create_endpoint(
        self,
        creator: RBACEntityCreator[EndpointRow],
        policy_config: DeploymentPolicyConfig | None = None,
    ) -> DeploymentInfo:
        """Create a new endpoint in the database and return DeploymentInfo.

        Args:
            creator: Creator containing DeploymentCreatorSpec with resolved image_id
            policy_config: Optional deployment policy configuration

        Returns:
            DeploymentInfo for the created endpoint
        """
        spec = cast(DeploymentCreatorSpec, creator.spec)
        async with self._begin_session_read_committed() as db_sess:
            await self._check_group_exists(db_sess, spec.metadata.domain, spec.metadata.project_id)
            await self._check_endpoint_name_exists(
                db_sess, spec.metadata.domain, spec.metadata.project_id, spec.metadata.name
            )

            # Create endpoint with RBAC scope association
            rbac_result = await execute_rbac_entity_creator(db_sess, creator)
            endpoint = rbac_result.row

            # Create deployment policy if provided
            if policy_config is not None:
                policy_spec = DeploymentPolicyCreatorSpec(
                    endpoint_id=endpoint.id,
                    strategy=policy_config.strategy,
                    strategy_spec=policy_config.strategy_spec,
                    rollback_on_failure=policy_config.rollback_on_failure,
                )
                policy_row = policy_spec.build_row()
                db_sess.add(policy_row)
                await db_sess.flush()

            stmt = (
                sa.select(EndpointRow)
                .where(EndpointRow.id == endpoint.id)
                .options(selectinload(EndpointRow.image_row))
            )
            result = await db_sess.execute(stmt)
            endpoint_result: EndpointRow = result.scalar_one()
            return endpoint_result.to_deployment_info()

    async def create_endpoint_legacy(
        self,
        creator: RBACEntityCreator[EndpointRow],
    ) -> DeploymentInfo:
        """Create a new endpoint using legacy DeploymentCreator.

        This is for backward compatibility with legacy deployment creation flow.

        Args:
            creator: RBACEntityCreator with LegacyEndpointCreatorSpec.
                The spec MUST be an instance of LegacyEndpointCreatorSpec.

        Returns:
            DeploymentInfo for the created endpoint
        """
        spec = cast(LegacyEndpointCreatorSpec, creator.spec)
        async with self._begin_session_read_committed() as db_sess:
            await self._check_group_exists(db_sess, spec.domain, spec.project)
            await self._check_endpoint_name_exists(db_sess, spec.domain, spec.project, spec.name)

            # Create endpoint with RBAC scope association
            rbac_result = await execute_rbac_entity_creator(db_sess, creator)
            endpoint = rbac_result.row

            # Create deployment policy if provided
            if spec.policy is not None:
                policy_row = spec.policy.build_row()
                db_sess.add(policy_row)
                await db_sess.flush()

            stmt = (
                sa.select(EndpointRow)
                .where(EndpointRow.id == endpoint.id)
                .options(selectinload(EndpointRow.image_row))
            )
            result = await db_sess.execute(stmt)
            endpoint_result: EndpointRow = result.scalar_one()
            return endpoint_result.to_deployment_info()

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

    async def _check_endpoint_name_exists(
        self,
        db_sess: SASession,
        domain_name: str,
        project_id: uuid.UUID,
        name: str,
    ) -> None:
        """Check if endpoint name already exists in the project.

        Raises:
            DeploymentNameAlreadyExists: If an endpoint with the same name exists.
        """
        query = (
            sa.select(EndpointRow.id)
            .where(
                sa.and_(
                    EndpointRow.domain == domain_name,
                    EndpointRow.project == project_id,
                    EndpointRow.name == name,
                    EndpointRow.lifecycle_stage != EndpointLifecycle.DESTROYED,
                )
            )
            .limit(1)
        )
        result = await db_sess.execute(query)
        if result.first() is not None:
            raise DeploymentNameAlreadyExists(
                f"Deployment with name '{name}' already exists in this project"
            )

    async def get_image_id(self, image: ImageIdentifier) -> uuid.UUID:
        """Get image ID from ImageIdentifier.

        Args:
            image: ImageIdentifier containing canonical and architecture

        Returns:
            UUID of the image
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            image_row = await ImageRow.lookup(db_sess, image)
            return image_row.id

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
                .options(
                    selectinload(EndpointRow.image_row),
                    selectinload(EndpointRow.revisions).selectinload(
                        DeploymentRevisionRow.image_row
                    ),
                )
            )
            result = await db_sess.execute(query)
            row: EndpointRow | None = result.scalar_one_or_none()

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
                .options(
                    selectinload(EndpointRow.image_row),
                    selectinload(EndpointRow.revisions).selectinload(
                        DeploymentRevisionRow.image_row
                    ),
                )
            )
            result = await db_sess.execute(query)
            rows: Sequence[EndpointRow] = result.scalars().all()

            return [row.to_deployment_info() for row in rows]

    async def get_scaling_group_cleanup_configs(
        self, scaling_group_names: Sequence[str]
    ) -> dict[str, ScalingGroupCleanupConfig]:
        """
        Get route cleanup target statuses configuration for scaling groups.

        Args:
            scaling_group_names: List of scaling group names to query

        Returns:
            Mapping of scaling group name to ScalingGroupCleanupConfig
        """
        if not scaling_group_names:
            return {}

        async with self._db.begin_readonly_session_read_committed() as db_sess:
            stmt = sa.select(ScalingGroupRow.name, ScalingGroupRow.scheduler_opts).where(
                ScalingGroupRow.name.in_(scaling_group_names)
            )
            result = await db_sess.execute(stmt)

            cleanup_configs: dict[str, ScalingGroupCleanupConfig] = {}
            for row in result:
                # Convert str to RouteStatus
                status_strs = row.scheduler_opts.route_cleanup_target_statuses
                statuses = []
                for status_str in status_strs:
                    try:
                        statuses.append(RouteStatus(status_str))
                    except ValueError:
                        # Skip invalid status strings
                        pass

                cleanup_configs[row.name] = ScalingGroupCleanupConfig(
                    scaling_group_name=row.name, cleanup_target_statuses=statuses
                )

            return cleanup_configs

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
            .options(
                selectinload(EndpointRow.image_row),
                selectinload(EndpointRow.revisions).selectinload(DeploymentRevisionRow.image_row),
            )
        )
        result = await db_sess.execute(query)
        return list(result.scalars().all())

    async def list_endpoints_by_name(
        self,
        session_owner_id: uuid.UUID,
        name: str | None = None,
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
            return cast(CursorResult[Any], result).rowcount > 0

    async def get_modified_endpoint(
        self,
        endpoint_id: uuid.UUID,
        updater: Updater[EndpointRow],
    ) -> DeploymentInfo:
        """Get modified endpoint without applying changes.

        Args:
            endpoint_id: ID of the endpoint to modify
            updater: Updater containing spec with partial updates

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
            existing_row: EndpointRow | None = result.scalar_one_or_none()

            if not existing_row:
                raise EndpointNotFound(f"Endpoint {endpoint_id} not found")

            # Apply spec to get updated values
            updater.spec.apply_to_row(existing_row)
            return existing_row.to_deployment_info()

    async def update_endpoint_with_spec(
        self,
        updater: Updater[EndpointRow],
    ) -> DeploymentInfo:
        """Update endpoint using an Updater.

        Args:
            updater: Updater containing spec and endpoint_id

        Returns:
            DeploymentInfo: Updated deployment information

        Raises:
            EndpointNotFound: If the endpoint does not exist
        """
        async with self._begin_session_read_committed() as db_sess:
            result = await execute_updater(db_sess, updater)
            if result is None:
                raise EndpointNotFound(f"Endpoint {updater.pk_value} not found")
            return result.row.to_deployment_info()

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

    async def update_endpoint_lifecycle_bulk_with_history(
        self,
        batch_updaters: Sequence[BatchUpdater[EndpointRow]],
        bulk_creator: BulkCreator[DeploymentHistoryRow],
    ) -> int:
        """Update lifecycle status and record history in same transaction.

        All batch updates and history creations are executed atomically
        in a single transaction. Uses merge logic to prevent duplicate
        history records when phase, error_code, and to_status match.

        Args:
            batch_updaters: Sequence of BatchUpdaters for status updates
            bulk_creator: BulkCreator containing all history records

        Returns:
            Total number of rows updated
        """
        if not batch_updaters:
            return 0

        async with self._begin_session_read_committed() as db_sess:
            total_updated = 0
            # 1. Execute all status updates
            for batch_updater in batch_updaters:
                update_result = await execute_batch_updater(db_sess, batch_updater)
                total_updated += update_result.updated_count

            if not bulk_creator.specs:
                return total_updated

            # 2. Build rows from specs
            new_rows = [spec.build_row() for spec in bulk_creator.specs]
            deployment_ids = [row.deployment_id for row in new_rows]

            # 3. Get last history records for all deployments
            last_records = await self._get_last_deployment_histories_bulk(db_sess, deployment_ids)

            # 4. Separate rows into merge and create groups
            merge_ids: list[uuid.UUID] = []
            create_rows: list[DeploymentHistoryRow] = []

            for new_row in new_rows:
                last_row = last_records.get(new_row.deployment_id)

                if last_row is not None and last_row.should_merge_with(new_row):
                    merge_ids.append(last_row.id)
                else:
                    create_rows.append(new_row)

            # 5. Batch update attempts for merge group
            if merge_ids:
                await db_sess.execute(
                    sa.update(DeploymentHistoryRow)
                    .where(DeploymentHistoryRow.id.in_(merge_ids))
                    .values(attempts=DeploymentHistoryRow.attempts + 1)
                )

            # 6. Batch insert for create group
            if create_rows:
                db_sess.add_all(create_rows)
                await db_sess.flush()

            return total_updated

    async def _get_last_deployment_histories_bulk(
        self,
        db_sess: SASession,
        deployment_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, DeploymentHistoryRow]:
        """Get last history records for multiple deployments efficiently."""
        if not deployment_ids:
            return {}

        # Use DISTINCT ON to get latest record per deployment
        query = (
            sa.select(DeploymentHistoryRow)
            .where(DeploymentHistoryRow.deployment_id.in_(deployment_ids))
            .distinct(DeploymentHistoryRow.deployment_id)
            .order_by(
                DeploymentHistoryRow.deployment_id,
                DeploymentHistoryRow.created_at.desc(),
            )
        )
        result = await db_sess.execute(query)
        rows = result.scalars().all()
        return {row.deployment_id: row for row in rows}

    async def delete_endpoint_with_routes(
        self,
        endpoint_id: uuid.UUID,
    ) -> bool:
        """Delete an endpoint and all its routes in a single transaction."""
        async with self._begin_session_read_committed() as db_sess:
            # Delete routes first, then endpoint
            return await self._delete_routes_and_endpoint(db_sess, endpoint_id)

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
            return row.to_autoscaling_rule()

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
            updated_row: EndpointAutoScalingRuleRow | None = result.scalar_one_or_none()

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
            return cast(CursorResult[Any], result).rowcount > 0

    # New Model Deployment Auto-scaling Rule methods (using new types)

    async def create_model_deployment_autoscaling_rule(
        self,
        creator: ModelDeploymentAutoScalingRuleCreator,
    ) -> ModelDeploymentAutoScalingRuleData:
        """Create a new autoscaling rule using ModelDeployment types."""
        async with self._begin_session_read_committed() as db_sess:
            # First get the endpoint to ensure it exists
            query = sa.select(EndpointRow).where(EndpointRow.id == creator.model_deployment_id)
            result = await db_sess.execute(query)
            endpoint = result.scalar_one_or_none()
            if not endpoint:
                raise EndpointNotFound(f"Endpoint {creator.model_deployment_id} not found")

            row = EndpointAutoScalingRuleRow.from_model_deployment_creator(creator)
            db_sess.add(row)
            await db_sess.flush()
            return row.to_model_deployment_data()

    async def update_model_deployment_autoscaling_rule(
        self,
        rule_id: uuid.UUID,
        modifier: ModelDeploymentAutoScalingRuleModifier,
    ) -> ModelDeploymentAutoScalingRuleData:
        """Update an autoscaling rule using ModelDeployment types."""
        async with self._begin_session_read_committed() as db_sess:
            query = sa.select(EndpointAutoScalingRuleRow).where(
                EndpointAutoScalingRuleRow.id == rule_id
            )
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()

            if not row:
                raise AutoScalingRuleNotFound(f"Autoscaling rule {rule_id} not found")

            row.apply_model_deployment_modifier(modifier)
            await db_sess.flush()
            return row.to_model_deployment_data()

    async def list_model_deployment_autoscaling_rules(
        self,
        endpoint_id: uuid.UUID,
    ) -> list[ModelDeploymentAutoScalingRuleData]:
        """List all autoscaling rules for an endpoint using ModelDeployment types."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointAutoScalingRuleRow).where(
                EndpointAutoScalingRuleRow.endpoint == endpoint_id
            )
            result = await db_sess.execute(query)
            rows = result.scalars().all()
            return [row.to_model_deployment_data() for row in rows]

    async def get_model_deployment_autoscaling_rule(
        self,
        rule_id: uuid.UUID,
    ) -> ModelDeploymentAutoScalingRuleData:
        """Get a single autoscaling rule by ID using ModelDeployment types."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointAutoScalingRuleRow).where(
                EndpointAutoScalingRuleRow.id == rule_id
            )
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if not row:
                raise AutoScalingRuleNotFound(f"Autoscaling rule {rule_id} not found")
            return row.to_model_deployment_data()

    # Route operations

    async def create_route(
        self,
        creator: Creator[RoutingRow],
    ) -> uuid.UUID:
        """Create a new route using the provided creator.

        The Creator is built at the upper layer (service/action) and injected here.
        This method only executes the creator.
        """
        async with self._begin_session_read_committed() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.id

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
                    created_at=row.created_at or datetime.now(tz=UTC),
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
            return cast(CursorResult[Any], result).rowcount > 0

    async def update_route(
        self,
        updater: Updater[RoutingRow],
    ) -> bool:
        """Update a route using the provided updater.

        The Updater is built at the upper layer (service/action) and injected here.
        This method only executes the updater.
        """
        async with self._begin_session_read_committed() as db_sess:
            result = await execute_updater(db_sess, updater)
            return result is not None

    async def update_route_status(
        self,
        route_id: uuid.UUID,
        status: RouteStatus,
        error_data: dict[str, Any] | None = None,
    ) -> bool:
        """Update route status."""
        async with self._begin_session_read_committed() as db_sess:
            values: dict[str, Any] = {"status": status}
            if error_data is not None:
                values["error_data"] = error_data

            query = sa.update(RoutingRow).where(RoutingRow.id == route_id).values(**values)
            result = await db_sess.execute(query)
            return cast(CursorResult[Any], result).rowcount > 0

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
            return cast(CursorResult[Any], result).rowcount > 0

    async def delete_route(
        self,
        route_id: uuid.UUID,
    ) -> bool:
        """Delete a route."""
        async with self._begin_session_read_committed() as db_sess:
            query = sa.delete(RoutingRow).where(RoutingRow.id == route_id)
            result = await db_sess.execute(query)
            return cast(CursorResult[Any], result).rowcount > 0

    async def search_routes(
        self,
        querier: BatchQuerier,
    ) -> RouteSearchResult:
        """Search routes with pagination and filtering.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination

        Returns:
            RouteSearchResult with items, total_count, and pagination info
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(RoutingRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.RoutingRow.to_route_info() for row in result.rows]

            return RouteSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def get_route(
        self,
        route_id: uuid.UUID,
    ) -> RouteInfo | None:
        """Get a route by ID.

        Args:
            route_id: ID of the route (replica)

        Returns:
            RouteInfo if found, None otherwise
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(RoutingRow).where(RoutingRow.id == route_id)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return row.to_route_info()

    async def search_endpoints(
        self,
        querier: BatchQuerier,
    ) -> DeploymentInfoSearchResult:
        """Search endpoints with pagination and filtering.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination

        Returns:
            DeploymentInfoSearchResult with items, total_count, and pagination info
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointRow).options(selectinload(EndpointRow.revisions))

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.EndpointRow.to_deployment_info() for row in result.rows]

            return DeploymentInfoSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def get_endpoint_id_by_session(
        self,
        session_id: uuid.UUID,
    ) -> uuid.UUID | None:
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
            return result.scalar_one_or_none()

    async def fetch_route_service_discovery_info(
        self,
        route_ids: set[uuid.UUID],
    ) -> list[RouteServiceDiscoveryInfo]:
        """Fetch service discovery information for routes.

        Joins routes with kernels and endpoints to get all necessary information
        for service discovery registration (kernel host/port, endpoint name, etc).

        Args:
            route_ids: Set of route IDs to fetch information for

        Returns:
            List of RouteServiceDiscoveryInfo containing kernel host/port and endpoint details
        """
        if not route_ids:
            return []

        async with self._begin_readonly_session_read_committed() as db_sess:
            # Join route -> session -> kernel -> endpoint to get all needed info
            query = (
                sa.select(
                    RoutingRow.id.label("route_id"),
                    RoutingRow.endpoint.label("endpoint_id"),
                    EndpointRow.name.label("endpoint_name"),
                    EndpointRow.runtime_variant.label("runtime_variant"),
                    KernelRow.kernel_host,
                    KernelRow.service_ports,
                )
                .select_from(RoutingRow)
                .join(EndpointRow, RoutingRow.endpoint == EndpointRow.id)
                .join(
                    KernelRow,
                    sa.and_(
                        KernelRow.session_id == RoutingRow.session,
                        KernelRow.cluster_role == "main",
                    ),
                )
                .where(RoutingRow.id.in_(route_ids))
            )

            result = await db_sess.execute(query)
            rows = result.all()

            # Process results
            discovery_infos: list[RouteServiceDiscoveryInfo] = []
            for row in rows:
                # Extract inference port from service_ports
                inference_port: int | None = None
                if row.service_ports:
                    for port_info in row.service_ports:
                        if port_info.get("is_inference", False):
                            host_ports = port_info.get("host_ports", [])
                            if host_ports:
                                inference_port = host_ports[0]
                            break

                if not inference_port:
                    # Skip routes without inference port
                    continue

                discovery_infos.append(
                    RouteServiceDiscoveryInfo(
                        route_id=row.route_id,
                        endpoint_id=row.endpoint_id,
                        endpoint_name=row.endpoint_name,
                        runtime_variant=row.runtime_variant.value,
                        kernel_host=row.kernel_host,
                        kernel_port=inference_port,
                    )
                )

            return discovery_infos

    async def _delete_routes_and_endpoint(
        self,
        db_sess: SASession,
        endpoint_id: uuid.UUID,
    ) -> bool:
        """Private method to delete routes, policy, and endpoint in a single transaction."""
        # First delete all routes for this endpoint
        routes_query = sa.delete(RoutingRow).where(RoutingRow.endpoint == endpoint_id)
        await db_sess.execute(routes_query)

        # Delete the deployment policy if exists
        policy_query = sa.delete(DeploymentPolicyRow).where(
            DeploymentPolicyRow.endpoint == endpoint_id
        )
        await db_sess.execute(policy_query)

        # Then delete the endpoint itself
        endpoint_query = sa.delete(EndpointRow).where(EndpointRow.id == endpoint_id)
        result = await db_sess.execute(endpoint_query)
        return cast(CursorResult[Any], result).rowcount > 0

    async def _fetch_endpoint_and_routes(
        self,
        db_sess: SASession,
        endpoint_id: uuid.UUID,
    ) -> EndpointWithRoutesRawData | None:
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
            route_rows=list(route_rows),
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
            return cast(CursorResult[Any], result).rowcount > 0

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
    ) -> uuid.UUID | None:
        """Private method to resolve group ID."""
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
            row: VFolderRow | None = result.scalar_one_or_none()
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
    ) -> Mapping[str, ScalingGroupProxyTarget | None]:
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select(
                    scaling_groups.c.name,
                    scaling_groups.c.wsproxy_addr,
                    scaling_groups.c.wsproxy_api_token,
                )
                .select_from(scaling_groups)
                .where(scaling_groups.c.name.in_(scaling_group))
            )
            result = await db_sess.execute(query)
            rows = result.all()
            if not rows:
                raise ScalingGroupProxyTargetNotFound(
                    f"Scaling group proxy target not found for groups: {scaling_group}"
                )
            scaling_group_targets: defaultdict[str, ScalingGroupProxyTarget | None] = defaultdict(
                lambda: None
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
        scale_out_creators: Sequence[Creator[RoutingRow]],
        scale_in_updater: BatchUpdater[RoutingRow] | None,
    ) -> None:
        """Scale out/in routes based on provided creators and updater."""
        async with self._begin_session_read_committed() as db_sess:
            # Scale out routes
            for creator in scale_out_creators:
                await execute_creator(db_sess, creator)
            # Scale in routes
            if scale_in_updater:
                await execute_batch_updater(db_sess, scale_in_updater)

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
                    created_at=row.created_at or datetime.now(tz=UTC),
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

    async def update_route_status_bulk_with_history(
        self,
        batch_updaters: Sequence[BatchUpdater[RoutingRow]],
        bulk_creator: BulkCreator[RouteHistoryRow],
    ) -> int:
        """Update route status and record history in same transaction.

        All batch updates and history creations are executed atomically
        in a single transaction. Uses merge logic to prevent duplicate
        history records when phase, error_code, and to_status match.

        Args:
            batch_updaters: Sequence of BatchUpdaters for status updates
            bulk_creator: BulkCreator containing all history records

        Returns:
            Total number of rows updated
        """
        if not batch_updaters:
            return 0

        async with self._begin_session_read_committed() as db_sess:
            total_updated = 0
            # 1. Execute all status updates
            for batch_updater in batch_updaters:
                update_result = await execute_batch_updater(db_sess, batch_updater)
                total_updated += update_result.updated_count

            if not bulk_creator.specs:
                return total_updated

            # 2. Build rows from specs
            new_rows = [spec.build_row() for spec in bulk_creator.specs]
            route_ids = [row.route_id for row in new_rows]

            # 3. Get last history records for all routes
            last_records = await self._get_last_route_histories_bulk(db_sess, route_ids)

            # 4. Separate rows into merge and create groups
            merge_ids: list[uuid.UUID] = []
            create_rows: list[RouteHistoryRow] = []

            for new_row in new_rows:
                last_row = last_records.get(new_row.route_id)

                if last_row is not None and last_row.should_merge_with(new_row):
                    merge_ids.append(last_row.id)
                else:
                    create_rows.append(new_row)

            # 5. Batch update attempts for merge group
            if merge_ids:
                await db_sess.execute(
                    sa.update(RouteHistoryRow)
                    .where(RouteHistoryRow.id.in_(merge_ids))
                    .values(attempts=RouteHistoryRow.attempts + 1)
                )

            # 6. Batch insert for create group
            if create_rows:
                db_sess.add_all(create_rows)
                await db_sess.flush()

            return total_updated

    async def _get_last_route_histories_bulk(
        self,
        db_sess: SASession,
        route_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, RouteHistoryRow]:
        """Get last history records for multiple routes efficiently."""
        if not route_ids:
            return {}

        # Use DISTINCT ON to get latest record per route
        query = (
            sa.select(RouteHistoryRow)
            .where(RouteHistoryRow.route_id.in_(route_ids))
            .distinct(RouteHistoryRow.route_id)
            .order_by(
                RouteHistoryRow.route_id,
                RouteHistoryRow.created_at.desc(),
            )
        )
        result = await db_sess.execute(query)
        rows = result.scalars().all()
        return {row.route_id: row for row in rows}

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
                raise UserNotFoundInDeployment(
                    f"Created user {deployment_info.metadata.created_user} not found"
                )

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
                    raise UserNotFoundInDeployment(
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
                raise DeploymentHasNoTargetRevision("Deployment has no target revision")

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
    ) -> Mapping[uuid.UUID, SessionStatus | None]:
        """Fetch session statuses for multiple routes.

        Args:
            route_ids: Set of route IDs to fetch session statuses for

        Returns:
            Mapping of route_id to SessionStatus (None if no session)
        """
        if not route_ids:
            return {}

        async with self._begin_readonly_session_read_committed() as db_sess:
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
            status_map: dict[uuid.UUID, SessionStatus | None] = {}
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
    ) -> ModelHealthCheck | None:
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
            if endpoint.model is None:
                return None
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
                            initial_delay=health_check_info.get("initial_delay"),
                        )
                        break

            return _info

    async def get_default_architecture_from_scaling_group(
        self, scaling_group_name: str
    ) -> str | None:
        """
        Get the default (most common) architecture from active agents in a scaling group.
        Returns None if no active agents exist.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            query = sa.select(AgentRow.architecture).where(
                sa.and_(
                    AgentRow.scaling_group == scaling_group_name,
                    AgentRow.status == AgentStatus.ALIVE,
                    AgentRow.schedulable == sa.true(),
                )
            )
            result = await session.execute(query)
            architectures = [row.architecture for row in result]

            if not architectures:
                return None

            architecture_counts = Counter(architectures)
            most_common_architecture, _ = architecture_counts.most_common(1)[0]
            return cast(str, most_common_architecture)

    # Deployment Revision Methods

    async def get_latest_revision_number(
        self,
        endpoint_id: uuid.UUID,
    ) -> int | None:
        """Get the latest revision number for an endpoint.

        Returns None if no revisions exist for the endpoint.
        Service layer should call this to calculate next revision_number.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(sa.func.max(DeploymentRevisionRow.revision_number)).where(
                DeploymentRevisionRow.endpoint == endpoint_id
            )
            result = await db_sess.execute(query)
            return result.scalar()

    async def create_revision(
        self,
        creator: Creator[DeploymentRevisionRow],
    ) -> ModelRevisionData:
        """Create a new deployment revision for an endpoint.

        The Creator must contain a spec with revision_number already set.
        Service layer should calculate revision_number using get_latest_revision_number()
        before calling this method.

        If a unique constraint violation occurs, the caller should retry.

        TODO: Implement revision history pruning (similar to K8s revisionHistoryLimit).
        After creating a new revision, old revisions beyond the limit should be deleted.
        This requires adding a `revision_history_limit` column to EndpointRow.
        """
        async with self._begin_session_read_committed() as db_sess:
            spec = cast(DeploymentRevisionCreatorSpec, creator.spec)

            rbac_creator: RBACFieldCreator[DeploymentRevisionRow] = RBACFieldCreator(
                spec=spec,
                entity_type=EntityType.MODEL_DEPLOYMENT,
                entity_id=str(spec.endpoint_id),
                field_type=FieldType.MODEL_REVISION,
            )
            rbac_result = await execute_rbac_field_creator(db_sess, rbac_creator)
            return rbac_result.row.to_data()

    async def get_revision(
        self,
        revision_id: uuid.UUID,
    ) -> ModelRevisionData:
        """Get a deployment revision by ID.

        Raises:
            DeploymentRevisionNotFound: If the revision does not exist.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(DeploymentRevisionRow).where(DeploymentRevisionRow.id == revision_id)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise DeploymentRevisionNotFound(f"Deployment revision {revision_id} not found")
            return row.to_data()

    async def get_revision_by_route_id(
        self,
        route_id: uuid.UUID,
    ) -> ModelRevisionData:
        """Get a deployment revision by route (replica) ID.

        Args:
            route_id: ID of the route (replica)

        Raises:
            RouteNotFound: If the route does not exist.
            DeploymentRevisionNotFound: If the route has no revision linked.
        """
        async with self._db.begin_readonly_session() as db_sess:
            route_query = sa.select(RoutingRow.revision).where(RoutingRow.id == route_id)
            result = await db_sess.execute(route_query)
            revision_id = result.scalar_one_or_none()
            if revision_id is None:
                raise DeploymentRevisionNotFound(f"Route {route_id} has no revision linked")

            revision_query = sa.select(DeploymentRevisionRow).where(
                DeploymentRevisionRow.id == revision_id
            )
            revision_result = await db_sess.execute(revision_query)
            row = revision_result.scalar_one_or_none()
            if row is None:
                raise DeploymentRevisionNotFound(f"Deployment revision {revision_id} not found")
            return row.to_data()

    async def get_current_revision(
        self,
        endpoint_id: uuid.UUID,
    ) -> ModelRevisionData:
        """Get the current revision of a deployment.

        Args:
            endpoint_id: ID of the deployment endpoint

        Raises:
            EndpointNotFound: If the endpoint does not exist.
            DeploymentRevisionNotFound: If the endpoint has no current revision.
        """
        async with self._db.begin_readonly_session() as db_sess:
            endpoint_query = sa.select(EndpointRow.current_revision).where(
                EndpointRow.id == endpoint_id
            )
            result = await db_sess.execute(endpoint_query)
            current_revision_id = result.scalar_one_or_none()
            if current_revision_id is None:
                raise DeploymentRevisionNotFound(f"Endpoint {endpoint_id} has no current revision")

            revision_query = sa.select(DeploymentRevisionRow).where(
                DeploymentRevisionRow.id == current_revision_id
            )
            revision_result = await db_sess.execute(revision_query)
            row = revision_result.scalar_one_or_none()
            if row is None:
                raise DeploymentRevisionNotFound(
                    f"Deployment revision {current_revision_id} not found"
                )
            return row.to_data()

    async def search_revisions(
        self,
        querier: BatchQuerier,
    ) -> RevisionSearchResult:
        """Search deployment revisions with pagination and filtering."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(DeploymentRevisionRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.DeploymentRevisionRow.to_data() for row in result.rows]

            return RevisionSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def update_endpoint(
        self,
        updater: Updater[EndpointRow],
    ) -> DeploymentInfo:
        """Update an endpoint using the provided updater spec.

        Returns:
            DeploymentInfo: The updated endpoint information.

        Raises:
            EndpointNotFound: If the endpoint does not exist.
        """
        async with self._begin_session_read_committed() as db_sess:
            result = await execute_updater(db_sess, updater)
            if result is None:
                raise EndpointNotFound(f"Endpoint {updater.pk_value} not found")

            # Query the updated endpoint with related objects in the same session
            query = (
                sa.select(EndpointRow)
                .where(EndpointRow.id == updater.pk_value)
                .options(
                    selectinload(EndpointRow.image_row),
                    selectinload(EndpointRow.revisions).selectinload(
                        DeploymentRevisionRow.image_row
                    ),
                )
            )
            query_result = await db_sess.execute(query)
            row: EndpointRow = query_result.scalar_one()

            return row.to_deployment_info()

    async def update_current_revision(
        self,
        endpoint_id: uuid.UUID,
        revision_id: uuid.UUID,
    ) -> uuid.UUID | None:
        """Update the current_revision of an endpoint and return the previous revision ID."""
        async with self._begin_session_read_committed() as db_sess:
            # Get current revision first
            query = sa.select(EndpointRow.current_revision).where(EndpointRow.id == endpoint_id)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            previous_revision_id = row

            # Update to new revision
            update_query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == endpoint_id)
                .values(current_revision=revision_id)
            )
            await db_sess.execute(update_query)

            return previous_revision_id

    # -------------------------------------------------------------------------
    # Auto-Scaling Policy Methods (DeploymentAutoScalingPolicyRow)
    # -------------------------------------------------------------------------

    async def create_auto_scaling_policy(
        self,
        creator: Creator[DeploymentAutoScalingPolicyRow],
    ) -> DeploymentAutoScalingPolicyData:
        """Create a new auto-scaling policy for an endpoint.

        Each endpoint can have at most one auto-scaling policy (1:1 relationship).
        If a policy already exists for the endpoint, the database will raise a
        unique constraint violation.
        """
        async with self._begin_session_read_committed() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.to_data()

    async def get_auto_scaling_policy(
        self,
        endpoint_id: uuid.UUID,
    ) -> DeploymentAutoScalingPolicyData:
        """Get the auto-scaling policy for an endpoint.

        Raises:
            AutoScalingPolicyNotFound: If no policy exists for the endpoint.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(DeploymentAutoScalingPolicyRow).where(
                DeploymentAutoScalingPolicyRow.endpoint == endpoint_id
            )
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise AutoScalingPolicyNotFound(
                    f"Auto-scaling policy for endpoint {endpoint_id} not found"
                )
            return row.to_data()

    async def update_auto_scaling_policy(
        self,
        updater: Updater[DeploymentAutoScalingPolicyRow],
    ) -> DeploymentAutoScalingPolicyData:
        """Update an auto-scaling policy using the provided updater spec.

        The updater's pk_value should be the policy ID (primary key).

        Raises:
            AutoScalingPolicyNotFound: If the policy does not exist.
        """
        async with self._begin_session_read_committed() as db_sess:
            result = await execute_updater(db_sess, updater)
            if result is None:
                raise AutoScalingPolicyNotFound(f"Auto-scaling policy {updater.pk_value} not found")
            return result.row.to_data()

    async def delete_auto_scaling_policy(
        self,
        purger: Purger[DeploymentAutoScalingPolicyRow],
    ) -> PurgerResult[DeploymentAutoScalingPolicyRow] | None:
        """Delete the auto-scaling policy by primary key.

        Args:
            purger: Purger containing the policy ID (primary key) to delete.

        Returns:
            PurgerResult containing the deleted row, or None if no policy existed.
        """
        async with self._begin_session_read_committed() as db_sess:
            return await execute_purger(db_sess, purger)

    async def create_deployment_policy(
        self,
        creator: Creator[DeploymentPolicyRow],
    ) -> DeploymentPolicyData:
        """Create a new deployment policy for an endpoint.

        Each endpoint can have at most one deployment policy (1:1 relationship).
        If a policy already exists for the endpoint, the database will raise a
        unique constraint violation.
        """
        async with self._begin_session_read_committed() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.to_data()

    async def get_deployment_policy(
        self,
        endpoint_id: uuid.UUID,
    ) -> DeploymentPolicyData:
        """Get the deployment policy for an endpoint.

        Raises:
            DeploymentPolicyNotFound: If no policy exists for the endpoint.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(DeploymentPolicyRow).where(
                DeploymentPolicyRow.endpoint == endpoint_id
            )
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise DeploymentPolicyNotFound(
                    f"Deployment policy for endpoint {endpoint_id} not found"
                )
            return row.to_data()

    async def update_deployment_policy(
        self,
        updater: Updater[DeploymentPolicyRow],
    ) -> DeploymentPolicyData:
        """Update a deployment policy using the provided updater spec.

        The updater's pk_value should be the policy ID (primary key).

        Raises:
            DeploymentPolicyNotFound: If the policy does not exist.
        """
        async with self._begin_session_read_committed() as db_sess:
            result = await execute_updater(db_sess, updater)
            if result is None:
                raise DeploymentPolicyNotFound(f"Deployment policy {updater.pk_value} not found")
            return result.row.to_data()

    async def delete_deployment_policy(
        self,
        purger: Purger[DeploymentPolicyRow],
    ) -> PurgerResult[DeploymentPolicyRow] | None:
        """Delete the deployment policy by primary key.

        Args:
            purger: Purger containing the policy ID (primary key) to delete.

        Returns:
            PurgerResult containing the deleted row, or None if no policy existed.
        """
        async with self._begin_session_read_committed() as db_sess:
            return await execute_purger(db_sess, purger)

    async def search_deployment_policies(
        self,
        querier: BatchQuerier,
    ) -> DeploymentPolicySearchResult:
        """Search deployment policies with pagination and filtering.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            DeploymentPolicySearchResult with items, total_count, and pagination info.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(DeploymentPolicyRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            return DeploymentPolicySearchResult(
                items=[row.to_data() for row in result.rows],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def complete_rolling_update_bulk(
        self,
        updates: dict[uuid.UUID, uuid.UUID],
    ) -> None:
        """Complete rolling update by setting current_revision and clearing deploying_revision.

        For each endpoint, atomically sets current_revision to the new revision
        and clears deploying_revision. Groups endpoints by new_revision_id to
        minimize database round-trips.

        Args:
            updates: Mapping of endpoint_id to new_revision_id.
        """
        if not updates:
            return
        # Group endpoint IDs by new_revision_id for batch execution
        revision_to_endpoints: dict[uuid.UUID, list[uuid.UUID]] = {}
        for endpoint_id, new_revision_id in updates.items():
            revision_to_endpoints.setdefault(new_revision_id, []).append(endpoint_id)
        async with self._begin_session_read_committed() as db_sess:
            for new_revision_id, endpoint_ids in revision_to_endpoints.items():
                stmt = (
                    sa.update(EndpointRow)
                    .where(EndpointRow.id.in_(endpoint_ids))
                    .values(
                        current_revision=new_revision_id,
                        deploying_revision=None,
                    )
                )
                await db_sess.execute(stmt)

    # ========== Access Token Operations ==========

    async def create_access_token(
        self,
        creator: Creator[EndpointTokenRow],
    ) -> EndpointTokenRow:
        """Create a new access token for a model deployment.

        Args:
            creator: Creator containing the EndpointTokenCreatorSpec.

        Returns:
            Created EndpointTokenRow.
        """
        async with self._begin_session_read_committed() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row

    # ========== Additional Search Operations ==========

    async def search_auto_scaling_rules(
        self,
        querier: BatchQuerier,
    ) -> AutoScalingRuleSearchResult:
        """Search auto-scaling rules with pagination and filtering.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            AutoScalingRuleSearchResult with items, total_count, and pagination info.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointAutoScalingRuleRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            return AutoScalingRuleSearchResult(
                items=[row.to_model_deployment_data() for row in result.rows],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_access_tokens(
        self,
        querier: BatchQuerier,
    ) -> AccessTokenSearchResult:
        """Search access tokens with pagination and filtering.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            AccessTokenSearchResult with items, total_count, and pagination info.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointTokenRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            return AccessTokenSearchResult(
                items=[
                    ModelDeploymentAccessTokenData(
                        id=row.id,
                        token=row.token,
                        valid_until=row.valid_until,
                        created_at=row.created_at,
                    )
                    for row in result.rows
                ],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

"""Database source implementation for deployment repository."""

import dataclasses
import logging
import uuid
from collections import Counter, defaultdict
from collections.abc import AsyncIterator, Iterable, Mapping, Sequence
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload

from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_preset import DeploymentPresetID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import (
    AccessKey,
    KernelId,
    MountPermission,
    SessionId,
    SlotName,
)
from ai.backend.logging.utils import BraceStyleAdapter
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
    DeploymentHandlerCategory,
    DeploymentInfo,
    DeploymentInfoWithAutoScalingRules,
    DeploymentLastHistory,
    DeploymentLifecycleSubStep,
    DeploymentOptions,
    DeploymentPolicyData,
    DeploymentPolicySearchResult,
    DeploymentPolicyUpsertResult,
    DeploymentRevisionReadBundle,
    DeploymentSummarySearchResult,
    DeploymentWithHistory,
    LegacyRevisionCreateReadBundle,
    ModelDeploymentAccessTokenData,
    ModelDeploymentAutoScalingRuleData,
    ModelDeploymentData,
    ModelDeploymentDataSearchResult,
    ModelRevisionData,
    RevisionSearchResult,
    RouteHandlerCategory,
    RouteHealthStatus,
    RouteInfo,
    RouteSearchResult,
    RouteStatus,
    ScalingGroupCleanupConfig,
)
from ai.backend.manager.data.deployment_revision_preset.types import ResourceSlotEntryData
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.model_serving.types import AppProxyRouteEntry
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.vfolder.types import VFolderLocation
from ai.backend.manager.errors.deployment import (
    DeploymentHasNoTargetRevision,
    DeploymentRevisionNotFound,
    UserNotFoundInDeployment,
)
from ai.backend.manager.errors.resource import (
    ProjectNotFound,
    RuntimeVariantNotFound,
    ScalingGroupNotFound,
    ScalingGroupProxyTargetNotFound,
)
from ai.backend.manager.errors.service import (
    AutoScalingPolicyNotFound,
    AutoScalingRuleNotFound,
    DeploymentPolicyNotFound,
    EndpointNotFound,
    EndpointTokenNotFound,
    NoUpdatesToApply,
)
from ai.backend.manager.errors.storage import VFolderNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyData,
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.row import (
    DeploymentRevisionPresetRow,
)
from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.group import GroupRow, groups
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.resource_slot.row import (
    DeploymentRevisionResourceSlotRow,
    PresetResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow, scaling_groups
from ai.backend.manager.models.scheduling_history import (
    DeploymentHistoryRow,
    RouteHistoryRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    execute_batch_querier,
    execute_creator,
)
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.purger import (
    Purger,
    PurgerResult,
    execute_purger,
)
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACEntityCreator,
    execute_rbac_entity_creator,
    execute_rbac_entity_creators,
)
from ai.backend.manager.repositories.base.updater import (
    BatchUpdater,
    Updater,
    execute_batch_updater,
    execute_updater,
)
from ai.backend.manager.repositories.base.upserter import (
    Upserter,
    execute_upserter,
)
from ai.backend.manager.repositories.deployment.creators import (
    DeploymentCreatorSpec,
    DeploymentPolicyCreatorSpec,
    DeploymentRevisionCreatorSpec,
)
from ai.backend.manager.repositories.deployment.types import (
    ProjectDeploymentSearchScope,
    RouteData,
    RouteServiceDiscoveryInfo,
    RouteSessionInfo,
    RouteSessionKernelInfo,
    UserDeploymentSearchScope,
)
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    ContainerUserContext,
    DeploymentContext,
    ImageContext,
    ResolvedPresetValues,
    UserContext,
)
from ai.backend.manager.repositories.scheduling_history.creators import (
    DeploymentHistoryCreatorSpec,
)
from ai.backend.manager.utils import query_userinfo_from_session


@dataclass
class EndpointWithRoutesRawData:
    """Internal data structure for endpoint with routes from database."""

    endpoint_row: EndpointRow
    route_rows: list[RoutingRow]


log = BraceStyleAdapter(logging.getLogger(__name__))


def _project_preset_slots(
    preset_row: DeploymentRevisionPresetRow | None,
    slot_entries: list[tuple[str, Decimal]],
) -> list[ResourceSlotEntryData] | None:
    if preset_row is None:
        return None
    return [
        ResourceSlotEntryData(resource_type=name, quantity=str(qty)) for name, qty in slot_entries
    ]


class DeploymentDBSource:
    """Database source for deployment-related operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
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

            # Create endpoint with RBAC scope association
            rbac_result = await execute_rbac_entity_creator(db_sess, creator)
            endpoint = rbac_result.row

            # Create deployment policy if provided
            if policy_config is not None:
                policy_creator_spec = DeploymentPolicyCreatorSpec(
                    deployment_id=endpoint.id,
                    strategy=policy_config.strategy,
                    strategy_spec=policy_config.strategy_spec,
                )
            else:
                policy_creator_spec = DeploymentPolicyCreatorSpec.build_default(endpoint.id)
            policy_creator = RBACEntityCreator(
                spec=policy_creator_spec,
                element_type=RBACElementType.DEPLOYMENT_POLICY,
                scope_ref=RBACElementRef(
                    element_type=RBACElementType.MODEL_DEPLOYMENT,
                    element_id=str(endpoint.id),
                ),
            )
            await execute_rbac_entity_creator(db_sess, policy_creator)
            await db_sess.flush()

            stmt = (
                sa.select(EndpointRow)
                .where(EndpointRow.id == endpoint.id)
                .options(
                    selectinload(EndpointRow.current_revision_row),
                    selectinload(EndpointRow.deploying_revision_row),
                    selectinload(EndpointRow.deployment_policy),
                )
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

    async def get_image_id(self, image: ImageIdentifier) -> ImageID:
        """Get image ID from ImageIdentifier.

        Args:
            image: ImageIdentifier containing canonical and architecture

        Returns:
            ImageID of the image
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            image_row = await ImageRow.lookup(db_sess, image)
            return ImageID(image_row.id)

    async def get_endpoint(
        self,
        endpoint_id: DeploymentID,
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
                    selectinload(EndpointRow.current_revision_row),
                    selectinload(EndpointRow.deploying_revision_row),
                    selectinload(EndpointRow.deployment_policy),
                )
            )
            result = await db_sess.execute(query)
            row: EndpointRow | None = result.scalar_one_or_none()

            if not row:
                raise EndpointNotFound(f"Endpoint {endpoint_id} not found")

            return row.to_deployment_info()

    async def get_deployment_data(
        self,
        endpoint_id: DeploymentID,
    ) -> ModelDeploymentData:
        """Fetch a deployment as the API-shaped ``ModelDeploymentData``.

        Bypasses the ``DeploymentInfo`` intermediate so the API path's
        revision-id columns flow through unchanged from the DB row.

        Raises:
            EndpointNotFound: If the endpoint does not exist.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointRow).where(EndpointRow.id == endpoint_id)
            result = await db_sess.execute(query)
            row: EndpointRow | None = result.scalar_one_or_none()

            if not row:
                raise EndpointNotFound(f"Endpoint {endpoint_id} not found")

            return row.to_model_deployment_data()

    async def get_deployments_by_ids(
        self,
        deployment_ids: set[DeploymentID],
    ) -> list[DeploymentInfo]:
        """Get deployments by their IDs."""
        if not deployment_ids:
            return []

        async with self._begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select(EndpointRow)
                .where(
                    sa.and_(
                        EndpointRow.id.in_(deployment_ids),
                        EndpointRow.lifecycle_stage.in_(EndpointLifecycle.active_states()),
                    )
                )
                .options(
                    selectinload(EndpointRow.current_revision_row),
                    selectinload(EndpointRow.deploying_revision_row),
                    selectinload(EndpointRow.deployment_policy),
                )
            )
            result = await db_sess.execute(query)
            rows: Sequence[EndpointRow] = result.scalars().all()

            return [row.to_deployment_info() for row in rows]

    async def get_resource_group_default_deployment_options(
        self, resource_group_name: ResourceGroupName
    ) -> DeploymentOptions:
        """Return the resource group's ``default_deployment_options``.

        The service / controller snapshot-copies this onto the newly
        created deployment so later resource-group changes don't
        retroactively affect running deployments.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            stmt = sa.select(ScalingGroupRow.default_deployment_options).where(
                ScalingGroupRow.name == resource_group_name
            )
            result = await db_sess.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                raise ScalingGroupNotFound(f"Resource group {resource_group_name!r} not found")
            return row

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
                # Convert str to RouteHealthStatus
                status_strs = row.scheduler_opts.route_cleanup_target_statuses
                statuses: list[RouteHealthStatus] = []
                for status_str in status_strs:
                    try:
                        statuses.append(RouteHealthStatus(status_str))
                    except ValueError:
                        # Skip invalid status strings
                        pass

                cleanup_configs[row.name] = ScalingGroupCleanupConfig(
                    scaling_group_name=row.name, cleanup_target_statuses=statuses
                )

            return cleanup_configs

    async def search_deployments_with_last_history(
        self,
        *,
        querier: BatchQuerier,
        category: DeploymentHandlerCategory,
    ) -> list[DeploymentWithHistory]:
        """Search deployments via ``querier`` and attach the last history
        row in ``category`` to each result.

        Returns :class:`DeploymentWithHistory` where ``last_history`` is
        the most recent ``deployment_history`` entry whose
        ``handler_category`` matches, or ``None`` if no such row exists.
        The coordinator is responsible for comparing
        ``last_history.phase`` against the current handler name when it
        needs to decide whether to carry attempts forward.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointRow).options(
                selectinload(EndpointRow.current_revision_row),
                selectinload(EndpointRow.deploying_revision_row),
                selectinload(EndpointRow.deployment_policy),
            )
            query_result = await execute_batch_querier(db_sess, query, querier)
            endpoint_rows = [row.EndpointRow for row in query_result.rows]
            if not endpoint_rows:
                return []

            deployment_ids = [row.id for row in endpoint_rows]
            history_map = await self._get_last_deployment_histories_by_category(
                db_sess, deployment_ids, category=category
            )

            results: list[DeploymentWithHistory] = []
            for row in endpoint_rows:
                history_row = history_map.get(row.id)
                last_history: DeploymentLastHistory | None = None
                if history_row is not None:
                    last_history = DeploymentLastHistory(
                        id=history_row.id,
                        phase=history_row.phase,
                        attempts=history_row.attempts,
                        started_at=history_row.created_at,
                        error_code=history_row.error_code,
                        to_status=history_row.to_status,
                    )
                results.append(
                    DeploymentWithHistory(
                        deployment_info=row.to_deployment_info(),
                        last_history=last_history,
                    )
                )
            return results

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
                .options(
                    selectinload(EndpointRow.current_revision_row),
                    selectinload(EndpointRow.deploying_revision_row),
                )
            )

            # Add name filter if provided
            if name is not None:
                query = query.where(EndpointRow.name == name)

            result = await db_sess.execute(query)
            rows = result.scalars().all()

            return [row.to_deployment_info() for row in rows]

    async def update_endpoint_lifecycle(
        self,
        endpoint_id: DeploymentID,
        lifecycle: EndpointLifecycle,
    ) -> bool:
        """Update endpoint lifecycle status.

        Transitioning to ``DESTROYING`` also wipes any access tokens
        bound to the endpoint in the same transaction, so a destroyed
        deployment cannot be re-authenticated against once the routes
        are torn down.
        """
        async with self._begin_session_read_committed() as db_sess:
            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == endpoint_id)
                .values(lifecycle_stage=lifecycle)
            )
            result = await db_sess.execute(query)
            updated = cast(CursorResult[Any], result).rowcount > 0
            if updated and lifecycle == EndpointLifecycle.DESTROYING:
                await db_sess.execute(
                    sa.delete(EndpointTokenRow).where(EndpointTokenRow.endpoint == endpoint_id)
                )
            return updated

    async def get_modified_endpoint(
        self,
        endpoint_id: DeploymentID,
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
            # Fetch existing endpoint with all relationships needed by to_deployment_info()
            # to avoid lazy-load attempts after apply_to_row dirties the row.
            query = (
                sa.select(EndpointRow)
                .where(EndpointRow.id == endpoint_id)
                .options(
                    selectinload(EndpointRow.current_revision_row),
                    selectinload(EndpointRow.deploying_revision_row),
                    selectinload(EndpointRow.deployment_policy),
                )
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
            stmt = (
                sa.select(EndpointRow)
                .where(EndpointRow.id == updater.pk_value)
                .options(
                    selectinload(EndpointRow.current_revision_row),
                    selectinload(EndpointRow.deploying_revision_row),
                    selectinload(EndpointRow.deployment_policy),
                )
            )
            query_result = await db_sess.execute(stmt)
            row: EndpointRow = query_result.scalar_one()
            return row.to_deployment_info()

    async def update_endpoint_lifecycle_bulk(
        self,
        endpoint_ids: list[DeploymentID],
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
        *,
        new_history_specs: Sequence[DeploymentHistoryCreatorSpec],
        merge_history_ids: Sequence[uuid.UUID],
    ) -> int:
        """Update lifecycle status and record history in same transaction.

        The caller (coordinator) is responsible for deciding which new
        history specs should merge onto an existing row (by passing
        ``merge_history_ids``) versus insert a fresh row. This method
        is a pure writer — no re-query of prior history happens inside.

        Args:
            batch_updaters: BatchUpdaters for endpoint-status updates.
            new_history_specs: Specs to INSERT as new history rows.
            merge_history_ids: Existing history-row ids whose
                ``attempts`` should be incremented.

        Returns:
            Total number of endpoint rows updated.
        """
        if not batch_updaters:
            return 0

        async with self._begin_session_read_committed() as db_sess:
            total_updated = 0
            # 1. Execute all status updates
            for batch_updater in batch_updaters:
                update_result = await execute_batch_updater(db_sess, batch_updater)
                total_updated += update_result.updated_count

            # 2. Increment attempts for merge targets
            if merge_history_ids:
                await db_sess.execute(
                    sa.update(DeploymentHistoryRow)
                    .where(DeploymentHistoryRow.id.in_(merge_history_ids))
                    .values(attempts=DeploymentHistoryRow.attempts + 1)
                )

            # 3. Insert new rows
            if new_history_specs:
                new_rows = [spec.build_row() for spec in new_history_specs]
                db_sess.add_all(new_rows)
                await db_sess.flush()

            return total_updated

    async def _get_last_deployment_histories_by_category(
        self,
        db_sess: SASession,
        deployment_ids: Sequence[DeploymentID],
        *,
        category: DeploymentHandlerCategory,
    ) -> dict[DeploymentID, DeploymentHistoryRow]:
        """Return the most recent history row in ``category`` for each
        deployment id."""
        if not deployment_ids:
            return {}

        query = (
            sa.select(DeploymentHistoryRow)
            .where(
                DeploymentHistoryRow.deployment_id.in_(deployment_ids),
                DeploymentHistoryRow.handler_category == category,
            )
            .distinct(DeploymentHistoryRow.deployment_id)
            .order_by(
                DeploymentHistoryRow.deployment_id,
                DeploymentHistoryRow.created_at.desc(),
            )
        )
        result = await db_sess.execute(query)
        rows = result.scalars().all()
        return {DeploymentID(row.deployment_id): row for row in rows}

    async def get_db_now(self) -> datetime:
        """Get current database server time."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(sa.select(sa.func.now()))
            return result.scalar_one()

    async def delete_endpoint_with_routes(
        self,
        endpoint_id: DeploymentID,
    ) -> bool:
        """Delete an endpoint and all its routes in a single transaction."""
        async with self._begin_session_read_committed() as db_sess:
            # Delete routes first, then endpoint
            return await self._delete_routes_and_endpoint(db_sess, endpoint_id)

    # AutoScalingRule operations

    async def create_autoscaling_rule(
        self,
        endpoint_id: DeploymentID,
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
        endpoint_id: DeploymentID,
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

    async def bulk_delete_autoscaling_rules(
        self,
        rule_ids: list[uuid.UUID],
    ) -> list[uuid.UUID]:
        """Delete multiple autoscaling rules and return the IDs that were actually deleted."""
        if not rule_ids:
            return []
        async with self._begin_session_read_committed() as db_sess:
            query = (
                sa.delete(EndpointAutoScalingRuleRow)
                .where(EndpointAutoScalingRuleRow.id.in_(rule_ids))
                .returning(EndpointAutoScalingRuleRow.id)
            )
            result = await db_sess.execute(query)
            return [row[0] for row in result.fetchall()]

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
        endpoint_id: DeploymentID,
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
        creator: RBACEntityCreator[RoutingRow],
    ) -> uuid.UUID:
        """Create a new route using the provided creator.

        The Creator is built at the upper layer (service/action) and injected here.
        This method only executes the creator.
        """
        async with self._begin_session_read_committed() as db_sess:
            result = await execute_rbac_entity_creator(db_sess, creator)
            return result.row.id

    async def get_routes_by_endpoint(
        self,
        endpoint_id: DeploymentID,
    ) -> list[RouteData]:
        """Get all routes for an endpoint."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(RoutingRow).where(RoutingRow.endpoint == endpoint_id)
            result = await db_sess.execute(query)
            rows = result.scalars().all()

            return [
                RouteData(
                    route_id=row.id,
                    deployment_id=row.endpoint,
                    session_id=SessionId(row.session) if row.session else None,
                    status=row.status,
                    health_status=row.health_status,
                    traffic_ratio=row.traffic_ratio,
                    created_at=row.created_at,
                    revision_id=DeploymentRevisionID(row.revision),
                    traffic_status=row.traffic_status,
                    health_check=row.health_check,
                    replica_host=row.replica_host,
                    replica_port=row.replica_port,
                    updated_at=row.updated_at,
                    sub_status=row.sub_status,
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

    async def admin_search_deployments(
        self,
        querier: BatchQuerier,
    ) -> ModelDeploymentDataSearchResult:
        """Search every endpoint without a scope filter, projecting each row
        directly to ``ModelDeploymentData``.

        Backs ``DeploymentAdminRepository.admin_search_deployments`` — the
        admin label makes the unscoped intent explicit at every layer of
        the stack (db_source → repository → service).
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.EndpointRow.to_model_deployment_data() for row in result.rows]

            return ModelDeploymentDataSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_user_deployments(
        self,
        querier: BatchQuerier,
        scope: UserDeploymentSearchScope,
    ) -> ModelDeploymentDataSearchResult:
        """Search deployments owned by a specific user, returning ``ModelDeploymentData``.

        Backs the v2 adapter's ``my_search`` path. Scope filter
        (``EndpointRow.created_user == user_id``) is injected via
        ``execute_batch_querier``'s ``scope`` argument.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
                scope=scope,
            )

            items = [row.EndpointRow.to_model_deployment_data() for row in result.rows]

            return ModelDeploymentDataSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_project_deployments(
        self,
        querier: BatchQuerier,
        scope: ProjectDeploymentSearchScope,
    ) -> ModelDeploymentDataSearchResult:
        """Search deployments in a project, returning ``ModelDeploymentData``.

        Distinct from :meth:`search_project_deployment_summary`, which
        returns the lighter-weight ``DeploymentSummaryData`` for project
        admin list pages. Backs the v2 adapter's ``project_search`` path.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
                scope=scope,
            )

            items = [row.EndpointRow.to_model_deployment_data() for row in result.rows]

            return ModelDeploymentDataSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_project_deployment_summary(
        self,
        querier: BatchQuerier,
        scope: ProjectDeploymentSearchScope,
    ) -> DeploymentSummarySearchResult:
        """Search lightweight deployment summaries within a project scope.

        Returns lightweight DeploymentSummaryData built from EndpointRow scalar
        columns only (no eager-loaded relationships). Revision and policy
        details are not included.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
                scopes=[scope],
            )

            items = [row.EndpointRow.to_summary_data() for row in result.rows]

            return DeploymentSummarySearchResult(
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
        route_ids: set[ReplicaID],
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
                    RuntimeVariantRow.name.label("runtime_variant"),
                    EndpointRow.session_owner.label("session_owner"),
                    EndpointRow.project.label("project"),
                    KernelRow.kernel_host,
                    KernelRow.service_ports,
                )
                .select_from(RoutingRow)
                .join(EndpointRow, RoutingRow.endpoint == EndpointRow.id)
                .join(
                    DeploymentRevisionRow,
                    EndpointRow.current_revision == DeploymentRevisionRow.id,
                )
                .join(
                    RuntimeVariantRow,
                    DeploymentRevisionRow.runtime_variant_id == RuntimeVariantRow.id,
                )
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
                        deployment_id=row.endpoint_id,
                        endpoint_name=row.endpoint_name,
                        runtime_variant=row.runtime_variant,
                        kernel_host=row.kernel_host,
                        kernel_port=inference_port,
                        session_owner=row.session_owner,
                        project=row.project,
                    )
                )

            return discovery_infos

    async def _delete_routes_and_endpoint(
        self,
        db_sess: SASession,
        endpoint_id: DeploymentID,
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
        endpoint_id: DeploymentID,
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
                .options(
                    selectinload(EndpointRow.current_revision_row),
                    selectinload(EndpointRow.deploying_revision_row),
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
                usage_mode=row.usage_mode,
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

    async def fetch_auto_scaling_rules_by_deployment_ids(
        self,
        deployment_ids: set[DeploymentID],
    ) -> Mapping[DeploymentID, list[AutoScalingRule]]:
        """Fetch autoscaling rules for given deployment IDs."""
        if not deployment_ids:
            return {}

        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointAutoScalingRuleRow).where(
                EndpointAutoScalingRuleRow.endpoint.in_(deployment_ids)
            )
            result = await db_sess.execute(query)
            rows: Sequence[EndpointAutoScalingRuleRow] = result.scalars().all()

            rules_by_deployment: defaultdict[DeploymentID, list[AutoScalingRule]] = defaultdict(
                list
            )
            for row in rows:
                rules_by_deployment[row.endpoint].append(row.to_autoscaling_rule())

            return rules_by_deployment

    async def fetch_active_routes_by_deployment_ids(
        self,
        deployment_ids: set[DeploymentID],
    ) -> Mapping[DeploymentID, list[RouteInfo]]:
        """Fetch routes for given deployment IDs."""
        if not deployment_ids:
            return {}

        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(RoutingRow).where(
                sa.and_(
                    RoutingRow.endpoint.in_(deployment_ids),
                    RoutingRow.status.in_(RouteStatus.active_route_statuses()),
                )
            )
            result = await db_sess.execute(query)
            rows: Sequence[RoutingRow] = result.scalars().all()
            routes_by_deployment: defaultdict[DeploymentID, list[RouteInfo]] = defaultdict(list)
            for row in rows:
                routes_by_deployment[row.endpoint].append(row.to_route_info())
            return routes_by_deployment

    async def scale_routes(
        self,
        scale_out_creators: Sequence[RBACEntityCreator[RoutingRow]],
        scale_in_updater: BatchUpdater[RoutingRow] | None,
    ) -> None:
        """Scale out/in routes based on provided creators and updater."""
        async with self._begin_session_read_committed() as db_sess:
            # Scale out routes
            for creator in scale_out_creators:
                await execute_rbac_entity_creator(db_sess, creator)
            # Scale in routes
            if scale_in_updater:
                await execute_batch_updater(db_sess, scale_in_updater)

    # Route operations

    async def search_route_datas(
        self,
        *,
        querier: BatchQuerier,
    ) -> list[RouteData]:
        """Search routes via :class:`BatchQuerier`.

        The caller composes ``querier`` with every filter that applies
        (lifecycle / health / traffic_status / endpoint id set, etc.).
        Pagination is part of the querier — pass ``NoPagination`` for
        unbounded scans.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(RoutingRow)
            query_result = await execute_batch_querier(db_sess, query, querier)
            route_rows: list[RoutingRow] = [row.RoutingRow for row in query_result.rows]
            return [
                RouteData(
                    route_id=row.id,
                    deployment_id=row.endpoint,
                    session_id=SessionId(row.session) if row.session else None,
                    status=row.status,
                    health_status=row.health_status,
                    traffic_ratio=row.traffic_ratio,
                    created_at=row.created_at,
                    revision_id=DeploymentRevisionID(row.revision),
                    traffic_status=row.traffic_status,
                    health_check=row.health_check,
                    replica_host=row.replica_host,
                    replica_port=row.replica_port,
                    updated_at=row.updated_at,
                    sub_status=row.sub_status,
                    error_data=row.error_data or {},
                )
                for row in route_rows
            ]

    async def search_route_datas_with_last_history(
        self,
        *,
        querier: BatchQuerier,
        category: RouteHandlerCategory,
    ) -> list[RouteData]:
        """Search routes and attach the last history row per ``category``.

        Mirrors :meth:`search_deployments_with_last_history` for the route layer.
        ``last_transition_at`` on each :class:`RouteData` is the ``created_at``
        of the most recent history record matching the given category, or
        ``None`` if no history exists yet.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(RoutingRow)
            query_result = await execute_batch_querier(db_sess, query, querier)
            route_rows: list[RoutingRow] = [row.RoutingRow for row in query_result.rows]
            if not route_rows:
                return []

            route_ids = [row.id for row in route_rows]
            history_map = await self._get_last_route_histories_by_category(
                db_sess, route_ids, category=category
            )

            return [
                RouteData(
                    route_id=row.id,
                    deployment_id=row.endpoint,
                    session_id=SessionId(row.session) if row.session else None,
                    status=row.status,
                    health_status=row.health_status,
                    traffic_ratio=row.traffic_ratio,
                    created_at=row.created_at,
                    revision_id=DeploymentRevisionID(row.revision),
                    traffic_status=row.traffic_status,
                    health_check=row.health_check,
                    replica_host=row.replica_host,
                    replica_port=row.replica_port,
                    updated_at=row.updated_at,
                    sub_status=row.sub_status,
                    last_transition_at=history_map[row.id].created_at
                    if row.id in history_map
                    else None,
                    error_data=row.error_data or {},
                )
                for row in route_rows
            ]

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

    async def _get_last_route_histories_by_category(
        self,
        db_sess: SASession,
        route_ids: list[ReplicaID],
        category: RouteHandlerCategory,
    ) -> dict[ReplicaID, RouteHistoryRow]:
        """Get last history records per route filtered by handler category."""
        if not route_ids:
            return {}

        query = (
            sa.select(RouteHistoryRow)
            .where(
                RouteHistoryRow.route_id.in_(route_ids),
                RouteHistoryRow.category == category,
            )
            .distinct(RouteHistoryRow.route_id)
            .order_by(
                RouteHistoryRow.route_id,
                RouteHistoryRow.created_at.desc(),
            )
        )
        result = await db_sess.execute(query)
        rows = result.scalars().all()
        return {row.route_id: row for row in rows}

    async def _get_last_route_histories_bulk(
        self,
        db_sess: SASession,
        route_ids: list[ReplicaID],
    ) -> dict[ReplicaID, RouteHistoryRow]:
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

    async def update_endpoint_url(
        self,
        endpoint_id: DeploymentID,
        url: str,
    ) -> None:
        """Update a single endpoint's registered URL.

        Args:
            endpoint_id: Endpoint UUID
            url: The registered endpoint URL
        """
        async with self._begin_session_read_committed() as db_sess:
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

    async def fetch_kernel_connection_info(
        self,
        session_ids: list[SessionId],
    ) -> dict[SessionId, tuple[str, int]]:
        """Fetch kernel_host and inference port for sessions."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(
                KernelRow.session_id,
                KernelRow.kernel_host,
                KernelRow.service_ports,
            ).where(
                KernelRow.session_id.in_(session_ids),
                KernelRow.cluster_role == "main",
            )
            result = await db_sess.execute(query)
            info: dict[SessionId, tuple[str, int]] = {}
            for row in result:
                if not row.kernel_host or not row.service_ports:
                    continue
                for sp in row.service_ports:
                    if sp.get("is_inference"):
                        host_ports = sp.get("host_ports", [])
                        if host_ports:
                            info[SessionId(row.session_id)] = (row.kernel_host, host_ports[0])
                        break
            return info

    async def update_route_replica_info(
        self,
        updates: dict[ReplicaID, RouteSessionKernelInfo],
    ) -> None:
        """Update replica_host and replica_port for routes."""
        async with self._begin_session_read_committed() as db_sess:
            for route_id, kernel in updates.items():
                query = (
                    sa.update(RoutingRow)
                    .where(RoutingRow.id == route_id)
                    .values(replica_host=kernel.replica_host, replica_port=kernel.replica_port)
                )
                await db_sess.execute(query)

    async def fetch_health_check_configs_by_revision_ids(
        self,
        revision_ids: set[DeploymentRevisionID],
    ) -> dict[DeploymentRevisionID, ModelHealthCheck | None]:
        """Fetch health check configurations for revisions.

        Reads only the ``model_definition`` column — variant-specific
        health check defaults are already baked into that column at
        revision-creation time, so no runtime dispatch by variant name
        and no other row fields are needed. SET NULL state on
        ``image`` / ``model`` does not affect this lookup.

        Returns:
            Mapping of revision_id to ModelHealthCheck (None if the
            revision has no model_definition or no health_check inside).
        """
        if not revision_ids:
            return {}

        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(
                DeploymentRevisionRow.id,
                DeploymentRevisionRow.model_definition,
            ).where(DeploymentRevisionRow.id.in_(revision_ids))
            result = await db_sess.execute(query)
            configs: dict[DeploymentRevisionID, ModelHealthCheck | None] = {}
            for revision_id, model_definition in result.all():
                configs[DeploymentRevisionID(revision_id)] = (
                    model_definition.health_check_config() if model_definition is not None else None
                )
            return configs

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
        revision_id: DeploymentRevisionID,
    ) -> DeploymentContext:
        """Fetch all context data needed for session creation from deployment info.

        Args:
            deployment_info: Deployment information
            revision_id: Revision to use for image resolution.

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
            user_info = await query_userinfo_from_session(
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
            group_id = user_info.group_id
            resource_policy = user_info.resource_policy

            revision_query = (
                sa.select(DeploymentRevisionRow)
                .where(DeploymentRevisionRow.id == revision_id)
                .options(selectinload(DeploymentRevisionRow.image_row))
            )
            revision_result = await db_sess.execute(revision_query)
            revision_row = revision_result.scalar_one_or_none()
            if revision_row is None or revision_row.image_row is None:
                raise DeploymentHasNoTargetRevision(
                    f"Revision {revision_id} not found or has no image"
                )
            image_identifier = ImageIdentifier(
                canonical=revision_row.image_row.name,
                architecture=revision_row.image_row.architecture,
            )
            image_row = await ImageRow.resolve(db_sess, [image_identifier])

            # Resolve preset_values from revision
            resolved_presets: ResolvedPresetValues | None = None
            if revision_row.preset_values:
                preset_ids = [pv.preset_id for pv in revision_row.preset_values]
                vp_stmt = sa.select(RuntimeVariantPresetRow).where(
                    RuntimeVariantPresetRow.id.in_(preset_ids)
                )
                vp_rows = (await db_sess.execute(vp_stmt)).scalars().all()
                vp_map = {row.id: row for row in vp_rows}
                resolved_environ: dict[str, str] = {}
                resolved_args: list[str] = []
                for pv in revision_row.preset_values:
                    vp = vp_map.get(pv.preset_id)
                    if vp is None:
                        continue
                    if vp.preset_target == PresetTarget.ENV:
                        resolved_environ[vp.key] = pv.value
                    elif vp.preset_target == PresetTarget.ARGS:
                        if vp.value_type == PresetValueType.FLAG:
                            if (pv.value or "").strip().lower() in ("true", "1"):
                                resolved_args.append(vp.key)
                        else:
                            resolved_args.append(vp.key)
                            resolved_args.append(pv.value)
                resolved_presets = ResolvedPresetValues(
                    environ=resolved_environ, args=resolved_args
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
                resolved_presets=resolved_presets,
            )

    async def fetch_session_statuses_by_route_ids(
        self,
        route_ids: set[ReplicaID],
    ) -> Mapping[ReplicaID, SessionStatus | None]:
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
            status_map: dict[ReplicaID, SessionStatus | None] = {}
            for route_id, session_status in rows:
                status_map[ReplicaID(route_id)] = session_status

            return status_map

    async def fetch_route_session_kernel_infos(
        self,
        route_ids: set[ReplicaID],
    ) -> Mapping[ReplicaID, RouteSessionInfo | None]:
        """Fetch session status and kernel connection info for multiple routes.

        Args:
            route_ids: Set of route IDs to fetch information for

        Returns:
            Mapping of route_id to RouteSessionInfo:
            - None → route has no session linked
            - RouteSessionInfo(status=TERMINAL, kernel=None) → session terminated
            - RouteSessionInfo(status=RUNNING, kernel=RouteSessionKernelInfo(host, port)) → ready
            - RouteSessionInfo(status=PREPARING, kernel=None) → not yet running
        """
        if not route_ids:
            return {}

        async with self._begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select(
                    RoutingRow.id,
                    SessionRow.status,
                    KernelRow.kernel_host,
                    KernelRow.service_ports,
                )
                .select_from(RoutingRow)
                .outerjoin(SessionRow, RoutingRow.session == SessionRow.id)
                .outerjoin(
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

            info_map: dict[ReplicaID, RouteSessionInfo | None] = {}
            for row in rows:
                route_id = ReplicaID(row.id)
                if row.status is None:
                    info_map[route_id] = None
                    continue

                kernel: RouteSessionKernelInfo | None = None
                if row.kernel_host and row.service_ports:
                    inference_port: int | None = None
                    for port_info in row.service_ports:
                        if port_info.get("is_inference", False):
                            host_ports = port_info.get("host_ports", [])
                            if host_ports:
                                inference_port = host_ports[0]
                            break
                    if inference_port is not None:
                        kernel = RouteSessionKernelInfo(
                            replica_host=row.kernel_host,
                            replica_port=inference_port,
                        )

                info_map[route_id] = RouteSessionInfo(
                    status=row.status,
                    kernel=kernel,
                )

            return info_map

    async def fetch_route_connection_infos(
        self,
        *,
        route_querier: BatchQuerier,
    ) -> Mapping[uuid.UUID, list[AppProxyRouteEntry]]:
        """Resolve routing-table entries grouped by endpoint id.

        The caller composes ``route_querier`` with every filter that
        applies (lifecycle / health / traffic_status / endpoint id set,
        etc.) — db_source does not impose defaults and does not take a
        separate ``endpoint_ids`` argument. The returned mapping only
        contains endpoints that actually have at least one matching
        route; the caller treats a missing key as "no traffic-receiving
        routes for this endpoint" itself.

        Internally fetches the filtered ``RoutingRow`` set, then bulk-
        loads the main kernel for each running session and extracts
        the inference port. Sessions that are not RUNNING/CREATING are
        skipped because their kernel host:port is not stable.
        """
        result_map: dict[uuid.UUID, list[AppProxyRouteEntry]] = {}

        async with self._begin_readonly_session_read_committed() as db_sess:
            route_query = sa.select(RoutingRow).options(
                selectinload(RoutingRow.session_row),
            )
            route_result = await execute_batch_querier(db_sess, route_query, route_querier)
            route_rows: list[RoutingRow] = [r.RoutingRow for r in route_result.rows]
            if not route_rows:
                return result_map

            # Only sessions whose kernel network address is stable contribute
            # to the routing table; the rest will fall in on the next sync
            # cycle once they reach RUNNING.
            route_by_session: dict[uuid.UUID, RoutingRow] = {}
            for r in route_rows:
                if r.session is None or r.session_row is None:
                    continue
                if r.session_row.status not in (
                    SessionStatus.RUNNING,
                    SessionStatus.CREATING,
                ):
                    continue
                route_by_session[r.session] = r

            if not route_by_session:
                return result_map

            kernels = await KernelRow.batch_load_main_kernels_by_session_id(
                db_sess, list(route_by_session.keys())
            )

            for kernel in kernels:
                route = route_by_session.get(kernel.session_id)
                if route is None or kernel.service_ports is None or not kernel.kernel_host:
                    continue
                # First inference port wins (legacy single-inference-port
                # contract preserved during the row-method removal).
                inference_port = next(
                    (p for p in kernel.service_ports if p.get("is_inference")),
                    None,
                )
                if inference_port is None or not inference_port.get("host_ports"):
                    continue
                entry = AppProxyRouteEntry(
                    session_id=kernel.session_id,
                    route_id=route.id,
                    kernel_host=kernel.kernel_host,
                    kernel_port=inference_port["host_ports"][0],
                )
                result_map.setdefault(uuid.UUID(str(route.endpoint)), []).append(entry)

        return result_map

    async def search_deployment_ids(self, *, querier: BatchQuerier) -> list[DeploymentID]:
        """Search deployment ids using ``BatchQuerier``.

        The caller composes filter predicates via :class:`DeploymentConditions`,
        so every call site shows the actual selection criteria (e.g. the
        ``active`` lifecycle filter used by the route sync loop) instead
        of hiding it behind a named method.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointRow.id)
            result = await execute_batch_querier(db_sess, query, querier)
            return [row.id for row in result.rows]

    async def get_endpoint_health_check_config(
        self,
        endpoint_id: DeploymentID,
    ) -> ModelHealthCheck | None:
        """Read the endpoint's active-revision health-check config.

        Returns exactly what is persisted on the active revision's
        ``model_definition`` — the merge result from variant baseline,
        preset, yaml, and user overrides. ``_find_active_revision`` falls
        back to ``deploying_revision`` while the initial rollout has not
        completed, so AppProxy picks up the health-check config of the
        spec being deployed. No vfolder re-reads at runtime.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            endpoint = await EndpointRow.get(
                db_sess,
                endpoint_id,
                load_revisions=True,
            )
            if not endpoint:
                raise EndpointNotFound(str(endpoint_id))
            active_rev = endpoint._find_active_revision()
            if active_rev is None or active_rev.model_definition is None:
                return None
            return active_rev.model_definition.health_check_config()

    async def resolve_vfolder_permissions(
        self, vfolder_ids: Sequence[VFolderUUID]
    ) -> dict[VFolderUUID, MountPermission]:
        """Return each vfolder's stored permission projected as a
        ``MountPermission``.

        Intentionally minimal: only the ``permission`` column is read,
        without RBAC / host-permission / cross-project checks — those
        apply at session creation (``prepare_vfolder_mounts``), not at
        revision write. Used to snapshot the vfolder permission when
        resolving ``MountInfo.mount_perm=None`` (inherit) into a
        concrete ``MountInfoEntry.mount_perm`` before persisting.

        Raises ``VFolderNotFound`` if any requested id is missing or its
        ``permission`` column is NULL — both indicate the caller cannot
        ground an inherited permission against this vfolder.
        """
        if not vfolder_ids:
            return {}
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(
                sa.select(VFolderRow.id, VFolderRow.permission).where(
                    VFolderRow.id.in_(list(vfolder_ids))
                )
            )
            rows = {row.id: row.permission for row in result.all()}
            unresolved = [str(vid) for vid in vfolder_ids if vid not in rows or rows[vid] is None]
            if unresolved:
                raise VFolderNotFound(
                    f"VFolder permission unavailable for: {', '.join(unresolved)}"
                )
            return {VFolderUUID(vid): MountPermission(perm.value) for vid, perm in rows.items()}

    async def get_default_architecture_from_scaling_group(
        self, scaling_group_name: str
    ) -> str | None:
        """Most common architecture among live agents in the scaling group.

        Used as the lowest-priority fallback when a legacy request supplies
        only the image canonical without an explicit architecture. Returns
        ``None`` when no live agents are attached.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(
                sa.select(AgentRow.architecture).where(
                    sa.and_(
                        AgentRow.scaling_group == scaling_group_name,
                        AgentRow.status == AgentStatus.ALIVE,
                        AgentRow.schedulable == sa.true(),
                    )
                )
            )
            architectures = [row.architecture for row in result]
            if not architectures:
                return None
            most_common, _ = Counter(architectures).most_common(1)[0]
            return cast(str, most_common)

    async def load_legacy_model_service_deployment_read_bundle(
        self,
        runtime_variant_id: RuntimeVariantID,
        preset_id: DeploymentPresetID | None,
    ) -> LegacyRevisionCreateReadBundle:
        async with self._db.begin_readonly_session_read_committed() as session:
            variant_row = await self._fetch_runtime_variant_by_id(session, runtime_variant_id)
            preset_row, preset_slots = await self._fetch_preset_with_slots(session, preset_id)
            return LegacyRevisionCreateReadBundle(
                variant=variant_row.to_data(),
                preset=preset_row.to_data() if preset_row is not None else None,
                preset_resource_slots=_project_preset_slots(preset_row, preset_slots),
            )

    async def load_deployment_revision_read_bundle(
        self,
        runtime_variant_id: RuntimeVariantID,
        preset_id: DeploymentPresetID | None,
    ) -> DeploymentRevisionReadBundle:
        async with self._db.begin_readonly_session_read_committed() as session:
            variant_row = await self._fetch_runtime_variant_by_id(session, runtime_variant_id)
            preset_row, preset_slots = await self._fetch_preset_with_slots(session, preset_id)
            return DeploymentRevisionReadBundle(
                variant=variant_row.to_data(),
                preset=preset_row.to_data() if preset_row is not None else None,
                preset_resource_slots=_project_preset_slots(preset_row, preset_slots),
            )

    async def fetch_revision_required_slot_names(self) -> Iterable[SlotName]:
        """Return the globally required resource slot names"""
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(ResourceSlotTypeRow.slot_name).where(
                ResourceSlotTypeRow.required.is_(True)
            )
            rows = (await session.execute(stmt)).scalars().all()
        return frozenset(SlotName(slot_name) for slot_name in rows)

    @staticmethod
    async def _fetch_runtime_variant_by_id(
        session: SASession, variant_id: RuntimeVariantID
    ) -> RuntimeVariantRow:
        row = (
            await session.execute(
                sa.select(RuntimeVariantRow).where(RuntimeVariantRow.id == variant_id)
            )
        ).scalar_one_or_none()
        if row is None:
            raise RuntimeVariantNotFound()
        return row

    @staticmethod
    async def _fetch_preset_with_slots(
        session: SASession, preset_id: DeploymentPresetID | None
    ) -> tuple[DeploymentRevisionPresetRow | None, list[tuple[str, Decimal]]]:
        if preset_id is None:
            return None, []
        preset_row = (
            await session.execute(
                sa.select(DeploymentRevisionPresetRow).where(
                    DeploymentRevisionPresetRow.id == preset_id
                )
            )
        ).scalar_one_or_none()
        if preset_row is None:
            return None, []
        slot_rows = (
            (
                await session.execute(
                    sa.select(PresetResourceSlotRow).where(
                        PresetResourceSlotRow.preset_id == preset_id
                    )
                )
            )
            .scalars()
            .all()
        )
        return preset_row, [(r.slot_name, r.quantity) for r in slot_rows]

    @staticmethod
    async def _fetch_latest_revision_row(
        session: SASession, endpoint_id: DeploymentID
    ) -> DeploymentRevisionRow:
        row = (
            await session.execute(
                sa.select(DeploymentRevisionRow)
                .where(DeploymentRevisionRow.endpoint == endpoint_id)
                .order_by(DeploymentRevisionRow.revision_number.desc())
                .limit(1)
                .options(
                    selectinload(DeploymentRevisionRow.resource_slot_rows),
                    selectinload(DeploymentRevisionRow.runtime_variant_row),
                    selectinload(DeploymentRevisionRow.image_row),
                )
            )
        ).scalar_one_or_none()
        if row is None:
            raise DeploymentRevisionNotFound(f"No revisions exist for endpoint {endpoint_id}")
        return row

    # Deployment Revision Methods

    async def get_latest_revision_number(
        self,
        endpoint_id: DeploymentID,
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
        creator: RBACEntityCreator[DeploymentRevisionRow],
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
            rbac_result = await execute_rbac_entity_creator(db_sess, creator)
            return rbac_result.row.to_data()

    async def create_revision_with_next_number(
        self,
        creator: RBACEntityCreator[DeploymentRevisionRow],
        endpoint_id: DeploymentID,
    ) -> ModelRevisionData:
        """Atomically read the latest revision number and create a new revision.

        Combines get_latest_revision_number and create_revision in a single
        transaction to prevent race conditions where concurrent requests
        could read the same latest revision number.

        Locks the parent EndpointRow with SELECT ... FOR UPDATE to
        serialize concurrent revision creation for the same endpoint.

        TODO: Implement revision history pruning (similar to K8s revisionHistoryLimit).
        """
        async with self._begin_session_read_committed() as db_sess:
            # Lock the parent endpoint row to serialize revision creation.
            # Locking the endpoint (not revision rows) ensures correctness
            # even when no revisions exist yet (first revision case).
            lock_query = (
                sa.select(EndpointRow.id).where(EndpointRow.id == endpoint_id).with_for_update()
            )
            await db_sess.execute(lock_query)

            max_query = sa.select(sa.func.max(DeploymentRevisionRow.revision_number)).where(
                DeploymentRevisionRow.endpoint == endpoint_id
            )
            result = await db_sess.execute(max_query)
            latest_revision_number = result.scalar()
            next_number = (latest_revision_number or 0) + 1

            spec = cast(DeploymentRevisionCreatorSpec, creator.spec)
            updated_creator = dataclasses.replace(
                creator, spec=spec.with_revision_number(next_number)
            )
            rbac_result = await execute_rbac_entity_creator(db_sess, updated_creator)
            return rbac_result.row.to_data()

    async def get_revision(
        self,
        revision_id: DeploymentRevisionID,
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
        endpoint_id: DeploymentID,
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

    async def get_latest_revision(
        self,
        endpoint_id: DeploymentID,
    ) -> ModelRevisionData:
        """Get the latest revision (highest ``revision_number``) of a deployment.

        Unlike :meth:`get_current_revision`, this does not consult
        ``EndpointRow.current_revision``: it returns the most recently
        created revision for the endpoint regardless of activation state.

        Args:
            endpoint_id: ID of the deployment endpoint

        Raises:
            DeploymentRevisionNotFound: If no revisions exist for the endpoint.
        """
        async with self._db.begin_readonly_session() as db_sess:
            row = await self._fetch_latest_revision_row(db_sess, DeploymentID(endpoint_id))
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
                    selectinload(EndpointRow.current_revision_row),
                    selectinload(EndpointRow.deploying_revision_row),
                    selectinload(EndpointRow.deployment_policy),
                )
            )
            query_result = await db_sess.execute(query)
            row: EndpointRow = query_result.scalar_one()

            return row.to_deployment_info()

    async def replace_deployment_options(
        self,
        deployment_id: DeploymentID,
        options: DeploymentOptions,
    ) -> DeploymentOptions:
        """Replace the ``endpoints.options`` JSONB column for a deployment
        and return the stored value in a single round-trip (``UPDATE ...
        RETURNING``).

        The column is typed as :class:`PydanticColumn` so the domain model
        is persisted verbatim. This is a full-replace — callers are
        expected to pass the complete new value.

        Raises:
            EndpointNotFound: If the endpoint does not exist.
        """
        async with self._begin_session_read_committed() as db_sess:
            stmt = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == deployment_id)
                .values(options=options)
                .returning(EndpointRow.options)
            )
            result = await db_sess.execute(stmt)
            row = result.first()
            if row is None:
                raise EndpointNotFound(f"Endpoint {deployment_id} not found")
            stored: DeploymentOptions = row[0]
            return stored

    async def set_deploying_revision(
        self,
        endpoint_id: DeploymentID,
        revision_id: DeploymentRevisionID,
    ) -> tuple[DeploymentRevisionID | None, bool]:
        """Set deploying_revision and transition lifecycle to DEPLOYING.

        Overrides any previous ``deploying_revision`` unconditionally;
        leftover routes from the previous rollout are picked up by
        ``RouteEvictionHandler``'s orphan-revision branch.

        Returns:
            Tuple of (previous_current_revision_id, updated).
            ``updated=False`` means the endpoint row was not found.
        """
        async with self._begin_session_read_committed() as db_sess:
            update_query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == endpoint_id)
                .values(
                    deploying_revision=revision_id,
                    lifecycle_stage=EndpointLifecycle.DEPLOYING,
                    sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
                )
                .returning(EndpointRow.current_revision)
            )
            result = await db_sess.execute(update_query)
            row = result.one_or_none()
            if row is None:
                return None, False
            return cast(DeploymentRevisionID | None, row[0]), True

    async def prune_old_revisions(
        self,
        endpoint_id: DeploymentID,
        revision_history_limit: int,
    ) -> int:
        """Delete old revisions exceeding the history limit.

        Preserves:
        - The revision referenced by ``current_revision``
        - The revision referenced by ``deploying_revision``

        Revisions are ordered by revision_number descending; the newest
        ``revision_history_limit`` revisions are kept (plus the two
        protected revisions above).

        Returns the number of deleted revisions.
        """
        async with self._begin_session_read_committed() as db_sess:
            # Fetch protected revision IDs
            endpoint_query = sa.select(
                EndpointRow.current_revision,
                EndpointRow.deploying_revision,
            ).where(EndpointRow.id == endpoint_id)
            ep_result = await db_sess.execute(endpoint_query)
            ep_row = ep_result.one_or_none()
            if ep_row is None:
                return 0

            protected_ids: set[uuid.UUID] = set()
            if ep_row[0] is not None:
                protected_ids.add(ep_row[0])
            if ep_row[1] is not None:
                protected_ids.add(ep_row[1])

            # Find revisions to keep (newest N by revision_number)
            keep_query = (
                sa.select(DeploymentRevisionRow.id)
                .where(DeploymentRevisionRow.endpoint == endpoint_id)
                .order_by(DeploymentRevisionRow.revision_number.desc())
                .limit(revision_history_limit)
            )
            keep_result = await db_sess.execute(keep_query)
            keep_ids = {row[0] for row in keep_result.all()}

            # Union: keep the newest N + the protected revisions
            keep_ids |= protected_ids

            # Delete everything else
            delete_query = (
                sa.delete(DeploymentRevisionRow)
                .where(
                    DeploymentRevisionRow.endpoint == endpoint_id,
                    DeploymentRevisionRow.id.notin_(keep_ids),
                )
                .returning(DeploymentRevisionRow.id)
            )
            delete_result = await db_sess.execute(delete_query)
            deleted_count = len(delete_result.all())
            if deleted_count > 0:
                log.info(
                    "Pruned {} old revisions for deployment {} (limit={})",
                    deleted_count,
                    endpoint_id,
                    revision_history_limit,
                )
            return deleted_count

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
        endpoint_id: DeploymentID,
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

    async def upsert_deployment_policy(
        self,
        upserter: Upserter[DeploymentPolicyRow],
    ) -> DeploymentPolicyUpsertResult:
        """Create or update a deployment policy using ON CONFLICT."""
        async with self._begin_session_read_committed() as db_sess:
            result = await execute_upserter(
                db_sess,
                upserter,
                index_elements=["endpoint"],
            )
            row = result.row
            return DeploymentPolicyUpsertResult(
                data=row.to_data(),
                created=row.created_at == row.updated_at,
            )

    async def get_deployment_policy(
        self,
        endpoint_id: DeploymentID,
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

    # ========== Access Token Operations ==========

    async def create_access_token(
        self,
        creator: RBACEntityCreator[EndpointTokenRow],
    ) -> EndpointTokenRow:
        """Create a new access token for a model deployment.

        Args:
            creator: RBACEntityCreator containing the EndpointTokenCreatorSpec.

        Returns:
            Created EndpointTokenRow.
        """
        async with self._begin_session_read_committed() as db_sess:
            result = await execute_rbac_entity_creator(db_sess, creator)
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
                items=[
                    row.EndpointAutoScalingRuleRow.to_model_deployment_data() for row in result.rows
                ],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def get_access_token(
        self,
        token_id: uuid.UUID,
    ) -> ModelDeploymentAccessTokenData:
        """Get a single access token by ID."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = sa.select(EndpointTokenRow).where(EndpointTokenRow.id == token_id)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if not row:
                raise EndpointTokenNotFound(f"Access token {token_id} not found")
            return ModelDeploymentAccessTokenData(
                id=row.id,
                token=row.token,
                expires_at=row.expires_at,
                created_at=row.created_at or datetime.now(UTC),
            )

    async def delete_access_token(
        self,
        token_id: uuid.UUID,
    ) -> bool:
        """Delete an access token."""
        async with self._begin_session_read_committed() as db_sess:
            query = sa.delete(EndpointTokenRow).where(EndpointTokenRow.id == token_id)
            result = await db_sess.execute(query)
            return cast(CursorResult[Any], result).rowcount > 0

    async def bulk_delete_access_tokens(
        self,
        token_ids: list[uuid.UUID],
    ) -> list[uuid.UUID]:
        """Delete multiple access tokens and return the IDs that were actually deleted."""
        if not token_ids:
            return []
        async with self._begin_session_read_committed() as db_sess:
            query = (
                sa.delete(EndpointTokenRow)
                .where(EndpointTokenRow.id.in_(token_ids))
                .returning(EndpointTokenRow.id)
            )
            result = await db_sess.execute(query)
            return [row[0] for row in result.fetchall()]

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
                        id=row.EndpointTokenRow.id,
                        token=row.EndpointTokenRow.token,
                        expires_at=row.EndpointTokenRow.expires_at,
                        created_at=row.EndpointTokenRow.created_at,
                    )
                    for row in result.rows
                ],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

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
                items=[row.DeploymentPolicyRow.to_data() for row in result.rows],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # -------------------------------------------------------------------------
    # Strategy Mutation Methods
    # -------------------------------------------------------------------------

    async def apply_strategy_mutations(
        self,
        rollout: Sequence[RBACEntityCreator[RoutingRow]],
        drain: BatchUpdater[RoutingRow] | None,
        completed_ids: set[DeploymentID],
    ) -> int:
        """Apply route mutations from a strategy evaluation cycle in a single transaction.

        Sub-step transitions are handled exclusively by the coordinator
        via ``EndpointLifecycleBatchUpdaterSpec``.

        Returns:
            Number of deployments whose revision was swapped.
        """
        async with self._begin_session_read_committed() as db_sess:
            await self._create_routes(db_sess, rollout)
            await self._drain_routes(db_sess, drain)
            return await self._complete_deployment_revision_swap(db_sess, completed_ids)

    @staticmethod
    async def _create_routes(
        db_sess: SASession,
        rollout: Sequence[RBACEntityCreator[RoutingRow]],
    ) -> None:
        """Create new routes for rollout."""
        if rollout:
            await execute_rbac_entity_creators(db_sess, rollout)

    @staticmethod
    async def _drain_routes(
        db_sess: SASession,
        drain: BatchUpdater[RoutingRow] | None,
    ) -> None:
        """Drain routes by marking them for termination."""
        if drain:
            await execute_batch_updater(db_sess, drain)

    @staticmethod
    async def _complete_deployment_revision_swap(
        db_sess: SASession,
        completed_ids: set[DeploymentID],
    ) -> int:
        """Swap deploying_revision → current_revision for completed deployments."""
        if not completed_ids:
            return 0
        query = (
            sa.update(EndpointRow)
            .where(
                EndpointRow.id.in_(completed_ids),
                EndpointRow.deploying_revision.is_not(None),
            )
            .values(
                current_revision=EndpointRow.deploying_revision,
                deploying_revision=None,
                sub_step=None,
            )
        )
        result = await db_sess.execute(query)
        return cast(CursorResult[Any], result).rowcount

    async def clear_deploying_revision(
        self,
        deployment_ids: set[DeploymentID],
    ) -> None:
        """Clear deploying_revision and sub_step for rolled-back deployments.

        This is called explicitly by ``DeployingRollingBackHandler`` after
        rollback completes, NOT automatically by apply_strategy_mutations.
        """
        if not deployment_ids:
            return
        async with self._begin_session_read_committed() as db_sess:
            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id.in_(deployment_ids))
                .values(
                    deploying_revision=None,
                    sub_step=None,
                )
            )
            await db_sess.execute(query)

    async def search_revision_resource_slots(
        self,
        revision_id: DeploymentRevisionID,
        querier: BatchQuerier,
    ) -> tuple[list[tuple[str, Decimal]], int, bool, bool]:
        """Search resource slots allocated to a deployment revision.

        Returns (items, total_count, has_next_page, has_previous_page).
        Each item is a (slot_name, quantity) tuple.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select(DeploymentRevisionResourceSlotRow, ResourceSlotTypeRow.rank)
                .join(
                    ResourceSlotTypeRow,
                    DeploymentRevisionResourceSlotRow.slot_name == ResourceSlotTypeRow.slot_name,
                )
                .where(DeploymentRevisionResourceSlotRow.revision_id == revision_id)
            )
            result = await execute_batch_querier(db_sess, query, querier)
            items: list[tuple[str, Decimal]] = [
                (
                    row.DeploymentRevisionResourceSlotRow.slot_name,
                    row.DeploymentRevisionResourceSlotRow.quantity,
                )
                for row in result.rows
            ]
            return items, result.total_count, result.has_next_page, result.has_previous_page

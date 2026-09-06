"""Database source for replica group repository operations."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerOptions,
    DeploymentInfo,
    ReplicaGroupData,
    ReplicaGroupHandlerCategory,
    ReplicaGroupHistoryData,
    ReplicaGroupLifecycle,
    RouteStatus,
    RouteSubStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.model_serving.types import RoutingData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.endpoint.updaters import EndpointReplicaGroupUpdater
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.replica_group.creators import ReplicaGroupCreator
from ai.backend.manager.models.replica_group.searchers import (
    ReplicaGroupDeploySchedulingViewSearcher,
    ReplicaGroupScalingSchedulingViewSearcher,
    ReplicaGroupSearcher,
)
from ai.backend.manager.models.replica_group.updaters import ReplicaGroupDeployUpdater
from ai.backend.manager.models.replica_group_history import ReplicaGroupHistoryRow
from ai.backend.manager.models.replica_group_history.conditions import (
    ReplicaGroupHistoryConditions,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.routing.creators import ReplicaCreator
from ai.backend.manager.models.routing.updaters import ReplicaBatchUpdater
from ai.backend.manager.models.session_group.creators import SessionGroupCreator
from ai.backend.manager.models.specs.creator import FieldToCreate
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.repositories.ops.v2.reconciler.write import ReconcileTransition
from ai.backend.manager.repositories.ops.v2.replica_group.provider import ReplicaGroupOpsProvider
from ai.backend.manager.repositories.ops.v2.replica_group.query import ReplicaGroupQueryOps
from ai.backend.manager.repositories.ops.v2.replica_group.read import ReplicaGroupReadOps
from ai.backend.manager.repositories.replica_group.types import (
    ApplyWritesResult,
    AutoscaleReconcileFetch,
    GroupRolloutSetup,
    GroupRouteCreateInstruction,
    GroupRouteDrainInstruction,
    LifecycleReconcileFetch,
    ReplicaGroupLifecycleReconcileApply,
    ReplicaGroupReconcileTransition,
    ReplicaGroupScalingReconcileApply,
    ScalingReconcileFetch,
)
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.manager.views.replica_group import (
    ReplicaGroupAutoscaleReconcileView,
    ReplicaGroupDeploySchedulingView,
    ReplicaGroupLifecycleReconcileView,
    ReplicaGroupScalingReconcileView,
    ReplicaGroupScalingSchedulingView,
    RevisionReplicaCount,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ReplicaGroupDBSource:
    _ops: ReplicaGroupOpsProvider

    def __init__(self, ops_provider: ReplicaGroupOpsProvider) -> None:
        self._ops = ops_provider

    async def search_deploy_scheduling_views(
        self,
        conditions: Sequence[QueryCondition],
    ) -> list[ReplicaGroupDeploySchedulingView]:
        async with self._ops.read_ops() as r:
            result = await r.search_in_global(
                ReplicaGroupDeploySchedulingViewSearcher(
                    pagination=NoPagination(), conditions=list(conditions)
                )
            )
            return result.items

    async def search_scaling_scheduling_views(
        self,
        conditions: Sequence[QueryCondition],
    ) -> list[ReplicaGroupScalingSchedulingView]:
        async with self._ops.read_ops() as r:
            result = await r.search_in_global(
                ReplicaGroupScalingSchedulingViewSearcher(
                    pagination=NoPagination(), conditions=list(conditions)
                )
            )
            return result.items

    async def fetch_scaling_reconcile_views(
        self,
        conditions: Sequence[QueryCondition],
        category: ReplicaGroupHandlerCategory,
    ) -> ScalingReconcileFetch:
        async with self._ops.read_ops() as r:
            now = await r.current_time()
            groups = await self._search_groups(r, conditions)
            group_ids = [group.id for group in groups]
            counts = await r.live_serving_counts_by_revision(group_ids)
            last_histories = await r.latest_history_by_group(group_ids, category)
            handler_options = await r.handler_options_by_deployment([
                group.deployment_id for group in groups
            ])
            empty = RevisionReplicaCount(live=0, serving=0)
            views: list[ReplicaGroupScalingReconcileView] = []
            for group in groups:
                group_counts = counts.get(group.id, {})
                current_counts = (
                    group_counts.get(group.current_revision_id, empty)
                    if group.current_revision_id is not None
                    else empty
                )
                target_counts = (
                    group_counts.get(group.target_revision_id, empty)
                    if group.target_revision_id is not None
                    else empty
                )
                views.append(
                    ReplicaGroupScalingReconcileView(
                        group_id=group.id,
                        deployment_id=group.deployment_id,
                        current_revision_id=group.current_revision_id,
                        target_revision_id=group.target_revision_id,
                        scaling_status=group.scaling_status,
                        desired_current_replica_count=group.desired_current_replica_count,
                        desired_target_replica_count=group.desired_target_replica_count,
                        current_live_replica_count=current_counts.live,
                        current_serving_replica_count=current_counts.serving,
                        target_live_replica_count=target_counts.live,
                        target_serving_replica_count=target_counts.serving,
                        last_history=last_histories.get(group.id),
                        handler_options=handler_options.get(
                            group.deployment_id, DeploymentHandlerOptions()
                        ),
                    )
                )
            return ScalingReconcileFetch(views=views, now=now)

    async def fetch_lifecycle_reconcile_views(
        self,
        conditions: Sequence[QueryCondition],
        category: ReplicaGroupHandlerCategory,
    ) -> LifecycleReconcileFetch:
        async with self._ops.read_ops() as r:
            now = await r.current_time()
            groups = await self._search_groups(r, conditions)
            group_ids = [group.id for group in groups]
            deployment_ids = [group.deployment_id for group in groups]
            counts = await r.live_serving_counts_by_revision(group_ids)
            last_histories = await r.latest_history_by_group(group_ids, category)
            handler_options = await r.handler_options_by_deployment(deployment_ids)
            deployment_desired = await r.desired_replicas_by_deployment(deployment_ids)
            empty = RevisionReplicaCount(live=0, serving=0)
            views = [
                ReplicaGroupLifecycleReconcileView(
                    group_id=group.id,
                    deployment_id=group.deployment_id,
                    current_revision_id=group.current_revision_id,
                    target_revision_id=group.target_revision_id,
                    lifecycle=group.lifecycle,
                    scaling_status=group.scaling_status,
                    desired_current_replica_count=group.desired_current_replica_count,
                    desired_target_replica_count=group.desired_target_replica_count,
                    current_live_replica_count=(
                        counts.get(group.id, {}).get(group.current_revision_id, empty).live
                        if group.current_revision_id is not None
                        else 0
                    ),
                    deployment_desired_replica_count=deployment_desired.get(group.deployment_id, 0),
                    rollout=group.rollout,
                    last_history=last_histories.get(group.id),
                    handler_options=handler_options.get(
                        group.deployment_id, DeploymentHandlerOptions()
                    ),
                )
                for group in groups
            ]
            return LifecycleReconcileFetch(views=views, now=now)

    async def fetch_autoscale_reconcile_views(
        self,
        conditions: Sequence[QueryCondition],
        category: ReplicaGroupHandlerCategory,
    ) -> AutoscaleReconcileFetch:
        async with self._ops.read_ops() as r:
            now = await r.current_time()
            groups = await self._search_groups(r, conditions)
            group_ids = [group.id for group in groups]
            deployment_ids = [group.deployment_id for group in groups]
            counts = await r.live_serving_counts_by_revision(group_ids)
            last_histories = await r.latest_history_by_group(group_ids, category)
            handler_options = await r.handler_options_by_deployment(deployment_ids)
            deployment_desired = await r.desired_replicas_by_deployment(deployment_ids)
            empty = RevisionReplicaCount(live=0, serving=0)
            views: list[ReplicaGroupAutoscaleReconcileView] = []
            for group in groups:
                current_counts = (
                    counts.get(group.id, {}).get(group.current_revision_id, empty)
                    if group.current_revision_id is not None
                    else empty
                )
                views.append(
                    ReplicaGroupAutoscaleReconcileView(
                        group_id=group.id,
                        deployment_id=group.deployment_id,
                        current_revision_id=group.current_revision_id,
                        lifecycle=group.lifecycle,
                        scaling_status=group.scaling_status,
                        desired_current_replica_count=group.desired_current_replica_count,
                        deployment_desired_replica_count=deployment_desired.get(
                            group.deployment_id, 0
                        ),
                        current_live_replica_count=current_counts.live,
                        current_serving_replica_count=current_counts.serving,
                        last_history=last_histories.get(group.id),
                        handler_options=handler_options.get(
                            group.deployment_id, DeploymentHandlerOptions()
                        ),
                    )
                )
            return AutoscaleReconcileFetch(views=views, now=now)

    async def _search_groups(
        self,
        r: ReplicaGroupReadOps,
        conditions: Sequence[QueryCondition],
    ) -> list[ReplicaGroupData]:
        result = await r.search_in_global(
            ReplicaGroupSearcher(pagination=NoPagination(), conditions=list(conditions))
        )
        return result.items

    async def current_time(self) -> datetime:
        async with self._ops.read_ops() as r:
            return await r.current_time()

    async def apply_writes(
        self,
        *,
        group_updaters: Sequence[DataUpdater[ReplicaGroupRow, ReplicaGroupData]],
        endpoint_updaters: Sequence[DataUpdater[EndpointRow, DeploymentInfo]],
    ) -> ApplyWritesResult:
        """Apply the given replica-group and endpoint updates in one transaction and return which
        rows were actually updated. Each update names one row, so a row that is gone is simply
        absent from the returned id sets."""
        updated_group_ids: set[ReplicaGroupID] = set()
        updated_endpoint_ids: set[DeploymentID] = set()
        if not group_updaters and not endpoint_updaters:
            return ApplyWritesResult(updated_group_ids, updated_endpoint_ids)
        async with self._ops.write_ops() as w:
            for group_updater in group_updaters:
                group_data = await w.update_data(group_updater)
                if group_data is not None:
                    updated_group_ids.add(group_data.id)
            for endpoint_updater in endpoint_updaters:
                endpoint_data = await w.update_data(endpoint_updater)
                if endpoint_data is not None:
                    updated_endpoint_ids.add(endpoint_data.id)
        return ApplyWritesResult(
            updated_group_ids=updated_group_ids,
            updated_endpoint_ids=updated_endpoint_ids,
        )

    async def setup_target_groups(self, setups: Sequence[GroupRolloutSetup]) -> set[DeploymentID]:
        """Set up each deployment's rollout target group in one transaction. ``use_primary_group``
        (rolling) reuses the deployment's primary group read here, creating one only if none exists;
        otherwise (blue-green/canary) a fresh group is created. Then the endpoint's
        ``target_replica_group_id`` is pointed at it. Returns the deployment ids whose endpoint
        pointer was actually set."""
        if not setups:
            return set()
        async with self._ops.write_ops() as w:
            contexts = await w.rollout_contexts([setup.deployment_id for setup in setups])
            reuse_updaters: list[ReplicaGroupDeployUpdater] = []
            endpoint_updaters: list[EndpointReplicaGroupUpdater] = []
            for setup in setups:
                context = contexts.get(setup.deployment_id)
                if context is None:
                    # The deployment disappeared between the read and here;
                    # its rollout has nothing left to point at.
                    continue
                primary_group_id = context.primary_replica_group_id
                if setup.spec.use_primary_group and primary_group_id is not None:
                    reuse_updaters.append(
                        ReplicaGroupDeployUpdater(
                            replica_group_id=primary_group_id,
                            target_revision_id=TriState.update(setup.target_revision_id),
                            lifecycle=OptionalState.update(ReplicaGroupLifecycle.ROLLING),
                        )
                    )
                    target_group_id = primary_group_id
                else:
                    # A fresh replica group (blue-green / canary) brings its own
                    # session group, inheriting the endpoint's ownership scope.
                    session_group = await w.create_entity(
                        SessionGroupCreator.for_replica_group(
                            domain_name=context.domain_name,
                            project_id=context.project_id,
                            owner_user_id=context.session_owner_id,
                        )
                    )
                    created = await w.create_field(
                        setup.deployment_id,
                        ReplicaGroupCreator.for_rollout_target(
                            session_group_id=session_group.id,
                            rollout=setup.spec.rollout,
                            target_revision_id=setup.target_revision_id,
                            desired_target_replica_count=setup.desired_target_replica_count,
                        ),
                    )
                    target_group_id = created.id
                endpoint_updaters.append(
                    EndpointReplicaGroupUpdater(
                        deployment_id=setup.deployment_id,
                        target_replica_group_id=TriState.update(target_group_id),
                    )
                )
            for reuse_updater in reuse_updaters:
                await w.update_data(reuse_updater)
            updated_deployment_ids: set[DeploymentID] = set()
            for endpoint_updater in endpoint_updaters:
                endpoint_data = await w.update_data(endpoint_updater)
                if endpoint_data is not None:
                    updated_deployment_ids.add(endpoint_data.id)
            return updated_deployment_ids

    async def apply_scaling_reconcile(
        self,
        apply: ReplicaGroupScalingReconcileApply,
    ) -> None:
        async with self._ops.write_ops() as w:
            creators = await self._build_route_creators(w, apply.create_instructions)
            drain_updater = await self._build_drain_updater(w, apply.drain_instructions)
            if creators:
                await w.atomic_create_fields(creators)
            if drain_updater is not None:
                await w.batch_update_in_global(drain_updater)
            await w.apply_transitions([
                self._to_ops_transition(transition) for transition in apply.transitions
            ])

    async def apply_lifecycle_reconcile(
        self,
        apply: ReplicaGroupLifecycleReconcileApply,
    ) -> None:
        async with self._ops.write_ops() as w:
            await w.apply_transitions([
                self._to_ops_transition(transition) for transition in apply.transitions
            ])

    def _to_ops_transition(
        self,
        transition: ReplicaGroupReconcileTransition,
    ) -> ReconcileTransition[
        DeploymentID,
        ReplicaGroupRow,
        ReplicaGroupData,
        ReplicaGroupHistoryRow,
        ReplicaGroupHistoryData,
    ]:
        creator = transition.history_creator
        return ReconcileTransition(
            owner_id=transition.deployment_id,
            history_creator=creator,
            match_conditions=[
                ReplicaGroupHistoryConditions.by_replica_group_ids([creator.replica_group_id]),
                ReplicaGroupHistoryConditions.by_category(creator.category),
            ],
            status_updater=transition.status_updater,
        )

    async def _build_route_creators(
        self,
        r: ReplicaGroupQueryOps,
        instructions: Sequence[GroupRouteCreateInstruction],
    ) -> list[FieldToCreate[DeploymentID, RoutingRow, RoutingData]]:
        if not instructions:
            return []
        contexts = await r.rollout_contexts([
            instruction.deployment_id for instruction in instructions
        ])
        route_configs = await r.revision_route_configs([
            instruction.revision_id for instruction in instructions
        ])
        creations: list[FieldToCreate[DeploymentID, RoutingRow, RoutingData]] = []
        for instruction in instructions:
            context = contexts[instruction.deployment_id]
            route_config = route_configs[instruction.revision_id]
            for _ in range(instruction.count):
                creations.append(
                    FieldToCreate(
                        owner_id=instruction.deployment_id,
                        creator=ReplicaCreator(
                            session_owner_id=context.session_owner_id,
                            domain=context.domain_name,
                            project_id=context.project_id,
                            revision_id=instruction.revision_id,
                            health_check=route_config.health_check,
                            termination_grace_period=route_config.termination_grace_period,
                            replica_group_id=instruction.replica_group_id,
                            traffic_status=RouteTrafficStatus.INACTIVE,
                        ),
                    )
                )
        return creations

    async def _build_drain_updater(
        self,
        r: ReplicaGroupQueryOps,
        drain_instructions: Sequence[GroupRouteDrainInstruction],
    ) -> ReplicaBatchUpdater | None:
        route_ids: list[UUID] = []
        for drain in drain_instructions:
            if drain.count <= 0:
                continue
            route_ids.extend(
                await r.drain_candidate_route_ids(
                    drain.replica_group_id, drain.revision_id, drain.count
                )
            )
        if not route_ids:
            return None
        return ReplicaBatchUpdater(
            replica_ids=route_ids,
            status=OptionalState.update(RouteStatus.TERMINATING),
            traffic_status=OptionalState.update(RouteTrafficStatus.INACTIVE),
            sub_status=TriState.update(RouteSubStatus.DRAINING),
        )

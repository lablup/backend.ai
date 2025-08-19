"""Auto-scaler for deployment replicas."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from ai.backend.common.types import AutoScalingMetricComparator
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.deployment import DeploymentRepository

from .exceptions import ScalingError
from .replica_controller import ReplicaController
from .types import ScalingDecision

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class AutoScalerArgs:
    """Arguments for initializing AutoScaler."""

    repository: DeploymentRepository
    replica_controller: ReplicaController
    config_provider: ManagerConfigProvider


class AutoScaler:
    """Auto-scaler for managing deployment replica counts based on metrics."""

    _repository: DeploymentRepository
    _replica_controller: ReplicaController
    _config_provider: ManagerConfigProvider

    def __init__(self, args: AutoScalerArgs) -> None:
        self._repository = args.repository
        self._replica_controller = args.replica_controller
        self._config_provider = args.config_provider

    async def evaluate_endpoints(self) -> list[ScalingDecision]:
        """
        Evaluate all endpoints for auto-scaling decisions.

        :return: List of scaling decisions
        """
        decisions = []

        try:
            # Get all active endpoints
            endpoint_ids = await self._repository.get_active_endpoint_ids()

            for endpoint_id in endpoint_ids:
                decision = await self._evaluate_endpoint(endpoint_id)
                if decision:
                    decisions.append(decision)

        except Exception as e:
            log.error("Failed to evaluate endpoints for auto-scaling: {}", str(e))

        return decisions

    async def _evaluate_endpoint(
        self,
        endpoint_id: UUID,
    ) -> Optional[ScalingDecision]:
        """
        Evaluate a single endpoint for auto-scaling.

        :param endpoint_id: ID of the endpoint
        :return: Scaling decision or None if no scaling needed
        """
        try:
            # Get scaling data
            scaling_data = await self._repository.get_scaling_data(endpoint_id)
            if not scaling_data:
                return None

            endpoint = scaling_data.endpoint
            rules = scaling_data.rules
            metrics = scaling_data.metrics

            # Check if endpoint has auto-scaling rules
            if not rules:
                return None

            # Check cooldown period
            if scaling_data.last_scaling_time:
                last_time = datetime.fromisoformat(scaling_data.last_scaling_time)
                cooldown = timedelta(seconds=min(r.cooldown_seconds for r in rules))
                if datetime.now(timezone.utc) - last_time < cooldown:
                    log.debug(
                        "Endpoint {} still in cooldown period",
                        endpoint_id,
                    )
                    return None

            # Evaluate each rule
            for rule in rules:
                if not rule.enabled:
                    continue

                decision = self._evaluate_rule(
                    endpoint,
                    rule,
                    metrics,
                )
                if decision:
                    return decision

            return None

        except Exception as e:
            log.error(
                "Failed to evaluate endpoint {} for auto-scaling: {}",
                endpoint_id,
                str(e),
            )
            return None

    def _evaluate_rule(
        self,
        endpoint,
        rule,
        metrics: dict[str, float],
    ) -> Optional[ScalingDecision]:
        """
        Evaluate a single auto-scaling rule.

        :param endpoint: Endpoint data
        :param rule: Auto-scaling rule
        :param metrics: Current metrics
        :return: Scaling decision or None
        """
        # Get metric value
        metric_value = metrics.get(rule.metric_name)
        if metric_value is None:
            log.debug(
                "Metric {} not available for endpoint {}",
                rule.metric_name,
                endpoint.id,
            )
            return None

        # Check threshold
        threshold = float(rule.threshold)
        should_scale = False
        scale_direction = 0  # -1 for down, 0 for no change, 1 for up

        if rule.comparator == AutoScalingMetricComparator.GREATER_THAN:
            if metric_value > threshold:
                should_scale = True
                scale_direction = 1
        elif rule.comparator == AutoScalingMetricComparator.LESS_THAN:
            if metric_value < threshold:
                should_scale = True
                scale_direction = -1
        elif rule.comparator == AutoScalingMetricComparator.GREATER_THAN_OR_EQUAL:
            if metric_value >= threshold:
                should_scale = True
                scale_direction = 1
        elif rule.comparator == AutoScalingMetricComparator.LESS_THAN_OR_EQUAL:
            if metric_value <= threshold:
                should_scale = True
                scale_direction = -1

        if not should_scale:
            return None

        # Calculate target replicas
        current_replicas = endpoint.replicas
        if scale_direction > 0:
            # Scale up
            target_replicas = current_replicas + rule.step_size
            if rule.max_replicas:
                target_replicas = min(target_replicas, rule.max_replicas)
            reason = f"Metric {rule.metric_name} ({metric_value}) > {threshold}"
        else:
            # Scale down
            target_replicas = current_replicas - rule.step_size
            if rule.min_replicas:
                target_replicas = max(target_replicas, rule.min_replicas)
            else:
                target_replicas = max(target_replicas, 1)  # Keep at least 1 replica
            reason = f"Metric {rule.metric_name} ({metric_value}) < {threshold}"

        # Check if scaling is needed
        if target_replicas == current_replicas:
            return None

        return ScalingDecision(
            endpoint_id=endpoint.id,
            current_replicas=current_replicas,
            target_replicas=target_replicas,
            reason=reason,
            metric_value=metric_value,
            rule_id=rule.id,
            timestamp=datetime.now(timezone.utc),
        )

    async def trigger_scaling(
        self,
        decision: ScalingDecision,
    ) -> None:
        """
        Trigger scaling based on a decision.

        :param decision: Scaling decision to execute
        """
        try:
            # Get replica spec
            replica_spec = await self._repository.get_replica_spec(decision.endpoint_id)
            if not replica_spec:
                raise ScalingError("Failed to get replica spec")

            # Calculate replicas to add/remove
            replica_diff = decision.target_replicas - decision.current_replicas

            if replica_diff > 0:
                # Scale up
                log.info(
                    "Scaling up endpoint {} by {} replicas",
                    decision.endpoint_id,
                    replica_diff,
                )
                await self._replica_controller.create_replicas(
                    replica_spec,
                    replica_diff,
                )
            elif replica_diff < 0:
                # Scale down
                log.info(
                    "Scaling down endpoint {} by {} replicas",
                    decision.endpoint_id,
                    abs(replica_diff),
                )

                # Get replicas to destroy (preferably unhealthy ones)
                all_replicas = await self._repository.get_endpoint_replicas(decision.endpoint_id)
                replicas_to_destroy = all_replicas[: abs(replica_diff)]
                replica_ids = [r.id for r in replicas_to_destroy]

                await self._replica_controller.destroy_replicas(
                    decision.endpoint_id,
                    replica_ids,
                )

            # Update endpoint replica count
            await self._repository.update_endpoint_replicas(
                decision.endpoint_id,
                decision.target_replicas,
            )

            # Update last scaling time
            await self._repository.update_last_scaling_time(
                decision.endpoint_id,
                datetime.now(timezone.utc).isoformat(),
            )

        except Exception as e:
            log.error(
                "Failed to trigger scaling for endpoint {}: {}",
                decision.endpoint_id,
                str(e),
            )
            raise ScalingError(f"Failed to trigger scaling: {str(e)}") from e

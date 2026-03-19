"""GraphQL types for DeploymentPolicy."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Self
from uuid import UUID

import strawberry
from strawberry import ID
from strawberry.relay import NodeID

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.deployment.request import (
    BlueGreenConfigInput as BlueGreenConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    RollingUpdateConfigInput as RollingUpdateConfigInputDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_node_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.data.deployment.upserter import DeploymentPolicyUpserter
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.deployment import InvalidDeploymentStrategySpec
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec

# Enum defined here to avoid circular import with deployment.py
DeploymentStrategyTypeGQL: type[DeploymentStrategy] = strawberry.enum(
    DeploymentStrategy,
    name="DeploymentStrategyType",
    description="Added in 25.19.0. This enum represents the deployment strategy type of a model deployment, indicating the strategy used for deployment.",
)

# ========== Output Types (Response) ==========


@strawberry.interface(
    name="DeploymentStrategySpec",
    description="Added in 25.19.0. Base interface for deployment strategy specifications.",
)
class DeploymentStrategySpecGQL:
    strategy: DeploymentStrategyTypeGQL


@gql_node_type(
    BackendAIGQLMeta(added_version="25.19.0", description="Rolling update strategy specification."),
    name="RollingUpdateStrategySpec",
)
class RollingUpdateStrategySpecGQL(DeploymentStrategySpecGQL):
    max_surge: int
    max_unavailable: int


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.19.0", description="Blue-green deployment strategy specification."
    ),
    name="BlueGreenStrategySpec",
)
class BlueGreenStrategySpecGQL(DeploymentStrategySpecGQL):
    auto_promote: bool
    promote_delay_seconds: int


@gql_node_type(
    BackendAIGQLMeta(added_version="25.19.0", description="Deployment policy configuration."),
    name="DeploymentPolicy",
)
class DeploymentPolicyGQL(PydanticNodeMixin[Any]):
    id: NodeID[str]
    strategy_spec: DeploymentStrategySpecGQL
    rollback_on_failure: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_data(cls, data: DeploymentPolicyData) -> Self:
        match data.strategy:
            case DeploymentStrategy.ROLLING:
                if not isinstance(data.strategy_spec, RollingUpdateSpec):
                    raise InvalidDeploymentStrategySpec(
                        "Expected RollingUpdateSpec for ROLLING strategy"
                    )
                return cls(
                    id=ID(str(data.id)),
                    strategy_spec=RollingUpdateStrategySpecGQL(
                        strategy=DeploymentStrategyTypeGQL.ROLLING,
                        max_surge=data.strategy_spec.max_surge,
                        max_unavailable=data.strategy_spec.max_unavailable,
                    ),
                    rollback_on_failure=data.rollback_on_failure,
                    created_at=data.created_at,
                    updated_at=data.updated_at,
                )
            case DeploymentStrategy.BLUE_GREEN:
                if not isinstance(data.strategy_spec, BlueGreenSpec):
                    raise InvalidDeploymentStrategySpec(
                        "Expected BlueGreenSpec for BLUE_GREEN strategy"
                    )
                return cls(
                    id=ID(str(data.id)),
                    strategy_spec=BlueGreenStrategySpecGQL(
                        strategy=DeploymentStrategyTypeGQL.BLUE_GREEN,
                        auto_promote=data.strategy_spec.auto_promote,
                        promote_delay_seconds=data.strategy_spec.promote_delay_seconds,
                    ),
                    rollback_on_failure=data.rollback_on_failure,
                    created_at=data.created_at,
                    updated_at=data.updated_at,
                )


# ========== Input Types ==========


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Configuration for rolling update strategy.", added_version="25.19.0"
    ),
    model=RollingUpdateConfigInputDTO,
    name="RollingUpdateConfigInput",
)
class RollingUpdateConfigInputGQL:
    max_surge: int = 1
    max_unavailable: int = 0

    def to_spec(self) -> RollingUpdateSpec:
        return RollingUpdateSpec(
            max_surge=self.max_surge,
            max_unavailable=self.max_unavailable,
        )

    def to_pydantic(self) -> RollingUpdateConfigInputDTO:
        return RollingUpdateConfigInputDTO(
            max_surge=self.max_surge,
            max_unavailable=self.max_unavailable,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Configuration for blue-green deployment strategy.", added_version="25.19.0"
    ),
    model=BlueGreenConfigInputDTO,
    name="BlueGreenConfigInput",
)
class BlueGreenConfigInputGQL:
    auto_promote: bool = False
    promote_delay_seconds: int = 0

    def to_spec(self) -> BlueGreenSpec:
        return BlueGreenSpec(
            auto_promote=self.auto_promote,
            promote_delay_seconds=self.promote_delay_seconds,
        )

    def to_pydantic(self) -> BlueGreenConfigInputDTO:
        return BlueGreenConfigInputDTO(
            auto_promote=self.auto_promote,
            promote_delay_seconds=self.promote_delay_seconds,
        )


# ========== Mutation Input/Payload Types ==========


@strawberry.input(
    name="UpdateDeploymentPolicyInput",
    description=dedent_strip("""
        Added in 26.4.0.
        Input for creating or updating a deployment policy (upsert semantics).
        Specify the target deployment_id and the desired strategy type.
        Exactly one of rolling_update or blue_green must be provided,
        matching the chosen strategy type.
        If a policy already exists for the deployment, it is replaced entirely.
    """),
)
class UpdateDeploymentPolicyInputGQL:
    deployment_id: ID
    strategy: DeploymentStrategyTypeGQL
    rollback_on_failure: bool = False
    rolling_update: RollingUpdateConfigInputGQL | None = None
    blue_green: BlueGreenConfigInputGQL | None = None

    def to_upserter(self) -> DeploymentPolicyUpserter:
        """Convert to DeploymentPolicyUpserter for the service layer."""

        strategy = DeploymentStrategy(self.strategy.value)
        strategy_spec: RollingUpdateSpec | BlueGreenSpec
        match strategy:
            case DeploymentStrategy.ROLLING:
                if self.rolling_update is None:
                    raise InvalidAPIParameters(
                        "rolling_update config required for ROLLING strategy"
                    )
                strategy_spec = self.rolling_update.to_spec()
            case DeploymentStrategy.BLUE_GREEN:
                if self.blue_green is None:
                    raise InvalidAPIParameters("blue_green config required for BLUE_GREEN strategy")
                strategy_spec = self.blue_green.to_spec()
            case _:
                raise InvalidAPIParameters(f"Unsupported deployment strategy: {strategy}")

        return DeploymentPolicyUpserter(
            deployment_id=UUID(str(self.deployment_id)),
            strategy=strategy,
            strategy_spec=strategy_spec,
            rollback_on_failure=self.rollback_on_failure,
        )


@strawberry.type(
    name="UpdateDeploymentPolicyPayload",
    description=dedent_strip("""
        Added in 26.4.0.
        Result payload returned after creating or updating a deployment policy.
        Contains the full deployment_policy object reflecting the applied configuration.
    """),
)
class UpdateDeploymentPolicyPayloadGQL:
    deployment_policy: DeploymentPolicyGQL

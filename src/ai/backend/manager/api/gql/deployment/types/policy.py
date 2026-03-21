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
from ai.backend.common.dto.manager.v2.deployment.request import (
    UpsertDeploymentPolicyInput as UpsertDeploymentPolicyInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    DeploymentPolicyNode as DeploymentPolicyNodeDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_node_type,
    gql_output_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.errors.deployment import InvalidDeploymentStrategySpec

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


@gql_output_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Rolling update strategy specification.",
    ),
    name="RollingUpdateStrategySpec",
)
class RollingUpdateStrategySpecGQL(DeploymentStrategySpecGQL):
    max_surge: int
    max_unavailable: int


@gql_output_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Blue-green deployment strategy specification.",
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
    def from_pydantic(
        cls,
        dto: DeploymentPolicyNodeDTO,
        extra: dict[str, Any] | None = None,
        *,
        id_field: str = "id",
    ) -> Self:
        match dto.strategy:
            case DeploymentStrategy.ROLLING:
                rolling = dto.rolling_update
                strategy_spec: DeploymentStrategySpecGQL = RollingUpdateStrategySpecGQL(
                    strategy=DeploymentStrategyTypeGQL.ROLLING,
                    max_surge=rolling.max_surge if rolling is not None else 1,
                    max_unavailable=rolling.max_unavailable if rolling is not None else 0,
                )
            case DeploymentStrategy.BLUE_GREEN:
                bg = dto.blue_green
                strategy_spec = BlueGreenStrategySpecGQL(
                    strategy=DeploymentStrategyTypeGQL.BLUE_GREEN,
                    auto_promote=bg.auto_promote if bg is not None else False,
                    promote_delay_seconds=bg.promote_delay_seconds if bg is not None else 0,
                )
            case _:
                raise InvalidDeploymentStrategySpec(
                    f"Unsupported deployment strategy: {dto.strategy}"
                )
        return cls(
            id=ID(str(dto.id)),
            strategy_spec=strategy_spec,
            rollback_on_failure=dto.rollback_on_failure,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
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

    def to_pydantic(self) -> BlueGreenConfigInputDTO:
        return BlueGreenConfigInputDTO(
            auto_promote=self.auto_promote,
            promote_delay_seconds=self.promote_delay_seconds,
        )


# ========== Mutation Input/Payload Types ==========


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=dedent_strip("""
            Input for creating or updating a deployment policy (upsert semantics).
            Specify the target deployment_id and the desired strategy type.
            Exactly one of rolling_update or blue_green must be provided,
            matching the chosen strategy type.
            If a policy already exists for the deployment, it is replaced entirely.
        """),
        added_version="26.4.0",
    ),
    model=UpsertDeploymentPolicyInputDTO,
    name="UpdateDeploymentPolicyInput",
)
class UpdateDeploymentPolicyInputGQL:
    deployment_id: ID
    strategy: DeploymentStrategyTypeGQL
    rollback_on_failure: bool = False
    rolling_update: RollingUpdateConfigInputGQL | None = None
    blue_green: BlueGreenConfigInputGQL | None = None

    def to_pydantic(self) -> UpsertDeploymentPolicyInputDTO:
        return UpsertDeploymentPolicyInputDTO(
            deployment_id=UUID(str(self.deployment_id)),
            strategy=self.strategy,
            rollback_on_failure=self.rollback_on_failure,
            rolling_update=self.rolling_update.to_pydantic() if self.rolling_update else None,
            blue_green=self.blue_green.to_pydantic() if self.blue_green else None,
        )


@gql_output_type(
    BackendAIGQLMeta(
        added_version="26.4.0",
        description="Result payload returned after creating or updating a deployment policy. Contains the full deployment_policy object reflecting the applied configuration.",
    ),
    name="UpdateDeploymentPolicyPayload",
)
class UpdateDeploymentPolicyPayloadGQL:
    deployment_policy: DeploymentPolicyGQL

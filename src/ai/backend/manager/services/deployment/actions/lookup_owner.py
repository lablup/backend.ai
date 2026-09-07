"""Owner resolutions reaching a deployment from the rows that live under it."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.deployment import DEPLOYMENT_ENTITY_TYPE, DeploymentID
from ai.backend.common.data.entity.deployment_policy import DeploymentPolicyID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.deployment_token import DeploymentTokenID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import (
    LookupFieldOwnerByKeyOpsAction,
    LookupFieldOwnerOpsAction,
)
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.deployment_policy.lookups import DeploymentPolicyOwnerLookup
from ai.backend.manager.models.deployment_revision.lookups import DeploymentRevisionOwnerLookup
from ai.backend.manager.models.endpoint.lookups import (
    AutoScalingRuleDeploymentLookup,
    DeploymentAccessTokenOwnerLookup,
)
from ai.backend.manager.models.routing.lookups import ReplicaOwnerLookup


@dataclass(frozen=True)
class AutoScalingRuleKey(LookupKey):
    """The auto-scaling rule a request names, which its deployment is read from."""

    rule_id: UUID

    @override
    def kind(self) -> str:
        return "auto_scaling_rule_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"auto_scaling_rule_id": str(self.rule_id)}


@dataclass
class LookupAutoScalingRuleDeploymentAction(LookupFieldOwnerByKeyOpsAction[DeploymentID]):
    """Resolve the auto-scaling rule's id into the deployment it belongs to."""

    rule_id: UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_auto_scaling_rule_deployment"

    @override
    def lookup_key(self) -> AutoScalingRuleKey:
        return AutoScalingRuleKey(rule_id=self.rule_id)

    @override
    def to_owner_lookup(self) -> AutoScalingRuleDeploymentLookup:
        return AutoScalingRuleDeploymentLookup(rule_id=self.rule_id)


@dataclass(frozen=True)
class DeploymentRevisionIDLookupKey(LookupKey):
    """A revision's id, resolved into the deployment it belongs to."""

    revision_id: DeploymentRevisionID

    @override
    def kind(self) -> str:
        return "deployment_revision_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.revision_id)}


@dataclass
class LookupDeploymentRevisionOwnerAction(
    LookupFieldOwnerOpsAction[DeploymentRevisionID, DeploymentID]
):
    """The deployment a revision was taken of."""

    revision_id: DeploymentRevisionID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_deployment_revision_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return DeploymentRevisionIDLookupKey(self.revision_id)

    @override
    def field_id(self) -> DeploymentRevisionID:
        return self.revision_id

    @override
    def to_owner_lookup(self) -> DeploymentRevisionOwnerLookup:
        return DeploymentRevisionOwnerLookup()


@dataclass
class LookupBulkDeploymentRevisionOwnerAction(
    LookupBulkFieldOwnerOpsAction[DeploymentRevisionID, DeploymentID]
):
    """The deployments several revisions were taken of."""

    revision_ids: Sequence[DeploymentRevisionID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_deployment_revision_owner"

    @override
    def to_lookup_key(self, field_id: DeploymentRevisionID) -> LookupKey:
        return DeploymentRevisionIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[DeploymentRevisionID]:
        return tuple(self.revision_ids)

    @override
    def to_owner_lookup(self) -> DeploymentRevisionOwnerLookup:
        return DeploymentRevisionOwnerLookup()


@dataclass(frozen=True)
class ReplicaIDLookupKey(LookupKey):
    """A replica's id, resolved into the deployment it serves."""

    replica_id: ReplicaID

    @override
    def kind(self) -> str:
        return "replica_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.replica_id)}


@dataclass
class LookupReplicaOwnerAction(LookupFieldOwnerOpsAction[ReplicaID, DeploymentID]):
    """The deployment a replica serves."""

    replica_id: ReplicaID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_replica_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return ReplicaIDLookupKey(self.replica_id)

    @override
    def field_id(self) -> ReplicaID:
        return self.replica_id

    @override
    def to_owner_lookup(self) -> ReplicaOwnerLookup:
        return ReplicaOwnerLookup()


@dataclass
class LookupBulkReplicaOwnerAction(LookupBulkFieldOwnerOpsAction[ReplicaID, DeploymentID]):
    """The deployments several replicas serve."""

    replica_ids: Sequence[ReplicaID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_replica_owner"

    @override
    def to_lookup_key(self, field_id: ReplicaID) -> LookupKey:
        return ReplicaIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[ReplicaID]:
        return tuple(self.replica_ids)

    @override
    def to_owner_lookup(self) -> ReplicaOwnerLookup:
        return ReplicaOwnerLookup()


@dataclass(frozen=True)
class DeploymentTokenIDLookupKey(LookupKey):
    """An access token's id, resolved into the deployment it grants access to."""

    access_token_id: DeploymentTokenID

    @override
    def kind(self) -> str:
        return "deployment_token_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.access_token_id)}


@dataclass
class LookupDeploymentAccessTokenOwnerAction(
    LookupFieldOwnerOpsAction[DeploymentTokenID, DeploymentID]
):
    """The deployment an access token grants access to."""

    access_token_id: DeploymentTokenID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_deployment_access_token_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return DeploymentTokenIDLookupKey(self.access_token_id)

    @override
    def field_id(self) -> DeploymentTokenID:
        return self.access_token_id

    @override
    def to_owner_lookup(self) -> DeploymentAccessTokenOwnerLookup:
        return DeploymentAccessTokenOwnerLookup()


@dataclass
class LookupBulkDeploymentAccessTokenOwnerAction(
    LookupBulkFieldOwnerOpsAction[DeploymentTokenID, DeploymentID]
):
    """The deployments several access tokens grant access to."""

    access_token_ids: Sequence[DeploymentTokenID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_deployment_access_token_owner"

    @override
    def to_lookup_key(self, field_id: DeploymentTokenID) -> LookupKey:
        return DeploymentTokenIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[DeploymentTokenID]:
        return tuple(self.access_token_ids)

    @override
    def to_owner_lookup(self) -> DeploymentAccessTokenOwnerLookup:
        return DeploymentAccessTokenOwnerLookup()


@dataclass(frozen=True)
class DeploymentPolicyIDLookupKey(LookupKey):
    """A policy's id, resolved into the deployment it belongs to."""

    policy_id: DeploymentPolicyID

    @override
    def kind(self) -> str:
        return "deployment_policy_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.policy_id)}


@dataclass
class LookupDeploymentPolicyOwnerAction(
    LookupFieldOwnerOpsAction[DeploymentPolicyID, DeploymentID]
):
    """The deployment a policy belongs to."""

    policy_id: DeploymentPolicyID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_deployment_policy_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return DeploymentPolicyIDLookupKey(self.policy_id)

    @override
    def field_id(self) -> DeploymentPolicyID:
        return self.policy_id

    @override
    def to_owner_lookup(self) -> DeploymentPolicyOwnerLookup:
        return DeploymentPolicyOwnerLookup()


@dataclass
class LookupBulkDeploymentPolicyOwnerAction(
    LookupBulkFieldOwnerOpsAction[DeploymentPolicyID, DeploymentID]
):
    """The deployments several policies belong to."""

    policy_ids: Sequence[DeploymentPolicyID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_deployment_policy_owner"

    @override
    def to_lookup_key(self, field_id: DeploymentPolicyID) -> LookupKey:
        return DeploymentPolicyIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[DeploymentPolicyID]:
        return tuple(self.policy_ids)

    @override
    def to_owner_lookup(self) -> DeploymentPolicyOwnerLookup:
        return DeploymentPolicyOwnerLookup()

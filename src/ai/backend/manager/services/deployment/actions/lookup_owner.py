"""Owner resolutions reaching a deployment from the rows that live under it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.deployment import DEPLOYMENT_ENTITY_TYPE, DeploymentID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerByKeyOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.endpoint.lookups import (
    AccessTokenDeploymentLookup,
    AutoScalingRuleDeploymentLookup,
    RevisionDeploymentLookup,
    RouteDeploymentLookup,
)


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
class AccessTokenKey(LookupKey):
    """The access token a request names, which its deployment is read from."""

    access_token_id: UUID

    @override
    def kind(self) -> str:
        return "access_token_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"access_token_id": str(self.access_token_id)}


@dataclass
class LookupAccessTokenDeploymentAction(LookupFieldOwnerByKeyOpsAction[DeploymentID]):
    """Resolve the access token's id into the deployment it belongs to."""

    access_token_id: UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_access_token_deployment"

    @override
    def lookup_key(self) -> AccessTokenKey:
        return AccessTokenKey(access_token_id=self.access_token_id)

    @override
    def to_owner_lookup(self) -> AccessTokenDeploymentLookup:
        return AccessTokenDeploymentLookup(access_token_id=self.access_token_id)


@dataclass(frozen=True)
class RouteKey(LookupKey):
    """The route a request names, which its deployment is read from."""

    route_id: UUID

    @override
    def kind(self) -> str:
        return "route_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"route_id": str(self.route_id)}


@dataclass
class LookupRouteDeploymentAction(LookupFieldOwnerByKeyOpsAction[DeploymentID]):
    """Resolve the route's id into the deployment it belongs to."""

    route_id: UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_route_deployment"

    @override
    def lookup_key(self) -> RouteKey:
        return RouteKey(route_id=self.route_id)

    @override
    def to_owner_lookup(self) -> RouteDeploymentLookup:
        return RouteDeploymentLookup(route_id=self.route_id)


@dataclass(frozen=True)
class RevisionKey(LookupKey):
    """The revision a request names, which its deployment is read from."""

    revision_id: UUID

    @override
    def kind(self) -> str:
        return "revision_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"revision_id": str(self.revision_id)}


@dataclass
class LookupRevisionDeploymentAction(LookupFieldOwnerByKeyOpsAction[DeploymentID]):
    """Resolve the revision's id into the deployment it belongs to."""

    revision_id: UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_revision_deployment"

    @override
    def lookup_key(self) -> RevisionKey:
        return RevisionKey(revision_id=self.revision_id)

    @override
    def to_owner_lookup(self) -> RevisionDeploymentLookup:
        return RevisionDeploymentLookup(revision_id=self.revision_id)

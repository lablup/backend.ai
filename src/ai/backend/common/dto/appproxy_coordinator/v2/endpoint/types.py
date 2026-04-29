"""Shared types for AppProxy coordinator endpoint DTOs.

Field aliases preserve wire-level compatibility with older Manager /
Coordinator peers that still send the pre-rename names (``group_id``
instead of ``project_id``, ``endpoint_id`` instead of ``deployment_id``).
Validation accepts both names; serialization emits the new canonical
name so the wire format converges over time.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import AliasChoices, AnyUrl, Field

from ai.backend.common.api_handlers import BaseFieldModel
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.identifier.deployment import DeploymentID


class SessionTagsModel(BaseFieldModel):
    """Session-scoped tags attached to an endpoint.

    These values identify the session that owns the endpoint (user,
    project, domain) so the proxy can authorize and scope traffic.
    """

    user_uuid: str = Field(
        ...,
        description="UUID of the session-owning user, encoded as a string.",
    )
    project_id: str = Field(
        ...,
        description=(
            "UUID of the session-owning project, encoded as a string. "
            "Formerly transmitted as ``group_id``; ``group_id`` remains a "
            "validation alias for backward compatibility."
        ),
        validation_alias=AliasChoices("project_id", "group_id"),
        serialization_alias="project_id",
    )
    domain_name: str = Field(
        ...,
        description="Name of the domain that owns the session / endpoint.",
    )


class EndpointTagsModel(BaseFieldModel):
    """Endpoint-level metadata tags.

    Carries the deployment identity and the runtime variant of the
    model service attached to this endpoint.
    """

    id: str = Field(
        ...,
        description=(
            "Deployment UUID encoded as a string. Mirrors the outer "
            "``deployment_id`` and is kept as a tag for observability."
        ),
    )
    runtime_variant: str = Field(
        ...,
        description=(
            "Runtime variant name (e.g. ``custom``, ``vllm``) of the model "
            "service hosted by this endpoint. Resolved from the typed "
            "``RuntimeVariantID`` at the wire boundary."
        ),
    )
    existing_url: str | None = Field(
        default=None,
        description=(
            "Caller-supplied URL to reuse for this endpoint (e.g. for "
            "resurrecting a previously-allocated URL). When set, the "
            "coordinator picks the worker whose frontend matches this URL."
        ),
    )


class TagsModel(BaseFieldModel):
    """Bundled session + endpoint tags attached to an endpoint."""

    session: SessionTagsModel = Field(
        ...,
        description="Session-scoped tags (user, project, domain).",
    )
    endpoint: EndpointTagsModel = Field(
        ...,
        description="Endpoint-level tags (deployment id, runtime variant, URL hint).",
    )


class CreateEndpointItem(BaseFieldModel):
    """A single endpoint to be created or synced.

    Used both as a stand-alone payload for the single-endpoint API and
    as an element of bulk create requests.
    """

    deployment_id: DeploymentID = Field(
        ...,
        description=(
            "Target deployment UUID. Formerly transmitted as "
            "``endpoint_id``; ``endpoint_id`` remains a validation alias "
            "for backward compatibility."
        ),
        validation_alias=AliasChoices("deployment_id", "endpoint_id"),
        serialization_alias="deployment_id",
    )
    version: str = Field(
        default="v2",
        description="Creation API version — always ``v2`` for this DTO.",
    )
    service_name: str = Field(
        ...,
        description=(
            "Human-readable service / endpoint name. Used when selecting "
            "a subdomain or building router names on the coordinator side."
        ),
    )
    tags: TagsModel = Field(
        ...,
        description="Session + endpoint metadata tags attached to the endpoint.",
    )
    open_to_public: bool = Field(
        default=False,
        description=(
            "If ``True``, AppProxy requires a valid API token on every "
            "incoming request and does not expose the endpoint publicly "
            "without authentication."
        ),
    )
    health_check: ModelHealthCheck | None = Field(
        default=None,
        description=(
            "Optional health check configuration. When present, the "
            "coordinator configures the load balancer to probe model "
            "service replicas using this path / interval / timeout."
        ),
    )


class CreatedEndpointItem(BaseFieldModel):
    """Result for a single created/synced endpoint."""

    deployment_id: DeploymentID = Field(
        ...,
        description=(
            "Deployment UUID that was created or synced. Formerly "
            "transmitted as ``endpoint_id``; ``endpoint_id`` remains a "
            "validation alias for backward compatibility."
        ),
        validation_alias=AliasChoices("deployment_id", "endpoint_id"),
        serialization_alias="deployment_id",
    )
    url: AnyUrl = Field(
        ...,
        description=(
            "Final endpoint URL assigned by the coordinator. Callers "
            "should persist this to the deployment row so subsequent "
            "syncs can pass it back as ``tags.endpoint.existing_url``."
        ),
    )
    health_check_enabled: bool = Field(
        ...,
        description=(
            "Whether the coordinator ended up with health checking "
            "enabled for this endpoint (mirrors whether the request "
            "supplied a ``health_check`` configuration)."
        ),
    )


class DeleteEndpointItem(BaseFieldModel):
    """A single endpoint to be removed."""

    deployment_id: DeploymentID = Field(
        ...,
        description=(
            "Deployment UUID to remove. Formerly transmitted as "
            "``endpoint_id``; ``endpoint_id`` remains a validation alias "
            "for backward compatibility."
        ),
        validation_alias=AliasChoices("deployment_id", "endpoint_id"),
        serialization_alias="deployment_id",
    )


class RouteEntry(BaseFieldModel):
    """A single (session, kernel host:port) tuple for an endpoint's routing table.

    The coordinator stores these on each circuit's ``route_info`` and the
    worker fans request traffic across them. Manager fills these in after
    a session reaches RUNNING + HEALTHY and pushes them via the bulk
    routes-sync API.
    """

    session_id: UUID = Field(
        ...,
        description="Session UUID hosting the model service replica for this route.",
    )
    route_id: UUID = Field(
        ...,
        description="Route UUID — the manager-side identity of this routing entry.",
    )
    kernel_host: str = Field(
        ...,
        description="Host / IP that the proxy uses to reach the kernel of the session.",
    )
    kernel_port: int = Field(
        ...,
        description="Port on ``kernel_host`` exposing the model service inference port.",
    )


class UpdateRoutesItem(BaseFieldModel):
    """One endpoint's routing table to be installed on the coordinator.

    The coordinator replaces ``circuit.route_info`` for the endpoint with
    ``routes`` (no merge), so the caller is expected to send the
    authoritative current set of HEALTHY routes. An empty list is valid
    and means "no traffic should land on this endpoint right now"; the
    circuit row stays.
    """

    deployment_id: DeploymentID = Field(
        ...,
        description=(
            "Target deployment UUID. ``endpoint_id`` is accepted as a "
            "validation alias for backward compatibility."
        ),
        validation_alias=AliasChoices("deployment_id", "endpoint_id"),
        serialization_alias="deployment_id",
    )
    routes: list[RouteEntry] = Field(
        ...,
        description="Authoritative routing entries (replaces the circuit's current set).",
    )


class UpdatedRoutesItem(BaseFieldModel):
    """Per-endpoint result of a bulk routes-sync call.

    Bulk routes-sync continues past per-entry failures (e.g. circuit not
    yet registered, race against deletion) and reports success / failure
    individually so the caller can decide how to handle partial failures.
    """

    deployment_id: DeploymentID = Field(
        ...,
        description="Deployment UUID that the coordinator attempted to update.",
        validation_alias=AliasChoices("deployment_id", "endpoint_id"),
        serialization_alias="deployment_id",
    )
    success: bool = Field(
        ...,
        description="``True`` when the route table was applied; ``False`` otherwise.",
    )
    error: str | None = Field(
        default=None,
        description="Human-readable error when ``success`` is ``False``; ``None`` on success.",
    )


class RegisterRoutesItem(BaseFieldModel):
    """One endpoint's set of routes to add to the coordinator (delta semantics).

    Unlike :class:`UpdateRoutesItem`, this does NOT replace
    ``circuit.route_info`` — it appends ``routes`` to whatever set the
    coordinator already has. Routes whose ``route_id`` is already present
    are silently ignored (idempotent re-register), so callers can push
    the same route twice without producing duplicates.
    """

    deployment_id: DeploymentID = Field(
        ...,
        description=(
            "Target deployment UUID. ``endpoint_id`` is accepted as a "
            "validation alias for backward compatibility."
        ),
        validation_alias=AliasChoices("deployment_id", "endpoint_id"),
        serialization_alias="deployment_id",
    )
    routes: list[RouteEntry] = Field(
        ...,
        description=(
            "Routes to append to the endpoint's circuit. Already-present route_ids are no-ops."
        ),
    )


class UnregisterRoutesItem(BaseFieldModel):
    """One endpoint's set of routes to remove from the coordinator (delta semantics).

    The caller only needs to send the ``route_id`` set — the coordinator
    looks up the matching entries on ``circuit.route_info`` and drops
    them. Already-absent route ids are silently ignored so the call is
    idempotent.
    """

    deployment_id: DeploymentID = Field(
        ...,
        description=(
            "Target deployment UUID. ``endpoint_id`` is accepted as a "
            "validation alias for backward compatibility."
        ),
        validation_alias=AliasChoices("deployment_id", "endpoint_id"),
        serialization_alias="deployment_id",
    )
    route_ids: list[UUID] = Field(
        ...,
        description=(
            "Route UUIDs to remove from the endpoint's circuit. "
            "Already-absent route ids are no-ops."
        ),
    )


class RegisteredRoutesItem(BaseFieldModel):
    """Per-endpoint result of a bulk routes-register call.

    Each entry reports which route ids were freshly added vs already
    present so callers can distinguish "first-time push" from "redundant
    push" without comparing payloads themselves.
    """

    deployment_id: DeploymentID = Field(
        ...,
        description="Deployment UUID that the coordinator attempted to register.",
        validation_alias=AliasChoices("deployment_id", "endpoint_id"),
        serialization_alias="deployment_id",
    )
    success: bool = Field(
        ...,
        description="``True`` when the registration was applied; ``False`` otherwise.",
    )
    registered_route_ids: list[UUID] = Field(
        default_factory=list,
        description="Route UUIDs that were freshly added to the circuit.",
    )
    already_registered_route_ids: list[UUID] = Field(
        default_factory=list,
        description="Route UUIDs that were already present on the circuit (idempotent no-op).",
    )
    error: str | None = Field(
        default=None,
        description="Human-readable error when ``success`` is ``False``; ``None`` on success.",
    )


class UnregisteredRoutesItem(BaseFieldModel):
    """Per-endpoint result of a bulk routes-unregister call.

    Each entry reports which route ids were dropped vs already absent so
    callers can distinguish "first-time removal" from "redundant
    removal". When ``success`` is ``False`` the caller should retry on
    the next sync cycle.
    """

    deployment_id: DeploymentID = Field(
        ...,
        description="Deployment UUID that the coordinator attempted to unregister.",
        validation_alias=AliasChoices("deployment_id", "endpoint_id"),
        serialization_alias="deployment_id",
    )
    success: bool = Field(
        ...,
        description="``True`` when the unregistration was applied; ``False`` otherwise.",
    )
    unregistered_route_ids: list[UUID] = Field(
        default_factory=list,
        description="Route UUIDs that were dropped from the circuit.",
    )
    already_absent_route_ids: list[UUID] = Field(
        default_factory=list,
        description="Route UUIDs that were already absent from the circuit (idempotent no-op).",
    )
    error: str | None = Field(
        default=None,
        description="Human-readable error when ``success`` is ``False``; ``None`` on success.",
    )


class DeletedEndpointItem(BaseFieldModel):
    """Result for a single removed endpoint.

    Delete is idempotent — an already-gone endpoint counts as
    ``success=True``. Bulk deletes continue past individual failures so
    the caller gets a complete per-entry report.
    """

    deployment_id: DeploymentID = Field(
        ...,
        description=(
            "Deployment UUID that the coordinator attempted to remove. "
            "Matches the request item order."
        ),
        validation_alias=AliasChoices("deployment_id", "endpoint_id"),
        serialization_alias="deployment_id",
    )
    success: bool = Field(
        ...,
        description=(
            "``True`` when the endpoint was removed or was already gone; "
            "``False`` when removal failed for this entry."
        ),
    )
    error: str | None = Field(
        default=None,
        description=(
            "Human-readable error message when ``success`` is ``False``. ``None`` on success."
        ),
    )

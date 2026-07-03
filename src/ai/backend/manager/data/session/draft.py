"""Progressive-fill draft shapes for session specs.

A ``SessionSpecDraft`` is the in-flight mirror of
:class:`~ai.backend.manager.data.session.spec.SessionSpec` with every
required field made Optional (or seeded with an empty default). The
preparer chain hands drafts between rules; each rule receives the
current draft plus a read-only context and returns a fresh draft via
``model_copy`` with additional fields populated.

Finalization is a Pydantic round-trip: the draft is dumped to a plain
dict with ``exclude_none=True`` and fed into ``SessionSpec.model_validate``.
That makes the spec schema the single source of truth for both
"what must be set" and error-path reporting — Pydantic's
``ValidationError`` gives the ``loc`` tuple for every missing or
ill-typed field with no hand-written path strings.

Naming contract: field names and nesting paths match 1-to-1 between
each draft and its spec sibling. Adding or renaming a spec field
requires the same change on the draft side.

Callers build :class:`SessionSpecDraft` directly from their own input
envelopes (action types, deployment revisions, ...). No conversion
method lives here — the opposite direction (deployment → session)
would force this module to import deployment types, which is the
wrong dependency direction. Each upstream layer owns its own
draft-assembly code (see e.g.
``sokovan/deployment/deployment_draft_builder.py``).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

import yarl
from pydantic import ConfigDict, Field

from ai.backend.common.identifier.domain import DomainName
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.identifier.session import SessionID
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    BackendAISchema,
    ClusterMode,
    MountInfoEntry,
    ResourceSlotEntry,
    SessionTypes,
    VFolderMount,
)
from ai.backend.manager.data.network.types import NetworkType
from ai.backend.manager.data.session.options import (
    AgentSelectionPolicy,
    FailurePolicy,
    InternalDataExtras,
    ResourceOpts,
    SessionHandlerOptions,
)


class _DraftBaseModel(BackendAISchema):
    """Base for draft sub-models.

    Matches the spec's ``_SpecBaseModel`` configuration so
    ``model_dump`` / ``model_validate`` round-trips preserve the
    embedded arbitrary types (``ResourceSlot`` and the like).
    ``frozen=True`` keeps updates pure via ``model_copy``.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)


class KernelExecutionSpecDraft(_DraftBaseModel):
    """Optional-heavy mirror of ``KernelExecutionSpec``."""

    image_id: ImageID | None = None
    resources: tuple[ResourceSlotEntry, ...] = ()
    resource_opts: ResourceOpts | None = None
    environ: Mapping[str, str] = Field(default_factory=dict)
    mounts: tuple[MountInfoEntry, ...] = ()
    startup_command: str | None = None
    bootstrap_script: str | None = None
    starts_at: datetime | None = None
    batch_timeout_sec: int | None = None


class KernelSpecDraft(_DraftBaseModel):
    """Optional-heavy mirror of ``KernelSpec``.

    Cluster-layout and user-mapping fields are filled by their
    respective rules; ``execution_spec`` is eagerly initialized so a
    rule can ``model_copy`` just the execution-level sub-draft without
    absence checks. ``vfolder_mounts`` is the per-kernel resolved slot
    :class:`ResolveVFolderMountsRule` populates after expand.
    """

    cluster_role: str | None = None
    cluster_idx: int | None = None
    cluster_hostname: str | None = None
    local_rank: int | None = None
    uid: int | None = None
    main_gid: int | None = None
    supplementary_gids: tuple[int, ...] = ()
    preopen_ports: tuple[int, ...] = ()
    internal_data: Mapping[str, Any] = Field(default_factory=dict)
    execution_spec: KernelExecutionSpecDraft = Field(default_factory=KernelExecutionSpecDraft)
    vfolder_mounts: tuple[VFolderMount, ...] = ()


class SchedulingTargetDraft(_DraftBaseModel):
    """Optional-heavy mirror of ``SchedulingTarget``."""

    designated_agents: tuple[AgentId, ...] = ()
    agent_selection_policy: AgentSelectionPolicy | None = None


class KernelGroupDraft(_DraftBaseModel):
    """Mirror of ``KernelGroup`` with an Optional-heavy ``execution_spec``.

    ``role`` and ``replica_count`` are required because a group is
    meaningless without them. ``execution_spec`` nests the execution-
    side draft so a rule can fill RG-default fields without forcing
    the caller to specify a full spec up front.

    ``preopen_ports`` is a group-level declaration (every replica in
    the group exposes the same preopen ports) that
    :class:`ExpandKernelGroupsRule` copies onto each expanded
    :attr:`KernelSpecDraft.preopen_ports`. Per-replica overrides land
    alongside task #33.
    """

    role: str
    replica_count: int
    execution_spec: KernelExecutionSpecDraft = Field(default_factory=KernelExecutionSpecDraft)
    failure_policy: FailurePolicy | None = None
    depends_on_roles: tuple[str, ...] = ()
    preopen_ports: tuple[int, ...] = ()


class SessionOptionsDraft(_DraftBaseModel):
    """Optional-heavy mirror of ``SessionOptions``."""

    priority: int | None = None
    is_preemptible: bool | None = None
    cluster_mode: ClusterMode | None = None
    cluster_size: int | None = None
    scheduling_target: SchedulingTargetDraft = Field(default_factory=SchedulingTargetDraft)
    kernel_groups: tuple[KernelGroupDraft, ...] | None = None
    handler_options: SessionHandlerOptions | None = None


class SessionIdentityDraft(_DraftBaseModel):
    """Optional-heavy mirror of ``SessionIdentity``."""

    session_id: SessionID | None = None
    creation_id: str | None = None
    session_name: str | None = None
    access_key: AccessKey | None = None
    user_uuid: UUID | None = None


class SessionNetworkDraft(_DraftBaseModel):
    """Optional-heavy mirror of ``SessionNetwork``.

    The caller typically sets ``network_id`` only (for PERSISTENT networks);
    ``network_type`` and ``use_host_network`` are populated by
    :class:`.assign_network_config_rule.AssignNetworkConfigRule`.
    """

    network_type: NetworkType | None = None
    network_id: str | None = None
    use_host_network: bool = False


class SessionScopeDraft(_DraftBaseModel):
    """Optional-heavy mirror of ``SessionScope``."""

    domain_name: DomainName | None = None
    project_id: ProjectID | None = None
    resource_group_name: ResourceGroupName | None = None


class SessionClassificationDraft(_DraftBaseModel):
    """Optional-heavy mirror of ``SessionClassification``."""

    session_type: SessionTypes | None = None
    tag: str | None = None


class SessionSpecDraft(_DraftBaseModel):
    """Top-level draft mirroring ``SessionSpec``.

    ``internal_data_extras`` carries request-envelope fields (sudo
    toggle, model-definition overlay) that feed
    :class:`KernelSpec.internal_data`. DB-sourced pieces like dotfiles
    are merged in by the preparer chain against its context — they
    never flow through the draft.
    """

    identity: SessionIdentityDraft = Field(default_factory=SessionIdentityDraft)
    scope: SessionScopeDraft = Field(default_factory=SessionScopeDraft)
    classification: SessionClassificationDraft = Field(default_factory=SessionClassificationDraft)
    network: SessionNetworkDraft = Field(default_factory=SessionNetworkDraft)
    callback_url: yarl.URL | None = None
    dependencies: tuple[SessionID, ...] = ()
    options: SessionOptionsDraft = Field(default_factory=SessionOptionsDraft)
    kernel_specs: tuple[KernelSpecDraft, ...] = ()
    internal_data_extras: InternalDataExtras = Field(default_factory=InternalDataExtras)

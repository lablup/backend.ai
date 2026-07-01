"""Resolved session and kernel creation specs.

These are the fully-materialized, per-session / per-replica shapes that
the scheduling controller finalizes from a
:class:`~ai.backend.manager.data.session.draft.SessionSpecDraft` and
hands off to the enqueue path that creates ``SessionRow`` and
``KernelRow`` records.

Top-level fields are grouped into small sub-models so a rule that only
resolves one concern (say project scope) can emit a single sub-type
without touching the rest. The same grouping is mirrored on
``SessionSpecDraft`` — finalize performs a ``model_validate`` over the
draft's ``model_dump`` so the schema here is the single source of
truth for both "what must be set" and "how it nests".
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, override
from uuid import UUID

import yarl
from pydantic import ConfigDict, Field

from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.domain import DomainID, DomainName
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.identifier.session import SessionID
from ai.backend.common.types import (
    AccessKey,
    BackendAISchema,
    SchemaValidationFailureInfo,
    SessionTypes,
    VFolderMount,
)
from ai.backend.manager.data.session.options import (
    InternalDataExtras,
    KernelExecutionSpec,
    SessionOptions,
)
from ai.backend.manager.errors.kernel import IncompleteSessionSpec
from ai.backend.manager.models.network import NetworkType


class _SpecBaseModel(BackendAISchema):
    """Base for resolved session-spec sub-models.

    ``arbitrary_types_allowed`` lets us use ``ResourceSlot`` and other
    UserDict-style types embedded in ``KernelExecutionSpec``. ``frozen``
    matches the intent of the previous ``@dataclass(frozen=True)``
    variant — downstream consumers mutate via ``model_copy``.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)


class SessionIdentity(_SpecBaseModel):
    """Unique handles a session is addressed by."""

    session_id: SessionID
    creation_id: str
    session_name: str
    access_key: AccessKey
    user_uuid: UUID


class SessionScope(_SpecBaseModel):
    """Ownership / placement scope of the session."""

    domain_id: DomainID
    domain_name: DomainName
    project_id: ProjectID
    resource_group_id: ResourceGroupID
    resource_group_name: ResourceGroupName


class SessionClassification(_SpecBaseModel):
    """Session-kind metadata that is neither identity nor scope."""

    session_type: SessionTypes
    tag: str | None = None


class SessionNetwork(_SpecBaseModel):
    """Inter-container networking plan resolved at enqueue time.

    Legacy priority (see :class:`.preparer.SessionPreparer._determine_network_config`):

      1. caller-specified persistent network → ``PERSISTENT`` + network id
      2. scaling-group's ``use_host_network`` flag → ``HOST``
      3. fallback → ``VOLATILE`` (bridge for single-node, overlay for multi-node)

    ``SessionRow.network_type`` is nullable in the DB, but every
    production session-creation path assigns a value here.
    """

    network_type: NetworkType
    network_id: str | None = None
    use_host_network: bool = False


class KernelSpec(_SpecBaseModel):
    """Full spec to create one ``KernelRow``.

    Wraps a resolved :class:`KernelExecutionSpec` (shared across every
    replica of one kernel group) with the per-replica cluster layout,
    user-mapping fields, preopen-port plan, ``internal_data`` blob
    (agent-consumed metadata — dotfiles, SSH key, sudo flag, model
    definition, ...) assigned during preparation, and ``vfolder_mounts``
    (resolved per-kernel mount list — each ``MountInfoEntry`` on
    ``execution_spec.mounts`` becomes a typed ``VFolderMount`` here).
    """

    cluster_role: str
    cluster_idx: int
    cluster_hostname: str
    local_rank: int
    uid: int | None = None
    main_gid: int | None = None
    supplementary_gids: tuple[int, ...] = ()
    preopen_ports: tuple[int, ...] = ()
    # ``internal_data`` is kept as an opaque mapping to preserve wire
    # compatibility with the agent, which already parses this JSONB blob
    # key-by-key. Structuring it into a typed model is deferred to a
    # follow-up task.
    internal_data: Mapping[str, Any] = Field(default_factory=dict)
    execution_spec: KernelExecutionSpec
    vfolder_mounts: tuple[VFolderMount, ...] = ()


class SessionSpec(_SpecBaseModel):
    """Full spec to create one ``SessionRow`` and its owned kernels.

    Vfolder mounts live on :attr:`KernelSpec.vfolder_mounts` —
    per-kernel at the spec level. The ``SessionRow.vfolder_mounts``
    JSONB column (session-level snapshot) is filled by the repository
    from the main kernel's resolved mount list at enqueue time.
    """

    identity: SessionIdentity
    scope: SessionScope
    classification: SessionClassification
    network: SessionNetwork
    callback_url: yarl.URL | None = None
    dependencies: tuple[SessionID, ...] = ()
    options: SessionOptions
    kernel_specs: tuple[KernelSpec, ...]
    internal_data_extras: InternalDataExtras = Field(default_factory=InternalDataExtras)

    @override
    @classmethod
    def build_validation_error(cls, info: SchemaValidationFailureInfo) -> BackendAIError:
        missing_paths = [cls._format_loc(tuple(err["loc"])) for err in info.errors]
        return IncompleteSessionSpec(
            extra_msg="SessionSpec fields not resolved: " + ", ".join(missing_paths),
            extra_data={"missing": missing_paths},
        )

    @staticmethod
    def _format_loc(loc: tuple[object, ...]) -> str:
        parts: list[str] = []
        for item in loc:
            if isinstance(item, int):
                parts.append(f"[{item}]")
            else:
                parts.append(f".{item}" if parts else str(item))
        return "".join(parts)

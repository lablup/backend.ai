from __future__ import annotations

import enum
from collections.abc import Mapping
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import AliasChoices, ConfigDict, Field, model_validator

from ai.backend.common.defs import RESERVED_VFOLDER_PATTERNS, RESERVED_VFOLDERS
from ai.backend.common.types import BackendAISchema, SessionTypes
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.exceptions import InvalidArgument


class TemplateType(enum.StrEnum):
    TASK = "task"
    CLUSTER = "cluster"


class _TemplateSection(BackendAISchema):
    """A nested section of a template document. Unknown keys are refused."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class _TemplateDocument(BackendAISchema):
    """The top level of a template document. Unknown keys are kept as they are."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @classmethod
    def check(cls, raw: Mapping[str, Any]) -> dict[str, Any]:
        """Validate ``raw`` and return it with aliases and defaults normalized."""
        return cls.model_validate(raw).model_dump(mode="json")


class TaskTemplateMetadata(_TemplateSection):
    name: str
    tag: str | None = None


class TaskTemplateRun(_TemplateSection):
    bootstrap: str | None = None
    startup_command: str | None = Field(
        default=None,
        validation_alias=AliasChoices("startup", "startup_command", "startupCommand"),
    )


class TaskTemplateGitCredential(_TemplateSection):
    username: str
    password: str


class TaskTemplateGit(_TemplateSection):
    repository: str
    commit: str | None = None
    branch: str | None = None
    credential: TaskTemplateGitCredential | None = None
    dest_dir: str | None = Field(
        default=None,
        validation_alias=AliasChoices("destination_dir", "destinationDir"),
    )


class TaskTemplateKernel(_TemplateSection):
    image: str
    architecture: str | None = "x86_64"
    environ: dict[str, str] | None = Field(default_factory=dict)
    run: TaskTemplateRun | None = None
    git: TaskTemplateGit | None = None


class TaskTemplateSpec(_TemplateSection):
    session_type: SessionTypes = Field(
        default=SessionTypes.INTERACTIVE,
        validation_alias=AliasChoices("type", "session_type", "sessionType"),
    )
    kernel: TaskTemplateKernel
    scaling_group: str | None = None
    mounts: dict[str, Any] | None = Field(default_factory=dict)
    resources: dict[str, Any] | None = None
    agent_list: list[str] | None = Field(
        default=None,
        validation_alias=AliasChoices("agent_list", "agentList"),
    )


class TaskTemplate(_TemplateDocument):
    api_version: str = Field(validation_alias=AliasChoices("api_version", "apiVersion"))
    kind: Literal["taskTemplate", "task_template"]
    metadata: TaskTemplateMetadata
    spec: TaskTemplateSpec

    @model_validator(mode="after")
    def _refuse_reserved_mounts(self) -> Self:
        for path in (self.spec.mounts or {}).values():
            if path is None:
                continue
            name = path.removeprefix("/home/work/")
            if name in RESERVED_VFOLDERS or any(p.match(name) for p in RESERVED_VFOLDER_PATTERNS):
                raise InvalidArgument(f"Path {name} is reserved for internal operations.")
        return self


class ClusterTemplateMetadata(_TemplateSection):
    name: str


class ClusterTemplateNode(_TemplateSection):
    role: str
    session_template: UUID = Field(
        validation_alias=AliasChoices("session_template", "sessionTemplate"),
    )
    replicas: int = 1


class ClusterTemplateSpec(_TemplateSection):
    environ: dict[str, str] | None = Field(default_factory=dict)
    mounts: dict[str, Any] | None = Field(default_factory=dict)
    nodes: list[ClusterTemplateNode]


class ClusterTemplate(_TemplateDocument):
    api_version: str = Field(validation_alias=AliasChoices("api_version", "apiVersion"))
    kind: Literal["clusterTemplate", "cluster_template"]
    mode: Literal["single-node", "multi-node"]
    metadata: ClusterTemplateMetadata
    spec: ClusterTemplateSpec

    @model_validator(mode="after")
    def _require_one_main_node(self) -> Self:
        roles = [node.role for node in self.spec.nodes]
        if len(roles) != len(set(roles)):
            raise InvalidArgument("Each role can only be defined once")
        main = next((node for node in self.spec.nodes if node.role == DEFAULT_ROLE), None)
        if main is None or main.replicas != 1:
            raise InvalidArgument(
                f"One and only one {DEFAULT_ROLE} node must be created per cluster",
            )
        return self

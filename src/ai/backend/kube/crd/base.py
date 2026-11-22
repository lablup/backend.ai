from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

BACKEND_AI_GROUP = "backend.ai"
SCHEDULING_GROUP = "scheduling.backend.ai"
CRD_VERSION = "v1alpha1"


class CRDScope(enum.StrEnum):
    NAMESPACED = "Namespaced"
    CLUSTER = "Cluster"


class CRDModel(BaseModel):
    """Base for CR spec/status parts. Field names are camelCase on the wire."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
        use_enum_values=True,
    )


@dataclass(frozen=True)
class PrinterColumn:
    name: str
    json_path: str
    type: str = "string"


@dataclass(frozen=True)
class CRDInfo:
    group: str
    kind: str
    plural: str
    scope: CRDScope
    short_names: tuple[str, ...] = ()
    printer_columns: tuple[PrinterColumn, ...] = ()

    @property
    def api_version(self) -> str:
        return f"{self.group}/{CRD_VERSION}"

    @property
    def name(self) -> str:
        return f"{self.plural}.{self.group}"


class CustomResource(CRDModel):
    """A whole CR object. Subclasses set `crd` and type `spec`/`status`."""

    crd: ClassVar[CRDInfo]

    api_version: str = Field(default="", alias="apiVersion")
    kind: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_manifest(self) -> dict[str, Any]:
        body = self.model_dump(by_alias=True, exclude_none=True, mode="json")
        body["apiVersion"] = self.crd.api_version
        body["kind"] = self.crd.kind
        return body

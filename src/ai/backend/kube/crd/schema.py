from __future__ import annotations

from typing import Any, get_args

from pydantic import BaseModel

from ai.backend.kube.crd.base import CRD_VERSION, CustomResource
from ai.backend.kube.crd.device import DeviceProfile
from ai.backend.kube.crd.scheduling import BindRequest, Queue
from ai.backend.kube.crd.session import SessionWorkload
from ai.backend.kube.crd.storage import StorageBinding

ALL_RESOURCES: tuple[type[CustomResource], ...] = (
    SessionWorkload,
    Queue,
    BindRequest,
    DeviceProfile,
    StorageBinding,
)


def _structural(node: Any, defs: dict[str, Any]) -> Any:
    """Convert a pydantic JSON schema node into a Kubernetes structural schema node."""
    if isinstance(node, list):
        return [_structural(item, defs) for item in node]
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        target = defs[node["$ref"].rsplit("/", 1)[-1]]
        merged = {**target, **{k: v for k, v in node.items() if k != "$ref"}}
        return _structural(merged, defs)
    if "anyOf" in node:
        variants = [v for v in node["anyOf"] if v.get("type") != "null"]
        if len(variants) == 1 and len(variants) < len(node["anyOf"]):
            rest = {k: v for k, v in node.items() if k != "anyOf"}
            converted = _structural({**variants[0], **rest}, defs)
            converted["nullable"] = True
            return converted
    out: dict[str, Any] = {}
    for key, value in node.items():
        match key:
            case "title" | "$defs":
                continue
            case "default" if value is None:
                continue
            case "additionalProperties" if value is True or value == {}:
                out["x-kubernetes-preserve-unknown-fields"] = True
            case "properties":
                out[key] = {name: _structural(sub, defs) for name, sub in value.items()}
            case _:
                out[key] = _structural(value, defs)
    if (
        out.get("type") == "object"
        and "properties" not in out
        and "additionalProperties" not in out
    ):
        out["x-kubernetes-preserve-unknown-fields"] = True
    return out


def _part_schema(resource: type[CustomResource], field: str) -> dict[str, Any]:
    annotation = resource.model_fields[field].annotation
    model = next(
        arg
        for arg in (annotation, *get_args(annotation))
        if isinstance(arg, type) and issubclass(arg, BaseModel)
    )
    raw = model.model_json_schema(by_alias=True, mode="serialization")
    converted: dict[str, Any] = _structural(raw, raw.get("$defs", {}))
    return converted


def build_crd(resource: type[CustomResource]) -> dict[str, Any]:
    info = resource.crd
    schema = {
        "type": "object",
        "required": ["spec"],
        "properties": {
            "apiVersion": {"type": "string"},
            "kind": {"type": "string"},
            "metadata": {"type": "object"},
            "spec": _part_schema(resource, "spec"),
            "status": _part_schema(resource, "status"),
        },
    }
    names: dict[str, Any] = {
        "kind": info.kind,
        "listKind": f"{info.kind}List",
        "plural": info.plural,
        "singular": info.kind.lower(),
    }
    if info.short_names:
        names["shortNames"] = list(info.short_names)
    version: dict[str, Any] = {
        "name": CRD_VERSION,
        "served": True,
        "storage": True,
        "subresources": {"status": {}},
        "schema": {"openAPIV3Schema": schema},
    }
    if info.printer_columns:
        version["additionalPrinterColumns"] = [
            {"name": c.name, "type": c.type, "jsonPath": c.json_path} for c in info.printer_columns
        ]
    return {
        "apiVersion": "apiextensions.k8s.io/v1",
        "kind": "CustomResourceDefinition",
        "metadata": {"name": info.name},
        "spec": {
            "group": info.group,
            "scope": str(info.scope),
            "names": names,
            "versions": [version],
        },
    }

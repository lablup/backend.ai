from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ai.backend.kube.crd.base import CustomResource
from ai.backend.kube.crd.generate import render_all
from ai.backend.kube.crd.schema import ALL_RESOURCES, build_crd
from ai.backend.kube.crd.session import (
    KernelImage,
    KernelSpec,
    SessionWorkload,
    SessionWorkloadSpec,
)

CHART_TEMPLATES = Path(__file__).resolve().parents[4] / "deploy/helm/backendai-crds/templates"


def _walk(node: Any, path: str = "") -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    if isinstance(node, dict):
        found.append((path, node))
        for key, value in node.items():
            found.extend(_walk(value, f"{path}.{key}"))
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            found.extend(_walk(value, f"{path}[{idx}]"))
    return found


@pytest.fixture(params=ALL_RESOURCES, ids=lambda r: r.crd.kind)
def openapi_schema(request: pytest.FixtureRequest) -> dict[str, Any]:
    resource: type[CustomResource] = request.param
    schema: dict[str, Any] = build_crd(resource)["spec"]["versions"][0]["schema"]["openAPIV3Schema"]
    return schema


@pytest.fixture
def session_workload() -> SessionWorkload:
    return SessionWorkload(
        metadata={"name": "s-1", "namespace": "bai-p"},
        spec=SessionWorkloadSpec(
            session_id="1",
            session_name="t",
            owner_user_id="u",
            resource_group="k8s",
            kernels=[KernelSpec(kernel_id="k1", image=KernelImage(canonical="python:3.12"))],
        ),
    )


class TestGeneratedManifests:
    def test_chart_templates_match_models(self) -> None:
        for name, body in render_all().items():
            assert (CHART_TEMPLATES / name).read_text() == body, f"{name} is stale"


class TestStructuralSchema:
    def test_has_no_json_schema_only_keywords(self, openapi_schema: dict[str, Any]) -> None:
        for path, node in _walk(openapi_schema):
            assert not {"$ref", "$defs", "anyOf", "title", "const"} & node.keys(), path

    def test_every_object_declares_its_fields(self, openapi_schema: dict[str, Any]) -> None:
        for path, node in _walk(openapi_schema):
            if node.get("type") == "object" and not path.endswith(".metadata"):
                assert {
                    "properties",
                    "additionalProperties",
                    "x-kubernetes-preserve-unknown-fields",
                } & node.keys(), path

    def test_optional_fields_are_nullable(self) -> None:
        schema = build_crd(SessionWorkload)["spec"]["versions"][0]["schema"]["openAPIV3Schema"]
        spec = schema["properties"]["spec"]
        assert spec["properties"]["ownerProjectId"] == {"type": "string", "nullable": True}
        assert "ownerProjectId" not in spec["required"]


class TestCustomResource:
    def test_manifest_uses_camel_case_and_crd_identity(
        self, session_workload: SessionWorkload
    ) -> None:
        manifest = session_workload.to_manifest()
        assert manifest["apiVersion"] == "backend.ai/v1alpha1"
        assert manifest["kind"] == "SessionWorkload"
        assert manifest["spec"]["kernels"][0]["kernelId"] == "k1"

    def test_manifest_round_trips(self, session_workload: SessionWorkload) -> None:
        restored = SessionWorkload.model_validate(session_workload.to_manifest())
        assert restored.spec == session_workload.spec

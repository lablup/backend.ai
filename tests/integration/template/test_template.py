from __future__ import annotations

import json

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.template import (
    CreateClusterTemplateRequest,
    CreateClusterTemplateResponse,
    CreateSessionTemplateRequest,
    CreateSessionTemplateResponse,
    DeleteClusterTemplateResponse,
    DeleteSessionTemplateResponse,
    GetClusterTemplateResponse,
    GetSessionTemplateResponse,
    UpdateClusterTemplateRequest,
    UpdateClusterTemplateResponse,
    UpdateSessionTemplateRequest,
    UpdateSessionTemplateResponse,
)


def _session_template_payload(name: str = "test-template") -> str:
    return json.dumps([
        {
            "name": name,
            "template": {
                "apiVersion": "v1",
                "kind": "taskTemplate",
                "metadata": {"name": name},
                "spec": {
                    "kernel": {"image": "cr.backend.ai/testing/python:3.9"},
                },
            },
        }
    ])


def _cluster_template_payload(
    name: str,
    session_template_id: str,
) -> str:
    return json.dumps({
        "apiVersion": "v1",
        "kind": "clusterTemplate",
        "mode": "single-node",
        "metadata": {"name": name},
        "spec": {
            "nodes": [
                {
                    "role": "default",
                    "session_template": session_template_id,
                    "replicas": 1,
                },
            ],
        },
    })


@pytest.mark.integration
class TestSessionTemplateLifecycle:
    @pytest.mark.asyncio
    async def test_create_get_update_delete(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Full CRUD lifecycle: create -> get -> update -> get -> delete -> verify gone."""
        # Create
        create_result = await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("lifecycle-st")),
        )
        assert isinstance(create_result, CreateSessionTemplateResponse)
        template_id = create_result.root[0].id
        assert template_id != ""

        # Get
        get_result = await admin_registry.template.get_session_template(template_id)
        assert isinstance(get_result, GetSessionTemplateResponse)
        assert get_result.name == "lifecycle-st"
        assert get_result.template is not None

        # Update
        update_result = await admin_registry.template.update_session_template(
            template_id,
            UpdateSessionTemplateRequest(
                payload=_session_template_payload("lifecycle-st-updated"),
            ),
        )
        assert isinstance(update_result, UpdateSessionTemplateResponse)
        assert update_result.success is True

        # Get after update
        get_result2 = await admin_registry.template.get_session_template(template_id)
        assert get_result2.name == "lifecycle-st-updated"

        # Delete
        delete_result = await admin_registry.template.delete_session_template(template_id)
        assert isinstance(delete_result, DeleteSessionTemplateResponse)
        assert delete_result.success is True

        # Verify soft-deleted template is not retrievable
        get_result3 = await admin_registry.template.get_session_template(template_id)
        assert get_result3.template == {}


@pytest.mark.integration
class TestClusterTemplateLifecycle:
    @pytest.mark.asyncio
    async def test_create_get_update_delete(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Full CRUD: create session tpl -> create cluster tpl -> get -> update -> delete."""
        # Create prerequisite session template
        st_result = await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("ct-lifecycle-dep")),
        )
        session_tpl_id = st_result.root[0].id

        # Create cluster template
        create_result = await admin_registry.template.create_cluster_template(
            CreateClusterTemplateRequest(
                payload=_cluster_template_payload("lifecycle-ct", session_tpl_id),
            ),
        )
        assert isinstance(create_result, CreateClusterTemplateResponse)
        cluster_tpl_id = create_result.id
        assert cluster_tpl_id != ""

        # Get
        get_result = await admin_registry.template.get_cluster_template(cluster_tpl_id)
        assert isinstance(get_result, GetClusterTemplateResponse)
        assert get_result.root is not None

        # Update
        update_result = await admin_registry.template.update_cluster_template(
            cluster_tpl_id,
            UpdateClusterTemplateRequest(
                payload=_cluster_template_payload("lifecycle-ct-updated", session_tpl_id),
            ),
        )
        assert isinstance(update_result, UpdateClusterTemplateResponse)
        assert update_result.success is True

        # Delete
        delete_result = await admin_registry.template.delete_cluster_template(cluster_tpl_id)
        assert isinstance(delete_result, DeleteClusterTemplateResponse)
        assert delete_result.success is True

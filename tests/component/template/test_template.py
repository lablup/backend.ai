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
    GetClusterTemplateRequest,
    GetClusterTemplateResponse,
    GetSessionTemplateRequest,
    GetSessionTemplateResponse,
    ListClusterTemplatesRequest,
    ListSessionTemplatesRequest,
    UpdateClusterTemplateRequest,
    UpdateClusterTemplateResponse,
    UpdateSessionTemplateRequest,
    UpdateSessionTemplateResponse,
)

_HMAC_XFAIL = pytest.mark.xfail(
    strict=True,
    reason=(
        "Client SDK v2 HMAC signing omits query params; server verifies against"
        " request.raw_path (including ?param=...). Endpoints passing query params"
        " cause 401."
    ),
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


# ====================================================================
# Session Template Tests
# ====================================================================


class TestCreateSessionTemplate:
    @pytest.mark.asyncio
    async def test_admin_creates_session_template(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("admin-tpl")),
        )
        assert isinstance(result, CreateSessionTemplateResponse)
        items = result.root
        assert len(items) == 1
        assert items[0].id != ""
        assert items[0].user != ""

    @pytest.mark.asyncio
    async def test_user_creates_session_template(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("user-tpl")),
        )
        assert isinstance(result, CreateSessionTemplateResponse)
        items = result.root
        assert len(items) == 1
        assert items[0].id != ""


class TestGetSessionTemplate:
    @pytest.mark.asyncio
    async def test_admin_gets_session_template(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        create_result = await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("get-test")),
        )
        template_id = create_result.root[0].id

        result = await admin_registry.template.get_session_template(template_id)
        assert isinstance(result, GetSessionTemplateResponse)
        assert result.name == "get-test"
        assert result.template is not None

    @pytest.mark.asyncio
    async def test_user_gets_session_template(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        create_result = await user_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("user-get-test")),
        )
        template_id = create_result.root[0].id

        result = await user_registry.template.get_session_template(template_id)
        assert isinstance(result, GetSessionTemplateResponse)
        assert result.name == "user-get-test"

    @_HMAC_XFAIL
    @pytest.mark.asyncio
    async def test_get_with_format_param(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        create_result = await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("fmt-test")),
        )
        template_id = create_result.root[0].id

        result = await admin_registry.template.get_session_template(
            template_id,
            GetSessionTemplateRequest(format="json"),
        )
        assert isinstance(result, GetSessionTemplateResponse)


class TestListSessionTemplates:
    @_HMAC_XFAIL
    @pytest.mark.asyncio
    async def test_list_session_templates(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("list-test")),
        )

        result = await admin_registry.template.list_session_templates(
            ListSessionTemplatesRequest(),
        )
        assert isinstance(result.root, list)


class TestUpdateSessionTemplate:
    @pytest.mark.asyncio
    async def test_admin_updates_session_template(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        create_result = await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("update-before")),
        )
        template_id = create_result.root[0].id

        result = await admin_registry.template.update_session_template(
            template_id,
            UpdateSessionTemplateRequest(
                payload=_session_template_payload("update-after"),
            ),
        )
        assert isinstance(result, UpdateSessionTemplateResponse)
        assert result.success is True

        get_result = await admin_registry.template.get_session_template(template_id)
        assert get_result.name == "update-after"


class TestDeleteSessionTemplate:
    @pytest.mark.asyncio
    async def test_admin_deletes_session_template(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        create_result = await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("delete-test")),
        )
        template_id = create_result.root[0].id

        result = await admin_registry.template.delete_session_template(template_id)
        assert isinstance(result, DeleteSessionTemplateResponse)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_deleted_template_returns_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        create_result = await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("del-verify")),
        )
        template_id = create_result.root[0].id

        await admin_registry.template.delete_session_template(template_id)

        result = await admin_registry.template.get_session_template(template_id)
        assert isinstance(result, GetSessionTemplateResponse)
        # After soft-delete, the template field should be empty (no rows matched).
        assert result.template == {}


# ====================================================================
# Cluster Template Tests
# ====================================================================


class TestCreateClusterTemplate:
    @pytest.mark.asyncio
    async def test_admin_creates_cluster_template(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        # First, create a session template to reference.
        st_result = await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("cluster-dep")),
        )
        session_tpl_id = st_result.root[0].id

        result = await admin_registry.template.create_cluster_template(
            CreateClusterTemplateRequest(
                payload=_cluster_template_payload("test-cluster", session_tpl_id),
            ),
        )
        assert isinstance(result, CreateClusterTemplateResponse)
        assert result.id != ""
        assert result.user != ""


class TestGetClusterTemplate:
    @pytest.mark.asyncio
    async def test_admin_gets_cluster_template(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        st_result = await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("ct-get-dep")),
        )
        session_tpl_id = st_result.root[0].id

        ct_result = await admin_registry.template.create_cluster_template(
            CreateClusterTemplateRequest(
                payload=_cluster_template_payload("ct-get-test", session_tpl_id),
            ),
        )
        cluster_tpl_id = ct_result.id

        result = await admin_registry.template.get_cluster_template(cluster_tpl_id)
        assert isinstance(result, GetClusterTemplateResponse)
        # Default format is yaml, but without query params the trafaret default kicks in.
        # The response is the template dict.
        assert result.root is not None

    @_HMAC_XFAIL
    @pytest.mark.asyncio
    async def test_get_with_format_param(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        st_result = await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("ct-fmt-dep")),
        )
        session_tpl_id = st_result.root[0].id

        ct_result = await admin_registry.template.create_cluster_template(
            CreateClusterTemplateRequest(
                payload=_cluster_template_payload("ct-fmt-test", session_tpl_id),
            ),
        )
        cluster_tpl_id = ct_result.id

        result = await admin_registry.template.get_cluster_template(
            cluster_tpl_id,
            GetClusterTemplateRequest(format="json"),
        )
        assert isinstance(result, GetClusterTemplateResponse)


class TestListClusterTemplates:
    @_HMAC_XFAIL
    @pytest.mark.asyncio
    async def test_list_cluster_templates(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        st_result = await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("ct-list-dep")),
        )
        session_tpl_id = st_result.root[0].id

        await admin_registry.template.create_cluster_template(
            CreateClusterTemplateRequest(
                payload=_cluster_template_payload("ct-list-test", session_tpl_id),
            ),
        )

        result = await admin_registry.template.list_cluster_templates(
            ListClusterTemplatesRequest(),
        )
        assert isinstance(result.root, list)


class TestUpdateClusterTemplate:
    @pytest.mark.asyncio
    async def test_admin_updates_cluster_template(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        st_result = await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("ct-upd-dep")),
        )
        session_tpl_id = st_result.root[0].id

        ct_result = await admin_registry.template.create_cluster_template(
            CreateClusterTemplateRequest(
                payload=_cluster_template_payload("ct-upd-before", session_tpl_id),
            ),
        )
        cluster_tpl_id = ct_result.id

        result = await admin_registry.template.update_cluster_template(
            cluster_tpl_id,
            UpdateClusterTemplateRequest(
                payload=_cluster_template_payload("ct-upd-after", session_tpl_id),
            ),
        )
        assert isinstance(result, UpdateClusterTemplateResponse)
        assert result.success is True


class TestDeleteClusterTemplate:
    @pytest.mark.asyncio
    async def test_admin_deletes_cluster_template(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        st_result = await admin_registry.template.create_session_template(
            CreateSessionTemplateRequest(payload=_session_template_payload("ct-del-dep")),
        )
        session_tpl_id = st_result.root[0].id

        ct_result = await admin_registry.template.create_cluster_template(
            CreateClusterTemplateRequest(
                payload=_cluster_template_payload("ct-del-test", session_tpl_id),
            ),
        )
        cluster_tpl_id = ct_result.id

        result = await admin_registry.template.delete_cluster_template(cluster_tpl_id)
        assert isinstance(result, DeleteClusterTemplateResponse)
        assert result.success is True

"""The compute cluster client loads only a validated kubeconfig."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.manager.clients.compute_cluster.client import ComputeClusterClient
from ai.backend.manager.errors.compute_cluster import InvalidKubeconfig

_EXEC_KUBECONFIG = """\
apiVersion: v1
kind: Config
clusters:
- name: c
  cluster:
    server: https://10.0.0.1:6443
users:
- name: u
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1
      command: /bin/touch
      args: [/tmp/pwned]
contexts:
- name: ctx
  context: {cluster: c, user: u}
current-context: ctx
"""


class TestFromKubeconfig:
    async def test_refuses_an_exec_credential_before_loading(self) -> None:
        with pytest.raises(InvalidKubeconfig):
            await ComputeClusterClient.from_kubeconfig(_EXEC_KUBECONFIG)


@pytest.fixture
def cluster_client() -> ComputeClusterClient:
    instance = ComputeClusterClient(MagicMock())
    instance._core = AsyncMock()
    instance._rbac = AsyncMock()
    return instance


def _conflict() -> ApiException:
    return ApiException(status=409, reason="Conflict")


class TestEnsureNamespace:
    async def test_binds_the_three_namespaced_cluster_roles(
        self, cluster_client: ComputeClusterClient
    ) -> None:
        await cluster_client.ensure_namespace("bai-p", {}, system_namespace="bai-system")

        calls = cluster_client._rbac.create_namespaced_role_binding.await_args_list
        bindings = [call.args[1] for call in calls]
        assert [
            (b["metadata"]["name"], b["roleRef"]["name"], b["subjects"][0]["name"])
            for b in bindings
        ] == [
            (
                "backendai-session-controller",
                "backendai-session-controller-namespaced",
                "session-controller",
            ),
            (
                "backendai-session-gateway",
                "backendai-session-gateway-namespaced",
                "session-gateway",
            ),
            ("backendai-manager", "backendai-manager-namespaced", "backendai-manager"),
        ]
        assert all(b["metadata"]["namespace"] == "bai-p" for b in bindings)
        assert all(b["subjects"][0]["namespace"] == "bai-system" for b in bindings)
        assert all(b["roleRef"]["kind"] == "ClusterRole" for b in bindings)

    async def test_defaults_to_the_backendai_system_namespace(
        self, cluster_client: ComputeClusterClient
    ) -> None:
        await cluster_client.ensure_namespace("bai-p", {})

        calls = cluster_client._rbac.create_namespaced_role_binding.await_args_list
        assert calls[0].args[1]["subjects"][0]["namespace"] == "backendai-system"

    async def test_patches_existing_namespace_and_bindings(
        self, cluster_client: ComputeClusterClient
    ) -> None:
        cluster_client._core.create_namespace.side_effect = _conflict()
        cluster_client._rbac.create_namespaced_role_binding.side_effect = _conflict()

        await cluster_client.ensure_namespace("bai-p", {"k": "v"}, system_namespace="sys")

        cluster_client._core.patch_namespace.assert_awaited_once()
        patches = cluster_client._rbac.patch_namespaced_role_binding.await_args_list
        assert [call.args[0] for call in patches] == [
            "backendai-session-controller",
            "backendai-session-gateway",
            "backendai-manager",
        ]
        assert patches[0].args[2]["subjects"][0]["namespace"] == "sys"

    async def test_raises_other_api_errors(self, cluster_client: ComputeClusterClient) -> None:
        cluster_client._rbac.create_namespaced_role_binding.side_effect = ApiException(
            status=403, reason="Forbidden"
        )
        with pytest.raises(ApiException):
            await cluster_client.ensure_namespace("bai-p", {})

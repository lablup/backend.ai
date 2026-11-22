"""The compute cluster client loads only a validated kubeconfig."""

from __future__ import annotations

import pytest

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

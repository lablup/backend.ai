"""A stored kubeconfig never runs a command or reads a file on the Manager's host."""

from __future__ import annotations

from typing import Any

import pytest
import yaml

from ai.backend.common.dto.manager.v2.compute_cluster.kubeconfig import (
    InvalidKubeconfigError,
    parse_kubeconfig,
)


def _config(
    *, cluster: dict[str, Any] | None = None, user: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {
                "name": "c",
                "cluster": cluster
                or {"server": "https://10.0.0.1:6443", "certificate-authority-data": "Y2E="},
            },
            {"name": "unused", "cluster": {"server": "https://10.0.0.2:6443"}},
        ],
        "users": [{"name": "u", "user": user or {"token": "t"}}],
        "contexts": [{"name": "ctx", "context": {"cluster": "c", "user": "u"}}],
        "current-context": "ctx",
    }


class TestParseKubeconfig:
    def test_returns_the_current_context_server(self) -> None:
        parsed = parse_kubeconfig(yaml.safe_dump(_config()))
        assert parsed.server == "https://10.0.0.1:6443"

    def test_keeps_only_the_current_context(self) -> None:
        parsed = parse_kubeconfig(yaml.safe_dump(_config()))
        assert [c["name"] for c in parsed.config["clusters"]] == ["c"]
        assert parsed.config["current-context"] == "ctx"

    def test_accepts_inline_client_certificates(self) -> None:
        user = {"client-certificate-data": "Y2VydA==", "client-key-data": "a2V5"}
        parsed = parse_kubeconfig(yaml.safe_dump(_config(user=user)))
        assert parsed.config["users"][0]["user"] == user

    @pytest.mark.parametrize(
        "user",
        [
            {"exec": {"command": "/bin/sh", "apiVersion": "client.authentication.k8s.io/v1"}},
            {"auth-provider": {"name": "gcp"}},
            {"tokenFile": "/var/run/secrets/token"},
            {"client-certificate": "/etc/cert", "client-key": "/etc/key"},
            {"token": "t", "username": "admin"},
        ],
        ids=["exec", "auth-provider", "tokenFile", "file-certificates", "unknown-key"],
    )
    def test_rejects_user_credentials_that_are_not_inline(self, user: dict[str, Any]) -> None:
        with pytest.raises(InvalidKubeconfigError):
            parse_kubeconfig(yaml.safe_dump(_config(user=user)))

    def test_rejects_a_certificate_authority_file(self) -> None:
        cluster = {"server": "https://10.0.0.1:6443", "certificate-authority": "/etc/ca.crt"}
        with pytest.raises(InvalidKubeconfigError):
            parse_kubeconfig(yaml.safe_dump(_config(cluster=cluster)))

    def test_rejects_a_plain_http_server(self) -> None:
        with pytest.raises(InvalidKubeconfigError):
            parse_kubeconfig(yaml.safe_dump(_config(cluster={"server": "http://10.0.0.1:8080"})))

    def test_rejects_a_missing_current_context(self) -> None:
        config = _config()
        config["current-context"] = "other"
        with pytest.raises(InvalidKubeconfigError):
            parse_kubeconfig(yaml.safe_dump(config))

    @pytest.mark.parametrize("text", ["apiVersion: v1", "- a\n- b", "{{not yaml"])
    def test_rejects_documents_that_are_not_kubeconfigs(self, text: str) -> None:
        with pytest.raises(InvalidKubeconfigError):
            parse_kubeconfig(text)

"""The kubeconfig a compute cluster is registered with: inline credentials only.

The Manager never lets a stored kubeconfig run a command (`exec`, `auth-provider`) or read a
file from its own disk (`client-certificate`, `client-key`, `certificate-authority`,
`tokenFile`). `parse_kubeconfig` refuses such a kubeconfig and returns the one context the
Manager uses, rebuilt from the accepted keys only.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final
from urllib.parse import urlparse

import yaml

__all__ = (
    "InvalidKubeconfigError",
    "ParsedKubeconfig",
    "parse_kubeconfig",
)

MAX_KUBECONFIG_BYTES: Final = 256 * 1024

_TOP_LEVEL_KEYS: Final = frozenset({
    "apiVersion",
    "kind",
    "clusters",
    "contexts",
    "users",
    "current-context",
    "preferences",
})
_CLUSTER_KEYS: Final = frozenset({
    "server",
    "certificate-authority-data",
    "tls-server-name",
    "insecure-skip-tls-verify",
})
_CLUSTER_STRING_KEYS: Final = frozenset({"certificate-authority-data", "tls-server-name"})
_USER_KEYS: Final = frozenset({"client-certificate-data", "client-key-data", "token"})
_CONTEXT_KEYS: Final = frozenset({"cluster", "user", "namespace"})


class InvalidKubeconfigError(ValueError):
    """The kubeconfig is not YAML, is incomplete, or names a key the Manager refuses."""


@dataclass(frozen=True)
class ParsedKubeconfig:
    server: str
    """The API server of the current context."""

    config: Mapping[str, Any]
    """A kubeconfig holding only the current context, its cluster and its user."""


def _named_entries(doc: Mapping[str, Any], section: str, body_key: str) -> dict[str, Any]:
    entries = doc.get(section)
    if not isinstance(entries, list):
        raise InvalidKubeconfigError(f"`{section}` must be a list")
    named: dict[str, Any] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise InvalidKubeconfigError(f"every entry of `{section}` must be a mapping")
        name = entry.get("name")
        body = entry.get(body_key)
        if not isinstance(name, str) or not name:
            raise InvalidKubeconfigError(f"every entry of `{section}` needs a `name`")
        if not isinstance(body, Mapping):
            raise InvalidKubeconfigError(f"`{section}[{name}]` needs a `{body_key}` mapping")
        named[name] = body
    return named


def _check_keys(where: str, body: Mapping[str, Any], allowed: frozenset[str]) -> None:
    refused = sorted(str(key) for key in body if key not in allowed)
    if refused:
        raise InvalidKubeconfigError(
            f"`{where}` has keys the Manager does not accept: {refused};"
            f" accepted: {sorted(allowed)}"
        )


def _check_strings(where: str, body: Mapping[str, Any], keys: frozenset[str]) -> None:
    """Each of `keys` present in `body` must be a non-empty string."""
    for key in sorted(keys):
        if key in body and (not isinstance(body[key], str) or not body[key]):
            raise InvalidKubeconfigError(f"`{where}.{key}` must be a non-empty string")


def _check_server(where: str, server: Any) -> str:
    if not isinstance(server, str):
        raise InvalidKubeconfigError(f"`{where}.server` must be a string")
    parsed = urlparse(server)
    if parsed.scheme != "https" or not parsed.hostname:
        raise InvalidKubeconfigError(f"`{where}.server` must be an https URL, got {server!r}")
    return server


def parse_kubeconfig(text: str) -> ParsedKubeconfig:
    """Validate a kubeconfig and return its current context, or raise InvalidKubeconfigError."""
    if len(text.encode()) > MAX_KUBECONFIG_BYTES:
        raise InvalidKubeconfigError(f"the kubeconfig exceeds {MAX_KUBECONFIG_BYTES} bytes")
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise InvalidKubeconfigError(f"the kubeconfig is not valid YAML: {e}") from e
    if not isinstance(doc, Mapping):
        raise InvalidKubeconfigError("the kubeconfig must be a YAML mapping")
    _check_keys("kubeconfig", doc, _TOP_LEVEL_KEYS)
    clusters = _named_entries(doc, "clusters", "cluster")
    users = _named_entries(doc, "users", "user")
    contexts = _named_entries(doc, "contexts", "context")
    for name, cluster in clusters.items():
        where = f"clusters[{name}].cluster"
        _check_keys(where, cluster, _CLUSTER_KEYS)
        _check_server(where, cluster.get("server"))
        _check_strings(where, cluster, _CLUSTER_STRING_KEYS)
        skip_verify = cluster.get("insecure-skip-tls-verify")
        if skip_verify is not None and not isinstance(skip_verify, bool):
            raise InvalidKubeconfigError(f"`{where}.insecure-skip-tls-verify` must be a boolean")
    for name, user in users.items():
        where = f"users[{name}].user"
        _check_keys(where, user, _USER_KEYS)
        _check_strings(where, user, _USER_KEYS)
        has_cert, has_key = "client-certificate-data" in user, "client-key-data" in user
        if has_cert != has_key or not (has_cert or "token" in user):
            raise InvalidKubeconfigError(
                f"`{where}` needs `token` or `client-certificate-data` with `client-key-data`"
            )
    for name, context in contexts.items():
        where = f"contexts[{name}].context"
        _check_keys(where, context, _CONTEXT_KEYS)
        _check_strings(where, context, _CONTEXT_KEYS)
    current = doc.get("current-context")
    if not isinstance(current, str) or current not in contexts:
        raise InvalidKubeconfigError("`current-context` must name one of `contexts`")
    context = contexts[current]
    cluster_name, user_name = context.get("cluster"), context.get("user")
    if cluster_name not in clusters:
        raise InvalidKubeconfigError(f"context {current!r} names an unknown cluster")
    if user_name not in users:
        raise InvalidKubeconfigError(f"context {current!r} names an unknown user")
    cluster = clusters[cluster_name]
    server = _check_server(f"clusters[{cluster_name}].cluster", cluster.get("server"))
    config = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [{"name": cluster_name, "cluster": dict(cluster)}],
        "users": [{"name": user_name, "user": dict(users[user_name])}],
        "contexts": [{"name": current, "context": dict(context)}],
        "current-context": current,
    }
    return ParsedKubeconfig(server=server, config=config)

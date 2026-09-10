"""Config provider for the kit: a validated ``ManagerUnifiedConfig`` handed in directly.

Moved here from ``tests/component/conftest.py`` (``_TestConfigProvider``) so the new tree
does not inherit that conftest.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.data.manager_status.types import ManagerStatus
from ai.backend.testutils.bootstrap import POSTGRES_PASSWORD, POSTGRES_USER

VFOLDER_HOST = "local:volume1"


class _KitLegacyEtcdLoader:
    """The two legacy-etcd reads the code under test still makes, answered from memory."""

    def __init__(self, vfolder_types: Sequence[str]) -> None:
        self._vfolder_types = list(vfolder_types)

    async def get_vfolder_types(self) -> list[str]:
        return list(self._vfolder_types)

    async def get_manager_status(self) -> ManagerStatus:
        return ManagerStatus.RUNNING


class ScenarioConfigProvider(ManagerConfigProvider):
    def __init__(
        self, config: ManagerUnifiedConfig, vfolder_types: Sequence[str] = ("user", "group")
    ) -> None:
        # The production __init__ wires a loader chain and an etcd watcher; neither exists here.
        self._config = config
        self._etcd_watcher_task = None
        self._legacy_etcd_config_loader = cast(
            LegacyEtcdLoader, _KitLegacyEtcdLoader(vfolder_types)
        )


def base_config_dict(
    db_addr: HostPortPairModel, dbname: str, redis_addr: HostPortPairModel | None
) -> dict[str, Any]:
    raw: dict[str, Any] = {
        "db": {
            "addr": {"host": db_addr.host, "port": db_addr.port},
            "name": dbname,
            "user": POSTGRES_USER,
            "password": POSTGRES_PASSWORD,
            "pool_size": 4,
            "max_overflow": 16,
            "pool_pre_ping": False,
            "lock_conn_timeout": 0,
        },
        "manager": {
            "rbac": {"enforcement_enabled": True},
        },
        "volumes": {
            "default_host": VFOLDER_HOST,
            "proxies": {
                "local": {
                    "client_api": "http://127.0.0.1:6021",
                    "manager_api": "http://127.0.0.1:6022",
                    "secret": "kit",
                    "ssl_verify": False,
                }
            },
        },
    }
    if redis_addr is not None:
        raw["redis"] = {"addr": {"host": redis_addr.host, "port": redis_addr.port}}
    return raw


def set_dotted(raw: dict[str, Any], dotted: str, value: Any) -> None:
    cursor = raw
    parts = dotted.split(".")
    for part in parts[:-1]:
        cursor = cursor.setdefault(part, {})
    cursor[parts[-1]] = value


def make_config(base: Mapping[str, Any], overrides: Mapping[str, Any]) -> ManagerUnifiedConfig:
    """``base`` with every ``Setup.config`` dotted override applied, validated once."""
    raw: dict[str, Any] = _deep_copy(base)
    for dotted, value in overrides.items():
        set_dotted(raw, dotted, value)
    return ManagerUnifiedConfig.model_validate(raw, by_name=True)


def _deep_copy(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _deep_copy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_deep_copy(v) for v in value]
    return value

from __future__ import annotations

from pathlib import Path
from typing import Any, override

from ai.backend.install.context import Context


class _FacingAddr:
    def __init__(self, host: str, port: int) -> None:
        self.face = type("_Face", (), {"host": host, "port": port})()


class _ClientEnvContext(Context):
    """Exercises configure_client alone, with the install info it reads stubbed out."""

    def __init__(self, base_path: Path) -> None:
        service = type(
            "_ServiceConfig",
            (),
            {
                "manager_addr": _FacingAddr("127.0.0.1", 8081),
                "webserver_addr": _FacingAddr("127.0.0.1", 8080),
            },
        )()
        self.install_info = type(
            "_InstallInfo", (), {"base_path": base_path, "service_config": service}
        )()

    @override
    def hydrate_install_info(self) -> Any:
        raise NotImplementedError

    @override
    def mangle_pkgname(self, name: str, fat: bool = False) -> str:
        return name


async def test_configure_client_writes_env_per_fixture_user(tmp_path: Path) -> None:
    """Guards against fixture-key drift: the manager fixtures are symlinked into the
    installer, so a key rename there silently breaks this step.
    """
    await _ClientEnvContext(tmp_path).configure_client()

    api_envs = sorted(p.name for p in tmp_path.glob("env-local-*-api.sh"))
    session_envs = sorted(p.name for p in tmp_path.glob("env-local-*-session.sh"))
    assert api_envs == [
        "env-local-admin-api.sh",
        "env-local-domain-admin-api.sh",
        "env-local-monitor-api.sh",
        "env-local-user-api.sh",
        "env-local-user2-api.sh",
    ]
    assert len(session_envs) == len(api_envs)

    admin_env = (tmp_path / "env-local-admin-api.sh").read_text()
    assert "BACKEND_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE" in admin_env
    assert "BACKEND_ENDPOINT=http://127.0.0.1:8081/" in admin_env

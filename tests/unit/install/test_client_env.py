from __future__ import annotations

from .conftest import InstallerHarness


class TestConfigureClient:
    async def test_writes_env_per_fixture_user(self, harness: InstallerHarness) -> None:
        """Guards against fixture-key drift: the manager fixtures are symlinked
        into the installer, so a key rename there silently breaks this step.
        """
        await harness.configure_client()

        api_envs = sorted(path.name for path in harness.base_path.glob("env-local-*-api.sh"))
        session_envs = sorted(
            path.name for path in harness.base_path.glob("env-local-*-session.sh")
        )
        assert api_envs == [
            "env-local-admin-api.sh",
            "env-local-domain-admin-api.sh",
            "env-local-monitor-api.sh",
            "env-local-user-api.sh",
            "env-local-user2-api.sh",
        ]
        assert len(session_envs) == len(api_envs)

    async def test_api_env_carries_the_keypair(self, harness: InstallerHarness) -> None:
        await harness.configure_client()

        manager_face = harness.install_info.service_config.manager_addr.face
        assert manager_face is not None
        admin_env = (harness.base_path / "env-local-admin-api.sh").read_text()
        assert "BACKEND_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE" in admin_env
        assert f"BACKEND_ENDPOINT=http://{manager_face.host}:{manager_face.port}/" in admin_env

"""
Credentials stage for kernel lifecycle.

This stage handles Docker credentials setup for containers.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, override

from ai.backend.common.asyncio import run_in_executor_with_context
from ai.backend.common.json import dump_json
from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage


@dataclass
class CredentialsSpec:
    config_dir: Path
    docker_credentials: Mapping[str, Any] | None


class CredentialsSpecGenerator(ArgsSpecGenerator[CredentialsSpec]):
    pass


@dataclass
class CredentialsResult:
    credentials_path: Path | None


class CredentialsProvisioner(Provisioner[CredentialsSpec, CredentialsResult]):
    """
    Provisioner for Docker credentials management.

    Writes Docker credentials to config directory if provided.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-credentials"

    @override
    async def setup(self, spec: CredentialsSpec) -> CredentialsResult:
        if not spec.docker_credentials:
            return CredentialsResult(credentials_path=None)

        credentials_path = spec.config_dir / "docker-creds.json"

        await run_in_executor_with_context(
            None,
            credentials_path.write_bytes,
            dump_json(spec.docker_credentials),
        )

        return CredentialsResult(credentials_path=credentials_path)

    @override
    async def teardown(self, resource: CredentialsResult) -> None:
        # Credentials file is cleaned up with scratch directory
        pass


class CredentialsStage(ProvisionStage[CredentialsSpec, CredentialsResult]):
    """
    Stage for managing Docker credentials in kernel containers.
    """

    pass

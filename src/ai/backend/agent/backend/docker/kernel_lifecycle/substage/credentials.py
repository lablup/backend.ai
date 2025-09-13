"""
Credentials stage for kernel lifecycle.

This stage handles Docker credentials setup for containers.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, override

from ai.backend.common.json import dump_json
from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage


@dataclass
class CredentialsSpec:
    config_dir: Path
    docker_credentials: Optional[Mapping[str, Any]]


class CredentialsSpecGenerator(ArgsSpecGenerator[CredentialsSpec]):
    pass


@dataclass
class CredentialsResult:
    credentials_path: Optional[Path]


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

        loop = asyncio.get_running_loop()
        credentials_path = spec.config_dir / "docker-creds.json"

        await loop.run_in_executor(
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

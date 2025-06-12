from dataclasses import dataclass
from typing import Any

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.session import AsyncSession
from ai.backend.common.types import ClusterMode
from ai.backend.test.templates.template import TestCode

# Test environment configuration
# TODO: Make these configurable loaderable by template wrapper
_IMAGE_NAME = "cr.backend.ai/stable/python:3.9-ubuntu20.04"
_TEST_TIMEOUT = 30.0  # seconds


@dataclass
class SessionCreationArgs:
    resources: dict[str, Any]
    container_count: int


class SessionCreationFailure(TestCode):
    _resources: dict[str, Any]
    _container_count: int
    _expected_error_code: str

    def __init__(self, args: SessionCreationArgs, expected_error_code: str) -> None:
        super().__init__()
        self._resources = args.resources
        self._container_count = args.container_count
        self._expected_error_code = expected_error_code

    async def test(self) -> None:
        async with AsyncSession() as client_session:
            session_name = "test-session-creation-failure"

            try:
                await client_session.ComputeSession.get_or_create(
                    _IMAGE_NAME,
                    name=session_name,
                    resources=self._resources,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=self._container_count,
                )
            except BackendAPIError as e:
                assert e.data["error_code"] == self._expected_error_code

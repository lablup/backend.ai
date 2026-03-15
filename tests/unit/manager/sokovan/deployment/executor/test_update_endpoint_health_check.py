"""Unit tests for DeploymentExecutor.update_endpoint_health_check().

Verifies the executor correctly reads the deploying revision's model definition
and updates the app-proxy health check config.

Test Scenarios:
- HC-001: Successful health check config update
- HC-002: No deploying_revision_id — skip silently
- HC-003: No proxy target — skip with warning
- HC-004: No vfolder on deploying revision — skip with warning
- HC-005: App-proxy client error — raises exception
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentState,
    ModelMountConfigData,
    ModelRevisionData,
    ReplicaSpec,
)
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor


def _create_deploying_deployment(
    deploying_revision_id: UUID | None = None,
    resource_group: str = "default",
) -> DeploymentInfo:
    """Create a DEPLOYING DeploymentInfo with deploying_revision_id."""
    return DeploymentInfo(
        id=uuid4(),
        metadata=DeploymentMetadata(
            name="test-deployment",
            domain="default",
            project=uuid4(),
            resource_group=resource_group,
            created_user=uuid4(),
            session_owner=uuid4(),
            created_at=datetime.now(tzutc()),
            revision_history_limit=10,
        ),
        state=DeploymentState(
            lifecycle=EndpointLifecycle.DEPLOYING,
            retry_count=0,
        ),
        replica_spec=ReplicaSpec(
            replica_count=2,
            desired_replica_count=2,
        ),
        network=DeploymentNetworkSpec(
            open_to_public=False,
            url=None,
        ),
        model_revisions=[MagicMock()],
        current_revision_id=uuid4(),
        deploying_revision_id=deploying_revision_id,
    )


class TestUpdateEndpointHealthCheck:
    """Tests for update_endpoint_health_check functionality."""

    async def test_successful_health_check_update(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """HC-001: Successfully update health check config in app-proxy.

        Given: DEPLOYING deployment with deploying_revision_id
        When: update_endpoint_health_check called
        Then: App-proxy receives updated health check config
        """
        deploying_revision_id = uuid4()
        deployment = _create_deploying_deployment(
            deploying_revision_id=deploying_revision_id,
        )

        # Arrange: proxy target
        proxy_target = ScalingGroupProxyTarget(
            addr="http://proxy:8080",
            api_token="test-token",
        )
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {
            "default": proxy_target,
        }

        # Arrange: revision data with vfolder
        vfolder_id = uuid4()
        mock_revision_data = MagicMock(spec=ModelRevisionData)
        mock_revision_data.model_mount_config = ModelMountConfigData(
            vfolder_id=vfolder_id,
            mount_destination="/models",
            definition_path="model-definition.yaml",
        )
        mock_deployment_repo.get_revision.return_value = mock_revision_data

        # Arrange: model definition with health check
        model_definition_content = {
            "name": "test-model",
            "models": [
                {
                    "name": "model",
                    "model_path": "/models",
                    "service": {
                        "start_command": ["python", "server.py"],
                        "port": 8000,
                        "health_check": {
                            "path": "/health",
                            "expected_status_code": 200,
                        },
                    },
                }
            ],
        }
        mock_deployment_repo.fetch_model_definition.return_value = model_definition_content

        # Arrange: mock app-proxy client
        mock_app_proxy_client = AsyncMock()
        with patch.object(
            deployment_executor,
            "_load_app_proxy_client",
            return_value=mock_app_proxy_client,
        ):
            # Act
            await deployment_executor.update_endpoint_health_check(deployment)

        # Assert
        mock_deployment_repo.get_revision.assert_awaited_once_with(deploying_revision_id)
        mock_deployment_repo.fetch_model_definition.assert_awaited_once_with(
            vfolder_id=vfolder_id,
            model_definition_path="model-definition.yaml",
        )
        mock_app_proxy_client.update_health_check.assert_awaited_once()
        call_args = mock_app_proxy_client.update_health_check.call_args
        assert call_args[0][0] == deployment.id
        actual_config = call_args[0][1]
        assert actual_config is not None
        assert actual_config.path == "/health"

    async def test_no_deploying_revision_skips(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """HC-002: Skip when deploying_revision_id is None.

        Given: Deployment without deploying_revision_id
        When: update_endpoint_health_check called
        Then: Returns immediately, no DB or app-proxy calls
        """
        deployment = _create_deploying_deployment(deploying_revision_id=None)

        # Act
        await deployment_executor.update_endpoint_health_check(deployment)

        # Assert: no repo calls
        mock_deployment_repo.fetch_scaling_group_proxy_targets.assert_not_awaited()
        mock_deployment_repo.get_revision.assert_not_awaited()

    async def test_no_proxy_target_skips(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """HC-003: Skip when no proxy target for scaling group.

        Given: Deployment with deploying_revision_id but no proxy target
        When: update_endpoint_health_check called
        Then: Returns after proxy target lookup, no revision fetch
        """
        deployment = _create_deploying_deployment(
            deploying_revision_id=uuid4(),
        )
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {}

        # Act
        await deployment_executor.update_endpoint_health_check(deployment)

        # Assert
        mock_deployment_repo.fetch_scaling_group_proxy_targets.assert_awaited_once()
        mock_deployment_repo.get_revision.assert_not_awaited()

    async def test_no_vfolder_skips(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """HC-004: Skip when deploying revision has no vfolder.

        Given: Deploying revision without vfolder_id
        When: update_endpoint_health_check called
        Then: Returns after revision fetch, no model definition read
        """
        deployment = _create_deploying_deployment(
            deploying_revision_id=uuid4(),
        )

        proxy_target = ScalingGroupProxyTarget(
            addr="http://proxy:8080",
            api_token="test-token",
        )
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {
            "default": proxy_target,
        }

        mock_revision_data = MagicMock(spec=ModelRevisionData)
        mock_revision_data.model_mount_config = ModelMountConfigData(
            vfolder_id=None,
            mount_destination="/models",
            definition_path="model-definition.yaml",
        )
        mock_deployment_repo.get_revision.return_value = mock_revision_data

        # Act
        await deployment_executor.update_endpoint_health_check(deployment)

        # Assert
        mock_deployment_repo.get_revision.assert_awaited_once()
        mock_deployment_repo.fetch_model_definition.assert_not_awaited()

    async def test_app_proxy_error_propagates(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """HC-005: App-proxy client error propagates to caller.

        Given: App-proxy returns error on health check update
        When: update_endpoint_health_check called
        Then: Exception propagates (caller handles it)
        """
        deployment = _create_deploying_deployment(
            deploying_revision_id=uuid4(),
        )

        proxy_target = ScalingGroupProxyTarget(
            addr="http://proxy:8080",
            api_token="test-token",
        )
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {
            "default": proxy_target,
        }

        vfolder_id = uuid4()
        mock_revision_data = MagicMock(spec=ModelRevisionData)
        mock_revision_data.model_mount_config = ModelMountConfigData(
            vfolder_id=vfolder_id,
            mount_destination="/models",
            definition_path="model-definition.yaml",
        )
        mock_deployment_repo.get_revision.return_value = mock_revision_data

        mock_deployment_repo.fetch_model_definition.return_value = {
            "name": "test-model",
            "models": [
                {
                    "name": "model",
                    "model_path": "/models",
                    "service": {
                        "start_command": ["python", "server.py"],
                        "port": 8000,
                        "health_check": {
                            "path": "/health",
                            "expected_status_code": 200,
                        },
                    },
                }
            ],
        }

        mock_app_proxy_client = AsyncMock()
        mock_app_proxy_client.update_health_check.side_effect = RuntimeError(
            "App-proxy unavailable"
        )

        with (
            patch.object(
                deployment_executor,
                "_load_app_proxy_client",
                return_value=mock_app_proxy_client,
            ),
            pytest.raises(RuntimeError, match="App-proxy unavailable"),
        ):
            await deployment_executor.update_endpoint_health_check(deployment)

    async def test_model_definition_without_health_check(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """HC-006: Model definition without health check config sends None.

        Given: Model definition without health_check section
        When: update_endpoint_health_check called
        Then: App-proxy receives None as health check config
        """
        deployment = _create_deploying_deployment(
            deploying_revision_id=uuid4(),
        )

        proxy_target = ScalingGroupProxyTarget(
            addr="http://proxy:8080",
            api_token="test-token",
        )
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {
            "default": proxy_target,
        }

        vfolder_id = uuid4()
        mock_revision_data = MagicMock(spec=ModelRevisionData)
        mock_revision_data.model_mount_config = ModelMountConfigData(
            vfolder_id=vfolder_id,
            mount_destination="/models",
            definition_path="model-definition.yaml",
        )
        mock_deployment_repo.get_revision.return_value = mock_revision_data

        # Model definition without health check
        mock_deployment_repo.fetch_model_definition.return_value = {
            "name": "test-model",
            "models": [
                {
                    "name": "model",
                    "model_path": "/models",
                    "service": {
                        "start_command": ["python", "-m", "http.server", "8080"],
                        "port": 8080,
                    },
                }
            ],
        }

        mock_app_proxy_client = AsyncMock()
        with patch.object(
            deployment_executor,
            "_load_app_proxy_client",
            return_value=mock_app_proxy_client,
        ):
            await deployment_executor.update_endpoint_health_check(deployment)

        # Assert: None passed as health_check_config
        mock_app_proxy_client.update_health_check.assert_awaited_once()
        call_args = mock_app_proxy_client.update_health_check.call_args
        assert call_args[0][1] is None

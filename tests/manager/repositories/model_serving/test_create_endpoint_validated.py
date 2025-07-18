import uuid
from unittest.mock import AsyncMock

import pytest

from ai.backend.manager.data.model_serving.types import EndpointData
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow


@pytest.mark.asyncio
async def test_create_endpoint_validated_success(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
):
    """Test successful creation of an endpoint."""
    # Arrange
    endpoint_row = sample_endpoint

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

    # Act
    result = await model_serving_repository.create_endpoint_validated(endpoint_row)

    # Assert
    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.id == endpoint_row.id
    assert result.name == endpoint_row.name

    # Verify database operations
    mock_session.add.assert_called_once_with(endpoint_row)
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once_with(endpoint_row)


@pytest.mark.asyncio
async def test_create_endpoint_validated_with_all_fields(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
    sample_user,
    sample_image,
    sample_vfolder,
):
    """Test creation of endpoint with all fields populated."""
    # Arrange
    from ai.backend.common.types import ClusterMode, ResourceSlot, RuntimeVariant

    endpoint_row = EndpointRow(
        name="full-featured-endpoint",
        domain="test-domain",
        project=uuid.uuid4(),
        resource_group="gpu-cluster",
        model=sample_vfolder.id,
        model_mount_destination="/models/custom",
        model_definition_path="model_definition.py",
        runtime_variant=RuntimeVariant.CUSTOM,
        session_owner=sample_user.uuid,
        tag="v1.0.0",
        startup_command="python -m model_server",
        bootstrap_script="pip install -r requirements.txt",
        callback_url="https://webhook.example.com/callback",
        environ={"API_KEY": "secret", "DEBUG": "false"},
        resource_slots=ResourceSlot({"cpu": "4", "mem": "8g", "cuda.device": "1"}),
        resource_opts={"shmem": "2g"},
        image=sample_image,
        replicas=3,
        cluster_mode=ClusterMode.MULTI_NODE,
        cluster_size=3,
        extra_mounts=[],
        created_user=sample_user.uuid,
    )
    # Set attributes normally set by database
    endpoint_row.id = uuid.uuid4()
    endpoint_row.created_at = None
    endpoint_row.destroyed_at = None
    endpoint_row.lifecycle_stage = EndpointLifecycle.CREATED
    endpoint_row.retries = 0
    endpoint_row.url = "https://api.example.com/v1/models/full-featured"
    endpoint_row.open_to_public = False
    endpoint_row.image_row = sample_image
    endpoint_row.session_owner_row = sample_user
    endpoint_row.created_user_row = sample_user
    endpoint_row.routings = []

    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

    # Act
    result = await model_serving_repository.create_endpoint_validated(endpoint_row)

    # Assert
    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.name == "full-featured-endpoint"
    assert result.replicas == 3
    assert result.cluster_mode == "multi-node"
    assert result.runtime_variant == "custom"


@pytest.mark.asyncio
async def test_create_endpoint_validated_transaction_handling(
    model_serving_repository,
    mock_db_engine,
    mock_session,
    sample_endpoint,
):
    """Test that creation properly handles database transactions."""
    # Arrange
    endpoint_row = sample_endpoint

    # Create a proper async context manager mock
    async_cm = AsyncMock()
    async_cm.__aenter__.return_value = mock_session
    async_cm.__aexit__.return_value = None
    mock_db_engine.begin_session.return_value = async_cm

    # Act
    result = await model_serving_repository.create_endpoint_validated(endpoint_row)

    # Assert
    assert result is not None

    # Verify that begin_session was called (transaction started)
    mock_db_engine.begin_session.assert_called_once()

    # Verify transaction operations
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once()

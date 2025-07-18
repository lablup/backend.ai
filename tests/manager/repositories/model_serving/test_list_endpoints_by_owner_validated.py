import uuid

import pytest

from ai.backend.manager.data.model_serving.types import EndpointData
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow

from .conftest import setup_mock_query_result


def create_additional_endpoint(base_endpoint, name_suffix="2"):
    endpoint = EndpointRow(
        name=f"test-endpoint-{name_suffix}",
        model=base_endpoint.model,
        model_mount_destination=base_endpoint.model_mount_destination,
        model_definition_path=base_endpoint.model_definition_path,
        runtime_variant=base_endpoint.runtime_variant,
        session_owner=base_endpoint.session_owner,
        tag=base_endpoint.tag,
        startup_command=base_endpoint.startup_command,
        bootstrap_script=base_endpoint.bootstrap_script,
        callback_url=base_endpoint.callback_url,
        environ=base_endpoint.environ,
        resource_slots=base_endpoint.resource_slots,
        resource_opts=base_endpoint.resource_opts,
        image=base_endpoint.image_row,
        replicas=base_endpoint.replicas,
        cluster_mode=base_endpoint.cluster_mode,
        cluster_size=base_endpoint.cluster_size,
        extra_mounts=base_endpoint.extra_mounts,
        created_user=base_endpoint.created_user,
        project=base_endpoint.project,
        domain=base_endpoint.domain,
        resource_group=base_endpoint.resource_group,
    )

    # Set database-generated attributes
    endpoint.id = uuid.uuid4()
    endpoint.created_at = base_endpoint.created_at
    endpoint.destroyed_at = None
    endpoint.lifecycle_stage = EndpointLifecycle.CREATED
    endpoint.retries = 0
    endpoint.url = f"https://api.example.com/v1/models/{endpoint.name}"
    endpoint.open_to_public = False
    endpoint.image_row = base_endpoint.image_row
    endpoint.session_owner_row = base_endpoint.session_owner_row
    endpoint.created_user_row = base_endpoint.created_user_row
    endpoint.routings = []

    return endpoint


@pytest.mark.asyncio
async def test_list_endpoints_by_owner_validated_success(
    model_serving_repository,
    setup_readonly_session,
    sample_endpoint,
    sample_user,
):
    """Test successful listing of endpoints owned by a user."""
    # Arrange
    session_owner_id = sample_user.uuid
    endpoint1 = sample_endpoint
    endpoint2 = create_additional_endpoint(sample_endpoint)

    setup_mock_query_result(setup_readonly_session, scalars_all_result=[endpoint1, endpoint2])

    # Act
    result = await model_serving_repository.list_endpoints_by_owner_validated(session_owner_id)

    # Assert
    assert len(result) == 2
    assert all(isinstance(endpoint, EndpointData) for endpoint in result)
    assert result[0].id == endpoint1.id
    assert result[1].id == endpoint2.id
    setup_readonly_session.execute.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenario,filter_name,expected_count",
    [
        ("with_name_filter", "specific-endpoint", 1),
        ("empty_result", None, 0),
        ("excludes_destroyed", None, 1),
    ],
)
async def test_list_endpoints_by_owner_validated_scenarios(
    model_serving_repository,
    setup_readonly_session,
    sample_endpoint,
    sample_user,
    scenario,
    filter_name,
    expected_count,
):
    """Test various scenarios for listing endpoints by owner."""
    # Arrange
    if scenario == "with_name_filter":
        session_owner_id = sample_user.uuid
        sample_endpoint.name = filter_name
        mock_result = [sample_endpoint]
    elif scenario == "empty_result":
        session_owner_id = uuid.uuid4()
        mock_result = []
    else:  # excludes_destroyed
        session_owner_id = sample_user.uuid
        mock_result = [sample_endpoint]  # Only active endpoint returned

    setup_mock_query_result(setup_readonly_session, scalars_all_result=mock_result)

    # Act
    if filter_name:
        result = await model_serving_repository.list_endpoints_by_owner_validated(
            session_owner_id, name=filter_name
        )
    else:
        result = await model_serving_repository.list_endpoints_by_owner_validated(session_owner_id)

    # Assert
    assert len(result) == expected_count

    if expected_count > 0:
        assert all(isinstance(endpoint, EndpointData) for endpoint in result)
        if filter_name:
            assert result[0].name == filter_name
        if scenario == "excludes_destroyed":
            assert result[0].lifecycle_stage == EndpointLifecycle.CREATED

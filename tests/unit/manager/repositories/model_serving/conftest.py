import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl

from ai.backend.common.types import ClusterMode, ResourceSlot, RuntimeVariant
from ai.backend.manager.data.model_serving.types import EndpointData
from ai.backend.manager.models.endpoint import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointAutoScalingRuleRow,
    EndpointLifecycle,
    EndpointRow,
)
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.routing import RouteStatus, RoutingRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.model_serving import EndpointCreatorSpec
from ai.backend.manager.repositories.model_serving.admin_repository import (
    AdminModelServingRepository,
)
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository


@pytest.fixture
def mock_db_engine():
    """Mock database engine for repository testing."""
    mock_engine = MagicMock(spec=ExtendedAsyncSAEngine)

    # Create async context manager mocks
    async_cm_readonly = AsyncMock()
    async_cm_readonly.__aenter__ = AsyncMock()
    async_cm_readonly.__aexit__ = AsyncMock()
    mock_engine.begin_readonly_session.return_value = async_cm_readonly

    async_cm = AsyncMock()
    async_cm.__aenter__ = AsyncMock()
    async_cm.__aexit__ = AsyncMock()
    mock_engine.begin_session.return_value = async_cm

    return mock_engine


@pytest.fixture
def model_serving_repository(mock_db_engine):
    """Create a ModelServingRepository instance with mocked database."""
    return ModelServingRepository(db=mock_db_engine)


@pytest.fixture
def admin_model_serving_repository(mock_db_engine):
    """Create an AdminModelServingRepository instance with mocked database."""
    return AdminModelServingRepository(db=mock_db_engine)


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return UserRow(
        uuid=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        password="hashed_password",
        need_password_change=False,
        full_name="Test User",
        description="Test user for unit tests",
        status=UserStatus.ACTIVE,
        status_info="active",
        domain_name="default",
        role=UserRole.USER,
        resource_policy="default",
        created_at=datetime.now(timezone.utc),
        modified_at=datetime.now(timezone.utc),
        main_access_key="test-access-key",
        sudo_session_enabled=False,
    )


@pytest.fixture
def sample_admin_user():
    """Create a sample admin user for testing."""
    return UserRow(
        uuid=uuid.uuid4(),
        username="adminuser",
        email="admin@example.com",
        password="hashed_password",
        need_password_change=False,
        full_name="Admin User",
        description="Admin user for unit tests",
        status=UserStatus.ACTIVE,
        status_info="active",
        domain_name="default",
        role=UserRole.ADMIN,
        resource_policy="default",
        created_at=datetime.now(timezone.utc),
        modified_at=datetime.now(timezone.utc),
        main_access_key="admin-access-key",
        sudo_session_enabled=True,
    )


@pytest.fixture
def sample_superadmin_user():
    """Create a sample superadmin user for testing."""
    return UserRow(
        uuid=uuid.uuid4(),
        username="superadmin",
        email="superadmin@example.com",
        password="hashed_password",
        need_password_change=False,
        full_name="Super Admin",
        description="Superadmin user for unit tests",
        status=UserStatus.ACTIVE,
        status_info="active",
        domain_name="default",
        role=UserRole.SUPERADMIN,
        resource_policy="default",
        created_at=datetime.now(timezone.utc),
        modified_at=datetime.now(timezone.utc),
        main_access_key="superadmin-access-key",
        sudo_session_enabled=True,
    )


@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    image = ImageRow(
        name="test-model-image", project=None, architecture="x86_64", registry_id=uuid.uuid4()
    )
    image.id = uuid.uuid4()
    image.registry = "docker.io"
    image.image = "test/model:latest"
    image.tag = "latest"
    image.is_local = False
    image.size_bytes = 1073741824  # 1GB
    image.type = "COMPUTE"
    image.accelerators = ""
    image.labels = {}
    image._resources = {}
    image.created_at = datetime.now(timezone.utc)
    image.config_digest = "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    image.status = "active"
    return image


@pytest.fixture
def sample_vfolder():
    """Create a sample vfolder for testing."""
    vfolder = VFolderRow()
    vfolder.id = uuid.uuid4()
    vfolder.name = "model-vfolder"
    vfolder.user = uuid.uuid4()
    vfolder.group = None
    vfolder.host = "storage-host"
    vfolder.domain_name = "default"
    vfolder.ownership_type = "user"
    vfolder.max_files = 10000
    vfolder.max_size = 10737418240  # 10GB
    vfolder.num_files = 100
    vfolder.cur_size = 1073741824  # 1GB
    vfolder.created_at = datetime.now(timezone.utc)
    vfolder.last_used = datetime.now(timezone.utc)
    vfolder.unmanaged_path = ""
    vfolder.usage_mode = "model"
    vfolder.permission = "rw"
    vfolder.last_size_update = datetime.now(timezone.utc)
    vfolder.status = "ready"
    return vfolder


@pytest.fixture
def sample_endpoint_creator_spec(sample_user, sample_image, sample_vfolder) -> EndpointCreatorSpec:
    return EndpointCreatorSpec(
        name="test-endpoint",
        model=sample_vfolder.id,
        model_mount_destination="/models",
        model_definition_path="model.py",
        runtime_variant=RuntimeVariant.CUSTOM,
        session_owner=sample_user.uuid,
        tag="test",
        startup_command="python serve.py",
        bootstrap_script="pip install -r requirements.txt",
        callback_url=yarl.URL("https://callback.example.com"),
        environ={"MODEL_NAME": "test"},
        resource_slots=ResourceSlot({"cpu": "2", "mem": "4g"}),
        resource_opts={},
        image=sample_image.id,
        replicas=1,
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=1,
        extra_mounts=[],
        created_user=sample_user.uuid,
        project=sample_user.groups if hasattr(sample_user, "groups") else uuid.uuid4(),
        domain="default",
        resource_group="default",
    )


@pytest.fixture
def sample_endpoint_creator(
    sample_endpoint_creator_spec: EndpointCreatorSpec,
) -> Creator[EndpointRow]:
    """Create a Creator wrapper for endpoint creation."""
    return Creator(spec=sample_endpoint_creator_spec)


@pytest.fixture
def sample_endpoint(
    sample_endpoint_creator_spec: EndpointCreatorSpec, sample_user, sample_image
) -> EndpointRow:
    """Create a sample endpoint for testing."""
    endpoint = sample_endpoint_creator_spec.build_row()
    # Set attributes that are normally set by the database
    endpoint.id = uuid.uuid4()
    endpoint.created_at = datetime.now(timezone.utc)
    endpoint.destroyed_at = None
    endpoint.lifecycle_stage = EndpointLifecycle.CREATED
    endpoint.retries = 0
    endpoint.url = f"https://api.example.com/v1/models/{endpoint.name}"
    endpoint.open_to_public = False
    # Set related rows for from_row method
    endpoint.image_row = sample_image
    endpoint.session_owner_row = sample_user
    endpoint.created_user_row = sample_user
    endpoint.routings = []
    return endpoint


@pytest.fixture
def sample_route(sample_endpoint):
    """Create a sample routing for testing."""
    route = RoutingRow(
        id=uuid.uuid4(),
        endpoint=sample_endpoint.id,
        session=uuid.uuid4(),
        status=RouteStatus.HEALTHY,
        traffic_ratio=1.0,
        session_owner=sample_endpoint.session_owner,
        domain=sample_endpoint.domain,
        project=sample_endpoint.project,
    )
    return route


@pytest.fixture
def sample_auto_scaling_rule(sample_endpoint):
    """Create a sample auto scaling rule for testing."""
    rule = EndpointAutoScalingRuleRow(
        id=uuid.uuid4(),
        endpoint=sample_endpoint.id,
        metric_source=AutoScalingMetricSource.KERNEL,
        metric_name="cpu_util",
        threshold=80.0,
        comparator=AutoScalingMetricComparator.GREATER_THAN,
        step_size=1,
        cooldown_seconds=300,
        min_replicas=1,
        max_replicas=10,
        created_at=datetime.now(timezone.utc),
        endpoint_row=sample_endpoint,
    )
    return rule


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.connection = AsyncMock()

    # Set up execute to return a mock result that has scalar methods
    mock_result = AsyncMock()
    mock_result.scalar = MagicMock()
    mock_result.scalar_one_or_none = MagicMock()
    mock_result.scalars = MagicMock()
    mock_result.first = MagicMock()
    session.execute.return_value = mock_result

    return session


@pytest.fixture
def setup_readonly_session(mock_db_engine, mock_session):
    """Automatically sets up a readonly session fixture"""
    mock_db_engine.begin_readonly_session.return_value.__aenter__.return_value = mock_session
    return mock_session


@pytest.fixture
def setup_writable_session(mock_db_engine, mock_session):
    """Automatically sets up a writable session fixture"""
    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    return mock_session


@pytest.fixture
def patch_endpoint_get(mocker):
    """Patch EndpointRow.get method using mocker."""
    return mocker.patch(
        "ai.backend.manager.models.endpoint.EndpointRow.get", new_callable=AsyncMock
    )


@pytest.fixture
def patch_routing_get(mocker):
    """Patch RoutingRow.get method using mocker."""
    return mocker.patch("ai.backend.manager.models.routing.RoutingRow.get", new_callable=AsyncMock)


@pytest.fixture
def patch_user_get(mocker):
    """Patch UserRow.get method using mocker."""
    return mocker.patch("ai.backend.manager.models.user.UserRow.get", new_callable=AsyncMock)


@pytest.fixture
def patch_vfolder_get(mocker):
    """Patch VFolderRow.get method using mocker."""
    return mocker.patch("ai.backend.manager.models.vfolder.VFolderRow.get", new_callable=AsyncMock)


@pytest.fixture
def patch_image_resolve(mocker):
    """Patch ImageRow.resolve method using mocker."""
    return mocker.patch("ai.backend.manager.models.image.ImageRow.resolve", new_callable=AsyncMock)


@pytest.fixture
def patch_session_get(mocker):
    """Patch SessionRow.get_session method using mocker."""
    return mocker.patch(
        "ai.backend.manager.models.session.SessionRow.get_session", new_callable=AsyncMock
    )


@pytest.fixture
def patch_auto_scaling_rule_get(mocker):
    """Patch EndpointAutoScalingRuleRow.get method using mocker."""
    return mocker.patch(
        "ai.backend.manager.models.endpoint.EndpointAutoScalingRuleRow.get", new_callable=AsyncMock
    )


@pytest.fixture
def patch_resolve_group_name_or_id(mocker):
    """Patch resolve_group_name_or_id function using mocker."""
    return mocker.patch(
        "ai.backend.manager.repositories.model_serving.repository.resolve_group_name_or_id"
    )


def setup_db_session_mock(mock_db_engine, mock_session):
    """Helper function to set up database session mocking consistently."""
    mock_db_engine.begin_readonly_session.return_value.__aenter__.return_value = mock_session
    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    return mock_session


def setup_mock_query_result(
    mock_session, scalar_result=None, scalars_all_result=None, scalar_one_or_none_result=None
):
    """Helper function to set up common query result patterns."""
    if scalar_result is not None:
        mock_session.execute.return_value.scalar.return_value = scalar_result
    if scalars_all_result is not None:
        mock_session.execute.return_value.scalars.return_value.all.return_value = scalars_all_result
    if scalar_one_or_none_result is not None:
        mock_session.execute.return_value.scalar_one_or_none.return_value = (
            scalar_one_or_none_result
        )
    return mock_session


def assert_update_query_executed(mock_session, expected_field=None):
    """Helper function to verify that an update query was executed"""
    mock_session.execute.assert_called()
    if expected_field:
        executed_query = mock_session.execute.call_args[0][0]
        assert expected_field in str(executed_query)


def assert_basic_endpoint_result(result, endpoint_row):
    """Helper function to validate basic endpoint result"""
    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.id == endpoint_row.id
    assert result.name == endpoint_row.name


def assert_endpoint_creation_operations(mock_session, endpoint_row):
    """Helper function to verify database operations related to endpoint creation"""
    mock_session.add.assert_called_once_with(endpoint_row)
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once_with(endpoint_row)


def create_full_featured_endpoint(sample_user, sample_image, sample_vfolder):
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
        callback_url=yarl.URL("https://webhook.example.com/callback"),
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

    return endpoint_row

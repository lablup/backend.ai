import uuid
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import AccessKey, DefaultForUnspecified, ResourceSlot
from ai.backend.manager.data.auth.types import AuthenticatedKeypair, AuthenticatedUser
from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.models.user import UserRole


@pytest.fixture
def mock_authenticated_request() -> MagicMock:
    mock_request = MagicMock()
    mock_request.__getitem__.side_effect = {
        "user": AuthenticatedUser(
            uuid=UserID(uuid.uuid4()),
            email="test@email.com",
            role=UserRole.USER,
            domain_name="default",
            domain_id=DomainID(uuid.uuid4()),
            sudo_session_enabled=False,
            main_access_key=None,
            allowed_client_ip=None,
            resource_policy=UserResourcePolicyData(name="default"),
        ),
        "keypair": AuthenticatedKeypair(
            access_key=AccessKey("TESTKEY"),
            secret_key=None,
            is_admin=False,
            rate_limit=None,
            resource_policy=KeyPairResourcePolicyData(
                name="default",
                created_at=None,
                default_for_unspecified=DefaultForUnspecified.LIMITED,
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=10,
                max_pending_session_count=None,
                max_pending_session_resource_slots=None,
                max_priority=None,
                max_concurrent_sftp_sessions=2,
                max_containers_per_session=1,
                idle_timeout=3600,
                allowed_vfolder_hosts={"local": "rw"},
            ),
        ),
    }.get

    vfolder_id = str(uuid.uuid4())
    mock_request.match_info = {"vfolder_id": vfolder_id}
    return mock_request


class TestResponse(BaseModel):
    test: str


@pytest.fixture
def mock_success_response() -> TestResponse:
    return TestResponse(test="response")

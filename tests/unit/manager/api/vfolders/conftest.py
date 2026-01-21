import uuid
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel


@pytest.fixture
def mock_authenticated_request():
    mock_request = MagicMock()
    mock_request.__getitem__.side_effect = {
        "user": {
            "uuid": uuid.uuid4(),
            "role": "user",
            "email": "test@email.com",
            "domain_name": "default",
        },
        "keypair": {
            "access_key": "TESTKEY",
            "resource_policy": {"allowed_vfolder_hosts": ["local"]},
        },
    }.get

    vfolder_id = str(uuid.uuid4())
    mock_request.match_info = {"vfolder_id": vfolder_id}
    return mock_request


class TestResponse(BaseModel):
    test: str


@pytest.fixture
def mock_success_response() -> TestResponse:
    return TestResponse(test="response")

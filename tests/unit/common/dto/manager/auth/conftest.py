from uuid import UUID

import pytest

_SAMPLE_CLIENT_TYPE_ID = UUID("00000000-0000-0000-0000-0000000000eb")


@pytest.fixture
def sample_client_type_id() -> UUID:
    return _SAMPLE_CLIENT_TYPE_ID

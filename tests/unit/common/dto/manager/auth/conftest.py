from uuid import UUID, uuid4

import pytest


@pytest.fixture
def sample_client_type_id() -> UUID:
    return uuid4()

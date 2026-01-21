import uuid

from ai.backend.common.contexts.request_id import (
    current_request_id,
    with_request_id,
)


def test_current_request_id_without_context():
    assert current_request_id() is None


def test_with_request_id_context():
    # Test with explicit request ID
    test_id = str(uuid.uuid4())
    with with_request_id(test_id):
        assert current_request_id() == test_id
    assert current_request_id() is None

    # Test with auto-generated request ID
    with with_request_id():
        req_id = current_request_id()
        assert req_id is not None
        assert isinstance(req_id, str)
        # Verify it's a valid UUID
        uuid.UUID(req_id)
    assert current_request_id() is None


def test_nested_request_id_contexts():
    outer_id = str(uuid.uuid4())
    inner_id = str(uuid.uuid4())

    with with_request_id(outer_id):
        assert current_request_id() == outer_id
        with with_request_id(inner_id):
            assert current_request_id() == inner_id
        assert current_request_id() == outer_id
    assert current_request_id() is None

import uuid

from ai.backend.common.contexts.request_id import (
    REQUEST_ID_HEADER,
    bind_request_id,
    current_request_id,
    receive_request_id,
    with_request_id,
)


def test_current_request_id_without_context() -> None:
    assert current_request_id() is None


def test_with_request_id_context() -> None:
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


def test_nested_request_id_contexts() -> None:
    outer_id = str(uuid.uuid4())
    inner_id = str(uuid.uuid4())

    with with_request_id(outer_id):
        assert current_request_id() == outer_id
        with with_request_id(inner_id):
            assert current_request_id() == inner_id
        assert current_request_id() == outer_id
    assert current_request_id() is None


def test_receive_request_id_sets_context() -> None:
    test_id = str(uuid.uuid4())
    # Use with_request_id to ensure clean context after test
    with with_request_id():
        receive_request_id(test_id, "test context")
        assert current_request_id() == test_id


def test_bind_request_id_adds_to_target() -> None:
    test_id = str(uuid.uuid4())
    target: dict[str, str] = {}

    with with_request_id(test_id):
        bind_request_id(target, "test context")
        assert target[REQUEST_ID_HEADER] == test_id


def test_bind_request_id_with_custom_key() -> None:
    test_id = str(uuid.uuid4())
    target: dict[str, str] = {}

    with with_request_id(test_id):
        bind_request_id(target, "test context", key="custom_key")
        assert target["custom_key"] == test_id

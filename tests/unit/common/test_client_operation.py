from ai.backend.common.contexts.client_operation import (
    get_client_operation,
    with_client_operation,
)


def test_get_client_operation_without_context() -> None:
    assert get_client_operation() == ""


def test_with_client_operation_context() -> None:
    with with_client_operation("list_sessions"):
        assert get_client_operation() == "list_sessions"
    assert get_client_operation() == ""


def test_with_empty_client_operation() -> None:
    with with_client_operation(""):
        assert get_client_operation() == ""


def test_nested_client_operation_contexts() -> None:
    with with_client_operation("list_sessions"):
        assert get_client_operation() == "list_sessions"
        with with_client_operation("list_agents"):
            assert get_client_operation() == "list_agents"
        assert get_client_operation() == "list_sessions"
    assert get_client_operation() == ""

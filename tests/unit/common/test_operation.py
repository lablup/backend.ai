from ai.backend.common.contexts.operation import (
    get_client_operation,
    with_client_operation,
)


class TestGetClientOperation:
    def test_returns_empty_string_when_not_set(self) -> None:
        assert get_client_operation() == ""

    def test_returns_correct_value_within_context(self) -> None:
        with with_client_operation("createSession"):
            assert get_client_operation() == "createSession"

    def test_resets_after_context_exit(self) -> None:
        with with_client_operation("createSession"):
            pass
        assert get_client_operation() == ""

    def test_handles_empty_string_operation(self) -> None:
        with with_client_operation(""):
            assert get_client_operation() == ""


class TestNestedClientOperationContexts:
    def test_nested_contexts_restore_correctly(self) -> None:
        with with_client_operation("outerOp"):
            assert get_client_operation() == "outerOp"
            with with_client_operation("innerOp"):
                assert get_client_operation() == "innerOp"
            assert get_client_operation() == "outerOp"
        assert get_client_operation() == ""

from ai.backend.agent.containerd.session_tracker import (
    SessionContainerTracker,
    TeardownScope,
)


class TestSessionContainerTracker:
    def test_last_container_returns_teardown_scope(self) -> None:
        t = SessionContainerTracker()
        t.track("s1", "c1")
        assert t.untrack("c1") == TeardownScope(session_id="s1")

    def test_teardown_only_after_last_container(self) -> None:
        t = SessionContainerTracker()
        t.track("s1", "c1")
        t.track("s1", "c2")
        assert t.untrack("c1") is None  # c2 still live
        assert t.untrack("c2") == TeardownScope(session_id="s1")

    def test_untracked_container_is_noop(self) -> None:
        t = SessionContainerTracker()
        assert t.untrack("unknown") is None

    def test_sessions_are_independent(self) -> None:
        t = SessionContainerTracker()
        t.track("s1", "c1")
        t.track("s2", "c2")
        assert t.untrack("c1") == TeardownScope(session_id="s1")
        assert t.untrack("c2") == TeardownScope(session_id="s2")

    def test_scope_is_returned_once(self) -> None:
        t = SessionContainerTracker()
        t.track("s1", "c1")
        assert t.untrack("c1") is not None
        assert t.untrack("c1") is None  # already gone

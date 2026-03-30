from ai.backend.manager.defs import LockID


def test_unique_global_lock_id_value() -> None:
    lock_id_value: set[int] = set()
    for _, member in LockID.__members__.items():
        int_value = member.value
        assert int_value not in lock_id_value
        lock_id_value.add(int_value)

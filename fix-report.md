# Fix Report: BA-4912

## Fix Items

| # | Item | Status | Action Taken |
|---|------|--------|-------------|
| 1 | Alembic migration revision ID was placeholder `a1b2c3d4e5f6` | ✅ Fixed | Generated proper hex ID `6f2f5d828a52`, deleted old file, created new `6f2f5d828a52_add_session_is_preemptible.py` with correct `down_revision = "b1009fe7f865"` |
| 2 | Test files missing `is_preemptible` argument (13 type errors, 5 files) | ✅ Fixed | Added `is_preemptible=True` to all 13 call sites across 5 test files |
| 3 | Migration `op.add_column()` missing `server_default` | ✅ Fixed | Added `server_default=sa.text("true")` to `op.add_column()` in new migration; also removed manual UPDATE step (server_default handles it) |
| 4 | ORM `mapped_column()` in `row.py` missing `server_default` | ✅ Fixed | Added `server_default=sa.text("true")` to `SessionRow.is_preemptible` column definition |
| 5 | KeyError risk in `service.py:667` using `params["is_preemptible"]` | ✅ Fixed | Changed to `params.get("is_preemptible", SESSION_IS_PREEMPTIBLE_DEFAULT)` and added import |

## Verification Results

| Criterion | Result |
|-----------|--------|
| `pants check src/ai/backend/manager:: src/ai/backend/common::` passes (no new errors beyond pre-existing processors.py issues) | ✅ Pass — `mypy succeeded` |
| `pants test tests/unit/manager/services/session/::` passes | ✅ Pass — 2/2 test files succeeded |
| `pants test tests/unit/manager/repositories/scheduler/::` passes | ✅ Pass — 4/4 test files succeeded |
| `pants test tests/unit/manager/api/compute_sessions/::` passes | ✅ Pass — 1/1 test file succeeded |
| `pants test tests/unit/manager/sokovan/scheduler/provisioner/::` passes | ✅ Pass — all test files succeeded |
| `pants lint src/ai/backend/manager/models/session/::` passes | ✅ Pass |
| Alembic migration file has valid unique revision ID (not `a1b2c3d4e5f6`) | ✅ Pass — new ID: `6f2f5d828a52` |

## Files Modified

- `src/ai/backend/manager/models/alembic/versions/6f2f5d828a52_add_session_is_preemptible.py` (new)
- `src/ai/backend/manager/models/alembic/versions/a1b2c3d4e5f6_add_session_is_preemptible.py` (deleted)
- `src/ai/backend/manager/models/session/row.py` — added `server_default=sa.text("true")`
- `src/ai/backend/manager/services/session/service.py` — fixed KeyError, added import
- `tests/unit/manager/services/session/test_session_service.py` — added `is_preemptible=True` (2 sites)
- `tests/unit/manager/services/session/test_session_lifecycle_service.py` — added `is_preemptible=True` (8 sites)
- `tests/unit/manager/repositories/scheduler/test_scheduling_history_recording.py` — added `is_preemptible=True` (1 site)
- `tests/unit/manager/api/compute_sessions/test_handler.py` — added `is_preemptible=True` (1 site)
- `tests/unit/manager/sokovan/scheduler/provisioner/test_provisioner.py` — added `is_preemptible=True` (1 site)

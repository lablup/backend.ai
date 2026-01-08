# SQLAlchemy 2.0 Migration Task List

## Current Status (2026-01-08)
- **Total Errors**: 1,374 errors in 175 files
- **Checked Files**: 3,138 source files

## Completed Work

### Phase 1: Basic Syntax Migration (Completed)
- [x] Row indexing: `row["column"]` → `row.column` (~360 errors)
- [x] Select list args: `select([col1, col2])` → `select(col1, col2)` (~260 errors)
- [x] Insert args: `insert(table, values)` → `insert(table).values(...)` (~10 errors)
- [x] Result.rowcount: Added `cast(CursorResult, result)` (~36 errors)

### Phase 2: ORM Row 2.0 Migration (Completed - 6 batches)
- [x] Batch 1: 4 files (commit: 204e4f8ca)
- [x] Batch 2: endpoint/row.py (commit: 367ee0361)
- [x] Batch 3: session/row.py + kernel/row.py (commit: f19a2fcf7)
- [x] Batch 4: 12 files (commit: e2620ab38)
- [x] Batch 5: 15 files (commit: 21e605789)
- [x] Batch 6: IDColumn patterns (commit: 99cf04673)

### Phase 3: Infrastructure (Completed)
- [x] TypeDecorator signature fixes
- [x] async_sessionmaker migration

---

## Remaining Work

### High Priority - Core Files (by error count)

| File | Errors | Primary Issues |
|------|--------|----------------|
| src/ai/backend/manager/registry.py | 105 | `Mapping[str, Any]` attribute access, AgentId type |
| src/ai/backend/manager/api/vfolder.py | 71 | Row attribute access, type issues |
| src/ai/backend/manager/repositories/permission_controller/db_source/db_source.py | 66 | ORM query types |
| src/ai/backend/manager/models/session/row.py | 41 | Column vs runtime value types |
| src/ai/backend/manager/models/endpoint/row.py | 37 | Column vs runtime value types |
| src/ai/backend/manager/api/stream.py | 34 | Row attribute access |
| src/ai/backend/manager/repositories/schedule/repository.py | 29 | ORM query types |
| src/ai/backend/appproxy/coordinator/models/worker.py | 29 | ORM migration needed |
| src/ai/backend/appproxy/coordinator/models/circuit.py | 27 | ORM migration needed |
| src/ai/backend/manager/repositories/vfolder/repository.py | 26 | ORM query types |
| src/ai/backend/manager/models/user/row.py | 26 | Column vs runtime value types |

### Error Type Categories

#### Category 1: Row/Mapping Attribute Access (High Priority)
**Total: ~60 errors**
```
"Mapping[str, Any]" has no attribute "id" (42)
"Mapping[str, Any]" has no attribute "host" (6)
etc.
```
**Fix**: Use proper Row class types instead of Mapping[str, Any]

#### Category 2: String Index on Rows (Medium Priority)
**Total: ~40 errors**
```
Invalid index type "str" for "str"; expected type "SupportsIndex | slice"
No overload variant of "__getitem__" of "Row" matches argument type "str"
```
**Fix**: Change `row["column"]` to `row.column`

#### Category 3: Boolean Expression Types (Medium Priority)
**Total: ~30 errors**
```
Argument 1 to "where" has incompatible type "bool"
Argument 2 to "and_" has incompatible type "bool"
Argument 2 to "join" has incompatible type "bool"
```
**Fix**: Use explicit comparison operators (e.g., `column == value` instead of `value`)

#### Category 4: select() List Args (Low Priority - Alembic)
**Total: ~20 errors**
```
No overload variant of "select" matches argument type "list[...]"
```
**Fix**: `select([cols])` → `select(*cols)` (mostly in alembic files - skip)

#### Category 5: Column vs Runtime Value Types (Medium Priority)
**Total: ~40 errors**
```
Incompatible types in assignment (expression has type "str", variable has type "Column[str]")
Argument "name" has incompatible type "Column[str]"; expected "str"
```
**Fix**: ORM 2.0 `Mapped[T]` type annotations fix these automatically

#### Category 6: Nullable Type Issues (Low Priority)
**Total: ~30 errors**
```
Item "None" of "Row[Any] | None" has no attribute "uuid"
Item "None" of "KernelRow | None" has no attribute "status"
```
**Fix**: Add proper None checks or use `cast()` where appropriate

#### Category 7: AppProxy Models (Separate Task)
**Total: ~100 errors**
Files:
- src/ai/backend/appproxy/coordinator/models/worker.py (29)
- src/ai/backend/appproxy/coordinator/models/circuit.py (27)
- src/ai/backend/appproxy/coordinator/api/worker_v2.py (20)
- src/ai/backend/appproxy/coordinator/api/health.py (14)
- etc.

**Fix**: Need ORM 2.0 migration for appproxy models

### Alembic Files (Skip - Legacy Code)
~200+ errors in alembic migration files
- `Inspector.from_engine(Connection)` type issues
- `existing_server_default` type issues
- `select([...])` list args
- `Row["column"]` indexing

**Decision**: These are legacy migration files, type errors don't affect runtime.

---

## Next Steps (Recommended Order)

### Step 1: Fix remaining Row["column"] patterns
Files to check:
```bash
grep -r 'row\["' src/ai/backend/manager/ --include="*.py" | grep -v alembic | grep -v __pycache__
```

### Step 2: Fix Boolean expression issues
Search pattern:
```bash
grep -rE '\.where\((True|False|[a-z_]+)\)' src/ai/backend/manager/ --include="*.py"
```

### Step 3: Fix Mapping[str, Any] attribute access
Primary file: `registry.py` (105 errors)
- Change function return types from `Mapping[str, Any]` to proper Row types

### Step 4: AppProxy ORM Migration (Separate Task)
- appproxy/coordinator/models/* need same ORM 2.0 migration as manager

---

## Commands

### Run full type check
```bash
pants --no-colors --no-dynamic-ui check :: 2>&1 | tee /tmp/typecheck-results.txt
```

### Count errors by file
```bash
grep ": error:" /tmp/typecheck-results.txt | cut -d: -f1 | sort | uniq -c | sort -rn | head -30
```

### Count error types
```bash
grep ": error:" /tmp/typecheck-results.txt | sed 's/.*: error: //' | sed 's/  \[.*//' | sort | uniq -c | sort -rn | head -30
```

### Check specific file errors
```bash
grep "specific/file.py" /tmp/typecheck-results.txt
```

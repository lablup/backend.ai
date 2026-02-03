---
Author: HyeokJin Kim (hyeokjin.kim@lablup.com)
Status: Draft
Created: 2026-01-30
Created-Version: 26.1.0
Target-Version:
Implemented-Version:
---

# MyPy Strict Mode Migration

## Related Issues

- JIRA Epic: [BA-4169](https://lablup.atlassian.net/browse/BA-4169) - MyPy Strict Mode Migration
  - [BA-4170](https://lablup.atlassian.net/browse/BA-4170) - Priority 1: unused-coroutine (20)
  - [BA-4171](https://lablup.atlassian.net/browse/BA-4171) - Priority 2: comparison-overlap (61)
  - [BA-4172](https://lablup.atlassian.net/browse/BA-4172) - Priority 3: call-arg (33)
  - [BA-4173](https://lablup.atlassian.net/browse/BA-4173) - Priority 4: arg-type (170)
  - [BA-4174](https://lablup.atlassian.net/browse/BA-4174) - Priority 5: assignment (33)
  - [BA-4175](https://lablup.atlassian.net/browse/BA-4175) - Priority 6: attr-defined (29)
  - [BA-4176](https://lablup.atlassian.net/browse/BA-4176) - Priority 7: union-attr (23)
  - [BA-4177](https://lablup.atlassian.net/browse/BA-4177) - Priority 8: return-value (5)
- GitHub: N/A

## Motivation

The Backend.AI project currently uses MyPy for type checking, but strict mode is not enabled.

### Problems

1. **Insufficient Type Safety**
   - `ignore_missing_imports = true` bypasses type checking for external libraries
   - Missing generic type parameters (`Task`, `dict`, `list`, etc.)
   - Missing type annotations on functions/methods

2. **Potential Real Bugs**
   - Coroutines not executing due to missing `await` (20 cases)
   - Logically impossible comparisons (61 cases)
   - Potential runtime errors due to type mismatches (293 cases)

3. **Degraded Code Quality**
   - Unnecessary `# type: ignore` comments (300 cases)
   - Limited IDE auto-completion due to bypassed type checking
   - Unable to detect type errors early during refactoring

### Current Status Analysis

When MyPy strict mode is enabled, **4,547 total errors** are detected:

| Error Type | Count | Risk Level | Primary Cause |
|-----------|-------|-----------|---------------|
| no-untyped-def | 1,380 | Low | Missing type annotations |
| type-arg | 1,120 | Medium-Low | Missing generic type parameters |
| no-any-return | 469 | Medium-Low | Returning Any type |
| misc | 466 | Medium | Other type errors |
| unused-ignore | 300 | Low | Unnecessary comments |
| arg-type | 170 | High | Argument type mismatch |
| no-untyped-call | 149 | Medium | Untyped function calls |
| import-untyped | 133 | Medium-Low | Imports without type info |
| **High-risk errors** | **374** | **High** | **Potential runtime errors** |

**Test vs Production Ratio** (374 high-risk errors):
- Test code: 358 (96%)
- Production code: 16 (4%)

## Current Design

### MyPy Configuration (pyproject.toml)

```toml
[tool.mypy]
plugins = ["pydantic.mypy", "strawberry.ext.mypy_plugin"]
ignore_missing_imports = true
follow_untyped_imports = false
implicit_reexport = false
mypy_path = "stubs:src"
namespace_packages = true
explicit_package_bases = true
python_executable = "dist/export/python/virtualenvs/python-default/3.13.7/bin/python"
disable_error_code = ["typeddict-unknown-key"]
```

### Issues

1. **Relaxed Settings**
   - `ignore_missing_imports = true`: Ignores external library types
   - Some modules have error codes completely disabled

2. **Incomplete Type Coverage**
   - Incomplete stub files (trafaret, etc.)
   - Missing generic type parameters
   - Incomplete function signatures

## Proposed Design

### Phase 1: Enable Strict Mode (Immediate)

```toml
[tool.mypy]
plugins = ["pydantic.mypy", "strawberry.ext.mypy_plugin"]
strict = true  # Add this
mypy_path = "stubs:src"
namespace_packages = true
explicit_package_bases = true
python_executable = "dist/export/python/virtualenvs/python-default/3.13.7/bin/python"
disable_error_code = ["typeddict-unknown-key"]
```

Strict mode automatically enables:
- `warn_unused_configs = true`
- `disallow_any_generics = true`
- `disallow_untyped_defs = true`
- `warn_redundant_casts = true`
- `warn_unused_ignores = true`
- `no_implicit_reexport = true` (already set)
- And 11 total options

### Phase 2: Fix High-Risk Errors (Priority-Based)

Fix 374 total errors classified into 8 Priorities:

#### Priority 1: unused-coroutine (20 errors) 🔴 Critical

**Risk Level**: Functions not executing
**Difficulty**: Very Low
**Estimated Time**: 1-2 hours

```python
# Before
session.Manager.freeze()  # Coroutine not executed

# After
await session.Manager.freeze()
```

**Affected Files**: 5 (all test files)

---

#### Priority 2: comparison-overlap (61 errors) 🔴 High

**Risk Level**: Conditions always false
**Difficulty**: Low to Medium
**Estimated Time**: 3-4 hours

##### 2.1 test_docker.py Concentration (20 errors)
```python
# Before
result = ImageRef.from_image_str(...)
assert result.tag_set == ("3.6", {"ubuntu"})  # Type mismatch

# After
result: ImageRef = ImageRef.from_image_str(...)
assert result.tag_set == ("3.6-ubuntu", set())
```

##### 2.2 Path vs "-" Comparison (12 errors, includes production)
```python
# Before
if output == "-":  # Path vs str

# After
if str(output) == "-":
```

##### 2.3 Enum vs String (5 errors)
```python
# Before
if user_role == UserRole.ADMIN or user_role == "admin":

# After
if user_role == UserRole.ADMIN:
```

---

#### Priority 3: call-arg (33 errors) 🟠 High

**Risk Level**: Runtime TypeError
**Difficulty**: Low
**Estimated Time**: 2-3 hours

##### 3.1 LoggingConfig Required Arguments (26 errors)
```python
# Option 1: Fixture pattern
@pytest.fixture
def minimal_logging_config() -> LoggingConfig:
    return LoggingConfig(
        version=1,
        level=LogLevel.INFO,
        disable_existing_loggers=False,
        handlers={},
        loggers={},
    )

# Option 2: Type ignore (temporary)
logging_config = LoggingConfig()  # type: ignore[call-arg]
```

---

#### Priority 4: arg-type (170 errors) 🟠 Medium-High

**Risk Level**: Potential runtime TypeError
**Difficulty**: Low to Medium
**Estimated Time**: 4-5 hours

##### 4.1 test_argparse.py (18 errors)
```python
# Before
port_no(22)  # int → str

# After
port_no("22")
```

##### 4.2 Domain Type Conversions (10 errors)
```python
# Before
BaseActionResultMeta(
    action_id=None,  # UUID required
    status="pending",  # Enum required
)

# After
BaseActionResultMeta(
    action_id=uuid4(),
    status=OperationStatus.PENDING,
)
```

---

#### Priority 5: assignment (33 errors) 🟡 Medium

**Risk Level**: Wrong type assignment
**Difficulty**: Low
**Estimated Time**: 2 hours

```python
# Before
role_source: RoleSource = OperationType.CREATE  # Wrong enum

# After
role_source: RoleSource = RoleSource.USER_DEFINED
```

---

#### Priority 6: attr-defined (29 errors) 🟡 Medium

**Risk Level**: AttributeError
**Difficulty**: Medium
**Estimated Time**: 2-3 hours

```python
# Before
a = host_port_pair("host:123")
assert a.host == "host"  # tuple has no .host

# After - Option 1: Use indexing
assert a[0] == "host"

# After - Option 2: NamedTuple
class HostPort(NamedTuple):
    host: str
    port: int
```

---

#### Priority 7: union-attr (23 errors) 🟡 Medium-Low

**Risk Level**: AttributeError on some types
**Difficulty**: Medium
**Estimated Time**: 2-3 hours

```python
# Before
event: QueueSentinel | Event = await queue.get()
assert event.key == "wow"  # QueueSentinel has no key

# After
if isinstance(event, Event):
    assert event.key == "wow"
```

---

#### Priority 8: return-value (5 errors) 🟠 High (Production)

**Risk Level**: Production code type mismatch
**Difficulty**: High
**Estimated Time**: 2-3 hours

```python
# Before
def decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

# After
from typing import TypeVar, ParamSpec, Callable

P = ParamSpec('P')
R = TypeVar('R')

def decorator(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)
    return wrapper
```

### Phase 3: Fix Medium-Risk Errors (Gradual)

Fix remaining 4,173 errors, prioritizing by importance:

1. **type-arg** (1,120): Add generic type parameters
2. **no-any-return** (469): Remove Any returns
3. **no-untyped-call** (149): Improve stub files

### Phase 4: Low Priority (Long-term)

1. **unused-ignore** (300): Remove unnecessary comments
2. **redundant-cast** (72): Remove unnecessary casts
3. **no-untyped-def** (1,380): Add type annotations

## Migration / Compatibility

### Backward Compatibility

✅ **No Behavioral Changes**
- Only type checking strengthened, runtime behavior identical
- Existing tests guaranteed to pass

✅ **Gradual Migration**
- Each phase can be fixed independently
- Rollback strategy prepared

### Breaking Changes

❌ **None**
- Type checking enforcement only affects development
- Deployed code behavior unchanged

### Migration Steps

1. **Immediate**: Enable MyPy strict mode (Phase 1)
2. **Within 1 week**: Fix 374 high-risk errors (Phase 2)
3. **Within 1 month**: Fix medium-risk errors (Phase 3)
4. **Within 3 months**: Fix low-priority errors (Phase 4)

## Implementation Plan

### Phase 1: Configuration Change (Day 1)

**Tasks**:
- Add `strict = true` to `pyproject.toml`
- Generate full error report
- Finalize error classification and priorities

**Verification**:
```bash
pants check :: > mypy_strict_report.txt
```

---

### Phase 2: Fix High-Risk Errors (Days 2-5)

#### 2.1 Quick Fixes (Day 2, 4 hours)

**Target**: 42 errors
1. Priority 1: unused-coroutine (20)
2. Priority 2.2: Path vs "-" (12)
3. Priority 2.3: Enum vs string (5)
4. Priority 3.2: AccessKey arguments (5)

**Verification**:
```bash
pants check tests/unit/client::
pants check src/ai/backend/cli::
```

**Commit**: `fix(mypy): Resolve critical errors (unused-coroutine, comparison-overlap)`

---

#### 2.2 Concentrated Fixes (Day 3, 6 hours)

**Target**: 62 errors
1. Priority 2.1: test_docker.py (20)
2. Priority 3.1: LoggingConfig (26)
3. Priority 4.1: test_argparse.py (18)

**Verification**:
```bash
pants check tests/unit/common/test_docker.py
pants check tests/unit::/conftest.py
```

**Commit**: `fix(mypy): Resolve test infrastructure errors`

---

#### 2.3 Type Cleanup (Day 4, 5 hours)

**Target**: 32 errors
1. Priority 4.2: Domain types (10)
2. Priority 5.1: Enum assignment (6)
3. Priority 6.2: Tuple attributes (6)
4. Priority 7.1: QueueSentinel (12)

**Verification**:
```bash
pants check tests/unit/manager/actions::
pants check tests/unit/common/test_etcd.py
```

**Commit**: `fix(mypy): Resolve type conversion and union errors`

---

#### 2.4 Production + Remaining (Day 5, 7 hours)

**Target**: 238 errors
1. Priority 8: return-value production (5) ⚠️ Review required
2. Priority 2.4: Other comparisons (24)
3. Remaining scattered errors

**Verification**:
```bash
pants check src/ai/backend/agent/agent.py
pants check src/ai/backend/manager/api::
pants test --changed-since=HEAD~1  # Behavioral verification required
```

**Commit**: `fix(mypy): Resolve production code type errors`

---

### Phase 3: Medium-Risk Errors (1-2 weeks)

**Approach**: Weekly focus on specific error types

**Week 1**: type-arg errors
- Add generic type parameters
- Goal: 1,120 → 500

**Week 2**: no-any-return, no-untyped-call
- Remove Any types
- Improve stub files
- Goal: 618 → 300

---

### Phase 4: Low Priority (1-2 months)

**Approach**: Gradual improvement alongside refactoring

- New code must comply with strict mode
- Existing code improved when modified
- Goal: Gradual reduction

## Open Questions

### Q1: LoggingConfig Default Value Handling

**Question**: Why call-arg error when LoggingConfig already has Field(default=...)?

**Answer Candidates**:
- Need to verify Pydantic v2 strict mode behavior
- MyPy plugin may not recognize defaults

**Decision**: Determine after examining actual error in Phase 2.2

---

### Q2: Stub File Improvement Scope

**Question**: How much should we improve stubs for external libraries like trafaret?

**Answer Candidates**:
- Option 1: Minimal fixes (only currently used APIs)
- Option 2: Complete implementation (all APIs)
- Option 3: Contribute to external projects (typeshed)

**Decision**: Determine after assessing actual needs in Phase 3

---

### Q3: Production Decorator Modification Approach

**Question**: How to fix return-value errors in production decorators?

**Answer Candidates**:
- Option 1: Use ParamSpec (type-safe, complex)
- Option 2: Type ignore (simple, less type safety)
- Option 3: Redesign decorators (complete but time-consuming)

**Decision**: Judge case-by-case in Phase 2.4

## Success Criteria

### Quantitative Goals

**After Phase 2** (High-risk errors):
- [ ] unused-coroutine: 0
- [ ] comparison-overlap: 0
- [ ] call-arg: 0
- [ ] arg-type: < 10
- [ ] assignment: 0
- [ ] attr-defined: < 5
- [ ] union-attr: < 5
- [ ] return-value: 0
- [ ] All existing tests pass

**After Phase 3** (Medium-risk errors):
- [ ] type-arg: < 500 (currently 1,120)
- [ ] no-any-return: < 200 (currently 469)
- [ ] no-untyped-call: < 50 (currently 149)

**After Phase 4** (Long-term goals):
- [ ] Total errors: < 1,000 (currently 4,547)
- [ ] Maintain 0 type errors in new code

### Qualitative Goals

- [ ] Confirm improved IDE type auto-completion
- [ ] Document cases of early type error detection during refactoring
- [ ] Developer feedback: > 50% agree type checking is helpful

## References

### Related BEPs

- N/A (First type checking enhancement BEP)

### External Resources

- [MyPy Strict Mode Documentation](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict)
- [PEP 612 - Parameter Specification Variables](https://peps.python.org/pep-0612/)
- [Gradual Typing Best Practices](https://mypy.readthedocs.io/en/stable/existing_code.html)

### Internal Documents

- Error analysis results: `mypy_strict_check_all.txt`
- Error priorities: `mypy_strict_priority.md`
- Implementation plan: `/Users/hyeokjin/.claude/plans/flickering-spinning-balloon.md`

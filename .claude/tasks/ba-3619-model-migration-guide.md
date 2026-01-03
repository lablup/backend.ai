# BA-3619: Model Migration Guide

## Goal
Migrate `models/{name}.py` → `models/{name}/row.py` with proper exports.

## Migration Steps (Per File)

### Step 1: Create Directory & Move File
```bash
mkdir -p src/ai/backend/manager/models/{name}
mv src/ai/backend/manager/models/{name}.py src/ai/backend/manager/models/{name}/row.py
```

### Step 2: Fix Relative Imports in row.py

| Before (in models/) | After (in models/{name}/) | Notes |
|---------------------|---------------------------|-------|
| `from .base import` | `from ..base import` | models 내부 모듈 |
| `from .rbac import` | `from ..rbac import` | models 내부 모듈 |
| `from .user import` | `from ..user import` | 다른 Row 모듈 |
| `from ..defs import` | `from ...defs import` | manager 레벨 |
| `from ai.backend.` | 그대로 유지 | 절대 경로 |

**규칙**: 상대 import에서 `.`을 `..`로, `..`를 `...`로 변경

### Step 3: Remove Self-References
순환 import 방지용 코드 제거:
```python
# Before (제거 대상)
async def some_method(self):
    from .domain import DomainRow  # 같은 파일에 정의됨
    ...

# After
async def some_method(self):
    # DomainRow는 이미 같은 파일에 있음
    ...
```

### Step 4: Create __init__.py
```python
from .row import (
    # 모든 public 심볼 나열
    SomeRow,
    some_function,
    SOME_CONSTANT,
)

__all__ = (
    "SomeRow",
    "some_function",
    "SOME_CONSTANT",
)
```

**Export 대상 찾기:**
1. 원본 파일의 `__all__` 확인
2. `pants check` 실행하여 누락된 export 확인
3. 외부에서 사용하는 모든 심볼 추가

### Step 5: Verify
```bash
pants --no-colors --no-dynamic-ui check src/ai/backend/manager/models/{name}/row.py
./py -m alembic heads
```

## Files to Migrate (33 remaining)

### Priority 1: Core Models (의존성 많음)
- [ ] user
- [ ] group
- [ ] keypair
- [ ] session
- [ ] kernel
- [ ] agent
- [ ] image

### Priority 2: Resource/Policy Models
- [ ] scaling_group
- [ ] resource_policy
- [ ] resource_preset
- [ ] vfolder

### Priority 3: Feature Models
- [ ] endpoint
- [ ] routing
- [ ] container_registry
- [ ] notification
- [ ] artifact
- [ ] artifact_revision
- [ ] artifact_registries

### Priority 4: Supporting Models
- [ ] app_config
- [ ] audit_log
- [ ] event_log
- [ ] network
- [ ] deployment_policy
- [ ] deployment_revision
- [ ] deployment_auto_scaling_policy
- [ ] scheduling_history
- [ ] storage_namespace
- [ ] object_storage
- [ ] vfs_storage
- [ ] huggingface_registry
- [ ] reservoir_registry
- [ ] association_artifacts_storages
- [ ] association_container_registries_groups

## Common Issues

### Issue 1: Missing Export
```
error: Module "ai.backend.manager.models.{name}" has no attribute "SomeClass"
```
**Solution**: `__init__.py`에 해당 심볼 추가

### Issue 2: Circular Import
```
ImportError: cannot import name 'X' from partially initialized module
```
**Solution**: TYPE_CHECKING 블록 사용 또는 lazy import

### Issue 3: Import Sorting
```
I001 [*] Import block is un-sorted or un-formatted
```
**Solution**: `pants fix` 실행

## Commit Pattern
```
refactor(BA-3619): Migrate {name} model to subpackage structure

- Move models/{name}.py to models/{name}/row.py
- Create models/{name}/__init__.py with exports
- Adjust relative imports for new directory depth

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Notes
- Legacy Table 파일 (error_logs, session_template)은 나중에 처리
- gql_models, rbac, rbac_models는 이동 대상 아님
- 한 파일씩 커밋하여 문제 발생 시 롤백 용이하게

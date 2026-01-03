# BA-3613: Migrate Repository Tests to Selective Table Loading

## Migration Pattern

### 1. db_with_cleanup fixture 생성/대체
- `database_engine` → `database_connection`
- `with_tables(db, [Row들...])` 적용
- **Row 순서**: FK 제약조건에 따라 부모 → 자식 순

```python
from ai.backend.testutils.db import with_tables

@pytest.fixture
async def db_with_cleanup(database_connection):
    async with with_tables(database_connection, [
        # FK dependency order: 부모 → 자식
        ParentRow,
        ChildRow,
    ]):
        yield database_connection
```

### 2. 정리 로직 제거
- 기존 `sa.delete()` 문 제거
- `with_tables`의 TRUNCATE CASCADE가 자동 처리

### 3. _create_xxx → fixture 기반 표현 (해당 시)
- 헬퍼 메서드 대신 의미있는 fixture 이름으로 테스트 상황 명확화

### 4. 기술적 주의사항
`commit()` 후 `to_dataclass()` 호출 시 refresh 필요:
```python
await session.commit()
await session.refresh(row)  # MissingGreenlet 에러 방지
return row.to_dataclass()
```

---

## Progress

### Completed (Phase 1 - 10 files)
- [x] auth/test_auth_repository.py
- [x] domain/test_domain.py
- [x] domain/test_admin_repository.py
- [x] group/test_admin_repository.py
- [x] notification/test_notification_repository.py
- [x] notification/test_notification_options.py
- [x] container_registry/test_container_registry_repository.py
- [x] deployment/test_deployment_repository.py
- [x] keypair_resource_policy/test_keypair_resource_policy.py
- [x] user/test_user_repository.py

### Remaining (27 files)

#### Very Large (800+ lines) - 3 files
- [ ] scheduling_history/test_scheduling_history_repository.py (1146)
- [ ] resource_preset/test_check_presets.py (1009)
- [ ] scheduler/test_termination.py (754)

#### Large (500-800 lines) - 6 files
- [ ] base/test_purger.py (748)
- [ ] schedule/test_termination.py (667)
- [ ] artifact_revision/test_artifact_revision_repository.py (650)
- [ ] scaling_group/test_scaling_group_repository.py (556)
- [ ] model_serving/test_search_auto_scaling_rule_validated.py (516)
- [ ] base/test_updater.py (509)

#### Medium (200-500 lines) - 15 files
- [ ] agent/test_sync_installed_images.py (483)
- [ ] artifact/test_artifact_repository.py (483)
- [ ] artifact_registry/test_artifact_registry_repository.py (468)
- [ ] schedule/test_schedule_repository.py (413)
- [ ] base/test_pagination_integration.py (411)
- [ ] app_config/test_app_config.py (398)
- [ ] reservoir_registry/test_reservoir_registry_repository.py (395)
- [ ] huggingface_registry/test_huggingface_registry_repository.py (387)
- [ ] schedule/test_fetch_pending_sessions.py (347)
- [ ] object_storage/test_object_storage_repository.py (339)
- [ ] base/test_querier.py (329)
- [ ] storage_namespace/test_storage_namespace_repository.py (321)
- [ ] vfs_storage/test_vfs_storage_repository.py (311)
- [ ] resource_preset/test_resource_preset_cache_invalidation.py (310)
- [ ] vfolder/test_vfolder_repository.py (272)
- [ ] user_resource_policy/test_user_resource_policy_repository.py (264)

#### Small (under 200 lines) - 3 files
- [ ] agent/test_repository.py (139)
- [ ] base/test_upserter.py (130)
- [ ] base/test_creator.py (117)

---

## Notes
- All paths relative to `tests/unit/manager/repositories/`
- `database_connection` fixture defined in `tests/unit/manager/repositories/conftest.py`
- `with_tables` from `src/ai/backend/testutils/db.py`

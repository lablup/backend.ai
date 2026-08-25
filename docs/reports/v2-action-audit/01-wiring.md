# 1. 코드 상 wiring 조사

배선 카탈로그와 코드를 대조한 정적 조사. 서버를 띄우지 않고 읽기만으로 답할 수 있는 것까지가
범위다. 요청이 실제로 어떻게 처리되는지는 2부(실 동작 테스트), 검사되는 권한이 옳은지는
3부(권한 검사 로직 확인)에서 다룬다. 세 조사의 관계와 진행 상태는 [README](./README.md)에 있다.

| | |
|---|---|
| Jira | BA-7486 |
| 기준 커밋 | `b2b200c0da` |
| 방법 | `ai.backend.manager` 전 모듈을 import해 v2 베이스 9개의 `__subclasses__()`를 훑고, `load_wiring_catalog()`와 대조 |
| 살아 있는 목록 | `backend.ai mgr ops list` |

## 총계

| 항목 | 수 |
|---|---:|
| 정의된 구상 v2 액션 클래스 | 652 |
| 카탈로그 행 (`mgr ops list`) | 652 |
| 배선된 고유 액션 클래스 | 651 |
| 이 문서의 행 수 | 653 |
| — 실패 | 66 |
| — 성공 | 587 |
| 발견이 하나 이상 달린 고유 액션 | 65 |

정의된 652 = 배선된 651 + 정의만 되고 배선되지 않은 1. 카탈로그 652행 = 고유 클래스 651 +
두 번 배선된 `lookup_bulk_kernel_owner`.

## 실패 분류

| 판정 | 분류 | 뜻 | 세부 케이스 | 건수 | 분류 합 |
|---|---|---|---|---:|---:|
| `W` | 죽은 배선 | 배선은 있으나 실행에 도달하지 않는다 | 정의됐지만 배선 안 됨 | 1 | **28** |
| | | | 배선됐지만 호출 안 됨 | 12 | |
| | | | 프로세서 우회 | 3 | |
| | | | 도달 불가 owner lookup | 12 | |
| `O` | operation 오선언 | 선언된 operation이 실제 동작과 달라 RBAC가 다른 권한을 검사한다 | field row 쓰기 | 4 | **21** |
| | | | soft delete 역전이 | 1 | |
| | | | upsert | 8 | |
| | | | v1/v2 불일치 | 8 | |
| `R` | 기록 결함 | 카탈로그나 감사 기록이 실제와 어긋난다 | 카탈로그 기록 결함 | 4 | **19** |
| | | | entity type 불일치 | 6 | |
| | | | action_name 자동 변환 | 9 | |
| `G` | 게이트 근거 미흡 | 게이트를 정당화하는 근거가 조건부다 | 게이트 근거 미흡 | 1 | **1** |
| | | | **합계** | **69** | **69** |

행 기준으로는 `W` 28행, `O` 21행, `R` 19행, `G` 1행이다.
한 행이 두 판정을 함께 다는 경우가 있어 발견 건수의 합이 실패 행 수보다 크다 —
`upsert_artifacts`, `associate_with_storage`, `disassociate_with_storage` 세 건이 그렇다.

## concern별 행 수

| concern | 실패 | 성공 | 합계 |
|---|---:|---:|---:|
| [app_config](#app-config) | 0 | 21 | 21 |
| [artifact_registry](#artifact-registry) | 13 | 59 | 72 |
| [container_registry](#container-registry) | 6 | 33 | 39 |
| [deployment](#deployment) | 8 | 77 | 85 |
| [label](#label) | 1 | 4 | 5 |
| [metric](#metric) | 0 | 14 | 14 |
| [notification_center](#notification-center) | 0 | 13 | 13 |
| [organization](#organization) | 6 | 93 | 99 |
| [rbac](#rbac) | 2 | 17 | 19 |
| [resource_group](#resource-group) | 9 | 68 | 77 |
| [resource_policy](#resource-policy) | 0 | 20 | 20 |
| [session](#session) | 4 | 59 | 63 |
| [system](#system) | 0 | 45 | 45 |
| [vfolder](#vfolder) | 8 | 60 | 68 |
| [visibility](#visibility) | 9 | 4 | 13 |
| **합계** | **66** | **587** | **653** |

컬럼은 `backend.ai mgr ops list`의 것에서 각 섹션 제목이 대신하는 `concern`을 뺀 나머지에
`판정`과 `사유`를 더한 구성이다. 사유는 `세부 케이스 — 내용` 꼴로 적는다.

## app_config

21행 — 실패 0, 성공 21.

### app_config — 실패 (0행)

없음.

### app_config — 성공 (21행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `app_config` | — | `search` | `anonymous_search_app_configs` | `scope` | `anonymous` | `custom` | `성공` | anonymous 게이트 — `anonymous_scope`가 쓰기를 거부(group.py:296) |
| `app_config` | — | `search` | `search_app_configs` | `scope` | `permission` | `custom` | `성공` | — |
| `app_config_allow_list` | — | `search` | `admin_search_app_config_allow_lists` | `global` | `permission` | `generic` | `성공` | — |
| `app_config_allow_list` | — | `get` | `bulk_get_app_config_allow_lists` | `bulk` | `permission` | `generic` | `성공` | — |
| `app_config_allow_list` | — | `create` | `create_app_config_allow_list` | `global` | `permission` | `generic` | `성공` | — |
| `app_config_allow_list` | — | `get` | `get_app_config_allow_list` | `single_entity` | `permission` | `generic` | `성공` | — |
| `app_config_allow_list` | — | `purge` | `purge_app_config_allow_list` | `single_entity` | `permission` | `generic` | `성공` | — |
| `app_config_allow_list` | — | `update` | `update_app_config_allow_list` | `single_entity` | `permission` | `generic` | `성공` | — |
| `app_config_definition` | — | `get` | `bulk_get_app_config_definitions` | `bulk` | `permission` | `generic` | `성공` | — |
| `app_config_definition` | — | `create` | `create_app_config_definition` | `global` | `permission` | `generic` | `성공` | — |
| `app_config_definition` | — | `get` | `get_app_config_definition` | `single_entity` | `permission` | `generic` | `성공` | — |
| `app_config_definition` | — | `search` | `global_search_app_config_definitions` | `global` | `permission` | `generic` | `성공` | — |
| `app_config_definition` | — | `purge` | `purge_app_config_definition` | `single_entity` | `permission` | `generic` | `성공` | — |
| `app_config_fragment` | — | `search` | `admin_search_app_config_fragments` | `global` | `permission` | `generic` | `성공` | — |
| `app_config_fragment` | — | `get` | `bulk_get_app_config_fragments` | `bulk` | `permission` | `generic` | `성공` | — |
| `app_config_fragment` | — | `purge` | `bulk_purge_app_config_fragments` | `bulk` | `permission` | `generic` | `성공` | — |
| `app_config_fragment` | — | `upsert` | `bulk_upsert_app_config_fragments` | `scope` | `permission` | `generic` | `성공` | UPSERT 선언 — 검사가 CREATE\|UPDATE |
| `app_config_fragment` | — | `get` | `get_app_config_fragment` | `single_entity` | `permission` | `generic` | `성공` | — |
| `app_config_fragment` | — | `upsert` | `global_bulk_upsert_app_config_fragments` | `global` | `permission` | `generic` | `성공` | UPSERT 선언 — 검사가 CREATE\|UPDATE |
| `app_config_fragment` | — | `purge` | `purge_app_config_fragment` | `single_entity` | `permission` | `generic` | `성공` | — |
| `app_config_fragment` | — | `search` | `search_app_config_fragments` | `scope` | `permission` | `generic` | `성공` | — |

## artifact_registry

72행 — 실패 13, 성공 59.

### artifact_registry — 실패 (13행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| — | — | `create` | `import_artifact_batch` | — | — | — | `W` | **정의됐지만 배선 안 됨** — import하는 모듈이 없다. `delegate_import_revision_batch`로 대체된 잔재. 가드 테스트는 자기 import closure만 훑어 수집하지 못한다(test_registry_catalog.py:208) |
| `artifact` | — | `create` | `delegate_import_artifact_revision_batch` | `global` | `permission` | `custom` | `R` | **entity type 불일치** — 카탈로그 `artifact` / 감사 `global`(base.py:21) |
| `artifact` | — | `search` | `get_artifact_revisions` | `single_entity` | `permission` | `custom` | `W` | **배선됐지만 호출 안 됨** — 호출자 없음 |
| `artifact` | — | `lookup` | `lookup_bulk_artifact_revision_owner` | `lookup` | `permission` | `generic` | `W` | **도달 불가 owner lookup** — `field_group()`이 등록하지만 이 도메인은 bulk field 연산을 배선하지 않는다 |
| `artifact` | — | `update` | `restore_artifacts` | `global` | `permission` | `custom` | `O` | **soft delete 역전이** — UPDATE 선언(restore_multi.py:21). 실제로는 DELETED→ALIVE 역전이(db_source.py:283)이므로 RESTORE여야 한다 |
| `artifact` | — | `search` | `search_artifact_revisions` | `global` | `permission` | `custom` | `R` | **entity type 불일치** — 카탈로그 `artifact` / 감사 `global`. base.py:21이 GLOBAL_ENTITY_TYPE 선언, 형제 `ArtifactAction`은 ARTIFACT_ENTITY_TYPE |
| `artifact` | — | `update` | `upsert_artifacts` | `global` | `permission` | `custom` | `W` `O` | **프로세서 우회** — 서비스가 프로세서 대신 자기 메서드를 직접 호출(artifact/service.py:334,651). 게이트·모니터·감사 기록이 건너뛰어진다 <br> **upsert** — UPDATE만 선언 → 검사가 CREATE\|UPDATE가 되지 않는다(upsert_multi.py:21) |
| `artifact` | `artifact_revision` | `create` | `associate_with_storage` | `single_entity` | `permission` | `custom` | `W` `O` | **프로세서 우회** — 서비스가 직접 호출(revision/service.py:586). 게이트·모니터·감사 기록이 건너뛰어진다 <br> **field row 쓰기** — CREATE 선언 → 소유 artifact에 CREATE 요구(associate_with_storage.py:26) |
| `artifact` | `artifact_revision` | `delete` | `cleanup_artifact_revision` | `single_entity` | `permission` | `custom` | `O` | **field row 쓰기** — DELETE 선언 → 소유 artifact에 SOFT_DELETE 요구(cleanup.py:21) |
| `artifact` | `artifact_revision` | `delete` | `disassociate_with_storage` | `single_entity` | `permission` | `custom` | `W` `O` | **프로세서 우회** — 서비스가 직접 호출(revision/service.py:676). 게이트·모니터·감사 기록이 건너뛰어진다 <br> **field row 쓰기** — DELETE 선언 → 소유 artifact에 SOFT_DELETE 요구(disassociate_with_storage.py:24) |
| `artifact` | `artifact_revision` | `create` | `import_artifact_revision` | `single_entity` | `permission` | `custom` | `O` | **field row 쓰기** — CREATE 선언 → 소유 artifact에 CREATE 요구. UPDATE여야 한다(import_revision.py:26) |
| `artifact_registry` | — | `search` | `list_hugging_face_registry` | `global` | `permission` | `custom` | `W` | **배선됐지만 호출 안 됨** — 호출자 없음 |
| `artifact_registry` | — | `search` | `list_reservoir_registries` | `global` | `permission` | `custom` | `W` | **배선됐지만 호출 안 됨** — 호출자 없음 |

### artifact_registry — 성공 (59행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `artifact` | — | `create` | `delegate_scan_artifacts` | `global` | `permission` | `custom` | `성공` | — |
| `artifact` | — | `delete` | `delete_artifacts` | `global` | `permission` | `custom` | `성공` | — |
| `artifact` | — | `get` | `get_artifact` | `single_entity` | `permission` | `custom` | `성공` | — |
| `artifact` | — | `lookup` | `lookup_artifact_revision_owner` | `lookup` | `permission` | `generic` | `성공` | — |
| `artifact` | — | `get` | `retrieve_model` | `global` | `permission` | `custom` | `성공` | — |
| `artifact` | — | `get` | `retrieve_models` | `global` | `permission` | `custom` | `성공` | — |
| `artifact` | — | `create` | `scan_artifacts` | `global` | `permission` | `custom` | `성공` | — |
| `artifact` | — | `search` | `search_artifacts` | `global` | `permission` | `custom` | `성공` | — |
| `artifact` | — | `search` | `search_artifacts_with_revisions` | `global` | `permission` | `custom` | `성공` | — |
| `artifact` | — | `update` | `update_artifact` | `single_entity` | `permission` | `custom` | `성공` | — |
| `artifact` | `artifact_revision` | `update` | `approve_artifact_revision` | `single_entity` | `permission` | `custom` | `성공` | field row 쓰기를 UPDATE로 선언 |
| `artifact` | `artifact_revision` | `update` | `cancel_import` | `single_entity` | `permission` | `custom` | `성공` | field row 쓰기를 UPDATE로 선언 |
| `artifact` | `artifact_revision` | `get` | `get_artifact_revision` | `single_entity` | `permission` | `generic` | `성공` | — |
| `artifact` | `artifact_revision` | `get` | `get_artifact_revision_readme` | `single_entity` | `permission` | `custom` | `성공` | — |
| `artifact` | `artifact_revision` | `get` | `get_artifact_revision_verification_result` | `single_entity` | `permission` | `custom` | `성공` | — |
| `artifact` | `artifact_revision` | `get` | `get_download_presigned_url` | `single_entity` | `permission` | `custom` | `성공` | — |
| `artifact` | `artifact_revision` | `get` | `get_download_progress` | `single_entity` | `permission` | `custom` | `성공` | — |
| `artifact` | `artifact_revision` | `update` | `get_upload_presigned_url` | `single_entity` | `permission` | `custom` | `성공` | field row 쓰기를 UPDATE로 선언 — 이름은 get이지만 쓰기 |
| `artifact` | `artifact_revision` | `update` | `reject_artifact_revision` | `single_entity` | `permission` | `custom` | `성공` | field row 쓰기를 UPDATE로 선언 |
| `artifact_registry` | — | `create` | `create_hugging_face_registry` | `global` | `permission` | `custom` | `성공` | — |
| `artifact_registry` | — | `create` | `create_reservoir_registry` | `global` | `permission` | `custom` | `성공` | — |
| `artifact_registry` | — | `delete` | `delete_hugging_face_registry` | `single_entity` | `permission` | `custom` | `성공` | — |
| `artifact_registry` | — | `delete` | `delete_reservoir_registry` | `single_entity` | `permission` | `custom` | `성공` | — |
| `artifact_registry` | — | `get` | `get_artifact_registry_meta` | `single_entity` | `permission` | `custom` | `성공` | — |
| `artifact_registry` | — | `get` | `get_artifact_registry_metas` | `global` | `permission` | `custom` | `성공` | — |
| `artifact_registry` | — | `get` | `get_hugging_face_registries` | `global` | `permission` | `custom` | `성공` | — |
| `artifact_registry` | — | `get` | `get_hugging_face_registry` | `single_entity` | `permission` | `custom` | `성공` | — |
| `artifact_registry` | — | `get` | `get_reservoir_registries` | `global` | `permission` | `custom` | `성공` | — |
| `artifact_registry` | — | `get` | `get_reservoir_registry` | `single_entity` | `permission` | `custom` | `성공` | — |
| `artifact_registry` | — | `lookup` | `lookup_artifact_registry` | `lookup` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `artifact_registry` | — | `search` | `search_artifact_registries` | `global` | `permission` | `custom` | `성공` | — |
| `artifact_registry` | — | `search` | `search_hugging_face_registries` | `global` | `permission` | `custom` | `성공` | — |
| `artifact_registry` | — | `search` | `search_reservoir_registries` | `global` | `permission` | `custom` | `성공` | — |
| `artifact_registry` | — | `update` | `update_hugging_face_registry` | `single_entity` | `permission` | `custom` | `성공` | — |
| `artifact_registry` | — | `update` | `update_reservoir_registry` | `single_entity` | `permission` | `custom` | `성공` | — |
| `object_storage` | — | `get` | `bulk_get_object_storages` | `bulk` | `permission` | `generic` | `성공` | — |
| `object_storage` | — | `create` | `create_object_storage` | `global` | `permission` | `generic` | `성공` | — |
| `object_storage` | — | `get` | `get_object_storage` | `single_entity` | `permission` | `generic` | `성공` | — |
| `object_storage` | — | `search` | `list_object_storages` | `global` | `permission` | `generic` | `성공` | — |
| `object_storage` | — | `purge` | `purge_object_storage` | `single_entity` | `permission` | `generic` | `성공` | — |
| `object_storage` | — | `search` | `search_object_storages` | `global` | `permission` | `generic` | `성공` | — |
| `object_storage` | — | `update` | `update_object_storage` | `single_entity` | `permission` | `generic` | `성공` | — |
| `storage_namespace` | — | `get` | `bulk_get_storage_namespaces` | `bulk` | `permission` | `generic` | `성공` | — |
| `storage_namespace` | — | `lookup` | `lookup_storage_namespace` | `lookup` | `permission` | `generic` | `성공` | — |
| `storage_namespace` | — | `create` | `register_storage_namespace` | `global` | `permission` | `generic` | `성공` | — |
| `storage_namespace` | — | `search` | `search_storage_namespaces` | `global` | `permission` | `generic` | `성공` | — |
| `storage_namespace` | — | `search` | `search_storage_namespaces_of_storage` | `global` | `permission` | `generic` | `성공` | — |
| `storage_namespace` | — | `purge` | `unregister_storage_namespace` | `single_entity` | `permission` | `generic` | `성공` | — |
| `vfs_storage` | — | `create` | `create_vfs_storage` | `global` | `permission` | `generic` | `성공` | — |
| `vfs_storage` | — | `get` | `get_vfs_quota_scope` | `global` | `permission` | `custom` | `성공` | — |
| `vfs_storage` | — | `get` | `get_vfs_storage` | `single_entity` | `permission` | `generic` | `성공` | — |
| `vfs_storage` | — | `search` | `list_vfs_storages` | `global` | `permission` | `generic` | `성공` | — |
| `vfs_storage` | — | `lookup` | `lookup_vfs_storage` | `lookup` | `permission` | `generic` | `성공` | — |
| `vfs_storage` | — | `purge` | `purge_vfs_storage` | `single_entity` | `permission` | `generic` | `성공` | — |
| `vfs_storage` | — | `search` | `search_vfs_quota_scopes` | `global` | `permission` | `custom` | `성공` | — |
| `vfs_storage` | — | `search` | `search_vfs_storages` | `global` | `permission` | `generic` | `성공` | — |
| `vfs_storage` | — | `update` | `set_vfs_quota_scope` | `global` | `permission` | `custom` | `성공` | — |
| `vfs_storage` | — | `delete` | `unset_vfs_quota_scope` | `global` | `permission` | `custom` | `성공` | — |
| `vfs_storage` | — | `update` | `update_vfs_storage` | `single_entity` | `permission` | `generic` | `성공` | — |

## container_registry

39행 — 실패 6, 성공 33.

### container_registry — 실패 (6행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `container_registry` | — | `update` | `handle_harbor_webhook` | `global` | `anonymous` | `custom` | `G` | **게이트 근거 미흡** — 시크릿 비교가 조건부. `extra["webhook_auth_header"]`가 없으면 검사가 없다(service.py:213) |
| `image` | — | `delete` | `clear_image_custom_resource_limit_by_id` | `global` | `permission` | `custom` | `W` | **배선됐지만 호출 안 됨** — 호출자 없음 |
| `image` | — | `create` | `preload_image` | `global` | `permission` | `custom` | `W` | **배선됐지만 호출 안 됨** — 호출자 없음. GraphQL 뮤테이션은 "Not implemented."만 반환(gql_legacy/image.py:943,964) |
| `image` | — | `purge` | `purge_images` | `global` | `permission` | `custom` | `W` | **배선됐지만 호출 안 됨** — 호출자 없음. bgtask는 단수 `purge_image`를 쓴다 |
| `image` | — | `update` | `set_image_resource_limit_by_id` | `global` | `permission` | `custom` | `W` | **배선됐지만 호출 안 됨** — 호출자 없음 |
| `image` | — | `delete` | `unload_image` | `global` | `permission` | `custom` | `W` | **배선됐지만 호출 안 됨** — 호출자 없음. GraphQL 뮤테이션은 "Not implemented."만 반환(gql_legacy/image.py:943,964) |

### container_registry — 성공 (33행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `container_registry` | — | `delete` | `clear_images` | `global` | `permission` | `custom` | `성공` | — |
| `container_registry` | — | `create` | `create_container_registry` | `global` | `permission` | `custom` | `성공` | — |
| `container_registry` | — | `create` | `create_registry_quota` | `global` | `permission` | `custom` | `성공` | — |
| `container_registry` | — | `delete` | `delete_container_registry` | `global` | `permission` | `custom` | `성공` | — |
| `container_registry` | — | `delete` | `delete_registry_quota` | `global` | `permission` | `custom` | `성공` | — |
| `container_registry` | — | `get` | `get_container_registries` | `global` | `permission` | `custom` | `성공` | — |
| `container_registry` | — | `get` | `load_all_container_registries` | `global` | `permission` | `custom` | `성공` | — |
| `container_registry` | — | `get` | `load_container_registries` | `global` | `permission` | `custom` | `성공` | — |
| `container_registry` | — | `get` | `read_registry_quota` | `global` | `permission` | `custom` | `성공` | — |
| `container_registry` | — | `update` | `rescan_images` | `global` | `permission` | `custom` | `성공` | — |
| `container_registry` | — | `search` | `search_container_registries` | `global` | `permission` | `custom` | `성공` | — |
| `container_registry` | — | `update` | `update_container_registry` | `global` | `permission` | `custom` | `성공` | — |
| `container_registry` | — | `update` | `update_registry_quota` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `create` | `alias_image` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `create` | `alias_image_by_id` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `delete` | `clear_image_custom_resource_limit` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `delete` | `dealias_image` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `delete` | `forget_image` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `delete` | `forget_image_by_id` | `single_entity` | `permission` | `custom` | `성공` | — |
| `image` | — | `search` | `get_all_images` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `search` | `get_image_by_id` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `search` | `get_image_by_identifier` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `get` | `get_image_installed_agents` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `search` | `get_images_by_canonicals` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `purge` | `purge_image` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `purge` | `purge_image_by_id` | `single_entity` | `permission` | `custom` | `성공` | — |
| `image` | — | `restore` | `restore_image_by_id` | `single_entity` | `permission` | `custom` | `성공` | soft delete 역전이를 RESTORE로 선언 |
| `image` | — | `create` | `scan_image` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `search` | `search_aliases` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `search` | `search_images` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `delete` | `untag_image_from_registry` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `update` | `update_image` | `global` | `permission` | `custom` | `성공` | — |
| `image` | — | `update` | `update_image_by_id` | `global` | `permission` | `custom` | `성공` | — |

## deployment

85행 — 실패 8, 성공 77.

### deployment — 실패 (8행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `deployment` | — | `delete` | `delete_model_service` | `single_entity` | `permission` | `custom` | `W` | **배선됐지만 호출 안 됨** — 호출자 없음 |
| `deployment` | — | `search` | `global_search_replica_group_history` | `global` | `permission` | `custom` | `R` | **entity type 불일치** — 카탈로그 `deployment` / 감사 `global` |
| `deployment` | — | `search` | `search_deployments_in_project` | `scope` | `permission` | `custom` | `W` | **배선됐지만 호출 안 됨** — 호출자 없음 |
| `deployment` | — | `update` | `upsert_deployment_policy` | `single_entity` | `permission` | `custom` | `O` | **upsert** — UPDATE만 선언(upsert_deployment_policy.py:28). docstring은 ON CONFLICT라고 적는다 |
| `deployment_preset` | — | `lookup` | `lookup_bulk_preset_resource_slot_owner` | `lookup` | `permission` | `generic` | `W` | **도달 불가 owner lookup** — `field_group()`이 등록하지만 이 도메인은 bulk field 연산을 배선하지 않는다 |
| `deployment_preset` | — | `lookup` | `lookup_preset_resource_slot_owner` | `lookup` | `permission` | `generic` | `W` | **도달 불가 owner lookup** — `field_group()`이 등록하지만 이 도메인은 single field 연산을 배선하지 않는다 |
| `model_card` | — | `lookup` | `lookup_bulk_model_card_resource_requirement_owner` | `lookup` | `permission` | `generic` | `W` | **도달 불가 owner lookup** — `field_group()`이 등록하지만 이 도메인은 bulk field 연산을 배선하지 않는다 |
| `model_card` | — | `lookup` | `lookup_model_card_resource_requirement_owner` | `lookup` | `permission` | `generic` | `W` | **도달 불가 owner lookup** — `field_group()`이 등록하지만 이 도메인은 single field 연산을 배선하지 않는다 |

### deployment — 성공 (77행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `deployment` | — | `update` | `activate_revision` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `create` | `add_model_revision` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `delete` | `bulk_delete_access_tokens` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `delete` | `bulk_delete_auto_scaling_rules` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `delete` | `clear_error` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `create` | `create_access_token` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `create` | `create_auto_scaling_rule` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `create` | `create_deployment` | `scope` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `create` | `create_endpoint_auto_scaling_rule` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `create` | `create_legacy_deployment` | `scope` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `delete` | `delete_access_token` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `delete` | `delete_auto_scaling_rule` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `delete` | `delete_endpoint_auto_scaling_rule` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `delete` | `delete_route` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `delete` | `destroy_deployment` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `create` | `dry_run_model_service` | `scope` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `update` | `force_sync` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `create` | `generate_token` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `get` | `get_access_token` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `get` | `get_auto_scaling_rule` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `get` | `get_deployment_by_id` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `get` | `get_deployment_policy` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `get` | `get_legacy_deployment_by_id` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `get` | `get_model_service_info` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `get` | `get_replica_by_id` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `get` | `get_revision_by_id` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `update` | `global_refresh_deployment_revisions` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `global_search_access_tokens` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `global_search_deployments` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `global_search_legacy_deployments` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `global_search_replicas` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `global_search_revisions` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `list_errors` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `list_model_service` | `scope` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `lookup` | `lookup_access_token_deployment` | `lookup` | `permission` | `generic` | `성공` | — |
| `deployment` | — | `lookup` | `lookup_auto_scaling_rule_deployment` | `lookup` | `permission` | `generic` | `성공` | — |
| `deployment` | — | `lookup` | `lookup_revision_deployment` | `lookup` | `permission` | `generic` | `성공` | — |
| `deployment` | — | `lookup` | `lookup_route_deployment` | `lookup` | `permission` | `generic` | `성공` | — |
| `deployment` | — | `update` | `replace_deployment_options` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `update` | `scale_service_replicas` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `scoped_search_replica_group_history` | `scope` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `search_access_tokens` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `search_auto_scaling_rules` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `search_deployment_history` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `search_deployment_policies` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `search_deployment_scoped_history` | `scope` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `search_replicas` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `search_revision_resource_slots` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `search_revisions` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `search_route_history` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `search_route_scoped_history` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `search_routes` | `global` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `search` | `search_services` | `scope` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `update` | `sync_replica` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `update` | `update_auto_scaling_rule` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `update` | `update_deployment` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `update` | `update_endpoint` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `update` | `update_endpoint_auto_scaling_rule` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `update` | `update_route` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `update` | `update_route_traffic_status` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment` | — | `get` | `validate_model_service` | `scope` | `permission` | `custom` | `성공` | — |
| `deployment_preset` | — | `create` | `create_deployment_preset` | `global` | `permission` | `generic` | `성공` | — |
| `deployment_preset` | — | `get` | `get_deployment_preset` | `single_entity` | `permission` | `generic` | `성공` | — |
| `deployment_preset` | — | `search` | `global_search_deployment_presets` | `global` | `permission` | `generic` | `성공` | — |
| `deployment_preset` | — | `purge` | `purge_deployment_preset` | `single_entity` | `permission` | `generic` | `성공` | — |
| `deployment_preset` | — | `update` | `update_deployment_preset` | `single_entity` | `permission` | `custom` | `성공` | — |
| `deployment_preset` | `deployment_preset_resource_slot` | `search` | `search_deployment_preset_resource_slots` | `scope` | `permission` | `generic` | `성공` | — |
| `model_card` | — | `search` | `available_presets` | `global` | `permission` | `custom` | `성공` | — |
| `model_card` | — | `delete` | `bulk_delete_model_card` | `global` | `permission` | `custom` | `성공` | — |
| `model_card` | — | `create` | `create_model_card` | `scope` | `permission` | `generic` | `성공` | — |
| `model_card` | — | `delete` | `delete_model_card` | `single_entity` | `permission` | `custom` | `성공` | — |
| `model_card` | — | `get` | `get_model_card` | `single_entity` | `permission` | `generic` | `성공` | — |
| `model_card` | — | `search` | `global_search_model_cards` | `global` | `permission` | `generic` | `성공` | — |
| `model_card` | — | `create` | `scan_project_model_cards` | `global` | `permission` | `custom` | `성공` | — |
| `model_card` | — | `search` | `search_model_cards_in_project` | `scope` | `permission` | `generic` | `성공` | — |
| `model_card` | — | `update` | `update_model_card` | `single_entity` | `permission` | `custom` | `성공` | — |
| `model_card` | `model_card_resource_requirement` | `search` | `scoped_search_model_card_resource_requirements` | `bulk` | `permission` | `generic` | `성공` | — |

## label

5행 — 실패 1, 성공 4.

### label — 실패 (1행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `global` | `label` | `lookup` | `lookup_bulk_entity_label_owner` | `lookup` | `permission` | `generic` | `W` | **도달 불가 owner lookup** — `field_group()`이 등록하지만 이 도메인은 bulk field 연산을 배선하지 않는다 |

### label — 성공 (4행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `global` | `label` | `lookup` | `lookup_entity_label_owner` | `lookup` | `permission` | `generic` | `성공` | — |
| `global` | `label` | `update` | `purge_entity_label` | `single_entity` | `permission` | `generic` | `성공` | field row 쓰기 — 규칙상 UPDATE가 정답 |
| `global` | `label` | `search` | `search_entity_labels` | `bulk` | `permission` | `generic` | `성공` | — |
| `global` | `label` | `update` | `upsert_entity_label` | `single_entity` | `permission` | `generic` | `성공` | field row 쓰기 — 규칙상 UPDATE가 정답 |

## metric

14행 — 실패 0, 성공 14.

### metric — 실패 (0행)

없음.

### metric — 성공 (14행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `prometheus_query_preset` | — | `create` | `create_prometheus_query_preset` | `global` | `permission` | `custom` | `성공` | — |
| `prometheus_query_preset` | — | `get` | `execute_prometheus_query_preset` | `single_entity` | `permission` | `custom` | `성공` | — |
| `prometheus_query_preset` | — | `get` | `get_prometheus_query_preset` | `single_entity` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `prometheus_query_preset` | — | `get` | `preview_prometheus_query_preset` | `global` | `permission` | `custom` | `성공` | — |
| `prometheus_query_preset` | — | `search` | `public_search_container_metric_metadata` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `prometheus_query_preset` | — | `search` | `public_search_container_metrics` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `prometheus_query_preset` | — | `purge` | `purge_prometheus_query_preset` | `single_entity` | `permission` | `generic` | `성공` | — |
| `prometheus_query_preset` | — | `search` | `search_prometheus_query_presets` | `global` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `prometheus_query_preset` | — | `update` | `update_prometheus_query_preset` | `single_entity` | `permission` | `custom` | `성공` | — |
| `prometheus_query_preset_category` | — | `create` | `create_prometheus_query_preset_category` | `global` | `permission` | `generic` | `성공` | — |
| `prometheus_query_preset_category` | — | `get` | `get_prometheus_query_preset_category` | `single_entity` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `prometheus_query_preset_category` | — | `get` | `public_bulk_get_prometheus_query_preset_categories` | `bulk` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `prometheus_query_preset_category` | — | `purge` | `purge_prometheus_query_preset_category` | `single_entity` | `permission` | `generic` | `성공` | — |
| `prometheus_query_preset_category` | — | `search` | `search_prometheus_query_preset_categories` | `global` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |

## notification_center

13행 — 실패 0, 성공 13.

### notification_center — 실패 (0행)

없음.

### notification_center — 성공 (13행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `notification_channel` | — | `create` | `create_notification_channel` | `global` | `permission` | `generic` | `성공` | — |
| `notification_channel` | — | `get` | `get_notification_channel` | `single_entity` | `permission` | `generic` | `성공` | — |
| `notification_channel` | — | `purge` | `purge_notification_channel` | `single_entity` | `permission` | `generic` | `성공` | — |
| `notification_channel` | — | `search` | `search_notification_channels` | `global` | `permission` | `generic` | `성공` | — |
| `notification_channel` | — | `update` | `update_notification_channel` | `single_entity` | `permission` | `generic` | `성공` | — |
| `notification_channel` | — | `update` | `validate_notification_channel` | `single_entity` | `permission` | `custom` | `성공` | — |
| `notification_rule` | — | `create` | `create_notification_rule` | `global` | `permission` | `generic` | `성공` | — |
| `notification_rule` | — | `get` | `get_notification_rule` | `single_entity` | `permission` | `generic` | `성공` | — |
| `notification_rule` | — | `create` | `process_notification` | `global` | `permission` | `custom` | `성공` | — |
| `notification_rule` | — | `purge` | `purge_notification_rule` | `single_entity` | `permission` | `generic` | `성공` | — |
| `notification_rule` | — | `search` | `search_notification_rules` | `global` | `permission` | `generic` | `성공` | — |
| `notification_rule` | — | `update` | `update_notification_rule` | `single_entity` | `permission` | `generic` | `성공` | — |
| `notification_rule` | — | `update` | `validate_notification_rule` | `single_entity` | `permission` | `custom` | `성공` | — |

## organization

99행 — 실패 6, 성공 93.

### organization — 실패 (6행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `user` | — | `lookup` | `lookup_bulk_error_log_owner` | `lookup` | `permission` | `generic` | `W` | **도달 불가 owner lookup** — `field_group()`이 등록하지만 이 도메인은 bulk field 연산을 배선하지 않는다 |
| `user` | — | `lookup` | `lookup_bulk_keypair_owner` | `lookup` | `permission` | `generic` | `W` | **도달 불가 owner lookup** — `field_group()`이 등록하지만 이 도메인은 bulk field 연산을 배선하지 않는다 |
| `user` | — | `lookup` | `lookup_bulk_login_history_owner` | `lookup` | `permission` | `generic` | `W` | **도달 불가 owner lookup** — `field_group()`이 등록하지만 이 도메인은 bulk field 연산을 배선하지 않는다 |
| `user` | — | `lookup` | `lookup_bulk_login_session_owner` | `lookup` | `permission` | `generic` | `W` | **도달 불가 owner lookup** — `field_group()`이 등록하지만 이 도메인은 bulk field 연산을 배선하지 않는다 |
| `user` | — | `lookup` | `lookup_login_history_owner` | `lookup` | `permission` | `generic` | `W` | **도달 불가 owner lookup** — `field_group()`이 등록하지만 이 도메인은 single field 연산을 배선하지 않는다 |
| `user` | — | `lookup` | `lookup_user_by_access_key` | `lookup` | `permission` | `generic` | `W` | **배선됐지만 호출 안 됨** — 호출자 없음 |

### organization — 성공 (93행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `auth` | — | `create` | `authorize` | `global` | `anonymous` | `custom` | `성공` | anonymous 게이트 — 서비스가 자격 증명을 직접 검사 |
| `auth` | — | `delete` | `global_revoke_login_session` | `global` | `permission` | `custom` | `성공` | — |
| `auth` | — | `update` | `global_unblock_user` | `global` | `permission` | `custom` | `성공` | — |
| `auth` | — | `get` | `public_get_role` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `auth` | — | `get` | `public_resolve_access_key_scope` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `auth` | — | `get` | `public_resolve_user_scope` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `auth` | — | `update` | `update_password_no_auth` | `global` | `anonymous` | `custom` | `성공` | anonymous 게이트 — 서비스가 자격 증명을 직접 검사 |
| `domain` | — | `update` | `create_domain_dotfile` | `single_entity` | `permission` | `custom` | `성공` | — |
| `domain` | — | `delete` | `delete_domain` | `single_entity` | `permission` | `generic` | `성공` | — |
| `domain` | — | `update` | `delete_domain_dotfile` | `single_entity` | `permission` | `custom` | `성공` | — |
| `domain` | — | `get` | `get_domain` | `single_entity` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `domain` | — | `create` | `global_create_domain` | `global` | `permission` | `generic` | `성공` | — |
| `domain` | — | `create` | `global_create_domain_node` | `global` | `permission` | `custom` | `성공` | — |
| `domain` | — | `search` | `global_search_domains` | `global` | `permission` | `generic` | `성공` | — |
| `domain` | — | `lookup` | `lookup_domain` | `lookup` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `domain` | — | `purge` | `purge_domain` | `single_entity` | `permission` | `custom` | `성공` | — |
| `domain` | — | `restore` | `restore_domain` | `single_entity` | `permission` | `generic` | `성공` | soft delete 역전이를 RESTORE로 선언 |
| `domain` | — | `search` | `search_rg_domains` | `global` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `domain` | — | `update` | `update_domain` | `single_entity` | `permission` | `generic` | `성공` | — |
| `domain` | — | `update` | `update_domain_dotfile` | `single_entity` | `permission` | `custom` | `성공` | — |
| `domain` | — | `update` | `update_domain_node` | `single_entity` | `permission` | `custom` | `성공` | — |
| `project` | — | `update` | `assign_users_to_project` | `single_entity` | `permission` | `custom` | `성공` | — |
| `project` | — | `create` | `create_project` | `scope` | `permission` | `generic` | `성공` | — |
| `project` | — | `update` | `create_project_dotfile` | `single_entity` | `permission` | `custom` | `성공` | — |
| `project` | — | `delete` | `delete_project` | `single_entity` | `permission` | `generic` | `성공` | — |
| `project` | — | `update` | `delete_project_dotfile` | `single_entity` | `permission` | `custom` | `성공` | — |
| `project` | — | `get` | `get_project` | `single_entity` | `permission` | `generic` | `성공` | — |
| `project` | — | `search` | `global_search_project_usage_per_month` | `global` | `permission` | `custom` | `성공` | — |
| `project` | — | `search` | `global_search_project_usage_per_period` | `global` | `permission` | `custom` | `성공` | — |
| `project` | — | `search` | `global_search_projects` | `global` | `permission` | `generic` | `성공` | — |
| `project` | — | `lookup` | `lookup_project` | `lookup` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `project` | — | `purge` | `purge_project` | `single_entity` | `permission` | `custom` | `성공` | — |
| `project` | — | `restore` | `restore_project` | `single_entity` | `permission` | `generic` | `성공` | soft delete 역전이를 RESTORE로 선언 |
| `project` | — | `search` | `search_projects_by_domain` | `scope` | `permission` | `generic` | `성공` | — |
| `project` | — | `search` | `search_projects_by_user` | `scope` | `permission` | `generic` | `성공` | — |
| `project` | — | `update` | `unassign_users_from_project` | `single_entity` | `permission` | `custom` | `성공` | — |
| `project` | — | `update` | `update_project` | `single_entity` | `permission` | `custom` | `성공` | — |
| `project` | — | `update` | `update_project_dotfile` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `update` | `admin_create_keypair` | `single_entity` | `permission` | `custom` | `성공` | field row 쓰기 — 규칙상 UPDATE가 정답 |
| `user` | — | `update` | `admin_delete_ssh_keypair` | `single_entity` | `permission` | `custom` | `성공` | field row 쓰기 — 규칙상 UPDATE가 정답 |
| `user` | — | `get` | `admin_get_ssh_keypair` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `update` | `admin_register_ssh_keypair` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `update` | `create_keypair_dotfile` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `create` | `create_user` | `scope` | `permission` | `custom` | `성공` | — |
| `user` | — | `update` | `delete_keypair_dotfile` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `delete` | `delete_user` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `update` | `generate_ssh_keypair` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `get` | `get_bootstrap_script` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `get` | `get_ssh_keypair` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `get` | `get_user` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `get` | `get_user_month_stats` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `create` | `global_create_users` | `global` | `permission` | `custom` | `성공` | — |
| `user` | — | `get` | `global_get_user_month_stats` | `global` | `permission` | `custom` | `성공` | — |
| `user` | — | `purge` | `global_purge_users` | `global` | `permission` | `custom` | `성공` | — |
| `user` | — | `search` | `global_search_keypairs` | `global` | `permission` | `custom` | `성공` | — |
| `user` | — | `search` | `global_search_users` | `global` | `permission` | `generic` | `성공` | — |
| `user` | — | `update` | `global_update_users` | `global` | `permission` | `custom` | `성공` | — |
| `user` | — | `update` | `issue_keypair` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `update` | `logout` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `lookup` | `lookup_error_log_owner` | `lookup` | `permission` | `generic` | `성공` | — |
| `user` | — | `lookup` | `lookup_keypair` | `lookup` | `permission` | `generic` | `성공` | — |
| `user` | — | `lookup` | `lookup_keypair_owner` | `lookup` | `permission` | `generic` | `성공` | — |
| `user` | — | `lookup` | `lookup_keypair_owner_by_access_key` | `lookup` | `permission` | `generic` | `성공` | — |
| `user` | — | `lookup` | `lookup_login_session_owner` | `lookup` | `permission` | `generic` | `성공` | — |
| `user` | — | `lookup` | `lookup_user` | `lookup` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `user` | — | `purge` | `purge_user` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `restore` | `restore_user` | `single_entity` | `permission` | `custom` | `성공` | soft delete 역전이를 RESTORE로 선언 |
| `user` | — | `search` | `search_keypairs` | `scope` | `permission` | `custom` | `성공` | — |
| `user` | — | `search` | `search_users_by_domain` | `scope` | `permission` | `generic` | `성공` | — |
| `user` | — | `search` | `search_users_by_project` | `scope` | `permission` | `generic` | `성공` | — |
| `user` | — | `search` | `search_users_by_role` | `global` | `permission` | `generic` | `성공` | — |
| `user` | — | `delete` | `signout` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `create` | `signup` | `global` | `anonymous` | `custom` | `성공` | anonymous 게이트 — 서비스가 자격 증명을 직접 검사 |
| `user` | — | `update` | `switch_default_access_key` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `update` | `update_bootstrap_script` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `update` | `update_full_name` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `update` | `update_keypair_dotfile` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `update` | `update_password` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `update` | `update_user` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `update` | `upload_ssh_keypair` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | `error_log` | `update` | `create_error_log` | `single_entity` | `permission` | `generic` | `성공` | field row 쓰기 — 규칙상 UPDATE가 정답 |
| `user` | `error_log` | `update` | `delete_error_log` | `single_entity` | `permission` | `generic` | `성공` | field row 쓰기 — 규칙상 UPDATE가 정답 |
| `user` | `error_log` | `search` | `global_search_error_logs` | `global` | `permission` | `generic` | `성공` | — |
| `user` | `error_log` | `search` | `search_error_logs` | `scope` | `permission` | `generic` | `성공` | — |
| `user` | `keypair` | `get` | `get_default_keypairs` | `bulk` | `permission` | `generic` | `성공` | — |
| `user` | `keypair` | `get` | `get_keypair` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | `keypair` | `update` | `purge_keypair` | `single_entity` | `permission` | `custom` | `성공` | field row 쓰기 — 규칙상 UPDATE가 정답 |
| `user` | `keypair` | `update` | `update_keypair` | `single_entity` | `permission` | `custom` | `성공` | field row 쓰기 — 규칙상 UPDATE가 정답 |
| `user` | `login_history` | `search` | `global_search_login_history` | `global` | `permission` | `generic` | `성공` | — |
| `user` | `login_history` | `search` | `search_login_history` | `scope` | `permission` | `generic` | `성공` | — |
| `user` | `login_session` | `search` | `global_search_login_sessions` | `global` | `permission` | `generic` | `성공` | — |
| `user` | `login_session` | `update` | `revoke_login_session` | `single_entity` | `permission` | `custom` | `성공` | field row 쓰기 — 규칙상 UPDATE가 정답 |
| `user` | `login_session` | `search` | `search_login_sessions` | `scope` | `permission` | `generic` | `성공` | — |

## rbac

19행 — 실패 2, 성공 17.

### rbac — 실패 (2행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `role_preset` | — | `lookup` | `lookup_role_permission_preset_owner` | `lookup` | `permission` | `generic` | `W` | **도달 불가 owner lookup** — `field_group()`이 등록하지만 이 도메인은 single field 연산을 배선하지 않는다 |
| `role_preset` | — | `purge` | `purge_role_preset` | `single_entity` | `permission` | `generic` | `W` | **배선됐지만 호출 안 됨** — 호출자 없음. API는 `bulk_purge`만 호출 |

### rbac — 성공 (17행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `entity_invitation` | — | `update` | `accept_entity_invitation` | `scope` | `permission` | `custom` | `성공` | — |
| `entity_invitation` | — | `delete` | `cancel_entity_invitation` | `single_entity` | `permission` | `custom` | `성공` | — |
| `entity_invitation` | — | `create` | `create_entity_invitation` | `scope` | `permission` | `generic` | `성공` | — |
| `entity_invitation` | — | `get` | `get_entity_invitation` | `single_entity` | `permission` | `generic` | `성공` | — |
| `entity_invitation` | — | `update` | `reject_entity_invitation` | `scope` | `permission` | `custom` | `성공` | — |
| `entity_invitation` | — | `search` | `search_entity_invitations` | `scope` | `permission` | `generic` | `성공` | — |
| `role_preset` | — | `delete` | `bulk_delete_role_presets` | `bulk` | `permission` | `generic` | `성공` | — |
| `role_preset` | — | `purge` | `bulk_purge_role_presets` | `bulk` | `permission` | `generic` | `성공` | — |
| `role_preset` | — | `restore` | `bulk_restore_role_presets` | `bulk` | `permission` | `generic` | `성공` | soft delete 역전이를 RESTORE로 선언 |
| `role_preset` | — | `create` | `create_role_preset` | `global` | `permission` | `custom` | `성공` | — |
| `role_preset` | — | `get` | `get_role_preset` | `single_entity` | `permission` | `generic` | `성공` | — |
| `role_preset` | — | `lookup` | `lookup_bulk_role_permission_preset_owner` | `lookup` | `permission` | `generic` | `성공` | — |
| `role_preset` | — | `search` | `search_role_presets` | `global` | `permission` | `generic` | `성공` | — |
| `role_preset` | — | `update` | `update_role_preset` | `single_entity` | `permission` | `custom` | `성공` | — |
| `role_preset` | `role_permission_preset` | `update` | `bulk_add_role_permission_presets` | `single_entity` | `permission` | `generic` | `성공` | field row 쓰기 — 규칙상 UPDATE가 정답 |
| `role_preset` | `role_permission_preset` | `update` | `bulk_remove_role_permission_presets` | `bulk` | `permission` | `generic` | `성공` | — |
| `role_preset` | `role_permission_preset` | `search` | `search_role_permission_presets` | `scope` | `permission` | `generic` | `성공` | — |

## resource_group

77행 — 실패 9, 성공 68.

### resource_group — 실패 (9행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `domain_fair_share` | — | `update` | `bulk_upsert_domain_fair_share_weights` | `scope` | `permission` | `custom` | `O` | **upsert** — UPDATE만 선언(fair_share/actions.py:157,188,305,337,456,489) |
| `domain_fair_share` | — | `update` | `upsert_domain_fair_share_weight` | `scope` | `permission` | `custom` | `O` | **upsert** — UPDATE만 선언(fair_share/actions.py:157,188,305,337,456,489) |
| `global` | `domain_usage_bucket` | `search` | `search_domain_usage_buckets` | `scope` | `permission` | `generic` | `R` | **entity type 불일치** — 카탈로그 `global` / 감사 `domain` |
| `global` | `project_usage_bucket` | `search` | `search_project_usage_buckets` | `scope` | `permission` | `generic` | `R` | **entity type 불일치** — 카탈로그 `global` / 감사 `project` |
| `global` | `user_usage_bucket` | `search` | `search_user_usage_buckets` | `scope` | `permission` | `generic` | `R` | **entity type 불일치** — 카탈로그 `global` / 감사 `user` |
| `project_fair_share` | — | `update` | `bulk_upsert_project_fair_share_weights` | `scope` | `permission` | `custom` | `O` | **upsert** — UPDATE만 선언(fair_share/actions.py:157,188,305,337,456,489) |
| `project_fair_share` | — | `update` | `upsert_project_fair_share_weight` | `scope` | `permission` | `custom` | `O` | **upsert** — UPDATE만 선언(fair_share/actions.py:157,188,305,337,456,489) |
| `user_fair_share` | — | `update` | `bulk_upsert_user_fair_share_weights` | `scope` | `permission` | `custom` | `O` | **upsert** — UPDATE만 선언(fair_share/actions.py:157,188,305,337,456,489) |
| `user_fair_share` | — | `update` | `upsert_user_fair_share_weight` | `scope` | `permission` | `custom` | `O` | **upsert** — UPDATE만 선언(fair_share/actions.py:157,188,305,337,456,489) |

### resource_group — 성공 (68행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `agent` | — | `get` | `get_agent_resource_by_slot` | `single_entity` | `permission` | `custom` | `성공` | — |
| `agent` | — | `get` | `global_get_agent_total_resources` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `agent` | — | `get` | `global_get_agent_watcher_status` | `global` | `permission` | `custom` | `성공` | — |
| `agent` | — | `get` | `global_load_agent_container_counts` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `agent` | — | `update` | `global_recalculate_agent_usage` | `global` | `permission` | `custom` | `성공` | — |
| `agent` | — | `update` | `global_restart_agent` | `global` | `permission` | `custom` | `성공` | — |
| `agent` | — | `search` | `global_search_agent_resources` | `global` | `permission` | `custom` | `성공` | — |
| `agent` | — | `search` | `global_search_agents` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `agent` | — | `update` | `global_start_agent` | `global` | `permission` | `custom` | `성공` | — |
| `agent` | — | `update` | `global_stop_agent` | `global` | `permission` | `custom` | `성공` | — |
| `agent` | — | `update` | `global_sync_agent_registry` | `global` | `permission` | `custom` | `성공` | — |
| `agent` | — | `update` | `global_update_agent_resource_group` | `global` | `permission` | `custom` | `성공` | — |
| `agent` | — | `lookup` | `lookup_agent` | `lookup` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `domain` | — | `get` | `get_domain_usage` | `single_entity` | `permission` | `custom` | `성공` | — |
| `domain_fair_share` | — | `get` | `get_domain_fair_share` | `scope` | `permission` | `custom` | `성공` | — |
| `domain_fair_share` | — | `search` | `global_search_domain_fair_shares` | `global` | `permission` | `custom` | `성공` | — |
| `domain_fair_share` | — | `search` | `search_domain_fair_shares` | `scope` | `permission` | `custom` | `성공` | — |
| `global` | `domain_usage_bucket` | `search` | `global_search_domain_usage_buckets` | `global` | `permission` | `generic` | `성공` | — |
| `global` | `project_usage_bucket` | `search` | `global_search_project_usage_buckets` | `global` | `permission` | `generic` | `성공` | — |
| `global` | `user_usage_bucket` | `search` | `global_search_user_usage_buckets` | `global` | `permission` | `generic` | `성공` | — |
| `project` | — | `get` | `get_project_usage` | `single_entity` | `permission` | `custom` | `성공` | — |
| `project_fair_share` | — | `get` | `get_project_fair_share` | `scope` | `permission` | `custom` | `성공` | — |
| `project_fair_share` | — | `search` | `global_search_project_fair_shares` | `global` | `permission` | `custom` | `성공` | — |
| `project_fair_share` | — | `search` | `search_project_fair_shares` | `scope` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `create` | `associate_resource_group_with_domains` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `create` | `associate_resource_group_with_keypairs` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `create` | `associate_resource_group_with_projects` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `delete` | `disassociate_resource_group_from_domains` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `delete` | `disassociate_resource_group_from_keypairs` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `delete` | `disassociate_resource_group_from_projects` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `get` | `get_allowed_domains_for_resource_group` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `get` | `get_allowed_projects_for_resource_group` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `get` | `get_resource_group_resource_info` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `create` | `global_create_resource_group` | `global` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `get` | `global_get_resource_group_usage` | `global` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `get` | `global_get_wsproxy_version` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `resource_group` | — | `get` | `global_resolve_resource_group_ids` | `global` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `search` | `global_search_resource_groups` | `global` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `lookup` | `lookup_resource_group` | `lookup` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `resource_group` | — | `purge` | `purge_resource_group` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `update` | `replace_resource_group_default_deployment_options` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `update` | `replace_resource_group_default_session_options` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `search` | `scoped_search_resource_groups` | `scope` | `permission` | `generic` | `성공` | — |
| `resource_group` | — | `update` | `update_allowed_domains_for_resource_group` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `update` | `update_allowed_projects_for_resource_group` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `update` | `update_allowed_resource_groups_for_domain` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `update` | `update_allowed_resource_groups_for_project` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `update` | `update_resource_group` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_group` | — | `update` | `update_resource_group_fair_share_spec` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_preset` | — | `search` | `check_preset_availability` | `scope` | `permission` | `custom` | `성공` | — |
| `resource_preset` | — | `delete` | `delete_resource_preset` | `single_entity` | `permission` | `custom` | `성공` | — |
| `resource_preset` | — | `search` | `global_check_resource_presets` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `resource_preset` | — | `create` | `global_create_resource_preset` | `global` | `permission` | `custom` | `성공` | — |
| `resource_preset` | — | `search` | `global_list_resource_presets` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `resource_preset` | — | `search` | `global_search_resource_presets` | `global` | `permission` | `custom` | `성공` | — |
| `resource_preset` | — | `lookup` | `lookup_resource_preset` | `lookup` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `resource_preset` | — | `update` | `update_resource_preset` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `get_domain_resource_overview` | `scope` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `get_effective_allocation` | `scope` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `get_kernel_allocation_by_slot` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `get_project_resource_overview` | `scope` | `permission` | `custom` | `성공` | — |
| `session` | — | `search` | `global_search_resource_allocations` | `global` | `permission` | `custom` | `성공` | — |
| `session` | — | `lookup` | `lookup_kernel_owner` | `lookup` | `permission` | `generic` | `성공` | — |
| `user` | — | `get` | `get_keypair_usage` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user` | — | `get` | `resolve_keypair_context` | `single_entity` | `permission` | `custom` | `성공` | — |
| `user_fair_share` | — | `get` | `get_user_fair_share` | `scope` | `permission` | `custom` | `성공` | — |
| `user_fair_share` | — | `search` | `global_search_user_fair_shares` | `global` | `permission` | `custom` | `성공` | — |
| `user_fair_share` | — | `search` | `search_user_fair_shares` | `scope` | `permission` | `custom` | `성공` | — |

## resource_policy

20행 — 실패 0, 성공 20.

### resource_policy — 실패 (0행)

없음.

### resource_policy — 성공 (20행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `keypair_resource_policy` | — | `get` | `get_keypair_resource_policy` | `single_entity` | `permission` | `generic` | `성공` | — |
| `keypair_resource_policy` | — | `create` | `global_create_keypair_resource_policy` | `global` | `permission` | `generic` | `성공` | — |
| `keypair_resource_policy` | — | `purge` | `global_purge_keypair_resource_policy` | `single_entity` | `permission` | `generic` | `성공` | — |
| `keypair_resource_policy` | — | `search` | `global_search_keypair_resource_policies` | `global` | `permission` | `generic` | `성공` | — |
| `keypair_resource_policy` | — | `lookup` | `lookup_keypair_resource_policy` | `lookup` | `permission` | `generic` | `성공` | — |
| `keypair_resource_policy` | — | `search` | `search_keypair_resource_policies` | `scope` | `permission` | `generic` | `성공` | — |
| `keypair_resource_policy` | — | `update` | `update_keypair_resource_policy` | `single_entity` | `permission` | `generic` | `성공` | — |
| `project_resource_policy` | — | `get` | `get_project_resource_policy` | `single_entity` | `permission` | `generic` | `성공` | — |
| `project_resource_policy` | — | `create` | `global_create_project_resource_policy` | `global` | `permission` | `generic` | `성공` | — |
| `project_resource_policy` | — | `purge` | `global_purge_project_resource_policy` | `single_entity` | `permission` | `generic` | `성공` | — |
| `project_resource_policy` | — | `search` | `global_search_project_resource_policies` | `global` | `permission` | `generic` | `성공` | — |
| `project_resource_policy` | — | `lookup` | `lookup_project_resource_policy` | `lookup` | `permission` | `generic` | `성공` | — |
| `project_resource_policy` | — | `update` | `update_project_resource_policy` | `single_entity` | `permission` | `generic` | `성공` | — |
| `user_resource_policy` | — | `get` | `get_user_resource_policy` | `single_entity` | `permission` | `generic` | `성공` | — |
| `user_resource_policy` | — | `create` | `global_create_user_resource_policy` | `global` | `permission` | `generic` | `성공` | — |
| `user_resource_policy` | — | `purge` | `global_purge_user_resource_policy` | `single_entity` | `permission` | `generic` | `성공` | — |
| `user_resource_policy` | — | `search` | `global_search_user_resource_policies` | `global` | `permission` | `generic` | `성공` | — |
| `user_resource_policy` | — | `lookup` | `lookup_user_resource_policy` | `lookup` | `permission` | `generic` | `성공` | — |
| `user_resource_policy` | — | `search` | `search_user_resource_policies` | `scope` | `permission` | `generic` | `성공` | — |
| `user_resource_policy` | — | `update` | `update_user_resource_policy` | `single_entity` | `permission` | `generic` | `성공` | — |

## session

63행 — 실패 4, 성공 59.

### session — 실패 (4행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `session` | — | `search` | `batch_get_kernel_live_stats` | `bulk` | `permission` | `custom` | `R` | **카탈로그 기록 결함** — `atomic_bulk_field()`가 field_type을 None으로 기록(group.py:241,370). kernel이 field type으로 나타나지 않는다 |
| `session` | — | `search` | `batch_get_kernel_resource_allocation` | `bulk` | `permission` | `custom` | `R` | **카탈로그 기록 결함** — `atomic_bulk_field()`가 field_type을 None으로 기록(group.py:241,370). kernel이 field type으로 나타나지 않는다 |
| `session` | — | `lookup` | `lookup_bulk_kernel_owner` | `lookup` | `permission` | `generic` | `R` | **카탈로그 기록 결함** — `atomic_bulk_field()` 두 번의 배선으로 중복 기록. 카탈로그의 유일한 중복 행 |
| `session` | — | `lookup` | `lookup_bulk_kernel_owner` | `lookup` | `permission` | `generic` | `R` | **카탈로그 기록 결함** — `atomic_bulk_field()` 두 번의 배선으로 중복 기록. 카탈로그의 유일한 중복 행 |

### session — 성공 (59행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `session` | — | `search` | `batch_get_session_resource_allocation` | `bulk` | `permission` | `custom` | `성공` | — |
| `session` | — | `create` | `commit_session` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `update` | `complete` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `compute_schedule` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `session` | — | `update` | `convert_session_to_image` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `create` | `create_cluster` | `scope` | `permission` | `custom` | `성공` | — |
| `session` | — | `create` | `create_from_params` | `scope` | `permission` | `custom` | `성공` | — |
| `session` | — | `create` | `create_from_template` | `scope` | `permission` | `custom` | `성공` | — |
| `session` | — | `delete` | `destroy_session` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `download_file` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `download_files` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `create` | `enqueue_session` | `scope` | `permission` | `custom` | `성공` | — |
| `session` | — | `update` | `exclude_session_idle_checks` | `bulk` | `permission` | `custom` | `성공` | — |
| `session` | — | `update` | `execute_in_stream` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `update` | `execute_session` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `get_abusing_report` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `get_commit_status` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `get_container_logs` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `get_dependency_graph` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `get_direct_access_info` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `get_session` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `get_session_info` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `get_status_history` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `get_streaming_session` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `delete` | `global_gc_stale_stream_connections` | `global` | `permission` | `custom` | `성공` | — |
| `session` | — | `update` | `include_session_idle_checks` | `bulk` | `permission` | `custom` | `성공` | — |
| `session` | — | `update` | `interrupt_in_stream` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `update` | `interrupt_session` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `search` | `list_files` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `lookup` | `lookup_session` | `lookup` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `session` | — | `search` | `match_sessions` | `scope` | `permission` | `custom` | `성공` | — |
| `session` | — | `update` | `rename_session` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `get` | `resolve_session_name` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `update` | `restart_in_stream` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `search` | `search_kernel_history` | `global` | `permission` | `custom` | `성공` | — |
| `session` | — | `search` | `search_kernel_scoped_history` | `scope` | `permission` | `custom` | `성공` | — |
| `session` | — | `search` | `search_kernels` | `scope` | `permission` | `custom` | `성공` | — |
| `session` | — | `search` | `search_session_history` | `global` | `permission` | `custom` | `성공` | — |
| `session` | — | `search` | `search_session_scoped_history` | `scope` | `permission` | `custom` | `성공` | — |
| `session` | — | `search` | `search_sessions` | `scope` | `permission` | `custom` | `성공` | — |
| `session` | — | `search` | `search_sessions_in_project` | `scope` | `permission` | `custom` | `성공` | — |
| `session` | — | `delete` | `shutdown_service` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `create` | `start_service` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `update` | `start_service_in_stream` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `delete` | `terminate_sessions` | `bulk` | `permission` | `custom` | `성공` | — |
| `session` | — | `update` | `track_stream_connection` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `update` | `untrack_stream_connection` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `update` | `update_session` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session` | — | `update` | `upload_files` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session_template` | — | `create` | `create_cluster_template` | `scope` | `permission` | `custom` | `성공` | — |
| `session_template` | — | `create` | `create_task_template` | `scope` | `permission` | `custom` | `성공` | — |
| `session_template` | — | `delete` | `delete_cluster_template` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session_template` | — | `delete` | `delete_task_template` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session_template` | — | `get` | `get_cluster_template` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session_template` | — | `get` | `get_task_template` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session_template` | — | `search` | `list_cluster_templates` | `scope` | `permission` | `custom` | `성공` | — |
| `session_template` | — | `search` | `list_task_templates` | `scope` | `permission` | `custom` | `성공` | — |
| `session_template` | — | `update` | `update_cluster_template` | `single_entity` | `permission` | `custom` | `성공` | — |
| `session_template` | — | `update` | `update_task_template` | `single_entity` | `permission` | `custom` | `성공` | — |

## system

45행 — 실패 0, 성공 45.

### system — 실패 (0행)

없음.

### system — 성공 (45행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `client_ip_masking_policy` | — | `purge` | `purge_client_ip_masking_policy` | `single_entity` | `permission` | `generic` | `성공` | — |
| `client_ip_masking_policy` | — | `search` | `search_client_ip_masking_policies` | `global` | `permission` | `generic` | `성공` | — |
| `client_ip_masking_policy` | — | `upsert` | `upsert_client_ip_masking_policy` | `global` | `permission` | `generic` | `성공` | UPSERT 선언 — 검사가 CREATE\|UPDATE |
| `etcd_config` | — | `delete` | `delete_etcd_config` | `global` | `permission` | `custom` | `성공` | — |
| `etcd_config` | — | `get` | `get_etcd_config` | `global` | `permission` | `custom` | `성공` | — |
| `etcd_config` | — | `get` | `get_resource_metadata` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `etcd_config` | — | `get` | `get_resource_slots` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `etcd_config` | — | `get` | `get_vfolder_types` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `etcd_config` | — | `update` | `set_etcd_config` | `global` | `permission` | `custom` | `성공` | — |
| `login_client_type` | — | `create` | `create_login_client_type` | `global` | `permission` | `generic` | `성공` | — |
| `login_client_type` | — | `get` | `get_login_client_type` | `single_entity` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `login_client_type` | — | `purge` | `purge_login_client_type` | `single_entity` | `permission` | `generic` | `성공` | — |
| `login_client_type` | — | `search` | `search_login_client_types` | `global` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `login_client_type` | — | `update` | `update_login_client_type` | `single_entity` | `permission` | `generic` | `성공` | — |
| `manager_admin` | — | `get` | `fetch_manager_status` | `global` | `permission` | `custom` | `성공` | — |
| `manager_admin` | — | `get` | `get_db_connection_status` | `global` | `permission` | `custom` | `성공` | — |
| `manager_admin` | — | `get` | `get_manager_announcement` | `global` | `permission` | `custom` | `성공` | — |
| `manager_admin` | — | `update` | `perform_scheduler_ops` | `global` | `permission` | `custom` | `성공` | — |
| `manager_admin` | — | `update` | `update_manager_announcement` | `global` | `permission` | `custom` | `성공` | — |
| `manager_admin` | — | `update` | `update_manager_status` | `global` | `permission` | `custom` | `성공` | — |
| `resource_slot_type` | — | `create` | `create_resource_slot_type` | `global` | `permission` | `generic` | `성공` | — |
| `resource_slot_type` | — | `get` | `get_resource_slot_type` | `single_entity` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `resource_slot_type` | — | `lookup` | `lookup_resource_slot_type` | `lookup` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `resource_slot_type` | — | `purge` | `purge_resource_slot_type` | `single_entity` | `permission` | `generic` | `성공` | — |
| `resource_slot_type` | — | `search` | `search_resource_slot_types` | `global` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `resource_slot_type` | — | `update` | `update_resource_slot_type` | `global` | `permission` | `generic` | `성공` | — |
| `retention_policy` | — | `create` | `create_retention_policy` | `global` | `permission` | `generic` | `성공` | — |
| `retention_policy` | — | `purge` | `delete_retention_policy` | `single_entity` | `permission` | `generic` | `성공` | — |
| `retention_policy` | — | `get` | `get_retention_policy` | `single_entity` | `permission` | `generic` | `성공` | — |
| `retention_policy` | — | `purge` | `purge_retention_policy` | `single_entity` | `permission` | `generic` | `성공` | — |
| `retention_policy` | — | `search` | `search_retention_policies` | `global` | `permission` | `generic` | `성공` | — |
| `retention_policy` | — | `update` | `update_retention_policy` | `single_entity` | `permission` | `generic` | `성공` | — |
| `runtime_variant` | — | `create` | `create_runtime_variant` | `global` | `permission` | `generic` | `성공` | — |
| `runtime_variant` | — | `lookup` | `lookup_runtime_variant` | `lookup` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `runtime_variant` | — | `get` | `public_bulk_get_runtime_variants` | `bulk` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `runtime_variant` | — | `get` | `public_get_runtime_variant` | `single_entity` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `runtime_variant` | — | `purge` | `purge_runtime_variant` | `single_entity` | `permission` | `generic` | `성공` | — |
| `runtime_variant` | — | `search` | `search_runtime_variants` | `global` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `runtime_variant` | — | `update` | `update_runtime_variant` | `single_entity` | `permission` | `generic` | `성공` | — |
| `runtime_variant_preset` | — | `create` | `create_runtime_variant_preset` | `global` | `permission` | `generic` | `성공` | — |
| `runtime_variant_preset` | — | `get` | `public_get_runtime_variant_preset` | `single_entity` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `runtime_variant_preset` | — | `purge` | `purge_runtime_variant_preset` | `single_entity` | `permission` | `generic` | `성공` | — |
| `runtime_variant_preset` | — | `search` | `search_runtime_variant_presets` | `global` | `public` | `generic` | `성공` | public 게이트 — 읽기 전용 확인 |
| `runtime_variant_preset` | — | `update` | `update_runtime_variant_preset` | `single_entity` | `permission` | `custom` | `성공` | — |
| `service_catalog` | — | `search` | `search_service_catalogs` | `global` | `permission` | `generic` | `성공` | — |

## vfolder

68행 — 실패 8, 성공 60.

### vfolder — 실패 (8행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `vfolder` | — | `create` | `create_vfolder_upload_session` | `single_entity` | `permission` | `custom` | `O` | **v1/v2 불일치** — CREATE. v2는 UPDATE(file.py:28) |
| `vfolder` | — | `update` | `create_vfolder_upload_session_v2` | `single_entity` | `permission` | `custom` | `O` | **v1/v2 불일치** — UPDATE. v1은 CREATE(upload_session_v2.py:20) |
| `vfolder` | — | `delete` | `delete_vfolder_files` | `single_entity` | `permission` | `custom` | `O` | **v1/v2 불일치** — DELETE=SOFT_DELETE. v2는 UPDATE(file.py:155) |
| `vfolder` | — | `update` | `delete_vfolder_files_v2` | `single_entity` | `permission` | `custom` | `O` | **v1/v2 불일치** — UPDATE. v1은 DELETE=SOFT_DELETE(file_v2.py:103) |
| `vfolder` | — | `search` | `list_vfolder_files` | `single_entity` | `permission` | `custom` | `O` | **v1/v2 불일치** — SEARCH. v2는 GET — 권한은 같고 감사 기록만 다르다(file.py:107) |
| `vfolder` | — | `get` | `list_vfolder_files_v2` | `single_entity` | `permission` | `custom` | `O` | **v1/v2 불일치** — GET. v1은 SEARCH — 권한은 같고 감사 기록만 다르다(file_v2.py:30) |
| `vfolder` | — | `create` | `vfolder_mkdir` | `single_entity` | `permission` | `custom` | `O` | **v1/v2 불일치** — CREATE. v2는 UPDATE(file.py:226) |
| `vfolder` | — | `update` | `vfolder_mkdir_v2` | `single_entity` | `permission` | `custom` | `O` | **v1/v2 불일치** — UPDATE. v1은 CREATE(file_v2.py:55) |

### vfolder — 성공 (60행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `vfolder` | — | `update` | `change_vfolder_ownership` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `create` | `clone_vfolder` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `create` | `clone_vfolder_v2` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `create` | `create_vfolder` | `scope` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `create_vfolder_archive_download_session` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `create_vfolder_download_session` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `create_vfolder_download_session_v2` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `create` | `create_vfolder_in_project` | `scope` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `create` | `create_vfolder_v2` | `scope` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `purge` | `delete_forever_vfolder` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `delete` | `delete_vfolder_files_async` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `delete` | `delete_vfolder_v2` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `purge` | `force_delete_vfolder` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `get_task_logs` | `scope` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `get_vfolder` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `get_vfolder_legacy_row` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `get_vfolder_quota` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `get_vfolder_usage` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `get_vfolder_usage_legacy` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `get_vfolder_used_bytes` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `get_vfolder_v2` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `global_batch_load_vfolders` | `global` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `global_get_fstab_contents` | `global` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `global_get_volume_perf_metric` | `global` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `search` | `global_list_all_hosts` | `global` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `search` | `global_list_allowed_types` | `global` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `search` | `global_list_mounts` | `global` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `update` | `global_mount_host` | `global` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `search` | `global_search_vfolders` | `global` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `update` | `global_umount_host` | `global` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `search` | `list_shared_vfolders` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `search` | `list_vfolder` | `scope` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `lookup` | `lookup_accessible_vfolder` | `lookup` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `lookup` | `lookup_vfolder` | `lookup` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `delete` | `move_to_trash_vfolder` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `update` | `move_vfolder_file` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `update` | `move_vfolder_file_v2` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `search` | `public_list_shared_vfolders` | `global` | `public` | `custom` | `성공` | public 게이트 — 읽기 전용 확인 |
| `vfolder` | — | `purge` | `purge_vfolder` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `purge` | `purge_vfolder_v2` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `update` | `rename_vfolder_file` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `restore` | `restore_vfolder_from_trash` | `single_entity` | `permission` | `custom` | `성공` | soft delete 역전이를 RESTORE로 선언 |
| `vfolder` | — | `search` | `search_hosts` | `scope` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `get` | `search_storage_host_permissions` | `scope` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `search` | `search_user_vfolders` | `scope` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `search` | `search_vfolders_in_project` | `scope` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `update` | `share_vfolder` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `delete` | `unshare_vfolder` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `update` | `update_vfolder_attribute` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `update` | `update_vfolder_quota` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder` | — | `update` | `update_vfolder_sharing_status` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder_invitation` | — | `update` | `accept_invitation` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder_invitation` | — | `create` | `invite_vfolder` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder_invitation` | — | `purge` | `leave_invited_vfolder` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder_invitation` | — | `search` | `list_invitation` | `scope` | `permission` | `custom` | `성공` | — |
| `vfolder_invitation` | — | `search` | `list_sent_invitations` | `scope` | `permission` | `custom` | `성공` | — |
| `vfolder_invitation` | — | `update` | `reject_invitation` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder_invitation` | — | `purge` | `revoke_invited_vfolder` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder_invitation` | — | `update` | `update_invitation` | `single_entity` | `permission` | `custom` | `성공` | — |
| `vfolder_invitation` | — | `update` | `update_invited_vfolder_mount_permission` | `single_entity` | `permission` | `custom` | `성공` | — |

## visibility

13행 — 실패 9, 성공 4.

### visibility — 실패 (9행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `export` | — | `create` | `export_audit_logs_c_s_v` | `global` | `permission` | `custom` | `R` | **action_name 자동 변환** — 클래스명의 `CSV`가 `_c_s_v`로 자동 변환됐다 |
| `export` | — | `create` | `export_keypairs_c_s_v` | `global` | `permission` | `custom` | `R` | **action_name 자동 변환** — 클래스명의 `CSV`가 `_c_s_v`로 자동 변환됐다 |
| `export` | — | `create` | `export_my_keypairs_c_s_v` | `scope` | `permission` | `custom` | `R` | **action_name 자동 변환** — 클래스명의 `CSV`가 `_c_s_v`로 자동 변환됐다 |
| `export` | — | `create` | `export_my_sessions_c_s_v` | `scope` | `permission` | `custom` | `R` | **action_name 자동 변환** — 클래스명의 `CSV`가 `_c_s_v`로 자동 변환됐다 |
| `export` | — | `create` | `export_projects_c_s_v` | `global` | `permission` | `custom` | `R` | **action_name 자동 변환** — 클래스명의 `CSV`가 `_c_s_v`로 자동 변환됐다 |
| `export` | — | `create` | `export_sessions_by_project_c_s_v` | `scope` | `permission` | `custom` | `R` | **action_name 자동 변환** — 클래스명의 `CSV`가 `_c_s_v`로 자동 변환됐다 |
| `export` | — | `create` | `export_sessions_c_s_v` | `global` | `permission` | `custom` | `R` | **action_name 자동 변환** — 클래스명의 `CSV`가 `_c_s_v`로 자동 변환됐다 |
| `export` | — | `create` | `export_users_by_domain_c_s_v` | `scope` | `permission` | `custom` | `R` | **action_name 자동 변환** — 클래스명의 `CSV`가 `_c_s_v`로 자동 변환됐다 |
| `export` | — | `create` | `export_users_c_s_v` | `global` | `permission` | `custom` | `R` | **action_name 자동 변환** — 클래스명의 `CSV`가 `_c_s_v`로 자동 변환됐다 |

### visibility — 성공 (4행)

| entity_type | field_type | operation | action_name | kind | gate | backing | 판정 | 사유 |
|---|---|---|---|---|---|---|---|---|
| `export` | — | `get` | `get_report` | `global` | `permission` | `custom` | `성공` | — |
| `export` | — | `search` | `list_reports` | `global` | `permission` | `custom` | `성공` | — |
| `global` | `audit_log` | `search` | `scoped_search_audit_logs` | `bulk` | `permission` | `generic` | `성공` | — |
| `global` | `audit_log` | `search` | `search_audit_logs` | `global` | `permission` | `generic` | `성공` | — |


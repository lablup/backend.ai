---
name: vfolder-adapter-scenarios
type: reference
description: what the vfolder adapter guarantees, as scenarios; the tests in tests/scenario/bai_scenario/manager/vfolder match these
scope: src/ai/backend/manager/api/adapters/vfolder
keywords: [vfolder, scenario, adapter, rbac, ownership]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
status: draft
---
# 폴더 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다.

개인 폴더는 만든 사람의 스코프에 생긴다. 그래서 폴더를 만들 권한은 그 사용자 자신에게
걸린다. 폴더가 놓일 스토리지 호스트는 도메인과 키페어 정책이 함께 허용해야 한다.

## 만들기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 권한을 받은 사용자가 만든다 | 자기 스코프에 폴더 생성 권한 | 만들기 | 소유가 그 사용자에게 있음 |
| 아무 권한도 받지 않은 사용자가 만든다 | 권한 없음 | 만들기 | 권한 부족으로 거부 |

## 조회

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 폴더를 만든 적 없는 사용자가 자기 것을 본다 | 폴더 없음 | 자기 폴더 조회 | 비어 있음 |

## 아직 적지 않은 것

`admin_search`, `batch_load_by_ids`, `batch_load_fields`, `bulk_delete`, `bulk_purge`,
`clone`, `create_download_session`, `create_in_project`, `create_upload_session`,
`delete`, `delete_files`, `deploy`, `get`, `get_folder_usage`, `list_files`, `mkdir`,
`move_file`, `project_search`, `purge`, `restore`.

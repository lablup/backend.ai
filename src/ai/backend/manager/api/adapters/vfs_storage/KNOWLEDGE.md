---
name: vfs-storage-adapter-scenarios
type: reference
description: what the vfs storage adapter guarantees, as scenarios; update, purge and their partial bulk forms, which only a superadmin passes because the row lives in global alone
scope: src/ai/backend/manager/api/adapters/vfs_storage
keywords: [vfs storage, scenario, adapter, superadmin, purge, partial bulk update, partial bulk purge]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
updated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# vfs_storage 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

VFS storage 행은 global 에만 소속되어 만들어진다. 하나나 여럿을 지정해 수정·purge 하는 호출은
그 행에 부여된 권한을 검사한다. 그 권한은 global 에서만 나오므로 슈퍼관리자만 통과한다.

## 수정

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 기본 경로만 바꾼다 | VFS storage 하나, 슈퍼관리자 | 기본 경로만 지정해 수정 | 기본 경로는 새 값이고 나머지는 그대로인 노드 |
| 슈퍼관리자가 없는 id 를 수정한다 | VFS storage 하나, 슈퍼관리자 | 없는 id 로 수정 | 대상 없음으로 거부 |
| 아무 권한도 받지 않은 사용자가 수정한다 | 같은 VFS storage, 아무 권한 없는 사용자 | 수정 | 권한 부족으로 거부 |

## purge

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 purge 한다 | VFS storage 하나, 슈퍼관리자 | purge | purge 한 VFS storage 의 id |
| 슈퍼관리자가 없는 id 를 purge 한다 | VFS storage 하나, 슈퍼관리자 | 없는 id 로 purge | 대상 없음으로 거부 |
| 아무 권한도 받지 않은 사용자가 purge 한다 | 같은 VFS storage, 아무 권한 없는 사용자 | purge | 권한 부족으로 거부 |

옛 이름의 삭제는 같은 purge 를 부른다.

## 여럿 수정하기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 여럿의 기본 경로를 한 번에 바꾼다 | VFS storage 둘, 슈퍼관리자 | 둘의 기본 경로 수정 | 둘 다 새 기본 경로로 오고 실패한 것은 없음 |
| 아무 권한도 받지 않은 사용자가 여럿을 수정한다 | 같은 VFS storage 둘 | 둘의 기본 경로 수정 | 수정된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

## 여럿 purge

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 둘과 없는 id 하나를 한 번에 purge 한다 | VFS storage 둘, 슈퍼관리자 | 셋 purge | 둘은 purge 된 목록에 오고, 없는 id 는 대상 없음 이유로 실패 목록에 옴 |
| 아무 권한도 받지 않은 사용자가 여럿을 purge 한다 | 같은 VFS storage 둘 | 둘 purge | purge 된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 VFS storage 는 처리된 목록에, 처리하지 못한 것은
id 와 이유를 실패 목록에 싣는다.

## 아직 적지 않은 것

| 호출 | 이유 |
|---|---|
| 생성, id 조회, id 여럿 조회, 전체 목록, 전역 검색 | 이름 정리 작업의 범위 밖이다 |
